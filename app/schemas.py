"""Pydantic request/response models for the API."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from ._numeric import validate_fact_config, validate_tolerances


class FactIn(BaseModel):
    name: str
    value: Optional[float] = Field(default=None, strict=True, allow_inf_nan=False)
    unit: str = ""


class EvaluateRequest(BaseModel):
    text: str = Field(..., description="The generated draft to check.")
    facts: List[FactIn] = Field(default_factory=list, description="Allowed ground-truth facts.")
    banned_phrases: List[str] = Field(default_factory=list)
    required_names: List[str] = Field(default_factory=list)
    abs_tol: float = Field(default=0.05, ge=0, strict=True, allow_inf_nan=False)
    rel_tol: float = Field(default=0.001, ge=0, strict=True, allow_inf_nan=False)

    @model_validator(mode="after")
    def valid_fact_contract(self):
        validate_tolerances(self.abs_tol, self.rel_tol)
        validate_fact_config(((f.name, f.value) for f in self.facts), self.required_names)
        return self


class FindingOut(BaseModel):
    check: str
    severity: str
    message: str


class EvaluateResponse(BaseModel):
    passed: bool
    n_errors: int
    findings: List[FindingOut]
