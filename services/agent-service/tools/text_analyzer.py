import re
from crewai.tools import tool

@tool("TextPatternAnalyzer")
def analyze_text_patterns(text: str) -> dict:
    """Analyzes text for linguistic patterns that indicate AI generation."""
    signals = {}

    # Avg sentence length (AI tends to be longer and more uniform)
    sentences = re.split(r'[.!?]+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    signals["avg_sentence_length"] = round(avg_len, 1)
    signals["long_sentences"] = avg_len > 25

    # First person usage (humans use it more naturally)
    first_person = len(re.findall(r'\b(I|my|me|we|our)\b', text, re.IGNORECASE))
    signals["first_person_count"] = first_person
    signals["low_first_person"] = first_person < 3

    # Filler/hesitation words (humans use these, AI rarely does)
    fillers = len(re.findall(r'\b(um|uh|basically|actually|honestly|like|you know|kind of|sort of)\b', text, re.IGNORECASE))
    signals["filler_words"] = fillers
    signals["no_fillers"] = fillers == 0

    # Transition words (AI overuses these)
    transitions = len(re.findall(r'\b(furthermore|moreover|additionally|consequently|therefore|thus|hence|nevertheless)\b', text, re.IGNORECASE))
    signals["formal_transitions"] = transitions
    signals["high_formal_transitions"] = transitions > 2

    # Bullet/numbered structure detection
    has_structure = bool(re.search(r'(\d+\.|•|-)\s+\w', text))
    signals["structured_format"] = has_structure

    # Calculate raw score
    score = 0
    if signals["long_sentences"]: score += 20
    if signals["low_first_person"]: score += 25
    if signals["no_fillers"]: score += 20
    if signals["high_formal_transitions"]: score += 20
    if signals["structured_format"]: score += 15

    signals["pattern_score"] = score
    return signals
