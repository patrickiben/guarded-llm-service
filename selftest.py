#!/usr/bin/env python3
"""Zero-dependency self-test for the service CORE (guard + metrics).

The FastAPI layer is exercised by tests/test_api.py (and a live container smoke
test) under CI. This proves the business logic with no dependencies installed.
Exits 0 on success, 1 on failure.
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from app.guard import evaluate_text  # noqa: E402
from app.metrics import Metrics, percentile  # noqa: E402


def main() -> int:
    ok = True
    facts = [
        {"name": "n_treated", "value": 24, "unit": "participants"},
        {"name": "pct_any_ae", "value": 79.2, "unit": "%"},
    ]
    banned = ["well tolerated"]
    required = ["pct_any_ae"]

    good = "Of 24 participants, 79.2% reported an adverse event."
    bad = "Of 24 participants, 83.0% reported an adverse event; the drug was well tolerated."

    g = evaluate_text(good, facts, banned, required)
    b = evaluate_text(bad, facts, banned, required)

    print("GUARD CORE")
    print(f"  grounded draft   -> passed={g['passed']}  errors={g['n_errors']}")
    print(f"  hallucinated draft -> passed={b['passed']}  errors={b['n_errors']}")
    for f in b["findings"]:
        print(f"     - [{f['severity']}] {f['check']}: {f['message']}")
    if not (g["passed"] and not b["passed"] and b["n_errors"] >= 2):
        ok = False
        print("  UNEXPECTED guard behavior.")

    print("METRICS CORE")
    m = Metrics()
    for d in (5.0, 7.0, 9.0, 11.0, 200.0):
        m.record_request(200, d)
    m.record_request(500, 3.0)
    m.record_evaluation(True)
    m.record_evaluation(False)
    snap = m.snapshot()
    print(f"  snapshot: {snap}")
    if not (snap["requests"] == 6 and snap["errors"] == 1
            and snap["evaluations"] == 2 and snap["gate_failures"] == 1):
        ok = False
        print("  UNEXPECTED metrics counters.")
    if abs(percentile([1.0, 2.0, 3.0, 4.0], 0.5) - 2.5) > 1e-9:
        ok = False
        print("  UNEXPECTED percentile computation.")
    prom = m.prometheus()
    if "guard_requests_total 6" not in prom:
        ok = False
        print("  UNEXPECTED prometheus exposition.")

    print("=" * 60)
    print("SELFTEST PASSED" if ok else "SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
