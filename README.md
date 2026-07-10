# 🧠 AI Meeting Intelligence System

An end-to-end, **100% free and open-source** AI platform that processes meeting
recordings (or live meetings), transcribes them, understands the discussion,
extracts decisions and action items, assigns priorities, creates calendar
events, sends email/Slack summaries, and lets you ask questions about any
past meeting using RAG.

> 📄 For a complete, in-depth explanation of every part of this project —
> problem statement, architecture, code walkthroughs, setup for live AND
> recorded meetings, GitHub upload steps, and interview Q&A — see the
> **"AI Meeting Intelligence System - Full Guide.docx"** document provided
> alongside this project.

## Quick Start

```bash
# 1. Clone / unzip the project, then move into it
cd meeting-ai

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your free API keys
cp .env.example .env
# then edit .env and add your GROQ_API_KEY (free from console.groq.com)

# 5. Try the pipeline instantly with sample data (no audio needed)
python sample_data/test_pipeline_with_sample.py

# 6. Run the full app
uvicorn backend.main:app --reload --port 8000      # Terminal 1
streamlit run frontend/streamlit_app.py             # Terminal 2
```

Then open the Streamlit UI (usually `http://localhost:8501`) and upload a
recorded meeting, or use the sample transcript to explore the RAG Q&A tab.

## Tech Stack (all free)

| Component | Technology |
|---|---|
| LLM | Groq API (free tier) — Llama 3.1 70B |
| Orchestration | LangGraph + LangChain |
| Speech-to-Text | OpenAI Whisper (local) |
| Speaker ID | pyannote.audio (free w/ HuggingFace token) |
| Vector DB | ChromaDB (local) + sentence-transformers embeddings |
| Backend | FastAPI |
| Frontend | Streamlit |
| Database | SQLite |
| Calendar | Google Calendar API (free tier) |
| Email | Gmail SMTP (App Password) |
| Slack | Incoming Webhooks (free) |

## Project Structure

```
meeting-ai/
├── backend/          FastAPI app + SQLite database models
├── agents/           Each AI "agent" (summarizer, decisions, action items, etc.)
├── graph/            LangGraph workflow tying all agents together
├── speech/           Whisper transcription + pyannote speaker diarization
├── rag/              ChromaDB vector store + RAG retriever (meeting memory)
├── live_capture/      Script to record a LIVE meeting's audio for free
├── frontend/         Streamlit web UI
├── sample_data/       Sample transcript + a script to test without audio
├── requirements.txt
└── .env.example
```

## License
Free to use for learning, portfolio, and interview-preparation purposes.
