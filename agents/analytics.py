"""
analytics.py
--------------
Agent 8: Analytics Agent

Job: Provide light-weight insights about a meeting or across all stored
meetings: most active speaker, common topics, repeated action items, etc.

This is intentionally kept simple (rule-based + one LLM call) so it runs
fast and free, without needing extra infrastructure.
"""

from collections import Counter
from agents.llm_client import call_llm

SYSTEM_PROMPT = """You are a meeting analytics agent.
Given a transcript, identify:
- The most actively speaking person (roughly, by line count / content)
- 3-5 key topics discussed
- The overall sentiment (Positive, Neutral, or Tense)

Answer in short plain-text bullet points.
"""


def speaker_line_counts(transcript: str) -> dict:
    """
    Very simple heuristic: counts lines per speaker assuming transcript
    lines are formatted as "SpeakerName: text".
    Works with the output of speech/diarization.py.
    """
    counts = Counter()
    for line in transcript.splitlines():
        if ":" in line:
            speaker = line.split(":", 1)[0].strip()
            if speaker:
                counts[speaker] += 1
    return dict(counts)


def generate_insights(transcript: str) -> str:
    """Uses the LLM to produce a short qualitative analytics summary."""
    return call_llm(SYSTEM_PROMPT, f"Transcript:\n\n{transcript}")
