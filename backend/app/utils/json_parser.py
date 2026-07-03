"""
Fault-tolerant JSON extractor for LLM responses.

DISSERTATION NOTE:
  LLMs frequently wrap JSON in markdown code fences or prepend preamble text.
  This utility implements a three-strategy cascade to extract valid JSON
  from any well-formed Gemini response. Defensive programming is essential
  when relying on external APIs in a law-enforcement context.
"""
import json
import re


def extract_json_from_llm_response(text: str) -> dict:
    """
    Robustly extracts a JSON object from an LLM response.
    Handles markdown fences, preamble text, and trailing content.

    Strategies (applied in order):
      1. Direct parse — ideal case, response is clean JSON
      2. Strip markdown code fences (```json ... ```)
      3. Regex extraction — find first {...} block, handles preamble text

    Raises:
        ValueError: If no valid JSON object can be extracted.
    """
    if not text or not isinstance(text, str):
        raise ValueError("No text provided to extract JSON from")

    # Strategy 1: Direct parse (best case)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code fences then parse
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find the outermost {...} block
    # We search for the last opening brace to avoid preamble text
    # and use a non-greedy match within the block
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 4: Find the first { and last } and try that range
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract JSON from LLM response. "
        f"First 200 chars: {text[:200]!r}"
    )
