"""
main.py (FastAPI backend)
----------------------------
Exposes the whole system as a web API so the Streamlit frontend (or
Postman, curl, or any other client) can use it.

Run with:
    uvicorn backend.main:app --reload --port 8000

Then open http://localhost:8000/docs for the interactive Swagger UI,
where you can test every endpoint directly in the browser.
"""

import os
import shutil
import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, get_session, Meeting, Task, Decision, CalendarEvent
from speech.transcribe import transcribe_audio
from graph.meeting_graph import run_meeting_pipeline
from rag.vector_store import add_meeting_to_vector_store
from rag.retriever import ask_about_past_meetings
from agents.analytics import generate_insights

app = FastAPI(title="AI Meeting Intelligence System")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

UPLOAD_DIR = "uploaded_meetings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

init_db()  # creates meeting_ai.db and tables on first run


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Meeting Intelligence System is running"}


@app.post("/process-meeting")
async def process_meeting(
    file: UploadFile = File(...),
    title: str = Form("Untitled Meeting"),
    attendee_emails: str = Form(""),  # comma separated
):
    """
    Main endpoint: upload a recorded meeting (audio/video file) and get
    back the full AI-generated meeting intelligence report.

    Steps performed:
        1. Save uploaded file to disk
        2. Transcribe it with Whisper
        3. Run the LangGraph multi-agent pipeline
        4. Save everything to the SQLite database
        5. Add the transcript to the RAG vector store for future Q&A
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    transcript = transcribe_audio(file_path)

    emails = [e.strip() for e in attendee_emails.split(",") if e.strip()]
    result = run_meeting_pipeline(transcript, title=title, attendee_emails=emails)

    # ---- Persist to SQLite ----
    session = get_session()
    meeting = Meeting(
        title=title,
        date=datetime.datetime.utcnow(),
        participants=attendee_emails,
        transcript=transcript,
        summary=result.get("summary", ""),
    )
    session.add(meeting)
    session.commit()
    session.refresh(meeting)

    for d in result.get("decisions", []):
        session.add(Decision(meeting_id=meeting.id, description=d.get("description", "")))

    for t in result.get("action_items", []):
        session.add(Task(
            meeting_id=meeting.id,
            employee=t.get("employee", "Unknown"),
            task=t.get("task", ""),
            deadline=t.get("deadline", "Not specified"),
            priority=t.get("priority", "Medium"),
        ))

    calendar_result = result.get("calendar_result", {})
    if calendar_result.get("status") == "created":
        session.add(CalendarEvent(
            meeting_id=meeting.id,
            google_event_id=calendar_result.get("event_id", ""),
            description=result.get("followup_meeting", {}).get("description", ""),
        ))

    session.commit()
    meeting_id = meeting.id   # Save the ID while session is still active
    session.close()

    # ---- Add to vector store for RAG / meeting memory ----
    add_meeting_to_vector_store(
        meeting_id=meeting.id, title=title, transcript=transcript,
        date=str(datetime.date.today())
    )

    return {
        "meeting_id": meeting.id,
        "transcript": transcript,
        "summary": result.get("summary"),
        "decisions": result.get("decisions"),
        "action_items": result.get("action_items"),
        "followup_meeting": result.get("followup_meeting"),
        "calendar_result": result.get("calendar_result"),
        "email_body": result.get("email_body"),
        "email_result": result.get("email_result"),
        "slack_result": result.get("slack_result"),
    }


@app.get("/meetings")
def list_meetings():
    """Returns a list of all previously processed meetings."""
    session = get_session()
    meetings = session.query(Meeting).order_by(Meeting.date.desc()).all()
    output = [
        {"id": m.id, "title": m.title, "date": str(m.date), "summary": m.summary}
        for m in meetings
    ]
    session.close()
    return output


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int):
    """Returns full details (tasks, decisions) for one meeting."""
    session = get_session()
    meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        session.close()
        return {"error": "Meeting not found"}
    output = {
        "id": meeting.id,
        "title": meeting.title,
        "date": str(meeting.date),
        "summary": meeting.summary,
        "transcript": meeting.transcript,
        "tasks": [
            {"employee": t.employee, "task": t.task, "deadline": t.deadline,
             "priority": t.priority, "status": t.status}
            for t in meeting.tasks
        ],
        "decisions": [d.description for d in meeting.decisions],
    }
    session.close()
    return output


@app.post("/ask")
def ask_question(question: str = Form(...)):
    """RAG endpoint: ask a question about any past meeting."""
    answer = ask_about_past_meetings(question)
    return {"question": question, "answer": answer}


@app.get("/meetings/{meeting_id}/insights")
def meeting_insights(meeting_id: int):
    """Analytics endpoint: get insights for a specific meeting."""
    session = get_session()
    meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
    session.close()
    if not meeting:
        return {"error": "Meeting not found"}
    return {"insights": generate_insights(meeting.transcript)}
