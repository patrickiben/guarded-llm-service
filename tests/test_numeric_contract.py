"""The same adversarial contract is shipped with every vendored parser."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import _numeric

CONTRACT = json.loads(Path(__file__).with_name("numeric_contract.json").read_text())


def test_vendored_source_matches_contract_digest():
    assert hashlib.sha256(Path(_numeric.__file__).read_bytes()).hexdigest() == CONTRACT["source_sha256"]


@pytest.mark.parametrize("case", CONTRACT["valid"])
def test_numeric_values_and_original_offsets(case):
    found = _numeric.extract_numbers(case["text"])
    assert [value for value, _, _ in found] == case["values"]
    for _, raw, offset in found:
        assert case["text"][offset:offset + len(raw)] == raw


@pytest.mark.parametrize("text", CONTRACT["invalid"])
def test_ambiguous_numeric_tokens_fail_instead_of_parsing_a_prefix(text):
    with pytest.raises(ValueError):
        _numeric.extract_numbers(text)
