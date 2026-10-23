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


@pytest.mark.parametrize("updates", [
    {"required_names": ["mortailty"]},
    {"facts": [{"name": "n", "value": 1}, {"name": "n", "value": 2}]},
    {"facts": [{"name": "", "value": 1}]},
    {"facts": [{"name": "n", "value": "inf"}]},
    {"facts": [{"name": "n", "value": True}]},
    {"facts": [{"name": "mortality", "value": None}], "required_names": ["mortality"]},
    {"abs_tol": "inf"}, {"abs_tol": -1}, {"rel_tol": "nan"}, {"rel_tol": True},
])
def test_invalid_fact_contract_returns_422(updates):
    payload = {"text": "There were 99999 participants.", "facts": [{"name": "mortality", "value": 0}]}
    payload.update(updates)
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 422, response.text


def test_malformed_draft_is_a_gate_failure_not_an_http_error():
    response = client.post("/evaluate", json={"text": "Count 1e999.", "facts": []})
    assert response.status_code == 200
    assert response.json()["passed"] is False
    assert response.json()["findings"][0]["check"] == "numeric_format"
