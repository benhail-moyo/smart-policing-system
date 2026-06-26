SUPPORTED_LANGUAGES = {"en": "English", "sn": "Shona", "nd": "Ndebele"}


def detect_language(text: str) -> str:
    lowered = (text or "").lower()
    if any(token in lowered for token in ("mhoro", "ndapota", "mapurisa")):
        return "sn"
    if any(token in lowered for token in ("sawubona", "ngicela", "amaphoyisa")):
        return "nd"
    return "en"
