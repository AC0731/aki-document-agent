import argparse
import json
import os
import sys
from pathlib import Path

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small document-agent answer check set.")
    parser.add_argument("dataset", type=Path, help="JSON file containing document IDs and expected answer terms.")
    parser.add_argument("--url", default=os.getenv("AGENT_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()

    token = os.getenv("AGENT_API_KEY")
    if not token:
        parser.error("Set AGENT_API_KEY in the environment.")

    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    results = []
    for case in cases:
        response = requests.post(
            f"{args.url.rstrip('/')}/v1/ask",
            headers=headers,
            json={"document_id": case["document_id"], "question": case["question"]},
            timeout=90,
        )
        if response.status_code >= 400:
            results.append({"id": case["id"], "passed": False, "error": response.text})
            continue
        payload = response.json()
        answer = payload.get("answer", "").casefold()
        terms = [term.casefold() for term in case.get("expected_terms", [])]
        missing = [term for term in terms if term not in answer]
        passed = not missing and bool(payload.get("sources"))
        results.append(
            {
                "id": case["id"],
                "passed": passed,
                "missing_expected_terms": missing,
                "source_count": len(payload.get("sources", [])),
                "answer": payload.get("answer", ""),
            }
        )

    passed_count = sum(1 for result in results if result["passed"])
    report = {
        "total": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "pass_rate": passed_count / len(results) if results else None,
        "cases": results,
        "note": "This is a lightweight regression check, not a semantic correctness score.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
