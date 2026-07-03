"""
Setup script to create and populate a vector database with the knowledge base.
Uses sentence-transformers for embeddings.
"""
import pickle
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

with open("knowledge_base.md", "r", encoding="utf-8") as f:
    knowledge_base = f.read()

chunks = []
current_doc = ""
lines = knowledge_base.split("\n")

for line in lines:
    if line.startswith("## Document"):
        if current_doc:
            chunks.append(current_doc.strip())
        current_doc = line + "\n"
    elif line.startswith("###") or line.startswith("Q:"):
        if current_doc:
            chunks.append(current_doc.strip())
        current_doc = line + "\n"
    else:
        current_doc += line + "\n"

if current_doc:
    chunks.append(current_doc.strip())

embeddings = model.encode(chunks)

vector_db = {
    'chunks': chunks,
    'embeddings': embeddings,
    'model_name': 'all-MiniLM-L6-v2'
}

with open('vector_db.pkl', 'wb') as f:
    pickle.dump(vector_db, f)

print(f"Saved {len(chunks)} chunks to vector_db.pkl")
