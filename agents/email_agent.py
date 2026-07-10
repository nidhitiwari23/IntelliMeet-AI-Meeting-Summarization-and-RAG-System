"""
email_agent.py
----------------
Agent 6: Email / Slack Notification Agent

Job: Turn the summary + decisions + action items into a professional
"meeting minutes" email, and optionally post the same content to Slack.

Email sending uses Gmail's free SMTP relay with an "App Password"
(explained in the document) - no paid API needed.
Slack uses a free Incoming Webhook URL.
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from agents.llm_client import call_llm

SYSTEM_PROMPT = """You write professional meeting-minutes emails.
Given a summary, a list of decisions, and a list of action items,
write a short, friendly, professional email to the team.

Format:
Hello Team,

<2-3 sentence summary>

Decisions:
- ...

Action Items:
- Person - Task (Deadline)

Thanks,
AI Meeting Assistant
"""


def generate_email_body(summary: str, decisions: list, action_items: list) -> str:
    """Uses the LLM to draft the email body text."""
    decisions_text = "\n".join(f"- {d.get('description','')}" for d in decisions) or "None"
    tasks_text = "\n".join(
        f"- {t.get('employee','?')} - {t.get('task','')} ({t.get('deadline','Not specified')})"
        for t in action_items
    ) or "None"

    user_prompt = (
        f"Summary:\n{summary}\n\nDecisions:\n{decisions_text}\n\nAction Items:\n{tasks_text}"
    )
    return call_llm(SYSTEM_PROMPT, user_prompt)


def send_email(subject: str, body: str, to_addresses: list) -> dict:
    """
    Sends the email via Gmail SMTP using an App Password.
    Requires the following environment variables:
        GMAIL_SENDER_ADDRESS
        GMAIL_APP_PASSWORD   (16-character app password, NOT your normal password)
    """
    sender = os.getenv("GMAIL_SENDER_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender or not app_password:
        return {"status": "skipped", "reason": "Gmail credentials not set in .env"}

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(to_addresses)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, to_addresses, msg.as_string())
        return {"status": "sent"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def send_slack_message(text: str) -> dict:
    """Posts a message to Slack using a free Incoming Webhook URL."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "skipped", "reason": "SLACK_WEBHOOK_URL not set in .env"}
    try:
        response = requests.post(webhook_url, json={"text": text}, timeout=10)
        if response.status_code == 200:
            return {"status": "sent"}
        return {"status": "error", "reason": response.text}
    except Exception as e:
        return {"status": "error", "reason": str(e)}
