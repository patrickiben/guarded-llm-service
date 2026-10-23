"""FastAPI application: serves the numguard guardrail over HTTP."""
from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from .guard import evaluate_text
from .metrics import Metrics
from .schemas import EvaluateRequest, EvaluateResponse

app = FastAPI(
    title="guarded-llm-service",
    version="0.1.0",
    description="Serves numguard numeric-membership checks: recognized values must be "
                "allowed facts; listed phrases and missing required values are flagged.",
)
metrics = Metrics()


@app.middleware("http")
async def record_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur_ms = (time.perf_counter() - start) * 1000.0
    metrics.record_request(response.status_code, dur_ms)
    response.headers["X-Response-Time-ms"] = f"{dur_ms:.2f}"
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "guarded-llm-service", "version": app.version}


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest):
    facts = [{"name": f.name, "value": f.value, "unit": f.unit} for f in req.facts]
    report = evaluate_text(
        req.text, facts, req.banned_phrases, req.required_names, req.abs_tol, req.rel_tol
    )
    metrics.record_evaluation(report["passed"])
    return report


@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    return metrics.prometheus()


@app.get("/metrics.json")
def json_metrics():
    return metrics.snapshot()
