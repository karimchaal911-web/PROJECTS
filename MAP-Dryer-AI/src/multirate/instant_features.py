"""Per-observation engineered features from process variables only.

These are the features available on every 5-second row, so the anomaly
model and the diagnosis engine can run without laboratory values. All
formulas live here — training, tests and the real-time service import this
module instead of re-deriving anything.

Formula reference (inputs are the nine 5-second process variables):

* ``air_product_delta``  = Dryer Air Temperature − Product Inlet Temperature
  (drying driving-force at the product inlet)
* ``cooler_delta``       = Dryer Air Temperature − Cooler Air Temperature
  (temperature step across the dryer→cooler path)
* ``air_per_feed``       = Air Flow Rate / Wet Product Feed Rate
  (specific drying-air allocation per unit of wet product)
* ``steam_per_feed``     = Steam Pressure / Wet Product Feed Rate
  (specific heating effort per unit of wet product)
* ``thermal_load``       = Steam Pressure × Dryer Air Temperature
  (combined thermal-energy proxy; the historical name in the 1-minute
  prototype was ``steam_temp_interaction``)
* ``thermal_exposure``   = Residence Time × Dryer Air Temperature
  (residence-time-adjusted heat exposure; historically ``heating_index``)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from multirate.preprocessing import PROCESS_VARIABLES, RAW_TO_SNAKE


PROCESS_SNAKE_FEATURES = [RAW_TO_SNAKE[name] for name in PROCESS_VARIABLES]

INSTANT_ENGINEERED_FEATURES = [
    "air_product_delta",
    "cooler_delta",
    "air_per_feed",
    "steam_per_feed",
    "thermal_load",
    "thermal_exposure",
]

# Exact model input order for the process-only anomaly model.
PROCESS_MODEL_FEATURES = PROCESS_SNAKE_FEATURES + INSTANT_ENGINEERED_FEATURES


def engineer_instant_features(process: pd.DataFrame) -> pd.DataFrame:
    """Compute the 15 process-only model features for one or many rows.

    ``process`` may use either the raw plant column names or the snake_case
    aliases. Missing or non-finite inputs raise instead of silently
    producing an invalid model row.
    """

    frame = process.copy()
    frame = frame.rename(
        columns={
            raw: snake
            for raw, snake in RAW_TO_SNAKE.items()
            if raw in frame.columns
        }
    )

    missing = [
        name for name in PROCESS_SNAKE_FEATURES if name not in frame.columns
    ]
    if missing:
        raise ValueError(f"Missing process variables: {missing}")

    result = frame.loc[:, PROCESS_SNAKE_FEATURES].copy()
    for column in PROCESS_SNAKE_FEATURES:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    missing_values = result.isna().sum()
    missing_values = missing_values[missing_values > 0]
    if not missing_values.empty:
        raise ValueError(
            "Instant features cannot be engineered because required "
            f"measurements are missing: {missing_values.to_dict()}"
        )

    if result["wet_product_feed_rate"].abs().lt(1e-12).any():
        raise ValueError(
            "wet_product_feed_rate must be non-zero for the per-feed ratios."
        )

    result["air_product_delta"] = (
        result["dryer_air_temperature"] - result["product_inlet_temperature"]
    )
    result["cooler_delta"] = (
        result["dryer_air_temperature"] - result["cooler_air_temperature"]
    )
    result["air_per_feed"] = (
        result["air_flow_rate"] / result["wet_product_feed_rate"]
    )
    result["steam_per_feed"] = (
        result["steam_pressure"] / result["wet_product_feed_rate"]
    )
    result["thermal_load"] = (
        result["steam_pressure"] * result["dryer_air_temperature"]
    )
    result["thermal_exposure"] = (
        result["residence_time"] * result["dryer_air_temperature"]
    )

    result = result[PROCESS_MODEL_FEATURES]

    if not np.isfinite(result.to_numpy(dtype=float)).all():
        raise ValueError(
            "Engineered instant features contain non-finite values."
        )

    return result
