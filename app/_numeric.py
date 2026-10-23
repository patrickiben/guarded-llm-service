"""Numeric contract v1; canonical source: patrickiben/numguard.

This dependency-free module is vendored byte-for-byte by the companion demos.
See NUMERIC_CONTRACT.md for the supported grammar and synchronization process.
It checks numeric values, not units, sentence meaning, or upstream truth.
"""
from __future__ import annotations

import math
import re
from typing import Iterable, List, Optional, Tuple


# Consume malformed separators/exponents as a whole so a prefix cannot pass.
_CANDIDATE = re.compile(
    r"(?<![\w.+\-−])([+\-−]?(?:\d[\d,]*(?:\.\d*)?|\.\d+)"
    r"(?:[eE][+\-−]?\d*)?)"
)
_VALID = re.compile(
    r"[+\-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d*)?|\.\d+)"
    r"(?:[eE][+\-]?\d+)?\Z"
)
_UNSUPPORTED_SEPARATOR = re.compile(r"\d[٫٬．，]\d")


def finite_number(value: float, name: str, nonnegative: bool = False) -> None:
    """Reject booleans, non-numeric values, infinities and NaNs."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (nonnegative and value < 0):
        suffix = "nonnegative finite number" if nonnegative else "finite number"
        raise ValueError(f"{name} must be a {suffix}")


def validate_tolerances(abs_tol: float, rel_tol: float) -> None:
    finite_number(abs_tol, "abs_tol", nonnegative=True)
    finite_number(rel_tol, "rel_tol", nonnegative=True)


def validate_fact_config(
    facts: Iterable[Tuple[str, Optional[float]]],
    required_names: Iterable[str] = (),
    context_values: Iterable[float] = (),
) -> None:
    """Validate names/values before evaluating a draft; configuration errors raise."""
    by_name = {}
    for name, value in facts:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Fact names must be nonempty strings")
        if name in by_name:
            raise ValueError(f"Duplicate fact name: {name!r}")
        if value is not None:
            finite_number(value, f"Fact {name!r}")
        by_name[name] = value
    for value in context_values:
        finite_number(value, "Context value")
    for name in required_names:
        if not isinstance(name, str) or name not in by_name:
            raise ValueError(f"Unknown required fact: {name!r}")
        if by_name[name] is None:
            raise ValueError(f"Required fact {name!r} must have a numeric value")


def extract_numbers(text: str) -> List[Tuple[float, str, int]]:
    """Return (value, original token, offset), preserving signs and exponents.

    Accept decimal digits, ASCII decimal/thousands separators, ASCII or Unicode
    minus, leading decimals and scientific notation. Identifier digits (CP101,
    CP-101, grade3) are outside this grammar. Ambiguous malformed numeric tokens
    raise ValueError, rather than grounding a valid-looking prefix. Write ranges
    using 'to' (e.g. '1 to 4'), not a joined hyphen.
    """
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    if re.search(r"(?<!\w)[+\-−]{2,}(?=\d|\.\d)", text):
        raise ValueError("Unsupported repeated numeric sign")
    if _UNSUPPORTED_SEPARATOR.search(text):
        raise ValueError("Unsupported numeric separator; use ASCII '.' and grouped ','")
    out = []
    for match in _CANDIDATE.finditer(text):
        raw = match.group(1)
        # A comma after a number may delimit a prose list, as in '10, 30'.
        if raw.endswith(",") and not raw.endswith(",,"):
            raw = raw[:-1]
        token = raw.replace("−", "-")
        end = match.start() + len(raw)
        tail = text[end:]
        if (not _VALID.fullmatch(token)
                or re.match(r"(?:[.,]\d|[+\-−]\d)", tail)):
            raise ValueError(f"Unsupported numeric format near {match.group(1)!r}")
        value = float(token.replace(",", ""))
        finite_number(value, f"Number {raw!r}")
        out.append((value, raw, match.start()))
    return out
