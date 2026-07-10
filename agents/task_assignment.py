"""
task_assignment.py
--------------------
Agent 4: Task Assignment Agent

Job: Take the raw action items (from action_items.py) and enrich each
one with a PRIORITY level (High / Medium / Low), based on the language
used and urgency implied in the transcript. This turns a plain to-do
list into something a project-management tool (Jira/Trello style) can use.
"""

import json
from agents.llm_client import call_llm_json

SYSTEM_PROMPT = """You are a task-prioritization agent.
You will receive a JSON list of action items extracted from a meeting.
For each item, decide a priority: "High", "Medium", or "Low", based on
urgency words (e.g. "urgent", "ASAP", "critical", "blocker") or how soon
the deadline is.

Return the SAME JSON array, with an added "priority" field per item:
[
  {"employee": "Bob", "task": "Update backend API", "deadline": "Friday", "priority": "High"}
]
"""


def assign_priority(action_items: list) -> list:
    """Adds a 'priority' field to each action item dict."""
    if not action_items:
        return []
    user_prompt = f"Action items:\n\n{json.dumps(action_items)}"
    raw_output = call_llm_json(SYSTEM_PROMPT, user_prompt)
    try:
        prioritized = json.loads(raw_output)
        if isinstance(prioritized, list):
            return prioritized
    except json.JSONDecodeError:
        pass
    # Fallback: default everything to Medium priority rather than losing data
    for item in action_items:
        item.setdefault("priority", "Medium")
    return action_items
