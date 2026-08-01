"""Threshold calibration and candidate-rate helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calibrate_conformal_threshold(
    calibration_scores,
    target_candidate_rate: float,
) -> tuple[float, int]:
    """Return a finite-sample upper-tail threshold and its order rank."""

    scores = np.asarray(calibration_scores, dtype=float)
    if scores.ndim != 1 or len(scores) == 0 or not np.isfinite(scores).all():
        raise ValueError("Calibration scores must be a finite non-empty vector.")
    if not 0 < target_candidate_rate < 1:
        raise ValueError("Target candidate rate must lie strictly between 0 and 1.")
    order_rank = int(np.ceil((len(scores) + 1) * (1 - target_candidate_rate)))
    order_rank = min(max(order_rank, 1), len(scores))
    return float(np.sort(scores)[order_rank - 1]), order_rank


def candidate_rate(score_table: pd.DataFrame, split_name: str) -> float:
    """Return the percentage of raw candidates in one named split."""

    split_rows = score_table.loc[score_table["Split"] == split_name]
    if split_rows.empty:
        raise ValueError(f"No rows found for split {split_name!r}.")
    return float(100 * split_rows["Raw anomaly flag"].mean())
