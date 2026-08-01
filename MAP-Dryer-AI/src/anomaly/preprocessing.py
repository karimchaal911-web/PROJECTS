"""Detector-input table helpers."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def build_scaled_feature_table(
    feature_names: Sequence[str],
    split_name: str,
    timestamps,
    scaled_features: pd.DataFrame,
) -> pd.DataFrame:
    """Attach timestamps and split identity to an ordered scaled feature table."""

    ordered_features = list(feature_names)
    missing = [feature for feature in ordered_features if feature not in scaled_features]
    if missing:
        raise KeyError(f"Scaled detector features are missing: {missing}")
    if len(timestamps) != len(scaled_features):
        raise ValueError("Timestamps and scaled features must have equal lengths.")
    split_table = scaled_features.loc[:, ordered_features].reset_index(drop=True).copy()
    split_table.insert(0, "Split", split_name)
    split_table.insert(0, "timestamp", timestamps.to_numpy())
    return split_table
