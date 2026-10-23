# Numeric contract v1

The canonical implementation is [`numguard/_numeric.py`](https://github.com/patrickiben/numguard/blob/main/numguard/_numeric.py). The service, RAG demo and tool harness vendor the exact same standard-library module to keep their zero-dependency cores independently runnable.

Supported numeric tokens include signed integers and decimals (`-2.3`, `−2.3`), leading decimals (`.5`), scientific notation (`1e9`, `-2.3e-4`), and correctly grouped thousands (`1,200.5`). Unicode decimal digits such as `１９` are accepted with ASCII punctuation. Signs and exponent magnitudes participate in grounding. Joined ranges (`1-4`), malformed grouping (`79,2`), incomplete exponents and non-finite magnitudes fail the numeric-format check; write ranges as `1 to 4`. Digits embedded in letter-led identifiers (`CP101`, `CP-101`, `grade3`), spelled-out numbers, Roman numerals and other numeric languages are outside this grammar.

Only numeric value membership is checked. Units, fact-to-sentence attribution, upstream correctness, completeness and qualitative interpretation are not certified. The configured tolerance can allow nearby values; choose it for the reporting precision in your use case.

Fact names must be unique nonempty strings. Numeric facts, context values and tolerances must be finite; tolerances must be nonnegative. A required fact must exist and have a numeric value. Invalid configuration raises `ValueError` in Python; the HTTP wrapper returns 422. Unsupported numeric tokens in a draft produce a failing report.

## Synchronizing copies

1. Change the canonical module and its regression contract in numguard first.
2. Copy `_numeric.py`, `tests/numeric_contract.json` and `tests/test_numeric_contract.py` into all three companion repositories. Change only the test's package import name.
3. Update the `numeric_contract.json` source digest from `sha256(_numeric.py)` in every repository. The synchronization test checks both that digest and the same adversarial token cases, so implementation changes require an explicit contract update.
4. Run all four full suites and zero-dependency self-tests. Compare the four module SHA-256 values before release; they must be identical. No network access is needed during tests.
