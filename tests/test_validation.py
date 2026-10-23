"""The HTTP and dependency-free cores share the same invalid-input contract."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.guard import evaluate_text


@pytest.mark.parametrize("text", ["Change -2.3 mg.", "Rate .5%.", "Count 1e9."])
def test_unsupported_numeric_meanings_fail(text):
    assert not evaluate_text(text, [{"name": "change", "value": 2.3}, {"name": "n", "value": 1}])["passed"]


def test_supported_signed_and_exponent_values_pass():
    facts = [{"name": "x", "value": -2.3}, {"name": "rate", "value": .5}, {"name": "n", "value": 1e9}]
    assert evaluate_text("Change −2.3, rate .5, count 1e9.", facts)["passed"]


def test_draft_format_errors_produce_failure():
    report = evaluate_text("Rate 79,2%.", [{"name": "x", "value": 79}])
    assert not report["passed"]
    assert report["findings"][0]["check"] == "numeric_format"


@pytest.mark.parametrize("kwargs", [
    {"required_names": ["missing"]}, {"abs_tol": float("inf")},
    {"rel_tol": -1},
])
def test_invalid_core_configuration_raises(kwargs):
    with pytest.raises(ValueError):
        evaluate_text("No values.", [{"name": "n", "value": 1}], **kwargs)
