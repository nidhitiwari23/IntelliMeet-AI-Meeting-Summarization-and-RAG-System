"""
diarization.py
-----------------
Speaker Identification ("who said what") using pyannote.audio.

pyannote.audio is free and open-source, but its pretrained pipeline is
gated on HuggingFace: you must (1) create a free HuggingFace account,
(2) accept the model's terms on its model page, and (3) generate a free
access token. This is explained step-by-step in the accompanying document.

This module combines Whisper's timestamped transcript with pyannote's
speaker turns to produce a transcript like:

    Alice: I think the UI needs a redesign.
    Bob: Agreed, I can update the backend by Friday.
"""

import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline

load_dotenv()

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise RuntimeError(
                "HF_TOKEN not set. Get a free token at https://huggingface.co/settings/tokens "
                "and accept the model terms at https://huggingface.co/pyannote/speaker-diarization-3.1"
            )
        _pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
        )
    return _pipeline


def diarize_audio(file_path: str) -> list:
    """
    Returns a list of speaker turns:
        [{"speaker": "SPEAKER_00", "start": 0.0, "end": 4.2}, ...]
    """
    pipeline = _get_pipeline()
    diarization = pipeline(file_path)
    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({"speaker": speaker, "start": turn.start, "end": turn.end})
    return turns


def merge_transcript_with_speakers(whisper_segments: list, speaker_turns: list,
                                    speaker_name_map: dict = None) -> str:
    """
    Combines Whisper's text segments with pyannote's speaker turns by
    matching on the closest overlapping time window.

    speaker_name_map lets you rename "SPEAKER_00" -> "Alice" etc.
    (You typically fill this in manually after a first pass, since the
    model only knows generic speaker IDs, not real names.)
    """
    speaker_name_map = speaker_name_map or {}
    lines = []
    for seg in whisper_segments:
        seg_mid = (seg["start"] + seg["end"]) / 2
        best_speaker = "Unknown"
        for turn in speaker_turns:
            if turn["start"] <= seg_mid <= turn["end"]:
                best_speaker = turn["speaker"]
                break
        display_name = speaker_name_map.get(best_speaker, best_speaker)
        lines.append(f"{display_name}: {seg['text']}")
    return "\n".join(lines)
