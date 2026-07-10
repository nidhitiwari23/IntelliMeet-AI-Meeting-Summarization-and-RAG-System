"""
test_pipeline_with_sample.py
------------------------------
Quickest way to see the whole system work WITHOUT needing any audio file,
Whisper, or microphone setup. It feeds the sample transcript directly
into the LangGraph pipeline.

Run with:
    python sample_data/test_pipeline_with_sample.py

Use this first to confirm your GROQ_API_KEY and dependencies are working
before dealing with audio/transcription setup.
"""

import sys
import os
import json

# allow running this script directly from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.meeting_graph import run_meeting_pipeline

if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "sample_transcript.txt")) as f:
        transcript = f.read()

    print("Running the full multi-agent pipeline on the sample transcript...\n")
    result = run_meeting_pipeline(transcript, title="Sample Product Sync")

    print(json.dumps(result, indent=2, default=str))
