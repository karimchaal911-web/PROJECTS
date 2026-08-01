"""Transparent, configuration-driven MAP dryer diagnostic rules."""

from __future__ import annotations

from typing import Any, Iterable

from .schemas import DiagnosisResult, FeatureEvidence, TemporalPattern


def _condition_parts(condition: str) -> tuple[str, set[str]]:
    if ":" not in condition:
        raise ValueError(f"Invalid diagnostic condition: {condition}")
    feature, allowed = condition.split(":", 1)
    return feature, {item.strip() for item in allowed.split("|") if item.strip()}


def _match_feature_condition(
    condition: str, evidence_by_feature: dict[str, FeatureEvidence]
) -> tuple[bool, str | None]:
    feature, allowed = _condition_parts(condition)
    item = evidence_by_feature.get(feature)
    if item is None or item.direction not in allowed:
        return False, None
    return True, f"{feature} {item.direction} (robust z={item.robust_z:.2f})"


def _match_temporal_condition(
    condition: str, patterns: list[TemporalPattern]
) -> tuple[bool, str | None, str | None]:
    feature, allowed = _condition_parts(condition)
    candidates = [
        pattern
        for pattern in patterns
        if (feature == "*" or pattern.feature == feature)
        and pattern.pattern in allowed
    ]
    if not candidates:
        return False, None, None
    winner = max(candidates, key=lambda item: item.strength)
    return (
        True,
        f"{winner.feature} {winner.pattern} ({winner.evidence})",
        winner.feature,
    )


def _match_fraction(matches: list[bool], mode: str = "all") -> float:
    if not matches:
        return 1.0
    if mode == "any":
        return 1.0 if any(matches) else 0.0
    if mode != "all":
        raise ValueError(f"Unsupported condition mode: {mode}")
    return float(sum(matches) / len(matches))


def confidence_band(confidence: float, confidence_config: dict[str, Any]) -> str:
    if confidence > float(confidence_config.get("high_cutoff", 0.70)):
        return "HIGH"
    if confidence >= float(confidence_config.get("medium_cutoff", 0.45)):
        return "MEDIUM"
    return "LOW"


def evaluate_diagnostic_rules(
    feature_evidence: Iterable[FeatureEvidence],
    temporal_patterns: Iterable[TemporalPattern],
    subsystem_scores: dict[str, float],
    rule_config: dict[str, Any],
    threshold_config: dict[str, Any],
) -> list[DiagnosisResult]:
    """Evaluate D01-D08 with explicit evidence, contradictions, and confidence."""

    evidence_items = list(feature_evidence)
    evidence_by_feature = {item.feature: item for item in evidence_items}
    patterns = list(temporal_patterns)
    confidence_config = threshold_config.get("confidence", {})
    weights = confidence_config.get("weights", {})
    required_weight = float(weights.get("required", 0.35))
    supporting_weight = float(weights.get("supporting", 0.20))
    attribution_weight = float(weights.get("attribution", 0.20))
    temporal_weight = float(weights.get("temporal", 0.15))
    contradiction_weight = float(weights.get("contradiction_absence", 0.10))
    if not abs(
        required_weight
        + supporting_weight
        + attribution_weight
        + temporal_weight
        + contradiction_weight
        - 1.0
    ) < 1e-9:
        raise ValueError("Diagnostic confidence weights must sum to 1.0.")

    guard_config = threshold_config.get("instrumentation_guard", {})
    guard_threshold = float(guard_config.get("pattern_strength_threshold", 0.55))
    process_discount = float(guard_config.get("process_rule_discount", 0.50))
    suspected_instrumentation_features = {
        pattern.feature
        for pattern in patterns
        if pattern.pattern in {"ISOLATED_JUMP", "STUCK"}
        and pattern.strength >= guard_threshold
    }

    results: list[DiagnosisResult] = []
    for rule in rule_config.get("rules", []):
        required_conditions = list(rule.get("required", []))
        supporting_conditions = list(rule.get("supporting", []))
        contradiction_conditions = list(rule.get("contradictions", []))
        temporal_conditions = list(rule.get("temporal", []))

        required_matches = []
        supporting_matches = []
        contradiction_matches = []
        temporal_matches = []
        matched_evidence: list[str] = []
        matched_contradictions: list[str] = []
        dependent_features: set[str] = set()

        for condition in required_conditions:
            dependent_features.add(_condition_parts(condition)[0])
            matched, message = _match_feature_condition(condition, evidence_by_feature)
            required_matches.append(matched)
            if message:
                matched_evidence.append(message)
        for condition in supporting_conditions:
            dependent_features.add(_condition_parts(condition)[0])
            matched, message = _match_feature_condition(condition, evidence_by_feature)
            supporting_matches.append(matched)
            if message:
                matched_evidence.append(message)
        for condition in contradiction_conditions:
            matched, message = _match_feature_condition(condition, evidence_by_feature)
            contradiction_matches.append(matched)
            if message:
                matched_contradictions.append(message)

        matched_temporal_features: set[str] = set()
        for condition in temporal_conditions:
            matched, message, feature = _match_temporal_condition(condition, patterns)
            temporal_matches.append(matched)
            if message:
                matched_evidence.append(message)
            if feature:
                matched_temporal_features.add(feature)

        required_fraction = _match_fraction(
            required_matches, str(rule.get("required_mode", "all"))
        )
        supporting_fraction = (
            _match_fraction(supporting_matches, str(rule.get("supporting_mode", "all")))
            if supporting_conditions
            else 0.0
        )
        temporal_fraction = (
            _match_fraction(temporal_matches, str(rule.get("temporal_mode", "all")))
            if temporal_conditions
            else 0.0
        )
        contradiction_fraction = (
            float(sum(contradiction_matches) / len(contradiction_matches))
            if contradiction_matches
            else 0.0
        )

        if required_conditions and required_fraction < 1.0:
            continue
        if rule.get("temporal_required", False) and temporal_fraction <= 0.0:
            continue

        configured_subsystem = str(rule["subsystem"])
        if configured_subsystem == "relevant_subsystem":
            eligible = {
                name: score
                for name, score in subsystem_scores.items()
                if name != "instrumentation"
            }
            resolved_subsystem = (
                max(eligible, key=eligible.get) if eligible else "insufficient_evidence"
            )
            attribution_fraction = max(eligible.values(), default=0.0)
        else:
            resolved_subsystem = configured_subsystem
            attribution_fraction = float(subsystem_scores.get(configured_subsystem, 0.0))

        confidence = (
            required_weight * required_fraction
            + supporting_weight * supporting_fraction
            + attribution_weight * min(max(attribution_fraction, 0.0), 1.0)
            + temporal_weight * temporal_fraction
            + contradiction_weight * (1.0 - contradiction_fraction)
        )

        instrumentation_discount_applied = False
        if configured_subsystem not in {"instrumentation", "relevant_subsystem"}:
            affected = dependent_features & suspected_instrumentation_features
            if affected:
                confidence *= process_discount
                instrumentation_discount_applied = True
                matched_contradictions.append(
                    "Possible instrumentation anomaly affects "
                    + ", ".join(sorted(affected))
                )

        confidence = float(min(max(confidence, 0.0), 1.0))
        minimum = float(
            rule.get(
                "minimum_confidence",
                confidence_config.get("minimum_rule_confidence", 0.30),
            )
        )
        if confidence < minimum:
            continue

        if matched_temporal_features:
            matched_evidence.append(
                "Temporal evidence features: "
                + ", ".join(sorted(matched_temporal_features))
            )
        results.append(
            DiagnosisResult(
                rule_id=str(rule["id"]),
                diagnosis=str(rule["diagnosis"]),
                subsystem=resolved_subsystem,
                confidence=confidence,
                confidence_band=confidence_band(confidence, confidence_config),
                suspected_causes=tuple(str(item) for item in rule.get("suspected_causes", [])),
                evidence=tuple(dict.fromkeys(matched_evidence)),
                contradictory_evidence=tuple(dict.fromkeys(matched_contradictions)),
                recommended_checks=tuple(
                    str(item) for item in rule.get("recommended_checks", [])
                ),
                instrumentation_discount_applied=instrumentation_discount_applied,
            )
        )

    results.sort(key=lambda item: (item.confidence, item.rule_id), reverse=True)
    return results
