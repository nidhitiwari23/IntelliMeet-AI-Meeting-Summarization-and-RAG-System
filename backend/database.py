"""
database.py
------------
Sets up a FREE, file-based SQLite database (no server / no installation needed).
SQLAlchemy is used as an ORM so the code reads like normal Python objects
instead of raw SQL.

Tables created:
    meetings        -> one row per meeting processed
    tasks           -> action items extracted from meetings
    decisions       -> decisions extracted from meetings
    calendar_events -> follow-up meetings created on Google Calendar
"""

import os
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./meeting_ai.db")

# check_same_thread=False is required because FastAPI/Streamlit may use
# the connection from different threads. Safe for our single-user use case.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="Untitled Meeting")
    date = Column(DateTime, default=datetime.datetime.utcnow)
    duration_minutes = Column(Integer, default=0)
    participants = Column(Text, default="")   # comma separated names
    transcript = Column(Text, default="")
    summary = Column(Text, default="")

    tasks = relationship("Task", back_populates="meeting")
    decisions = relationship("Decision", back_populates="meeting")
    events = relationship("CalendarEvent", back_populates="meeting")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    employee = Column(String)
    task = Column(Text)
    deadline = Column(String, default="Not specified")
    priority = Column(String, default="Medium")
    status = Column(String, default="Pending")

    meeting = relationship("Meeting", back_populates="tasks")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    meeting = relationship("Meeting", back_populates="decisions")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    google_event_id = Column(String, default="")
    event_date = Column(String, default="")
    event_time = Column(String, default="")
    description = Column(Text, default="")

    meeting = relationship("Meeting", back_populates="events")


def init_db():
    """Creates the SQLite file and all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Returns a new database session. Caller is responsible for closing it."""
    return SessionLocal()


if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DATABASE_URL)
