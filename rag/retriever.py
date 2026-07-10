"""
retriever.py
--------------
Agent 7: RAG Agent (Meeting Memory)

Job: Answer natural-language questions about past meetings, e.g.
    "Did we discuss Kubernetes before?"
    "What did Bob promise last month?"

How it works:
    1. Search the vector store (rag/vector_store.py) for the most
       relevant transcript chunks to the question.
    2. Feed those chunks + the question to the LLM.
    3. The LLM answers ONLY using the retrieved chunks (reduces
       hallucination) and cites which meeting/date the info came from.
"""

from agents.llm_client import call_llm
from rag.vector_store import search_meetings

SYSTEM_PROMPT = """You are a meeting-memory assistant.
You will be given a question and several transcript excerpts from past
meetings, each labelled with its meeting title and date.

Answer the question using ONLY the information in these excerpts.
If the excerpts don't contain the answer, say so honestly - do not guess.
Always mention which meeting/date your answer came from.
"""


def ask_about_past_meetings(question: str) -> str:
    """Full RAG pipeline: retrieve relevant chunks, then answer with the LLM."""
    chunks = search_meetings(question, top_k=5)
    if not chunks:
        return "I don't have any stored meetings that relate to this question yet."

    context = "\n\n".join(
        f"[Meeting: {c['title']} | Date: {c['date']}]\n{c['text']}" for c in chunks
    )
    user_prompt = f"Question: {question}\n\nRelevant excerpts:\n\n{context}"
    return call_llm(SYSTEM_PROMPT, user_prompt)
