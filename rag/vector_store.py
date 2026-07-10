"""
vector_store.py
------------------
Sets up a FREE, local vector database using ChromaDB, with FREE local
embeddings from sentence-transformers (no OpenAI API key needed).

Every meeting transcript gets split into chunks and stored here so we
can later ask natural-language questions like "What did Bob promise
last month?" and retrieve the relevant chunks (this is RAG = Retrieval
Augmented Generation).
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")

# Free local embedding model - runs on CPU, no API cost.
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(
    name="meeting_transcripts", embedding_function=_embedding_fn
)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Splits long transcript text into overlapping chunks for better retrieval."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks


def add_meeting_to_vector_store(meeting_id: int, title: str, transcript: str, date: str):
    """Splits the transcript into chunks and stores each chunk with metadata."""
    chunks = chunk_text(transcript)
    ids = [f"meeting-{meeting_id}-chunk-{i}" for i in range(len(chunks))]
    metadatas = [{"meeting_id": meeting_id, "title": title, "date": date} for _ in chunks]
    _collection.add(documents=chunks, ids=ids, metadatas=metadatas)


def search_meetings(query: str, top_k: int = 5) -> list:
    """
    Searches across ALL stored meetings for chunks relevant to the query.
    Returns a list of {"text":..., "meeting_id":..., "title":..., "date":...}
    """
    results = _collection.query(query_texts=[query], n_results=top_k)
    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append({
            "text": doc,
            "meeting_id": meta.get("meeting_id"),
            "title": meta.get("title"),
            "date": meta.get("date"),
        })
    return output
