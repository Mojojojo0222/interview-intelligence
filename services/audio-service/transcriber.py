"""
Audio Service — captures mic audio, transcribes with Whisper,
extracts voice signals: hesitation count, response time, confidence.
"""
import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import os
import time
import re
from dataclasses import dataclass

# Load whisper model once at startup
_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading Whisper model (tiny — fast on CPU)...")
        _model = whisper.load_model("tiny")
    return _model


@dataclass
class VoiceAnalysis:
    transcript: str
    response_time_seconds: float
    hesitation_count: int        # um, uh, err, hmm
    filler_count: int            # like, basically, you know
    word_count: int
    words_per_minute: float
    confidence_signal: str       # "high", "medium", "low"
    reading_signal: bool         # True if likely reading from screen
    pause_ratio: float           # ratio of silence to speech


def record_audio(duration_seconds: int = 30, sample_rate: int = 16000) -> np.ndarray:
    """Record audio from microphone."""
    print(f"Recording for up to {duration_seconds}s... (press Ctrl+C to stop early)")
    audio = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()
    return audio.flatten()


def transcribe_audio(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """Transcribe audio array using Whisper."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    try:
        wav.write(tmp_path, sample_rate, (audio * 32767).astype(np.int16))
        model = get_model()
        result = model.transcribe(tmp_path, language="en", fp16=False)
        return result["text"].strip()
    finally:
        os.unlink(tmp_path)


def transcribe_file(file_path: str) -> str:
    """Transcribe an audio file."""
    model = get_model()
    result = model.transcribe(file_path, language="en", fp16=False)
    return result["text"].strip()


def analyze_voice(transcript: str, response_time: float, audio: np.ndarray = None) -> VoiceAnalysis:
    """Extract voice signals from transcript and audio."""
    text = transcript.lower()
    words = text.split()
    word_count = len(words)

    # Hesitation words — natural human speech markers
    hesitations = re.findall(r'\b(um+|uh+|err+|hmm+|ah+|oh+)\b', text)
    hesitation_count = len(hesitations)

    # Filler words
    fillers = re.findall(r'\b(like|basically|you know|kind of|sort of|actually|honestly|right)\b', text)
    filler_count = len(fillers)

    # Words per minute
    wpm = (word_count / response_time * 60) if response_time > 0 else 0

    # Reading signal — very high WPM + no hesitations = likely reading
    reading_signal = wpm > 160 and hesitation_count == 0 and filler_count == 0

    # Confidence signal based on hesitations and fillers
    if hesitation_count == 0 and filler_count <= 1 and wpm > 120:
        confidence_signal = "high"
    elif hesitation_count <= 2 and filler_count <= 3:
        confidence_signal = "medium"
    else:
        confidence_signal = "low"

    # Pause ratio from audio energy (silence detection)
    pause_ratio = 0.0
    if audio is not None:
        energy = np.abs(audio)
        silence_threshold = np.percentile(energy, 30)
        silence_frames = np.sum(energy < silence_threshold)
        pause_ratio = round(silence_frames / len(audio), 2)

    return VoiceAnalysis(
        transcript=transcript,
        response_time_seconds=round(response_time, 1),
        hesitation_count=hesitation_count,
        filler_count=filler_count,
        word_count=word_count,
        words_per_minute=round(wpm, 1),
        confidence_signal=confidence_signal,
        reading_signal=reading_signal,
        pause_ratio=pause_ratio,
    )


def record_and_analyze(question: str, max_seconds: int = 120) -> dict:
    """
    Full pipeline: record candidate answer, transcribe, analyze.
    Returns dict ready for agent analysis.
    """
    print(f"\nQuestion: {question}")
    print("Waiting for candidate to start answering...")
    time.sleep(1)

    start_time = time.time()
    audio = record_audio(duration_seconds=max_seconds)
    response_time = time.time() - start_time

    print("Transcribing...")
    transcript = transcribe_audio(audio)

    if not transcript:
        return {"error": "No speech detected", "transcript": ""}

    analysis = analyze_voice(transcript, response_time, audio)

    return {
        "transcript": transcript,
        "response_time_seconds": analysis.response_time_seconds,
        "hesitation_count": analysis.hesitation_count,
        "filler_count": analysis.filler_count,
        "word_count": analysis.word_count,
        "words_per_minute": analysis.words_per_minute,
        "confidence_signal": analysis.confidence_signal,
        "reading_signal": analysis.reading_signal,
        "pause_ratio": analysis.pause_ratio,
    }
