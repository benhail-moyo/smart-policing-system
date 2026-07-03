#!/usr/bin/env python3
"""
NLP Triage Accuracy Evaluator — Crime-Watch
=============================================
Runs the triage pipeline against ml/nlp/corpus/labeled_test_set.json
and measures accuracy against the expected labels.

DISSERTATION NOTE:
  The output of this script IS your Chapter 4 finding for the NLP module.
  Run it after building the corpus and record the results in your results table.
  Target: ≥75% severity accuracy overall.

Usage:
  # From project root:
  python -m ml.nlp.evaluations.evaluate_triage

  # With verbose output (prints each misclassified report):
  python -m ml.nlp.evaluations.evaluate_triage --verbose

  # To save results to JSON:
  python -m ml.nlp.evaluations.evaluate_triage --output ml/nlp/evaluations/results.json

Flags:
  --verbose     Print each misclassification
  --output PATH Write full result dict to a JSON file
  --limit N     Only evaluate the first N entries (for quick smoke-tests)
  --no-gemini   Force keyword fallback only (useful for API-free testing)
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# ── Add project root to path so we can import app ─────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

CORPUS_PATH = PROJECT_ROOT / "ml" / "nlp" / "corpus" / "labeled_test_set.json"


def load_corpus(limit: Optional[int] = None) -> list:
    if not CORPUS_PATH.exists():
        print(f"ERROR: Corpus not found at {CORPUS_PATH}")
        print("Create ml/nlp/corpus/labeled_test_set.json first.")
        sys.exit(1)
    with open(CORPUS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if limit:
        data = data[:limit]
    return data


def run_evaluation(
    verbose: bool = False,
    limit: Optional[int] = None,
    no_gemini: bool = False,
    output_path: Optional[str] = None,
):
    entries = load_corpus(limit)
    print(f"\nCrime-Watch NLP Triage Evaluation")
    print(f"=" * 50)
    print(f"Corpus size  : {len(entries)} entries")

    # ── App context required for triage service ───────────────────────────
    from app import create_app
    from app.services.nlp.triage import triage_service

    config = "testing" if no_gemini else "development"
    app = create_app(config)

    if no_gemini:
        # Override config so Gemini is disabled
        app.config["GEMINI_API_KEY"] = ""
        print("Mode         : Keyword fallback only (--no-gemini)")
    else:
        key = app.config.get("GEMINI_API_KEY", "")
        mode = "Gemini API" if key else "Keyword fallback (no API key)"
        print(f"Mode         : {mode}")

    print(f"" + "-" * 50)

    # ── Evaluation tracking ───────────────────────────────────────────────
    results = []
    severity_correct = 0
    category_correct = 0
    language_correct = 0
    total = len(entries)

    # Per-severity breakdown
    sev_totals = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    sev_correct = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    # Per-language breakdown
    lang_totals = {"en": 0, "sn": 0, "nd": 0}
    lang_correct = {"en": 0, "sn": 0, "nd": 0}

    with app.app_context():
        for i, entry in enumerate(entries, 1):
            text = entry.get("text", "")
            expected_severity = entry.get("expected_severity", "").upper()
            expected_category = entry.get("expected_category", "")
            expected_language = entry.get("language", "en")

            start = time.time()
            try:
                result = triage_service.triage(text)
            except Exception as exc:
                result = {
                    "severity": "LOW",
                    "category": "other",
                    "language_detected": "en",
                    "confidence": 0.0,
                    "summary": f"ERROR: {exc}",
                }
            elapsed_ms = (time.time() - start) * 1000

            predicted_severity = (result.get("severity") or "LOW").upper()
            predicted_category = result.get("category") or "other"
            predicted_language = result.get("language_detected") or "en"
            confidence = result.get("confidence", 0.0)

            sev_ok = predicted_severity == expected_severity
            cat_ok = predicted_category == expected_category
            lang_ok = predicted_language == expected_language

            severity_correct += int(sev_ok)
            category_correct += int(cat_ok)
            language_correct += int(lang_ok)

            if expected_severity in sev_totals:
                sev_totals[expected_severity] += 1
                if sev_ok:
                    sev_correct[expected_severity] += 1

            if expected_language in lang_totals:
                lang_totals[expected_language] += 1
                if lang_ok:
                    lang_correct[expected_language] += 1

            row = {
                "id": entry.get("id"),
                "text_preview": text[:80],
                "expected_severity": expected_severity,
                "predicted_severity": predicted_severity,
                "severity_correct": sev_ok,
                "expected_category": expected_category,
                "predicted_category": predicted_category,
                "category_correct": cat_ok,
                "expected_language": expected_language,
                "predicted_language": predicted_language,
                "language_correct": lang_ok,
                "confidence": round(confidence, 3),
                "elapsed_ms": round(elapsed_ms, 1),
                "summary": result.get("summary", ""),
            }
            results.append(row)

            if verbose and not sev_ok:
                print(
                    f"  [MISS #{entry.get('id')}] '{text[:60]}...'\n"
                    f"    Severity: expected={expected_severity} got={predicted_severity} "
                    f"(conf={confidence:.2f})\n"
                    f"    Category: expected={expected_category} got={predicted_category}"
                )

            # Progress indicator
            if i % 10 == 0 or i == total:
                sev_acc = severity_correct / i * 100
                print(f"  Progress: {i}/{total} | Severity acc so far: {sev_acc:.1f}%")

    # ── Results ───────────────────────────────────────────────────────────
    sev_accuracy = severity_correct / total * 100
    cat_accuracy = category_correct / total * 100
    lang_accuracy = language_correct / total * 100

    print(f"\n{'=' * 50}")
    print(f"RESULTS — {total} incidents evaluated")
    print(f"{'=' * 50}")
    print(f"Severity Accuracy : {severity_correct}/{total}  = {sev_accuracy:.1f}%  {'✓ PASS' if sev_accuracy >= 75 else '✗ BELOW TARGET'} (target ≥75%)")
    print(f"Category Accuracy : {category_correct}/{total}  = {cat_accuracy:.1f}%")
    print(f"Language Accuracy : {language_correct}/{total}  = {lang_accuracy:.1f}%")

    print(f"\nSeverity Breakdown:")
    for sev in ("HIGH", "MEDIUM", "LOW"):
        t = sev_totals[sev]
        c = sev_correct[sev]
        pct = (c / t * 100) if t > 0 else 0.0
        print(f"  {sev:6s} : {c:3d}/{t:3d} = {pct:.1f}%")

    print(f"\nLanguage Detection Breakdown:")
    lang_names = {"en": "English", "sn": "Shona", "nd": "Ndebele"}
    for lang in ("en", "sn", "nd"):
        t = lang_totals[lang]
        c = lang_correct[lang]
        pct = (c / t * 100) if t > 0 else 0.0
        print(f"  {lang_names[lang]:8s} ({lang}) : {c:3d}/{t:3d} = {pct:.1f}%")

    print(f"{'=' * 50}\n")

    # ── Save output ───────────────────────────────────────────────────────
    summary = {
        "total": total,
        "severity_accuracy_pct": round(sev_accuracy, 2),
        "category_accuracy_pct": round(cat_accuracy, 2),
        "language_accuracy_pct": round(lang_accuracy, 2),
        "severity_breakdown": {
            s: {
                "correct": sev_correct[s],
                "total": sev_totals[s],
                "accuracy_pct": round((sev_correct[s] / sev_totals[s] * 100) if sev_totals[s] else 0, 2),
            }
            for s in ("HIGH", "MEDIUM", "LOW")
        },
        "language_breakdown": {
            l: {
                "correct": lang_correct[l],
                "total": lang_totals[l],
                "accuracy_pct": round((lang_correct[l] / lang_totals[l] * 100) if lang_totals[l] else 0, 2),
            }
            for l in ("en", "sn", "nd")
        },
        "individual_results": results,
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Full results saved to: {out}")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Crime-Watch NLP triage accuracy against labeled corpus."
    )
    parser.add_argument("--verbose", action="store_true", help="Print each misclassification")
    parser.add_argument("--output", type=str, default=None, help="Path to write JSON results")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only first N entries")
    parser.add_argument("--no-gemini", action="store_true", help="Force keyword fallback only")
    args = parser.parse_args()

    run_evaluation(
        verbose=args.verbose,
        limit=args.limit,
        no_gemini=args.no_gemini,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
