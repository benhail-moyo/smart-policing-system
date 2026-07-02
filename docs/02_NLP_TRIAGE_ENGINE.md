# Phase 2: NLP Triage Engine

> **Prerequisite:** Phase 1 complete. JWT login works. Database tables exist.  
> **Estimated time:** 6–8 hours  
> **This phase is done when:** A POST to `/api/v1/incidents/` with a Shona crime report returns a classified response with severity, category, and confidence above 0.0.

---

## Context for Claude

Building the NLP triage pipeline for Crime-Watch. The system must:
1. Accept incident reports in English, Shona, or Ndebele
2. Detect the language
3. Classify severity (HIGH/MEDIUM/LOW) and category (robbery, assault, etc.)
4. Fall back to keyword matching if Gemini API is unavailable
5. Store the result including confidence score and raw Gemini response

Existing files to complete (do NOT rewrite from scratch, extend what exists):
- `backend/app/services/nlp/triage.py` — `NLPTriageService` class with `triage()` method
- `backend/app/services/nlp/language_utils.py` — `detect_language()` and `translate_to_english()`
- `backend/app/services/nlp/dictionaries/shona_crime_terms.txt` — needs expanding
- `backend/app/services/nlp/dictionaries/ndebele_crime_terms.txt` — needs expanding
- `backend/app/api/v1/routes/incidents.py` — `submit_incident()` route exists, needs hardening

---

## What Needs to Be Built in This Phase

### 2.1 Expand the Language Dictionaries

The existing dictionary files have ~15 terms each. Expand each to at least 60 terms.

**For `shona_crime_terms.txt` — add terms for:**
- Reporting violence: `ndaona`, `akandirova`, `vakandipamba`, `akapindura`, `ari kutya`
- Weapons: `banga`, `pfuti`, `chando`, `mupanga`
- Drugs: `mbanje`, `zvinodhaka`, `kudhunga`
- Urgency/emergency: `batsira`, `ndibatsireiwo`, `kukurumidza`, `police`
- Property crime: `buri`, `gedhi`, `mota`, `mari`, `bhegi`
- People: `murume`, `mukadzi`, `vana`, `vaviri`

**For `ndebele_crime_terms.txt` — add terms for:**
- Violence: `ukubetha`, `ukulimaza`, `ukubulala`, `ngozi`
- Weapons: `isibhamu`, `umkhonto`, `inkemba`, `isikhali`
- Drugs: `izidakamizwa`, `insangu`
- Urgency: `ngisize`, `amapolisa`, `shesha`, `msindo`
- Property: `imoto`, `imali`, `indlu`, `isango`

**Language detection threshold (in `language_utils.py`):**
The current implementation returns `sn` if `shona_score >= ndebele_score`. Improve this:
- Require at least 2 word matches before claiming a language (avoids false positives on bilingual reports)
- If 0 matches for both: return `en`
- If exactly 1 match for one language: still return `en` (too ambiguous)

```python
MIN_MATCHES_FOR_DETECTION = 2

if shona_score < MIN_MATCHES_FOR_DETECTION and ndebele_score < MIN_MATCHES_FOR_DETECTION:
    return "en"
```

### 2.2 Harden the Gemini Prompt

The existing classification prompt works but needs improvement for Zimbabwean context.

**Replace the existing `CLASSIFICATION_PROMPT` with this refined version:**

```python
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
```

### 2.3 Fault-Tolerant JSON Parsing

The existing Gemini response parser is fragile. Gemini sometimes returns responses like:
- `json\n{...}\n` (with markdown fence)
- `Sure! Here is the JSON:\n{...}` (with preamble text)
- `{...}` (perfect — but don't rely on it)

**Create `backend/app/utils/json_parser.py`:**

```python
import json
import re

def extract_json_from_llm_response(text: str) -> dict:
    """
    Robustly extracts a JSON object from an LLM response.
    Handles markdown fences, preamble text, and trailing content.
    
    Raises:
        ValueError: If no valid JSON object can be extracted.
    """
    # Strategy 1: Direct parse (ideal case)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Strip markdown code fences
    cleaned = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Extract first {...} block using regex
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract JSON from LLM response: {text[:200]}")
```

Update `triage.py` to use this utility.

### 2.4 Complete the Incidents API

The existing `incidents.py` route needs these additions:

**Input validation:**
```python
# Validate raw_text length
if len(data["raw_text"]) < 5:
    return jsonify({"error": "Report too short to classify"}), 400
if len(data["raw_text"]) > 5000:
    return jsonify({"error": "Report exceeds maximum length"}), 400
```

**Add a `GET /api/v1/incidents/stats` endpoint:**
```python
@incidents_bp.get("/stats")
@jwt_required()
def get_stats():
    """Returns incident counts by severity — used by the dashboard."""
    from sqlalchemy import func
    results = (
        db.session.query(Incident.severity, func.count(Incident.id))
        .group_by(Incident.severity)
        .all()
    )
    return jsonify({
        "by_severity": {str(sev): count for sev, count in results},
        "total": sum(count for _, count in results)
    }), 200
```

### 2.5 NLP Corpus — Build the Test Dataset

This is NOT code — this is your academic work. You must create:

**File:** `ml/nlp/corpus/labeled_test_set.json`

**Minimum 200 entries** with this structure:
```json
[
  {
    "id": 1,
    "text": "Munhu akabva akapamba bhazi rangu neGun paMbare",
    "expected_severity": "HIGH",
    "expected_category": "robbery",
    "language": "sn",
    "notes": "Armed robbery, Shona language"
  }
]
```

**Distribution to target:**
- 30% HIGH severity (60 reports)
- 40% MEDIUM severity (80 reports)  
- 30% LOW severity (60 reports)
- Language: 60% English, 25% Shona, 15% Ndebele

**How to generate these efficiently:**
Use Claude/ChatGPT to generate batches of synthetic reports by prompting:
> "Generate 20 realistic but fictional crime incident reports as if submitted by Zimbabwe community members. Mix severity levels. Write 12 in English, 5 in Shona, 3 in Ndebele. Output as JSON array with text, expected_severity, expected_category, language fields."

Then manually review and correct the labels. This manual review IS part of your research methodology.

---

## Acceptance Checklist

```bash
# 1. English HIGH severity report
curl -X POST http://localhost:5000/api/v1/incidents/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "A man with a firearm robbed the CBZ bank on Samora Machel Avenue. He is still in the area.",
    "location_lat": -17.8292,
    "location_lng": 31.0522,
    "location_description": "Samora Machel Ave, Harare CBD"
  }'
# Expected: severity=HIGH, category=robbery, confidence>0.8

# 2. Shona report
curl -X POST http://localhost:5000/api/v1/incidents/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "Ndaona murume akakwira mota yangu without permission. Aenda kuMbare.", "location_lat": -17.85, "location_lng": 31.05}'
# Expected: language_detected=sn, severity classified

# 3. Fallback mode (set GEMINI_API_KEY= empty in .env, restart)
# Expected: same endpoint returns a result, lower confidence, summary says "[Keyword-based triage]"

# 4. Stats endpoint
curl http://localhost:5000/api/v1/incidents/stats \
  -H "Authorization: Bearer <token>"
# Expected: { "by_severity": { "HIGH": 1, ... }, "total": N }

# 5. Too-short report rejected
# raw_text: "hi" → 400 "Report too short to classify"
```

---

## Dissertation Notes for This Phase

**Chapter 3 (Methodology) — Algorithm Design section:**

Document the triage pipeline as a numbered process:
1. Input validation and length check
2. Language detection via dictionary overlap (cite your dictionaries as a contribution)
3. Conditional translation annotation for non-English input
4. Keyword pre-scan for immediate HIGH severity detection
5. Gemini API call with structured prompt
6. Fault-tolerant JSON extraction
7. Keyword override: if keywords found but LLM returned LOW → escalate to HIGH
8. Confidence threshold check: if < 0.4 → flag for human review
9. Persist to database with full audit trail (raw_gemini_response stored)

**Chapter 3 — Limitations to document:**
- Translation to English is currently done via prompt annotation, not a full translation. Gemini handles this well for code-switched text but accuracy may degrade for fully Shona/Ndebele reports.
- Gemini has usage quotas — keyword fallback maintains system availability.
- Bias risk: if Shona/Ndebele terms for crime overlap with innocent usage, false positives can occur. This is mitigated by the confidence threshold.

**Your key measurement for Chapter 4:**
Run `evaluate_triage.py` after building the corpus. The output accuracy score IS your dissertation finding. Target: ≥75% overall accuracy.

---

## What You Learn in This Phase

- **Prompt engineering:** How you phrase instructions to an LLM dramatically changes output quality. The refined prompt specifies exact JSON keys, exact severity definitions, and a fallback instruction for vague reports. This is a real skill.
- **Defensive programming:** Never trust external API responses. Always parse with try/catch and have a fallback.
- **Service layer pattern:** `triage_service` is a singleton. The route just calls it. Business logic lives in the service, not in the route.
- **Audit trail design:** Storing `raw_gemini_response` means you can review what the AI actually said for any incident. Critical for law enforcement accountability.
