"""
action_items.py
----------------
Agent 3: Action Item Agent

Job: Find every commitment / promise made by a specific person, e.g.
    "Bob, can you update authentication by Friday?"
    "I'll prepare the testing documents."

Output: JSON list with employee, task, and deadline (deadline defaults
to "Not specified" if nobody mentioned one).
"""

import json
from agents.llm_client import call_llm_json

SYSTEM_PROMPT = """You are an action-item extraction agent for meeting transcripts.
Find every task that a specific person committed to doing.

Return a JSON array like this:
[
  {"employee": "Bob", "task": "Update backend API", "deadline": "Friday"},
  {"employee": "Charlie", "task": "Prepare testing documents", "deadline": "Monday"}
]

Rules:
- "employee" must be a name mentioned in the transcript, never "someone" or "team".
- If no deadline was mentioned, set deadline to "Not specified".
- If no action items exist, return an empty array: []
"""


def extract_action_items(transcript: str) -> list:
    """Returns a list of dicts: [{"employee","task","deadline"}, ...]"""
    user_prompt = f"Transcript:\n\n{transcript}"
    raw_output = call_llm_json(SYSTEM_PROMPT, user_prompt)
    try:
        items = json.loads(raw_output)
        if isinstance(items, list):
            return items
    except json.JSONDecodeError:
        pass
    return []
