"""Stable, JSON-serializable diagnostic data contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


@dataclass(frozen=True)
class FeatureEvidence:
    feature: str
    direction: str
    current_value: float
    reference_median: float
    robust_z: float
    robust_deviation: float
    counterfactual_contribution: float
    attribution: float
    unit: str | None = None
    kind: str = "raw"
    parents: tuple[str, ...] = ()
    subsystems: tuple[str, ...] = ()
    criticality: str = "medium"
    explanation_group: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True)
class TemporalPattern:
    feature: str
    pattern: str
    strength: float
    direction: str
    evidence: str
    window_observations: int

    def as_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True)
class DiagnosisResult:
    rule_id: str
    diagnosis: str
    subsystem: str
    confidence: float
    confidence_band: str
    suspected_causes: tuple[str, ...]
    evidence: tuple[str, ...]
    contradictory_evidence: tuple[str, ...]
    recommended_checks: tuple[str, ...]
    instrumentation_discount_applied: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True)
class DiagnosticEvent:
    event_id: str
    timestamp: Any
    anomaly: bool
    anomaly_score: float
    threshold: float
    severity: str
    severity_score: float
    severity_basis: str
    primary_subsystem: str
    subsystem_scores: dict[str, float]
    top_features: tuple[FeatureEvidence, ...]
    diagnoses: tuple[DiagnosisResult, ...]
    temporal_patterns: tuple[TemporalPattern, ...]
    operator_status: str = "UNREVIEWED"
    confirmed_fault: str | None = None
    confirmed_root_cause: str | None = None
    maintenance_action: str | None = None
    process_action: str | None = None
    quality_impact: str | None = None
    lab_moisture_after_event: float | None = None
    notes: str | None = None
    diagnostic_version: str = "diag_v1.0"
    config_versions: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return _json_value(payload)
