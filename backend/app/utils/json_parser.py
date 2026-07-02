import json
import re

def extract_json_from_llm_response(text: str) -> dict:
    """
    Robustly extracts a JSON object from an LLM response.
    Handles markdown fences, preamble text, and trailing content.
    Raises ValueError if extraction fails.
    """
    if not text or not isinstance(text, str):
        raise ValueError('No text provided')

    # Strategy 1: direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown fences
    cleaned = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: find first {...} block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f'Could not extract JSON from LLM response: {text[:200]}')
