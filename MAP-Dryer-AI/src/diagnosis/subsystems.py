"""Physical subsystem aggregation without attribution double counting."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .schemas import FeatureEvidence, TemporalPattern


def score_subsystems(
    feature_evidence: Iterable[FeatureEvidence],
    subsystem_config: dict[str, Any],
    temporal_patterns: Iterable[TemporalPattern] | None = None,
) -> dict[str, float]:
    """Aggregate feature attributions and normalize subsystem scores to sum to one.

    If a feature belongs to several subsystems, its attribution is split in
    proportion to the configured membership weights. This prevents accidental
    double counting. Instrumentation-only temporal evidence is added separately.
    """

    subsystem_payload = subsystem_config.get("subsystems", subsystem_config)
    raw_scores = {name: 0.0 for name in subsystem_payload}
    feature_memberships: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for subsystem, details in subsystem_payload.items():
        for feature, weight in details.get("members", {}).items():
            numeric_weight = float(weight)
            if numeric_weight < 0:
                raise ValueError("Subsystem membership weights cannot be negative.")
            feature_memberships[feature].append((subsystem, numeric_weight))

    for evidence in feature_evidence:
        memberships = feature_memberships.get(evidence.feature, [])
        membership_total = sum(weight for _, weight in memberships)
        if membership_total <= 0:
            continue
        for subsystem, weight in memberships:
            raw_scores[subsystem] += evidence.attribution * weight / membership_total

    instrumentation_strength = max(
        (
            pattern.strength
            for pattern in (temporal_patterns or [])
            if pattern.pattern in {"ISOLATED_JUMP", "STUCK"}
        ),
        default=0.0,
    )
    if "instrumentation" in raw_scores and instrumentation_strength > 0:
        raw_scores["instrumentation"] += min(float(instrumentation_strength), 1.0)

    total = sum(raw_scores.values())
    if total <= 0:
        return {name: 0.0 for name in raw_scores}
    return {
        name: float(score / total)
        for name, score in sorted(raw_scores.items())
    }
