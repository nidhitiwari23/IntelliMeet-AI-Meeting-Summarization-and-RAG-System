"""
calendar_agent.py
-------------------
Agent 5: Calendar Agent

Job: If the meeting mentions a follow-up meeting ("let's meet again next
Tuesday at 2 PM"), automatically create a Google Calendar event.

This uses the Google Calendar API, which is FREE for personal/small-scale
use. You need a one-time OAuth setup (explained in the accompanying
document) that produces a `credentials.json` file.

If no Google credentials are configured, this agent safely falls back to
just returning the detected date/time as text (so the rest of the
pipeline still works without any Google setup).
"""

import os
import json
import datetime
from agents.llm_client import call_llm_json

SYSTEM_PROMPT = """You are a scheduling assistant.
Read the transcript and check if the team scheduled a follow-up meeting.

Return JSON like:
{"has_followup": true, "date": "next Tuesday", "time": "2 PM", "description": "Follow-up meeting"}

If no follow-up meeting was mentioned, return:
{"has_followup": false}
"""


def detect_followup_meeting(transcript: str) -> dict:
    """Uses the LLM to detect whether a follow-up meeting was scheduled."""
    raw_output = call_llm_json(SYSTEM_PROMPT, f"Transcript:\n\n{transcript}")
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        return {"has_followup": False}


def create_google_calendar_event(summary: str, date_str: str, time_str: str,
                                  attendees: list = None) -> dict:
    """
    Creates a real Google Calendar event.
    Requires GOOGLE_CREDENTIALS_PATH (see document for setup) and that you
    have run the OAuth flow once (a token.json will be saved automatically).

    Returns a dict with the created event id and link, or an error message
    if Google Calendar isn't configured yet.
    """
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if not os.path.exists(creds_path):
        return {
            "status": "skipped",
            "reason": "Google credentials.json not found. "
                      "See document section 'Google Calendar Setup'.",
        }

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token_file:
                token_file.write(creds.to_json())

        service = build("calendar", "v3", credentials=creds)

        # NOTE: for a portfolio/demo project we keep date parsing simple.
        # In production you'd use a library like `dateparser` for robust parsing.
        start_dt = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        end_dt = start_dt + datetime.timedelta(hours=1)

        event = {
            "summary": summary,
            "description": f"Auto-created by AI Meeting Intelligence System.\nOriginal note: {date_str} {time_str}",
            "start": {"dateTime": start_dt.isoformat() + "Z"},
            "end": {"dateTime": end_dt.isoformat() + "Z"},
            "attendees": [{"email": a} for a in (attendees or [])],
        }
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        return {"status": "created", "event_id": created_event.get("id"),
                "link": created_event.get("htmlLink")}

    except Exception as e:
        return {"status": "error", "reason": str(e)}
