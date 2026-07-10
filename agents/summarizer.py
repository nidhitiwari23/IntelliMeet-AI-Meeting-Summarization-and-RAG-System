"""
summarizer.py
--------------
Agent 1: Meeting Summarizer

Job: Read the raw transcript (which has filler words, interruptions,
"um"s, cross-talk, etc.) and produce a clean, concise summary that a
manager could read in 20 seconds.
"""

from agents.llm_client import call_llm

SYSTEM_PROMPT = """You are an expert meeting-minutes writer.
You will receive a raw, messy meeting transcript.
Produce a clean, professional summary of what was discussed.

Rules:
- Remove filler words and small talk.
- Group the discussion into key topics.
- Keep it under 150 words.
- Do not invent information that is not in the transcript.
- Write in plain, simple business English.
"""


def summarize_meeting(transcript: str) -> str:
    """Returns a short professional summary of the transcript."""
    user_prompt = f"Meeting transcript:\n\n{transcript}\n\nWrite the summary now."
    return call_llm(SYSTEM_PROMPT, user_prompt)
