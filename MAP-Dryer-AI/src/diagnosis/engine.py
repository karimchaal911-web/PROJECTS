"""End-to-end anomaly diagnosis and operator-safe presentation."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd

from .attribution import localize_anomaly
from .reference_profile import ReferenceProfile
from .rules import evaluate_diagnostic_rules
from .schemas import DiagnosticEvent
from .severity import calculate_severity
from .subsystems import score_subsystems
from .temporal import analyze_temporal_patterns


def _event_id(timestamp: Any, anomaly_score: float, diagnostic_version: str) -> str:
    timestamp_text = pd.Timestamp(timestamp).isoformat()
    payload = f"{diagnostic_version}|{timestamp_text}|{float(anomaly_score):.12g}"
    return "MAPD-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def diagnose_anomaly(
    *,
    timestamp: Any,
    anomaly: bool,
    anomaly_score: float,
    threshold: float,
    x_current: pd.Series | pd.DataFrame | dict[str, float] | None,
    history_df: pd.DataFrame | None,
    model: Any,
    scaler: Any,
    reference_profile: ReferenceProfile,
    feature_metadata: dict[str, Any],
    subsystem_config: dict[str, Any],
    rule_config: dict[str, Any],
    threshold_config: dict[str, Any],
    config_versions: dict[str, str] | None = None,
    approved_limit_crossing: bool = False,
    confirmed_fault: str | None = None,
    confirmed_root_cause: str | None = None,
    lab_moisture_after_event: float | None = None,
    notes: str | None = None,
) -> DiagnosticEvent:
    """Diagnose one detector event without changing detector state or output.

    The diagnostic branch is bypassed for normal observations. Mechanical root
    cause fields remain empty unless direct trusted evidence is supplied by the
    caller.
    """

    score_value = float(anomaly_score)
    threshold_value = float(threshold)
    if not np.isfinite([score_value, threshold_value]).all():
        raise ValueError("Anomaly score and threshold must be finite.")
    diagnostic_version = str(threshold_config.get("diagnostic_version", "diag_v1.0"))
    identifier = _event_id(timestamp, score_value, diagnostic_version)

    if not anomaly:
        return DiagnosticEvent(
            event_id=identifier,
            timestamp=timestamp,
            anomaly=False,
            anomaly_score=score_value,
            threshold=threshold_value,
            severity="INFO",
            severity_score=0.0,
            severity_basis="Monitoring only; no anomaly event was raised.",
            primary_subsystem="monitoring_only",
            subsystem_scores={},
            top_features=(),
            diagnoses=(),
            temporal_patterns=(),
            confirmed_fault=confirmed_fault,
            confirmed_root_cause=confirmed_root_cause,
            lab_moisture_after_event=lab_moisture_after_event,
            notes=notes,
            diagnostic_version=diagnostic_version,
            config_versions=dict(config_versions or {}),
        )

    if x_current is None or history_df is None:
        raise ValueError("An anomalous event requires current features and history.")

    all_evidence = localize_anomaly(
        x_current=x_current,
        model=model,
        scaler=scaler,
        reference_profile=reference_profile,
        feature_metadata=feature_metadata,
        config=threshold_config,
        top_n=None,
    )
    patterns = analyze_temporal_patterns(
        history_df=history_df,
        reference_profile=reference_profile,
        config=threshold_config,
    )
    subsystem_scores = score_subsystems(
        all_evidence,
        subsystem_config,
        temporal_patterns=patterns,
    )
    diagnoses = evaluate_diagnostic_rules(
        all_evidence,
        patterns,
        subsystem_scores,
        rule_config,
        threshold_config,
    )
    primary_subsystem = (
        max(subsystem_scores, key=subsystem_scores.get)
        if subsystem_scores and max(subsystem_scores.values()) > 0
        else "insufficient_diagnostic_evidence"
    )
    severity, severity_score, severity_basis = calculate_severity(
        anomaly_score=score_value,
        threshold=threshold_value,
        feature_evidence=all_evidence,
        temporal_patterns=patterns,
        config=threshold_config,
        approved_limit_crossing=approved_limit_crossing,
    )
    top_n = int(threshold_config.get("attribution", {}).get("top_n", 5))
    return DiagnosticEvent(
        event_id=identifier,
        timestamp=timestamp,
        anomaly=True,
        anomaly_score=score_value,
        threshold=threshold_value,
        severity=severity,
        severity_score=severity_score,
        severity_basis=severity_basis,
        primary_subsystem=primary_subsystem,
        subsystem_scores=subsystem_scores,
        top_features=tuple(all_evidence[:top_n]),
        diagnoses=tuple(diagnoses),
        temporal_patterns=tuple(patterns),
        confirmed_fault=confirmed_fault,
        confirmed_root_cause=confirmed_root_cause,
        lab_moisture_after_event=lab_moisture_after_event,
        notes=notes,
        diagnostic_version=diagnostic_version,
        config_versions=dict(config_versions or {}),
    )


def format_operator_report(event: DiagnosticEvent) -> str:
    """Return an uncertainty-aware operator summary with no root-cause assertion."""

    if not event.anomaly:
        return (
            f"NORMAL MONITORING | Score {event.anomaly_score:.4f} is below "
            f"threshold {event.threshold:.4f}; diagnosis was not invoked."
        )
    if event.diagnoses:
        primary = event.diagnoses[0]
        diagnosis_text = primary.diagnosis
        confidence_text = f"{primary.confidence:.0%} ({primary.confidence_band})"
        suspected = ", ".join(primary.suspected_causes[:3]) or "none listed"
        checks = "; ".join(
            item.rstrip(".") for item in primary.recommended_checks[:3]
        ) or "review event evidence"
    else:
        diagnosis_text = "Insufficient diagnostic evidence"
        confidence_text = "not assigned"
        suspected = "none assigned"
        checks = "review the ranked evidence and process trends"
    feature_text = ", ".join(
        f"{item.feature} {item.direction} ({item.attribution:.0%})"
        for item in event.top_features[:3]
    ) or "no ranked feature evidence"
    return (
        f"ANOMALY DETECTED | Severity: {event.severity} | Primary subsystem: "
        f"{event.primary_subsystem} | Probable diagnosis: {diagnosis_text} | "
        f"Confidence: {confidence_text}. Observed evidence: {feature_text}. "
        f"Suspected causes requiring verification: {suspected}. Recommended "
        f"checks: {checks}. {event.severity_basis}"
    )
