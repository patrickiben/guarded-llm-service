"""In-memory request & guardrail metrics, with Prometheus-style exposition.

Pure standard library; thread-safe. Keeps a bounded window of latency samples
for p50/p95. For a single-instance demo this is plenty; a production deployment
would swap in prometheus_client / OpenTelemetry behind the same call sites.
"""
from __future__ import annotations

import threading
from typing import Dict, List


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


class Metrics:
    def __init__(self, max_samples: int = 1024):
        self._lock = threading.Lock()
        self.max_samples = max_samples
        self.requests = 0
        self.errors = 0
        self.evaluations = 0
        self.gate_failures = 0
        self._latencies: List[float] = []

    def record_request(self, status: int, dur_ms: float) -> None:
        with self._lock:
            self.requests += 1
            if status >= 500:
                self.errors += 1
            self._latencies.append(dur_ms)
            if len(self._latencies) > self.max_samples:
                self._latencies.pop(0)

    def record_evaluation(self, passed: bool) -> None:
        with self._lock:
            self.evaluations += 1
            if not passed:
                self.gate_failures += 1

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            lat = list(self._latencies)
        return {
            "requests": self.requests,
            "errors": self.errors,
            "evaluations": self.evaluations,
            "gate_failures": self.gate_failures,
            "latency_ms_p50": round(percentile(lat, 0.5), 2),
            "latency_ms_p95": round(percentile(lat, 0.95), 2),
            "latency_ms_max": round(max(lat), 2) if lat else 0.0,
        }

    def prometheus(self) -> str:
        s = self.snapshot()
        lines = [
            "# HELP guard_requests_total Total HTTP requests served.",
            "# TYPE guard_requests_total counter",
            f"guard_requests_total {s['requests']}",
            "# HELP guard_errors_total Total 5xx responses.",
            "# TYPE guard_errors_total counter",
            f"guard_errors_total {s['errors']}",
            "# HELP guard_evaluations_total Total guardrail evaluations.",
            "# TYPE guard_evaluations_total counter",
            f"guard_evaluations_total {s['evaluations']}",
            "# HELP guard_gate_failures_total Drafts that failed the guardrail.",
            "# TYPE guard_gate_failures_total counter",
            f"guard_gate_failures_total {s['gate_failures']}",
            "# HELP guard_request_latency_ms Request latency in milliseconds.",
            "# TYPE guard_request_latency_ms summary",
            f'guard_request_latency_ms{{quantile="0.5"}} {s["latency_ms_p50"]}',
            f'guard_request_latency_ms{{quantile="0.95"}} {s["latency_ms_p95"]}',
        ]
        return "\n".join(lines) + "\n"
