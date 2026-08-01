"""Cadence-aware temporal symptom classification for diagnosis."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .reference_profile import ReferenceProfile
from .schemas import TemporalPattern


def _strength(value: float, threshold: float) -> float:
    if threshold <= 0:
        return 1.0
    return float(min(max(value / threshold, 0.0), 1.0))


def _related_features(feature: str, profile: ReferenceProfile) -> list[str]:
    metadata = profile.feature_metadata.get(feature, {})
    feature_subsystems = set(metadata.get("subsystems", []))
    related = []
    for candidate, candidate_metadata in profile.feature_metadata.items():
        if candidate == feature:
            continue
        if feature_subsystems & set(candidate_metadata.get("subsystems", [])):
            related.append(candidate)
    return related


def analyze_temporal_patterns(
    history_df: pd.DataFrame,
    reference_profile: ReferenceProfile,
    config: dict[str, Any],
) -> list[TemporalPattern]:
    """Classify sudden, drift, oscillation, stuck, inconsistent, and persistent behavior."""

    settings = config.get("temporal", config)
    window_size = int(settings.get("history_window", 6))
    feature_names = [
        name
        for name in reference_profile.feature_names
        if reference_profile.feature_metadata.get(name, {}).get("kind", "raw") == "raw"
    ]
    available_features = [name for name in feature_names if name in history_df.columns]
    if not available_features:
        return []
    history = history_df.loc[:, available_features].tail(window_size).astype(float)
    if len(history) < 2 or not np.isfinite(history.to_numpy()).all():
        return []

    sudden_threshold = float(settings.get("sudden_delta_scale", 2.5))
    drift_threshold = float(settings.get("drift_slope_scale", 0.45))
    drift_consistency_threshold = float(
        settings.get("drift_direction_consistency", 0.75)
    )
    oscillation_reversals = int(settings.get("oscillation_min_reversals", 3))
    oscillation_std_ratio = float(settings.get("oscillation_std_iqr_ratio", 0.55))
    stuck_observations = int(settings.get("stuck_observations", 4))
    stuck_tolerance_fraction = float(
        settings.get("stuck_tolerance_iqr_fraction", 0.01)
    )
    related_movement_fraction = float(
        settings.get("related_movement_iqr_fraction", 0.25)
    )
    context_related_scale = float(settings.get("context_related_delta_scale", 1.0))
    persistent_observations = int(settings.get("persistent_observations", 2))
    persistent_z_threshold = float(settings.get("persistent_z_threshold", 1.5))
    epsilon = 1e-9

    patterns: list[TemporalPattern] = []
    sudden_ratios: dict[str, float] = {}
    sudden_directions: dict[str, str] = {}
    movement_ranges = {
        feature: float(np.ptp(history[feature].to_numpy(dtype=float)))
        / max(float(reference_profile.statistics[feature]["iqr"]), epsilon)
        for feature in available_features
    }

    for feature in available_features:
        values = history[feature].to_numpy(dtype=float)
        stats = reference_profile.statistics[feature]
        iqr = max(float(stats["iqr"]), epsilon)
        delta_scale = max(float(stats["delta_iqr"]), 0.05 * iqr, epsilon)
        delta = float(values[-1] - values[-2])
        centered_delta = delta - float(stats.get("delta_median", 0.0))
        sudden_ratio = abs(centered_delta) / delta_scale
        sudden_ratios[feature] = sudden_ratio
        sudden_directions[feature] = "SUDDEN_RISE" if delta > 0 else "SUDDEN_DROP"
        if sudden_ratio >= sudden_threshold:
            patterns.append(
                TemporalPattern(
                    feature=feature,
                    pattern=sudden_directions[feature],
                    strength=_strength(sudden_ratio, sudden_threshold),
                    direction="HIGH" if delta > 0 else "LOW",
                    evidence=(
                        f"Last change {delta:.4g} equals {sudden_ratio:.2f} "
                        "reference delta scales."
                    ),
                    window_observations=len(values),
                )
            )

        x_axis = np.arange(len(values), dtype=float)
        slope = float(np.polyfit(x_axis, values, 1)[0])
        differences = np.diff(values)
        nonzero = differences[np.abs(differences) > epsilon]
        consistency = (
            max(np.mean(nonzero > 0), np.mean(nonzero < 0))
            if len(nonzero)
            else 0.0
        )
        slope_ratio = abs(slope) / iqr
        if slope_ratio >= drift_threshold and consistency >= drift_consistency_threshold:
            patterns.append(
                TemporalPattern(
                    feature=feature,
                    pattern="DRIFT",
                    strength=min(
                        _strength(slope_ratio, drift_threshold)
                        * _strength(consistency, drift_consistency_threshold),
                        1.0,
                    ),
                    direction="HIGH" if slope > 0 else "LOW",
                    evidence=(
                        f"Window slope {slope:.4g} with {consistency:.0%} "
                        "one-direction movement."
                    ),
                    window_observations=len(values),
                )
            )

        signs = np.sign(differences[np.abs(differences) > epsilon])
        reversals = int(np.sum(signs[1:] != signs[:-1])) if len(signs) > 1 else 0
        std_ratio = float(np.std(values, ddof=0)) / iqr
        if reversals >= oscillation_reversals and std_ratio >= oscillation_std_ratio:
            patterns.append(
                TemporalPattern(
                    feature=feature,
                    pattern="OSCILLATION",
                    strength=min(
                        _strength(reversals, oscillation_reversals)
                        * _strength(std_ratio, oscillation_std_ratio),
                        1.0,
                    ),
                    direction="BIDIRECTIONAL",
                    evidence=(
                        f"{reversals} direction reversals; rolling standard "
                        f"deviation is {std_ratio:.2f} reference IQR."
                    ),
                    window_observations=len(values),
                )
            )

        tolerance = max(stuck_tolerance_fraction * iqr, epsilon)
        unchanged_run = 1
        for difference in differences[::-1]:
            if abs(difference) <= tolerance:
                unchanged_run += 1
            else:
                break
        related = [name for name in _related_features(feature, reference_profile) if name in history]
        related_movement = max(
            (movement_ranges.get(name, 0.0) for name in related), default=0.0
        )
        if (
            unchanged_run >= stuck_observations
            and related_movement >= related_movement_fraction
        ):
            patterns.append(
                TemporalPattern(
                    feature=feature,
                    pattern="STUCK",
                    strength=min(
                        _strength(unchanged_run, stuck_observations)
                        * _strength(related_movement, related_movement_fraction),
                        1.0,
                    ),
                    direction="UNCHANGED",
                    evidence=(
                        f"Near-identical for {unchanged_run} observations while "
                        f"related movement reached {related_movement:.2f} reference IQR."
                    ),
                    window_observations=len(values),
                )
            )

        if len(values) >= persistent_observations:
            recent = values[-persistent_observations:]
            robust_z = (recent - float(stats["median"])) / iqr
            high = np.all(robust_z >= persistent_z_threshold)
            low = np.all(robust_z <= -persistent_z_threshold)
            if high or low:
                patterns.append(
                    TemporalPattern(
                        feature=feature,
                        pattern="PERSISTENT",
                        strength=min(float(np.mean(np.abs(robust_z))) / persistent_z_threshold, 1.0),
                        direction="HIGH" if high else "LOW",
                        evidence=(
                            f"Abnormal in the same direction for the last "
                            f"{persistent_observations} observations."
                        ),
                        window_observations=len(values),
                    )
                )

    for feature, sudden_ratio in sudden_ratios.items():
        if sudden_ratio < sudden_threshold:
            continue
        related = [name for name in _related_features(feature, reference_profile) if name in sudden_ratios]
        corroboration = max((sudden_ratios[name] for name in related), default=0.0)
        if corroboration < context_related_scale:
            patterns.append(
                TemporalPattern(
                    feature=feature,
                    pattern="ISOLATED_JUMP",
                    strength=min(
                        _strength(sudden_ratio, sudden_threshold)
                        * (1.0 - min(corroboration / max(context_related_scale, epsilon), 1.0)),
                        1.0,
                    ),
                    direction=(
                        "HIGH" if sudden_directions[feature] == "SUDDEN_RISE" else "LOW"
                    ),
                    evidence=(
                        f"Strong isolated change ({sudden_ratio:.2f} delta scales) "
                        f"with related-variable response {corroboration:.2f}."
                    ),
                    window_observations=len(history),
                )
            )

    patterns.sort(key=lambda item: (item.strength, item.feature, item.pattern), reverse=True)
    return patterns
