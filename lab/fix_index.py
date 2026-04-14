"""
fix_index.py — Copy data from rag_lab collection to day09_docs collection.
The index.py script indexed into 'rag_lab' but retrieval.py queries 'day09_docs'.
"""
import chromadb
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

db = chromadb.PersistentClient(path="./chroma_db")

# Check current state
print("=== Current Collections ===")
for c in db.list_collections():
    print(f"  {c.name}: {c.count()} docs")

# Get data from rag_lab
rag_lab = db.get_collection("rag_lab")
all_data = rag_lab.get(include=["documents", "metadatas", "embeddings"])
total = len(all_data["ids"])
print(f"\nFound {total} chunks in rag_lab")

# Delete and recreate day09_docs
try:
    db.delete_collection("day09_docs")
    print("Deleted old day09_docs collection")
except:
    pass

collection = db.create_collection("day09_docs", metadata={"hnsw:space": "cosine"})

# Fix source metadata: extract just filename from full path
for i in range(total):
    meta = all_data["metadatas"][i]
    source = meta.get("source", "")
    if "\\" in source or "/" in source:
        meta["source"] = Path(source).name

# Copy all data
collection.add(
    ids=all_data["ids"],
    documents=all_data["documents"],
    metadatas=all_data["metadatas"],
    embeddings=all_data["embeddings"],
)

print(f"Copied {total} chunks to day09_docs")
print(f"day09_docs now has {collection.count()} chunks")

# Verify with test query
print("\n=== Verification ===")
from openai import OpenAI
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
test_emb = client_ai.embeddings.create(input="SLA ticket P1", model="text-embedding-3-small").data[0].embedding

results = collection.query(query_embeddings=[test_emb], n_results=3, include=["documents", "metadatas"])
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"  [{meta.get('source')}] {doc[:100]}...")

print("\n✅ Index fix complete!")
