"""
workers/policy_tool.py — Policy & Tool Worker
Sprint 2+3: Kiểm tra policy dựa vào context, gọi MCP tools khi cần.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: context từ retrieval_worker
    - needs_tool: True nếu supervisor quyết định cần tool call

Output (vào AgentState):
    - policy_result: {"policy_applies", "policy_name", "exceptions_found", "source", "rule"}
    - mcp_tools_used: list of tool calls đã thực hiện
    - worker_io_log: log

Gọi độc lập để test:
    python workers/policy_tool.py
"""

import os
import sys
from typing import Optional

WORKER_NAME = "policy_tool_worker"


# ─────────────────────────────────────────────
# MCP Client — Sprint 3: Thay bằng real MCP call
# ─────────────────────────────────────────────

def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Gọi MCP tool.

    Sprint 3 Bonus: Gọi qua HTTP server thực tế nếu đang chạy.
    Fallback: Import trực tiếp từ mcp_server.py (trong-process mock).
    """
    from datetime import datetime
    import requests

    result = None
    try:
        # Thử gọi qua HTTP MCP Server (Sprint 3 Bonus)
        resp = requests.post(
            "http://localhost:8000/tools/call",
            json={"tool_name": tool_name, "tool_input": tool_input},
            timeout=2
        )
        if resp.status_code == 200:
            result = resp.json()
    except requests.exceptions.RequestException:
        # Fallback về in-process nếu MCP HTTP server không bật
        result = None

    if result is None:
        try:
            from mcp_server import dispatch_tool
            result = dispatch_tool(tool_name, tool_input)
        except Exception as e:
            return {
                "tool": tool_name,
                "input": tool_input,
                "output": None,
                "error": {"code": "MCP_CALL_FAILED", "reason": str(e)},
                "timestamp": datetime.now().isoformat(),
            }

    return {
        "tool": tool_name,
        "input": tool_input,
        "output": result,
        "error": None,
        "timestamp": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────
# Policy Analysis Logic
# ─────────────────────────────────────────────

def analyze_policy(task: str, chunks: list) -> dict:
    """
    Phân tích policy bằng cách kết hợp Rule-based và LLM reasoning.
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    task_lower = task.lower()
    context_text = "\n".join([f"- {c.get('text', '')} (Nguồn: {c.get('source', 'unknown')})" for c in chunks])

    # 1. Rule-based detection (quick check)
    exceptions_found = []
    if "flash sale" in task_lower or "flash sale" in context_text.lower():
        exceptions_found.append({"type": "flash_sale_exception", "rule": "Flash Sale không hoàn tiền.", "source": "policy_refund_v4.txt"})
    if any(kw in task_lower for kw in ["license key", "license", "subscription"]):
        exceptions_found.append({"type": "digital_product_exception", "rule": "Sản phẩm kỹ thuật số không hoàn tiền.", "source": "policy_refund_v4.txt"})

    # 2. LLM Analysis for complex reasoning
    try:
        prompt = f"""Bạn là chuyên gia phân tích chính sách nội bộ.
Dựa vào các đoạn văn bản (context) dưới đây, hãy xác định câu hỏi của người dùng có vi phạm chính sách nào không.

Câu hỏi: {task}

Context:
{context_text}

Yêu cầu output dạng JSON:
{{
  "policy_applies": boolean,
  "policy_name": string,
  "exceptions_found": [{{ "type": string, "rule": string, "source": string }}],
  "policy_version_note": string,
  "explanation": string
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Trả lời dưới dạng JSON nguyên bản."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        result = json.loads(response.choices[0].message.content)

        # Merge rule-based exceptions if not already present
        for ex in exceptions_found:
            if not any(e['type'] == ex['type'] for e in result.get('exceptions_found', [])):
                result.setdefault('exceptions_found', []).append(ex)

        result["source"] = list({c.get("source", "unknown") for c in chunks if c})
        return result

    except Exception as e:
        print(f"⚠️  LLM Policy Analysis failed: {e}")
        # Fallback to rule-based only
        return {
            "policy_applies": len(exceptions_found) == 0,
            "policy_name": "refund_policy_v4 (fallback)",
            "exceptions_found": exceptions_found,
            "source": list({c.get("source", "unknown") for c in chunks if c}),
            "policy_version_note": "",
            "explanation": f"Fallback to rule-based check due to error: {e}",
        }


# ─────────────────────────────────────────────
# Worker Entry Point
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState với policy_result và mcp_tools_used
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "needs_tool": needs_tool,
        },
        "output": None,
        "error": None,
    }

    try:
        # Step 1: Nếu chưa có chunks, gọi MCP search_kb
        if not chunks and needs_tool:
            mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP search_kb")

            if mcp_result.get("output") and mcp_result["output"].get("chunks"):
                chunks = mcp_result["output"]["chunks"]
                state["retrieved_chunks"] = chunks

        # Step 2: Phân tích policy
        policy_result = analyze_policy(task, chunks)
        state["policy_result"] = policy_result

        # Step 3: Nếu cần thêm info từ MCP (e.g., ticket status), gọi get_ticket_info
        if needs_tool and any(kw in task.lower() for kw in ["ticket", "p1", "jira"]):
            mcp_result = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP get_ticket_info")

        worker_io["output"] = {
            "policy_applies": policy_result["policy_applies"],
            "exceptions_count": len(policy_result.get("exceptions_found", [])),
            "mcp_calls": len(state["mcp_tools_used"]),
        }
        state["history"].append(
            f"[{WORKER_NAME}] policy_applies={policy_result['policy_applies']}, "
            f"exceptions={len(policy_result.get('exceptions_found', []))}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "POLICY_CHECK_FAILED", "reason": str(e)}
        state["policy_result"] = {"error": str(e)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Policy Tool Worker — Standalone Test")
    print("=" * 50)

    test_cases = [
        {
            "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
            "retrieved_chunks": [
                {"text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.9}
            ],
        },
        {
            "task": "Khách hàng muốn hoàn tiền license key đã kích hoạt.",
            "retrieved_chunks": [
                {"text": "Sản phẩm kỹ thuật số (license key, subscription) không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.88}
            ],
        },
        {
            "task": "Khách hàng yêu cầu hoàn tiền trong 5 ngày, sản phẩm lỗi, chưa kích hoạt.",
            "retrieved_chunks": [
                {"text": "Yêu cầu trong 7 ngày làm việc, sản phẩm lỗi nhà sản xuất, chưa dùng.", "source": "policy_refund_v4.txt", "score": 0.85}
            ],
        },
    ]

    for tc in test_cases:
        print(f"\n▶ Task: {tc['task'][:70]}...")
        result = run(tc.copy())
        pr = result.get("policy_result", {})
        print(f"  policy_applies: {pr.get('policy_applies')}")
        if pr.get("exceptions_found"):
            for ex in pr["exceptions_found"]:
                print(f"  exception: {ex['type']} — {ex['rule'][:60]}...")
        print(f"  MCP calls: {len(result.get('mcp_tools_used', []))}")

    print("\n✅ policy_tool_worker test done.")
