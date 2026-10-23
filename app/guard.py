"""The guardrail core -- pure standard library (mirrors the numguard library).

Recognized numeric values must match provided facts; listed phrases and
missing required numeric values are flagged. This does not certify units or
claim semantics. Deterministic; runs no model.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from ._numeric import extract_numbers as _extract_numbers, validate_fact_config, validate_tolerances


def extract_numbers(text: str) -> List[tuple]:
    return [(value, raw) for value, raw, _ in _extract_numbers(text)]


def _fmt(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x)


def _tol(v: float, abs_tol: float, rel_tol: float) -> float:
    return max(abs_tol, rel_tol * abs(v))


def evaluate_text(
    text: str,
    facts: List[Dict[str, Any]],
    banned_phrases: Iterable[str] = (),
    required_names: Iterable[str] = (),
    abs_tol: float = 0.05,
    rel_tol: float = 0.001,
) -> Dict[str, Any]:
    """Evaluate a draft. ``facts`` is a list of {name, value, unit?} dicts."""
    required_names = tuple(required_names)
    validate_tolerances(abs_tol, rel_tol)
    validate_fact_config(((f.get("name"), f.get("value")) for f in facts), required_names)
    try:
        return _evaluate_text(text, facts, banned_phrases, required_names, abs_tol, rel_tol)
    except ValueError as error:
        return {"passed": False, "n_errors": 1, "findings": [{
            "check": "numeric_format", "severity": "ERROR", "message": str(error),
        }]}


def _evaluate_text(text, facts, banned_phrases, required_names, abs_tol, rel_tol):
    values = [f["value"] for f in facts if f.get("value") is not None]
    findings: List[Dict[str, str]] = []

    for n, raw in extract_numbers(text):
        if not any(abs(n - v) <= _tol(v, abs_tol, rel_tol) for v in values):
            findings.append({
                "check": "numbers_grounded",
                "severity": "ERROR",
                "message": f"Untraceable number '{raw}' is not supported by any fact.",
            })

    low = text.lower()
    for phrase in banned_phrases:
        if phrase.lower() in low:
            findings.append({
                "check": "unsupported_claims",
                "severity": "ERROR",
                "message": f"Unsupported qualitative claim: '{phrase}'.",
            })

    by_name = {f["name"]: f for f in facts if "name" in f}
    nums = [v for v, _ in extract_numbers(text)]
    for name in required_names:
        fact = by_name.get(name)
        if not fact or fact.get("value") is None:
            raise ValueError(f"Invalid required fact: {name!r}")
        v = fact["value"]
        if not any(abs(n - v) <= _tol(v, abs_tol, rel_tol) for n in nums):
            unit = f" {fact['unit']}" if fact.get("unit") else ""
            findings.append({
                "check": "required_facts",
                "severity": "ERROR",
                "message": f"Required fact '{name}' ({_fmt(v)}{unit}) is missing from the text.",
            })

    n_errors = sum(1 for f in findings if f["severity"] == "ERROR")
    return {"passed": n_errors == 0, "n_errors": n_errors, "findings": findings}
