"""Pydantic request/response models for the API."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class FactIn(BaseModel):
    name: str
    value: Optional[float] = None
    unit: str = ""


class EvaluateRequest(BaseModel):
    text: str = Field(..., description="The generated draft to check.")
    facts: List[FactIn] = Field(default_factory=list, description="Allowed ground-truth facts.")
    banned_phrases: List[str] = Field(default_factory=list)
    required_names: List[str] = Field(default_factory=list)
    abs_tol: float = 0.05
    rel_tol: float = 0.001


class FindingOut(BaseModel):
    check: str
    severity: str
    message: str


class EvaluateResponse(BaseModel):
    passed: bool
    n_errors: int
    findings: List[FindingOut]
