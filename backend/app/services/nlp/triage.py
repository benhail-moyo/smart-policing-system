from app.services.nlp.language_utils import detect_language


class TriageService:
    def triage(self, report_text: str) -> dict:
        text = report_text or ""
        category = "other"
        lowered = text.lower()
        if any(word in lowered for word in ("robbery", "theft", "stolen")):
            category = "property_crime"
        elif any(word in lowered for word in ("assault", "attack", "violence")):
            category = "violent_crime"

        return {
            "category": category,
            "severity": "medium",
            "language": detect_language(text),
            "confidence": 0.5,
        }


triage_service = TriageService()
