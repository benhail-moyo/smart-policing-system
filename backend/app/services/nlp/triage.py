"""
NLP Triage Service — Crime-Watch
==================================
Pipeline:
  1. Input validation (done at route level)
  2. Language detection via dictionary overlap
  3. Language annotation for non-English input
  4. Keyword pre-scan for immediate HIGH severity signals
  5. Gemini API call with structured prompt
  6. Fault-tolerant JSON extraction
  7. Keyword override: LLM returned LOW but keywords say HIGH → escalate
  8. Confidence threshold check: < 0.4 → flag for human review
  9. Return structured triage result (persisted by route layer)

DISSERTATION NOTE:
  This module is the academic centrepiece of Chapter 3.
  Every step above is a numbered methodology item. Document each
  decision (why keyword pre-scan? why 0.4 confidence threshold?).
  The fallback behaviour (keyword-only) demonstrates fault tolerance —
  a required property for a law-enforcement DSS.
"""
import json
import logging
import os

from flask import current_app

from app.services.nlp.language_utils import detect_language, translate_to_english
from app.utils.json_parser import extract_json_from_llm_response

logger = logging.getLogger(__name__)

# ── Gemini prompt ──────────────────────────────────────────────────────────
CLASSIFICATION_PROMPT = """
You are a crime incident triage assistant supporting law enforcement in Zimbabwe.
The report below may be in English, Shona, or Ndebele — process it regardless of language.

Incident report:
"{report_text}"

Your task is to classify this report for emergency dispatch prioritization.

SEVERITY DEFINITIONS (use these exactly):
- HIGH: Involves weapons (firearms, knives), physical assault in progress, murder, rape,
  robbery with violence, or any immediate threat to life. Requires IMMEDIATE officer response.
- MEDIUM: Property crime (theft, burglary, vandalism), drug activity, fraud, past assault
  (not ongoing). Requires response within the hour.
- LOW: Suspicious behavior, noise complaints, minor disputes, loitering, non-urgent reports.
  Can be scheduled.

CATEGORY (choose the single most accurate category):
murder | assault | robbery | rape | theft | burglary | vandalism | drug_offence |
fraud | suspicious_activity | noise_complaint | domestic_dispute | other

Respond ONLY with this exact JSON (no markdown, no explanation outside JSON):
{{
  "category": "<category from list above>",
  "severity": "<HIGH | MEDIUM | LOW>",
  "confidence": <float 0.0-1.0>,
  "summary": "<one sentence English summary of the incident>",
  "reasoning": "<one sentence explaining severity choice>"
}}

If the report is too vague to classify with confidence > 0.4, set severity to LOW and confidence accordingly.
"""

# ── Keyword-based fallback ─────────────────────────────────────────────────
# These are unmistakable HIGH-severity signals in all three languages.
# Used for: (a) pre-scan override and (b) fallback when Gemini is unavailable.
HIGH_SEVERITY_KEYWORDS = {
    # English
    "firearm", "gun", "pistol", "rifle", "shot", "shooting", "stabbed",
    "knife", "murder", "killed", "rape", "raped", "bomb", "explosive",
    "hostage", "kidnap", "armed robbery", "hold up", "holdup",
    # Shona
    "pfuti", "banga", "mupanga", "chando", "kupondwa", "kupfurwa",
    "vakandipamba", "akandirova", "kurwiswa",
    # Ndebele
    "isibhamu", "umkhonto", "inkemba", "isikhali", "ukubulala",
    "ukudlwengula", "ukuphanga", "ngisize",
}

MEDIUM_SEVERITY_KEYWORDS = {
    # English
    "theft", "stolen", "broke in", "break-in", "burglary", "robbery",
    "drug", "drugs", "fraud", "vandal", "vandalism", "assault",
    "fight", "threatened", "threat",
    # Shona
    "kubira", "kubiwa", "kuba", "buri", "mbanje", "zvinodhaka",
    "kuputswa", "kupamba",
    # Ndebele
    "ukweba", "insangu", "izidakamizwa", "ukubhidliza", "ukushaywa",
}

VALID_CATEGORIES = {
    "murder", "assault", "robbery", "rape", "theft", "burglary",
    "vandalism", "drug_offence", "fraud", "suspicious_activity",
    "noise_complaint", "domestic_dispute", "other",
}

VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}


def _keyword_triage(text: str) -> dict:
    """
    Keyword-only fallback classification used when Gemini is unavailable.
    Deliberately conservative: prefers FALSE NEGATIVE (miss) over FALSE POSITIVE (wrong HIGH).

    Returns a triage dict with low confidence and a [Keyword-based triage] tag in summary.
    """
    lowered = text.lower()
    words = set(lowered.split())

    if any(kw in lowered for kw in HIGH_SEVERITY_KEYWORDS):
        severity = "HIGH"
        confidence = 0.55
        category = "robbery" if any(
            k in lowered for k in ("rob", "pamba", "phanga")
        ) else "assault"
    elif any(kw in lowered for kw in MEDIUM_SEVERITY_KEYWORDS):
        severity = "MEDIUM"
        confidence = 0.45
        category = "theft"
    else:
        severity = "LOW"
        confidence = 0.35
        category = "suspicious_activity"

    return {
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "summary": f"[Keyword-based triage] {text[:120]}",
        "reasoning": "Classified via keyword matching — Gemini API unavailable.",
        "raw_gemini_response": None,
    }


class NLPTriageService:
    """
    Orchestrates the full NLP triage pipeline for a single incident report.

    Usage:
        result = triage_service.triage("Someone was robbed at knifepoint")
        # result keys: category, severity, confidence, summary, reasoning,
        #              language_detected, raw_gemini_response
    """

    def triage(self, report_text: str) -> dict:
        """
        Run the full triage pipeline.

        Args:
            report_text: Raw incident text submitted by user.

        Returns:
            dict with triage fields ready to be persisted to the Incident model.
        """
        text = (report_text or "").strip()

        # Step 2: Language detection
        language = detect_language(text)

        # Step 3: Annotate non-English for Gemini
        annotated_text = translate_to_english(text, language)

        # Step 4: Keyword pre-scan — HIGH severity fast path
        lowered = text.lower()
        keyword_high_signal = any(kw in lowered for kw in HIGH_SEVERITY_KEYWORDS)

        # Step 5-6: Attempt Gemini classification
        gemini_api_key = current_app.config.get("GEMINI_API_KEY", "")
        raw_response = None

        if gemini_api_key:
            result = self._call_gemini(annotated_text, gemini_api_key)
            raw_response = result.get("raw_gemini_response")
        else:
            logger.warning("GEMINI_API_KEY not set — using keyword fallback")
            result = _keyword_triage(text)
            result["language_detected"] = language
            return result

        if result is None:
            # Gemini call failed entirely — fall back to keywords
            logger.error("Gemini call failed — using keyword fallback")
            result = _keyword_triage(text)
            result["language_detected"] = language
            return result

        # Step 7: Keyword override — never let HIGH keywords slip to LOW
        if keyword_high_signal and result.get("severity") == "LOW":
            logger.info(
                "Keyword override: escalating severity from LOW to HIGH "
                "(HIGH keywords detected: '%s')", text[:60]
            )
            result["severity"] = "HIGH"
            result["confidence"] = max(result.get("confidence", 0.5), 0.55)
            result["reasoning"] = (
                result.get("reasoning", "")
                + " [Severity escalated by keyword pre-scan override.]"
            )

        # Step 8: Flag low-confidence results
        if result.get("confidence", 1.0) < 0.4:
            result["summary"] = (
                "[LOW CONFIDENCE — HUMAN REVIEW REQUIRED] "
                + result.get("summary", "")
            )

        result["language_detected"] = language
        result["raw_gemini_response"] = raw_response
        return result

    def _call_gemini(self, text: str, api_key: str) -> dict | None:
        """
        Call the Gemini 1.5 Flash API and parse the JSON response.

        Returns:
            Parsed triage dict, or None if the call fails.
        """
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = CLASSIFICATION_PROMPT.format(report_text=text)
            response = model.generate_content(prompt)

            raw_text = response.text
            parsed = extract_json_from_llm_response(raw_text)

            # Validate and sanitise the parsed fields
            category = parsed.get("category", "other")
            if category not in VALID_CATEGORIES:
                category = "other"

            severity = str(parsed.get("severity", "LOW")).upper()
            if severity not in VALID_SEVERITIES:
                severity = "LOW"

            confidence = float(parsed.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            return {
                "category": category,
                "severity": severity,
                "confidence": confidence,
                "summary": str(parsed.get("summary", "No summary provided."))[:500],
                "reasoning": str(parsed.get("reasoning", ""))[:500],
                "raw_gemini_response": raw_text,
            }

        except ImportError:
            logger.error(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )
            return None
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            return None


# Module-level singleton — imported by routes
triage_service = NLPTriageService()
