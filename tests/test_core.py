import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from app.guard import evaluate_text  # noqa: E402
from app.metrics import Metrics, percentile  # noqa: E402

FACTS = [
    {"name": "n_treated", "value": 24, "unit": "participants"},
    {"name": "pct_any_ae", "value": 79.2, "unit": "%"},
]


def test_grounded_draft_passes():
    r = evaluate_text("Of 24 participants, 79.2% had an event.", FACTS,
                      required_names=["pct_any_ae"])
    assert r["passed"] is True
    assert r["n_errors"] == 0


def test_hallucinated_draft_fails():
    r = evaluate_text("Of 24, 83.0% had an event and it was well tolerated.",
                      FACTS, banned_phrases=["well tolerated"])
    assert r["passed"] is False
    msgs = " ".join(f["message"] for f in r["findings"])
    assert "83.0" in msgs
    assert any("well tolerated" in f["message"].lower() for f in r["findings"])


def test_identifier_digits_not_flagged():
    r = evaluate_text("Study CP101 had 24 participants.", FACTS)
    assert r["passed"] is True


def test_metrics_counters_and_percentile():
    m = Metrics()
    for d in (10.0, 20.0, 30.0):
        m.record_request(200, d)
    m.record_request(503, 5.0)
    m.record_evaluation(False)
    snap = m.snapshot()
    assert snap["requests"] == 4
    assert snap["errors"] == 1
    assert snap["gate_failures"] == 1
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5


def test_prometheus_exposition_well_formed():
    m = Metrics()
    m.record_request(200, 1.0)
    text = m.prometheus()
    assert "guard_requests_total 1" in text
    assert "# TYPE guard_requests_total counter" in text
