import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# Skip the HTTP-layer tests gracefully if the web deps aren't installed.
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_evaluate_grounded_draft():
    payload = {
        "text": "Of 24 participants, 79.2% reported an event.",
        "facts": [{"name": "n", "value": 24}, {"name": "p", "value": 79.2}],
        "required_names": ["p"],
    }
    r = client.post("/evaluate", json=payload)
    assert r.status_code == 200
    assert r.json()["passed"] is True


def test_evaluate_hallucinated_draft():
    payload = {
        "text": "Actually 83.0% and the drug was well tolerated.",
        "facts": [{"name": "p", "value": 79.2}],
        "banned_phrases": ["well tolerated"],
    }
    r = client.post("/evaluate", json=payload)
    body = r.json()
    assert body["passed"] is False
    assert body["n_errors"] >= 2


def test_metrics_exposition():
    client.get("/health")  # generate at least one request
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "guard_requests_total" in r.text


def test_response_time_header():
    r = client.get("/health")
    assert "X-Response-Time-ms" in r.headers
