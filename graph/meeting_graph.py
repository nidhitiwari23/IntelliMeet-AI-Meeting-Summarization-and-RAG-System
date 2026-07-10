"""
meeting_graph.py
------------------
This is the heart of the project: a LangGraph workflow ("state graph")
that runs the Summary, Decision, and Action-Item agents, then feeds
their outputs into Task Assignment, Calendar, and Email agents.

WHY LANGGRAPH?
    A plain Python script would run everything one line after another.
    LangGraph instead models the work as a GRAPH of nodes that share a
    common "state" object. This makes it easy to:
      - Run independent agents in parallel (summary + decisions + actions
        don't depend on each other, so they could run concurrently)
      - Add new agents later without rewriting existing ones
      - Visualize and debug the flow of information

STATE:
    A single Python dict (typed with TypedDict) is passed between every
    node. Each agent reads what it needs from the state and writes its
    own output back into the state.
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from agents.summarizer import summarize_meeting
from agents.decisions import extract_decisions
from agents.action_items import extract_action_items
from agents.task_assignment import assign_priority
from agents.calendar_agent import detect_followup_meeting, create_google_calendar_event
from agents.email_agent import generate_email_body, send_email, send_slack_message


class MeetingState(TypedDict, total=False):
    transcript: str
    title: str
    attendee_emails: List[str]
    summary: str
    decisions: List[Dict[str, Any]]
    action_items: List[Dict[str, Any]]
    followup_meeting: Dict[str, Any]
    calendar_result: Dict[str, Any]
    email_body: str
    email_result: Dict[str, Any]
    slack_result: Dict[str, Any]


# ---------- Node functions ----------
# Each node takes the current state, does its job, and returns the
# fields it wants to UPDATE in that state (LangGraph merges them in).

def node_summarize(state: MeetingState) -> dict:
    return {"summary": summarize_meeting(state["transcript"])}


def node_decisions(state: MeetingState) -> dict:
    return {"decisions": extract_decisions(state["transcript"])}


def node_action_items(state: MeetingState) -> dict:
    return {"action_items": extract_action_items(state["transcript"])}


def node_task_assignment(state: MeetingState) -> dict:
    return {"action_items": assign_priority(state.get("action_items", []))}


def node_calendar(state: MeetingState) -> dict:
    followup = detect_followup_meeting(state["transcript"])
    result = {"followup_meeting": followup}
    if followup.get("has_followup"):
        calendar_result = create_google_calendar_event(
            summary=f"Follow-up: {state.get('title', 'Meeting')}",
            date_str=followup.get("date", ""),
            time_str=followup.get("time", ""),
            attendees=state.get("attendee_emails", []),
        )
        result["calendar_result"] = calendar_result
    return result


def node_email(state: MeetingState) -> dict:
    body = generate_email_body(
        state.get("summary", ""),
        state.get("decisions", []),
        state.get("action_items", []),
    )
    result = {"email_body": body}
    if state.get("attendee_emails"):
        result["email_result"] = send_email(
            subject=f"Meeting Minutes: {state.get('title', 'Meeting')}",
            body=body,
            to_addresses=state["attendee_emails"],
        )
    result["slack_result"] = send_slack_message(body)
    return result


# ---------- Build the graph ----------

def build_meeting_graph():
    """
    Builds and compiles the LangGraph workflow.

    Flow:
        START -> summarize -> decisions -> action_items -> task_assignment
              -> calendar -> email -> END

    (For simplicity this project runs nodes sequentially; in a larger
    production system, summarize/decisions/action_items could branch
    out from a single entry node and run in parallel, then join before
    task_assignment - LangGraph supports this with add_edge from one
    node to multiple nodes.)
    """
    graph = StateGraph(MeetingState)

    graph.add_node("summary_agent", node_summarize)
    graph.add_node("decision_agent", node_decisions)
    graph.add_node("action_item_agent", node_action_items)
    graph.add_node("task_assignment_agent", node_task_assignment)
    graph.add_node("calendar_agent", node_calendar)
    graph.add_node("email_agent", node_email)

    graph.set_entry_point("summary_agent")

    graph.add_edge("summary_agent", "decision_agent")
    graph.add_edge("decision_agent", "action_item_agent")
    graph.add_edge("action_item_agent", "task_assignment_agent")
    graph.add_edge("task_assignment_agent", "calendar_agent")
    graph.add_edge("calendar_agent", "email_agent")
    graph.add_edge("email_agent", END)

    return graph.compile()


def run_meeting_pipeline(transcript: str, title: str = "Untitled Meeting",
                          attendee_emails: list = None) -> dict:
    """
    Convenience function: builds the graph and runs it once on a transcript.
    Returns the final state dict containing summary, decisions, action
    items, calendar result, and email result.
    """
    app = build_meeting_graph()
    initial_state: MeetingState = {
        "transcript": transcript,
        "title": title,
        "attendee_emails": attendee_emails or [],
    }
    final_state = app.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    sample_transcript = """
    Alice: I think the UI needs a complete redesign before launch.
    Bob: Agreed. I can update the backend API by Friday.
    Charlie: I'll prepare the testing documents by Monday.
    Manager: Great, let's finalize the UI redesign and meet again next Tuesday at 2 PM.
    """
    result = run_meeting_pipeline(sample_transcript, title="Product Sync")
    import json
    print(json.dumps(result, indent=2, default=str))
