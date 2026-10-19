# guarded-llm-service

**A FastAPI microservice that serves the [`numguard`](https://github.com/patrickiben/numguard) guardrail over HTTP — the "ship it beyond the notebook" piece: Docker, CI, health checks, and Prometheus-style metrics.**

![ci](https://github.com/patrickiben/guarded-llm-service/actions/workflows/ci.yml/badge.svg)
&nbsp;·&nbsp; FastAPI · Docker · Python ≥ 3.9 · MIT

`POST` a generated draft plus its allowed facts and get a deterministic pass/fail grounding verdict: every number in the draft must be traceable to a fact, banned qualitative claims are caught, and required facts must be present. The guardrail itself (`app/guard.py`) and the metrics (`app/metrics.py`) are **pure standard library** — so they run and self-test with zero dependencies — and the FastAPI layer wraps them in a production-shaped service.

---

## Quickstart

**Local:**
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Docker:**
```bash
docker build -t guarded-llm-service .
docker run -p 8000:8000 guarded-llm-service
```

**No dependencies at all** (core logic only):
```bash
python selftest.py
```

---

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | Liveness probe (used by the Docker `HEALTHCHECK`). |
| `POST` | `/evaluate` | Evaluate a draft against its facts → `{passed, n_errors, findings}`. |
| `GET`  | `/metrics` | Prometheus exposition (requests, evaluations, gate failures, latency quantiles). |
| `GET`  | `/metrics.json` | The same metrics as JSON. |

Every response carries an `X-Response-Time-ms` header from the timing middleware.

---

## Example

```bash
curl -X POST localhost:8000/evaluate -H 'content-type: application/json' --data @examples/request.json
```

Request (`examples/request.json`) contains two fabricated numbers and a banned claim. Real response:

```json
{
  "passed": false,
  "n_errors": 4,
  "findings": [
    {"check": "numbers_grounded",   "severity": "ERROR", "message": "Untraceable number '18' is not supported by any fact."},
    {"check": "numbers_grounded",   "severity": "ERROR", "message": "Untraceable number '75.0' is not supported by any fact."},
    {"check": "unsupported_claims", "severity": "ERROR", "message": "Unsupported qualitative claim: 'well tolerated'."},
    {"check": "required_facts",     "severity": "ERROR", "message": "Required fact 'pct_any_ae' (79.2 %) is missing from the text."}
  ]
}
```

`GET /metrics` (real output):

```
# HELP guard_requests_total Total HTTP requests served.
# TYPE guard_requests_total counter
guard_requests_total 3
# HELP guard_evaluations_total Total guardrail evaluations.
# TYPE guard_evaluations_total counter
guard_evaluations_total 2
# HELP guard_gate_failures_total Drafts that failed the guardrail.
# TYPE guard_gate_failures_total counter
guard_gate_failures_total 1
# TYPE guard_request_latency_ms summary
guard_request_latency_ms{quantile="0.5"} 0.9
guard_request_latency_ms{quantile="0.95"} 0.92
```

---

## How it's built (and why)

```
app/
├── guard.py     # the guardrail core      — pure stdlib, mirrors numguard
├── metrics.py   # counters + p50/p95      — pure stdlib, thread-safe, Prometheus exposition
├── schemas.py   # pydantic request/response models
└── main.py      # FastAPI: routes + timing middleware  (the only part needing fastapi)
```

The design deliberately keeps the **business logic dependency-free** so it has a runnable proof (`python selftest.py`) that needs nothing installed, while the HTTP concerns live in a thin, swappable layer. The Dockerfile runs as a **non-root user** with a built-in `HEALTHCHECK`; the metrics are real (latency is sampled in a bounded window) but intentionally in-memory — a production deployment would swap in `prometheus_client` / OpenTelemetry behind the same call sites.

---

## Tests & CI

```bash
pytest -q        # 10 passed (5 core, 5 API)
```

GitHub Actions runs three things on every push: the zero-dependency core self-test, the full pytest suite (with deps), and a **Docker build + live container smoke test** (`docker run` → `curl /health` and `/evaluate`). So "it builds and serves" is proven by CI, not just claimed.

## Deploy

The image runs on any container host — Fly.io, Render, Google Cloud Run, AWS App Runner, a Kubernetes pod. It listens on `:8000`, exposes `/health` for probes, and `/metrics` for scraping.

## Roadmap

- [ ] Pluggable **model backend** (route a real local/cloud LLM to *generate*, then guard its output)
- [ ] Shared guard core imported from the `numguard` package (instead of vendored)
- [ ] Structured request logging + trace IDs
- [ ] Rate limiting and API-key auth for a public deployment

## Status & honesty note

A **working proof-of-concept** that demonstrates production *shape* — containerized, health-checked, observable, CI-built — around a real, tested guardrail. It is not a hardened production service (in-memory metrics, no auth/rate-limiting yet). The point it proves: I ship beyond the notebook.

## License

MIT — see [LICENSE](LICENSE). Built by Patrick Iben (`p.iben@saeny.net`). Companion projects: [`numguard`](https://github.com/patrickiben/numguard), [`grounded-rag`](https://github.com/patrickiben/grounded-rag).
