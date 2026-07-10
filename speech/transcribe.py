"""
transcribe.py
--------------
Converts an audio/video file into text using OpenAI's Whisper model,
running 100% locally and free (no API cost, no internet needed after
the model is downloaded once).

Supported inputs: .mp3, .wav, .m4a, .mp4 (audio is auto-extracted).
"""

import whisper

# Model size options (bigger = more accurate but slower):
#   "tiny", "base", "small", "medium", "large"
# "base" is a good free balance of speed vs accuracy for a laptop/CPU.
MODEL_SIZE = "tiny"

_model = None


def _get_model():
    global _model
    if _model is None:
        print(f"Loading Whisper '{MODEL_SIZE}' model (first run downloads it, ~150MB)...")
        _model = whisper.load_model(MODEL_SIZE)
    return _model


def transcribe_audio(file_path: str) -> str:
    """
    Transcribes the given audio/video file and returns plain text.

    Example:
        text = transcribe_audio("sample_data/meeting.mp3")
    """
    model = _get_model()
    result = model.transcribe(file_path)
    return result["text"].strip()


def transcribe_with_timestamps(file_path: str) -> list:
    """
    Returns a list of segments with start/end timestamps, useful for
    aligning with speaker diarization output.
    Each item: {"start": float, "end": float, "text": str}
    """
    model = _get_model()
    result = model.transcribe(file_path)
    return [
        {"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()}
        for seg in result["segments"]
    ]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python speech/transcribe.py <path_to_audio_or_video>")
    else:
        print(transcribe_audio(sys.argv[1]))
