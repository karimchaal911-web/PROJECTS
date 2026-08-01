"""Synthetic detector-sensitivity scenarios."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from features.engineering import recompute_engineered_features


def build_synthetic_validation_scenario(
    validation_features: pd.DataFrame,
    normal_reference: pd.DataFrame,
    direct_process_features: Sequence[str],
    model_features: Sequence[str],
    scaler,
    features_per_row: int,
    shift_standard_deviations: float,
    random_state: int,
) -> pd.DataFrame:
    """Create coherent outward-shifted validation rows and scale them."""

    direct_features = list(direct_process_features)
    ordered_model_features = list(model_features)
    if not 1 <= features_per_row <= len(direct_features):
        raise ValueError("features_per_row must fit within direct_process_features.")
    synthetic_direct = validation_features.loc[:, direct_features].reset_index(
        drop=True
    ).copy()
    reference_center = normal_reference.loc[:, direct_features].median()
    reference_scale = normal_reference.loc[:, direct_features].std(ddof=0)
    if (reference_scale <= 0).any():
        raise ValueError("Synthetic testing requires variable reference features.")

    scenario_rng = np.random.default_rng(random_state)
    for row_position in range(len(synthetic_direct)):
        feature_positions = scenario_rng.choice(
            len(direct_features),
            size=features_per_row,
            replace=False,
        )
        row_values = synthetic_direct.iloc[row_position, feature_positions].to_numpy()
        center_values = reference_center.iloc[feature_positions].to_numpy()
        outward_direction = np.where(row_values >= center_values, 1.0, -1.0)
        synthetic_direct.iloc[row_position, feature_positions] = (
            row_values
            + outward_direction
            * shift_standard_deviations
            * reference_scale.iloc[feature_positions].to_numpy()
        )

    synthetic_features = recompute_engineered_features(
        synthetic_direct,
        output_features=ordered_model_features,
    )
    return pd.DataFrame(
        scaler.transform(synthetic_features),
        columns=ordered_model_features,
        index=validation_features.index,
    )
