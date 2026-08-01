"""Regression-model evaluation helpers."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import max_error, mean_absolute_error, mean_squared_error, r2_score


def calculate_regression_metrics(actual, predicted) -> dict[str, float]:
    """Return the common soft-sensor metrics used by Notebook 03."""

    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": float(np.sqrt(mean_squared_error(actual, predicted))),
        "R2": float(r2_score(actual, predicted)),
        "Maximum absolute error": float(max_error(actual, predicted)),
    }
