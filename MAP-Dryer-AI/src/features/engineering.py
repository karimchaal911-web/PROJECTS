"""Reusable MAP dryer feature-engineering transformations."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


RAW_PROCESS_FEATURES = (
    "dryer_air_temperature",
    "cooler_air_temperature",
    "air_flow_rate",
    "wet_product_feed_rate",
    "product_inlet_temperature",
    "residence_time",
    "vacuum",
    "steam_pressure",
    "fan_speed",
    "product_density",
    "final_product_temp",
)

ENGINEERED_FEATURES = (
    "temperature_drop",
    "air_product_delta",
    "air_per_feed",
    "steam_temp_interaction",
    "heating_index",
)


def recompute_engineered_features(
    data: pd.DataFrame,
    output_features: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Recompute the five shared dryer indicators from raw measurements."""

    missing = sorted(set(RAW_PROCESS_FEATURES) - set(data.columns))
    if missing:
        raise KeyError(f"Raw features required for engineering are missing: {missing}")
    if (data["wet_product_feed_rate"] == 0).any():
        raise ValueError("wet_product_feed_rate must be non-zero for air_per_feed.")

    result = data.copy()
    result["temperature_drop"] = (
        result["dryer_air_temperature"] - result["final_product_temp"]
    )
    result["air_product_delta"] = (
        result["dryer_air_temperature"] - result["product_inlet_temperature"]
    )
    result["air_per_feed"] = (
        result["air_flow_rate"] / result["wet_product_feed_rate"]
    )
    result["steam_temp_interaction"] = (
        result["steam_pressure"] * result["dryer_air_temperature"]
    )
    result["heating_index"] = (
        result["residence_time"] * result["dryer_air_temperature"]
    )

    if output_features is None:
        return result
    ordered = list(output_features)
    unknown = [feature for feature in ordered if feature not in result.columns]
    if unknown:
        raise KeyError(f"Requested engineered output features are missing: {unknown}")
    output = result.loc[:, ordered].copy()
    if not np.isfinite(output.select_dtypes(include="number")).all().all():
        raise ValueError("Feature engineering produced non-finite values.")
    return output
