"""The guardrail core -- pure standard library (mirrors the numguard library).

A draft may only restate numbers that exist in the provided facts; banned
qualitative claims and missing required facts are flagged. Deterministic; runs
no model.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

_NUM = re.compile(r"(?<![\w.])(\d+(?:,\d{3})*(?:\.\d+)?)")


def extract_numbers(text: str) -> List[tuple]:
    """Return (value, raw_string) for each standalone number, keeping the raw
    token so messages echo exactly what the draft wrote (e.g. '83.0')."""
    out: List[tuple] = []
    for m in _NUM.finditer(text):
        raw = m.group(1)
        try:
            out.append((float(raw.replace(",", "")), raw))
        except ValueError:  # pragma: no cover
            continue
    return out


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
            continue
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
