"""Canonical scoring helpers for unsupervised anomaly detectors."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def canonical_anomaly_score(model: Any, scaled_features: Any) -> np.ndarray:
    """Return scores where larger values always mean more abnormal.

    Scikit-learn's OneClassSVM and IsolationForest expose ``score_samples``
    values where larger means more normal. The diagnostic layer uses the
    negative of that native score so every downstream component has one
    documented convention.
    """

    if not hasattr(model, "score_samples"):
        raise TypeError("The detector must expose score_samples().")
    model_input = scaled_features
    if not hasattr(model_input, "columns") and hasattr(model, "feature_names_in_"):
        model_input = pd.DataFrame(
            model_input,
            columns=list(model.feature_names_in_),
        )
    scores = -np.asarray(model.score_samples(model_input), dtype=float)
    if scores.ndim != 1 or not np.isfinite(scores).all():
        raise ValueError("The detector returned non-finite or non-vector scores.")
    return scores


def is_anomaly(score: float, threshold: float) -> bool:
    """Apply the canonical inclusive anomaly threshold contract."""

    score_value = float(score)
    threshold_value = float(threshold)
    if not np.isfinite([score_value, threshold_value]).all():
        raise ValueError("Score and threshold must be finite.")
    return score_value >= threshold_value
