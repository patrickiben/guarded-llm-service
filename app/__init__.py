"""guarded-llm-service -- a FastAPI service that serves the numguard guardrail.

POST a draft + its allowed facts to /evaluate and get a pass/fail grounding
verdict; /health for liveness; /metrics for Prometheus-style request and
guardrail counters. The guard core (app/guard.py) and metrics (app/metrics.py)
are pure standard library, so they run and self-test with no dependencies; the
HTTP layer is the only part that needs FastAPI.
"""
__version__ = "0.1.0"
