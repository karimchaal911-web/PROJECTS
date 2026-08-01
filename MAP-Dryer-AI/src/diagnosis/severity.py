"""Model-based operational severity, separate from diagnostic confidence."""

from __future__ import annotations

from typing import Any, Iterable

from .schemas import FeatureEvidence, TemporalPattern


def calculate_severity(
    anomaly_score: float,
    threshold: float,
    feature_evidence: Iterable[FeatureEvidence],
    temporal_patterns: Iterable[TemporalPattern],
    config: dict[str, Any],
    approved_limit_crossing: bool = False,
) -> tuple[str, float, str]:
    settings = config.get("severity", config)
    weights = settings.get("weights", {})
    distance_weight = float(weights.get("distance_from_threshold", 0.45))
    persistence_weight = float(weights.get("persistence", 0.20))
    critical_weight = float(weights.get("critical_features", 0.25))
    limits_weight = float(weights.get("approved_limit_crossing", 0.10))
    if not abs(distance_weight + persistence_weight + critical_weight + limits_weight - 1.0) < 1e-9:
        raise ValueError("Severity weights must sum to 1.0.")

    distance_ratio = max(float(anomaly_score) - float(threshold), 0.0) / max(
        abs(float(threshold)), 1e-9
    )
    distance_component = min(
        distance_ratio / max(float(settings.get("high_distance_ratio", 0.50)), 1e-9),
        1.0,
    )
    patterns = list(temporal_patterns)
    persistence_component = max(
        (pattern.strength for pattern in patterns if pattern.pattern == "PERSISTENT"),
        default=0.0,
    )
    critical_z = float(settings.get("critical_feature_z", 2.50))
    critical_items = [
        item
        for item in feature_evidence
        if item.criticality == "high" and item.robust_deviation >= critical_z
    ]
    critical_component = min(len(critical_items) / 2.0, 1.0)
    score = (
        distance_weight * distance_component
        + persistence_weight * persistence_component
        + critical_weight * critical_component
        + limits_weight * float(bool(approved_limit_crossing))
    )
    high_cutoff = float(settings.get("high_cutoff", 0.70))
    moderate_cutoff = float(settings.get("moderate_cutoff", 0.35))
    severity = "HIGH" if score >= high_cutoff else "MODERATE" if score >= moderate_cutoff else "INFO"
    return severity, float(score), str(
        settings.get(
            "statement",
            "Model-based operational severity; not a safety classification.",
        )
    )
