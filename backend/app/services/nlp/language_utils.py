"""
Language detection for Crime-Watch NLP triage.

DISSERTATION NOTE:
  We do not use langdetect because it does not support Shona (sn) or
  Ndebele (nd). Instead, we use a dictionary-based word-overlap approach.
  This is academically defensible as a domain-specific solution.

  Threshold: at least 2 dictionary matches required before claiming a
  language. Below that threshold we fall back to English (safer assumption).
"""
import os
from pathlib import Path

# Minimum word matches before asserting a language
MIN_MATCHES_FOR_DETECTION = 2

SUPPORTED_LANGUAGES = {"en": "English", "sn": "Shona", "nd": "Ndebele"}

_DICT_DIR = Path(__file__).parent / "dictionaries"


def _load_dictionary(filename: str) -> set:
    """Load a word-list file into a lowercase set. One term per line."""
    path = _DICT_DIR / filename
    if not path.exists():
        return set()
    terms = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            term = line.strip().lower()
            if term:
                terms.add(term)
    return terms


# Load once at module import — fast for all subsequent calls
_SHONA_TERMS: set = _load_dictionary("shona_crime_terms.txt")
_NDEBELE_TERMS: set = _load_dictionary("ndebele_crime_terms.txt")


def detect_language(text: str) -> str:
    """
    Detect whether the report is in Shona ('sn'), Ndebele ('nd'), or
    English ('en') by counting dictionary term overlaps.

    Returns:
        'sn' | 'nd' | 'en'
    """
    if not text:
        return "en"

    words = text.lower().split()
    word_set = set(words)

    shona_score = len(word_set & _SHONA_TERMS)
    ndebele_score = len(word_set & _NDEBELE_TERMS)

    # Must exceed minimum threshold to avoid false positives
    if shona_score < MIN_MATCHES_FOR_DETECTION and ndebele_score < MIN_MATCHES_FOR_DETECTION:
        return "en"

    if shona_score >= ndebele_score:
        return "sn"
    return "nd"


def translate_to_english(text: str, language: str) -> str:
    """
    Returns the original text with a language annotation prepended.
    Actual translation is performed by the Gemini prompt at classification time.
    We do NOT call a separate translation API — Gemini handles multilingual input
    natively in the classification prompt.

    DISSERTATION NOTE (Limitation §3.x):
      This is annotation-based rather than full machine translation.
      Gemini handles the multilingual processing in a single pass, which is
      acceptable for a proof-of-concept. A production system would use a
      dedicated translation layer.
    """
    if language == "en":
        return text
    lang_name = SUPPORTED_LANGUAGES.get(language, "Unknown")
    return f"[Language: {lang_name}] {text}"
