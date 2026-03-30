import chromadb
from sentence_transformers import SentenceTransformer
from typing import Optional

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=".chroma")
collection = client.get_or_create_collection("messages")

def add_to_memory(message_id: str, text: str, url: str) -> None:
    embedding = model.encode(text).tolist()
    collection.add(
        ids=[message_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"url": url}]
    )

def search_similar(text: str, threshold: float = 0.50) -> Optional[str]:
    if collection.count() == 0:
        return None
    
    embedding = model.encode(text).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results = 1
    )

    if not results["distances"][0]:
        return None
    
    distance = results["distances"][0][0]
    similarity = 1 - distance

    if similarity >= threshold:
        return {
            "text": results["documents"][0][0],
            "notion": results["metadatas"][0][0]["url"]
        }
    
    return None