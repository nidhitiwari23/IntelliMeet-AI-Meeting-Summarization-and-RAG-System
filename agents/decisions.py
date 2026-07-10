"""
decisions.py
-------------
Agent 2: Decision Extraction Agent

Job: Scan the transcript for sentences that represent a DECISION being
made (as opposed to just discussion/opinion), e.g.:
    "We have decided to launch on August 10"
    "Let's finalize the new pricing"
    "I think we should go with option B" (when followed by agreement)

Output: a JSON list of decisions, so it can be stored in the database
and displayed as a clean bullet list.
"""

import json
from agents.llm_client import call_llm_json

SYSTEM_PROMPT = """You are a decision-extraction agent for meeting transcripts.
Read the transcript and identify every concrete DECISION the team made
(not just topics discussed, and not action items assigned to a single person).

Return a JSON array like this:
[
  {"description": "UI redesign approved"},
  {"description": "Backend optimization approved"}
]

If no clear decisions were made, return an empty array: []
"""


def extract_decisions(transcript: str) -> list:
    """Returns a list of dicts: [{"description": "..."}, ...]"""
    user_prompt = f"Transcript:\n\n{transcript}"
    raw_output = call_llm_json(SYSTEM_PROMPT, user_prompt)
    try:
        decisions = json.loads(raw_output)
        if isinstance(decisions, list):
            return decisions
    except json.JSONDecodeError:
        pass
    # Fallback: if the model didn't return clean JSON, don't crash the pipeline
    return []
