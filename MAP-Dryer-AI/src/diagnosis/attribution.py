"""Robust and model-sensitive localization of anomalous process states."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from anomaly.scoring import canonical_anomaly_score
from .reference_profile import ReferenceProfile
from .schemas import FeatureEvidence


def _normalize_nonnegative(values: np.ndarray) -> np.ndarray:
    clean = np.clip(np.asarray(values, dtype=float), 0.0, None)
    total = float(clean.sum())
    if total <= 0.0:
        return np.zeros_like(clean)
    return clean / total


def _as_feature_series(
    x_current: pd.Series | pd.DataFrame | dict[str, float],
    feature_names: tuple[str, ...],
) -> pd.Series:
    if isinstance(x_current, pd.DataFrame):
        if len(x_current) != 1:
            raise ValueError("x_current DataFrame must contain exactly one row.")
        current = x_current.iloc[0]
    else:
        current = pd.Series(x_current)
    missing = sorted(set(feature_names) - set(current.index))
    if missing:
        raise ValueError(f"Current observation is missing features: {missing}")
    current = pd.to_numeric(current.loc[list(feature_names)], errors="raise").astype(float)
    if not np.isfinite(current.to_numpy()).all():
        raise ValueError("Current observation contains missing or non-finite values.")
    return current


def localize_anomaly(
    x_current: pd.Series | pd.DataFrame | dict[str, float],
    model: Any,
    scaler: Any,
    reference_profile: ReferenceProfile,
    feature_metadata: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    top_n: int | None = None,
) -> list[FeatureEvidence]:
    """Rank feature evidence using robust deviation and OCSVM sensitivity.

    The counterfactual contribution follows the canonical score convention:
    replacing a feature by its train-only median contributes when it lowers
    the anomaly score, so ``contribution = max(0, base_score - cf_score)``.
    """

    settings = (config or {}).get("attribution", config or {})
    epsilon = float(settings.get("epsilon", 1e-9))
    deviation_weight = float(settings.get("robust_deviation_weight", 0.40))
    model_weight = float(settings.get("counterfactual_weight", 0.60))
    if not np.isclose(deviation_weight + model_weight, 1.0):
        raise ValueError("Attribution weights must sum to 1.0.")

    feature_names = reference_profile.feature_names
    current = _as_feature_series(x_current, feature_names)
    metadata_payload = (
        (feature_metadata or {}).get("features", feature_metadata)
        if feature_metadata is not None
        else reference_profile.feature_metadata
    )

    medians = np.array(
        [reference_profile.statistics[name]["median"] for name in feature_names],
        dtype=float,
    )
    iqrs = np.array(
        [reference_profile.statistics[name]["iqr"] for name in feature_names],
        dtype=float,
    )
    robust_z = (current.to_numpy() - medians) / np.maximum(iqrs, epsilon)
    deviation_component = _normalize_nonnegative(np.abs(robust_z))

    current_frame = current.to_frame().T
    scaled_current = scaler.transform(current_frame.loc[:, list(feature_names)])
    base_score = float(canonical_anomaly_score(model, scaled_current)[0])
    raw_contributions = np.zeros(len(feature_names), dtype=float)
    for index, feature in enumerate(feature_names):
        counterfactual = current.copy()
        counterfactual.loc[feature] = medians[index]
        scaled_counterfactual = scaler.transform(counterfactual.to_frame().T)
        counterfactual_score = float(
            canonical_anomaly_score(model, scaled_counterfactual)[0]
        )
        raw_contributions[index] = max(0.0, base_score - counterfactual_score)
    model_component = _normalize_nonnegative(raw_contributions)

    combined = deviation_weight * deviation_component + model_weight * model_component
    combined = _normalize_nonnegative(combined)
    direction_threshold = float(settings.get("direction_z_threshold", 1.5))

    evidence: list[FeatureEvidence] = []
    for index, feature in enumerate(feature_names):
        z_value = float(robust_z[index])
        direction = (
            "HIGH"
            if z_value >= direction_threshold
            else "LOW"
            if z_value <= -direction_threshold
            else "NORMAL"
        )
        metadata = dict(metadata_payload.get(feature, {}))
        evidence.append(
            FeatureEvidence(
                feature=feature,
                direction=direction,
                current_value=float(current.loc[feature]),
                reference_median=float(medians[index]),
                robust_z=z_value,
                robust_deviation=abs(z_value),
                counterfactual_contribution=float(model_component[index]),
                attribution=float(combined[index]),
                unit=metadata.get("unit"),
                kind=str(metadata.get("kind", "raw")),
                parents=tuple(metadata.get("parents", [])),
                subsystems=tuple(metadata.get("subsystems", [])),
                criticality=str(metadata.get("criticality", "medium")),
                explanation_group=metadata.get("explanation_group"),
            )
        )

    evidence.sort(
        key=lambda item: (item.attribution, item.robust_deviation, item.feature),
        reverse=True,
    )
    if top_n is None:
        return evidence
    return evidence[: int(top_n)]
