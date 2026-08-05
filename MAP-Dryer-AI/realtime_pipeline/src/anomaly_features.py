from __future__ import annotations

import math

import pandas as pd


RAW_FEATURES = [
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
]

MODEL_FEATURES = [
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
    "temperature_drop",
    "air_product_delta",
    "air_per_feed",
    "steam_temp_interaction",
    "heating_index",
]


def engineer_anomaly_features(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create the exact 16-feature input expected by the anomaly model.

    The input DataFrame must contain the 11 raw features listed in
    RAW_FEATURES. The output columns follow MODEL_FEATURES exactly.
    """

    missing_columns = [
        column
        for column in RAW_FEATURES
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing raw anomaly features: "
            f"{missing_columns}"
        )

    result = data[RAW_FEATURES].copy()

    # Convert all inputs to numeric.
    for column in RAW_FEATURES:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    # Do not silently infer anomalies from incomplete measurements.
    missing_values = result.isna().sum()
    missing_values = missing_values[missing_values > 0]

    if not missing_values.empty:
        raise ValueError(
            "Anomaly inference cannot run because required "
            "measurements are missing:\n"
            f"{missing_values.to_dict()}"
        )

    if (
        result["wet_product_feed_rate"]
        .abs()
        .lt(1e-12)
        .any()
    ):
        raise ValueError(
            "wet_product_feed_rate must be non-zero "
            "for air_per_feed."
        )

    result["temperature_drop"] = (
        result["dryer_air_temperature"]
        - result["final_product_temp"]
    )

    result["air_product_delta"] = (
        result["dryer_air_temperature"]
        - result["product_inlet_temperature"]
    )

    result["air_per_feed"] = (
        result["air_flow_rate"]
        / result["wet_product_feed_rate"]
    )

    result["steam_temp_interaction"] = (
        result["steam_pressure"]
        * result["dryer_air_temperature"]
    )

    result["heating_index"] = (
        result["residence_time"]
        * result["dryer_air_temperature"]
    )

    result = result[MODEL_FEATURES]

    numeric_values = result.to_numpy(dtype=float)

    if not all(
        math.isfinite(value)
        for value in numeric_values.ravel()
    ):
        raise ValueError(
            "Engineered anomaly features contain "
            "non-finite values."
        )

    return result