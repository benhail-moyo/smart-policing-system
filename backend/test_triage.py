from app import create_app
from app.services.nlp.triage import triage_service

app = create_app()
with app.app_context():
    print("Testing NLP triage with Gemini API...")
    result = triage_service.triage("Someone stole my phone at gunpoint")
    print(f"Result: {result}")
    print(f"Severity: {result.get('severity')}")
    print(f"Category: {result.get('category')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Used Gemini: {result.get('raw_gemini_response') is not None}")