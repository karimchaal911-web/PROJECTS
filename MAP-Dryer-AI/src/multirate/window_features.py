"""Optional aggregated process-window features for exploratory analysis.

One feature row summarises the process conditions inside a configurable
window that ends *before* the laboratory sample time (see
``alignment.effective_window_end``). The canonical moisture model instead uses
the original 16-feature direct-snapshot contract implemented by
``compute_moisture_features`` below.

Per-variable statistics (for each of the nine process variables):

* ``__mean`` ``__std`` ``__min`` ``__max`` ``__median`` — plain window stats
* ``__last``          — final value in the window (most recent condition)
* ``__range``         — max − min inside the window
* ``__slope_per_min`` — least-squares slope against minutes elapsed
* ``__delta_short``   — mean of the last SHORT_DELTA_MINUTES minus the mean
  of the SHORT_DELTA_MINUTES before those (recent short-term shift)
* ``__cv``            — std / |mean| (only where |mean| is meaningful)

Derived physical series (formulas identical to
``instant_features``; aggregated as mean and last):

* ``thermal_load``   = Steam Pressure × Dryer Air Temperature
* ``air_per_feed``   = Air Flow Rate / Wet Product Feed Rate
* ``steam_per_feed`` = Steam Pressure / Wet Product Feed Rate
* ``air_product_delta`` = Dryer Air Temp − Product Inlet Temp
* ``cooler_delta``   = Dryer Air Temp − Cooler Air Temp
* ``thermal_exposure`` = Residence Time × Dryer Air Temp

Plus one rolling stability indicator:

* ``process_stability_index`` — mean coefficient of variation across the
  four dominant manipulated variables (dryer air temperature, air flow,
  wet feed, steam pressure). Higher = less stable window.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from multirate.preprocessing import PROCESS_VARIABLES, RAW_TO_SNAKE


SHORT_DELTA_MINUTES = 5.0

_STAT_SUFFIXES = [
    "mean",
    "std",
    "min",
    "max",
    "median",
    "last",
    "range",
    "slope_per_min",
    "delta_short",
    "cv",
]

_DERIVED_SERIES = [
    "thermal_load",
    "air_per_feed",
    "steam_per_feed",
    "air_product_delta",
    "cooler_delta",
    "thermal_exposure",
]

_STABILITY_VARIABLES = [
    "Dryer Air Temperature",
    "Air Flow Rate",
    "Wet Product Feed Rate",
    "Steam Pressure",
]

WINDOW_FEATURE_NAMES: list[str] = (
    [
        f"{RAW_TO_SNAKE[variable]}__{suffix}"
        for variable in PROCESS_VARIABLES
        for suffix in _STAT_SUFFIXES
    ]
    + [
        f"{series}__{suffix}"
        for series in _DERIVED_SERIES
        for suffix in ("mean", "last")
    ]
    + ["process_stability_index"]
)

# Final Notebook 03 moisture contract. These are the feature names originally
# defined in the notebook: direct process/laboratory values plus the five
# engineered indicators. The process values are taken from the final causal
# row at the residence-adjusted time; density and product temperature are the
# most recent strictly previous laboratory observations.
MOISTURE_FEATURE_NAMES: list[str] = [
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


def compute_moisture_features(
    process_snapshot: Mapping[str, object] | pd.Series,
    product_density: float,
    final_product_temp: float,
) -> dict[str, float]:
    """Build the notebook's original 16 moisture features.

    ``process_snapshot`` uses the nine plant-facing process column names. The
    two laboratory inputs must be the latest observations strictly preceding
    the prediction/target timestamp.
    """

    direct = {
        RAW_TO_SNAKE[name]: float(process_snapshot[name])
        for name in PROCESS_VARIABLES
    }
    direct["product_density"] = float(product_density)
    direct["final_product_temp"] = float(final_product_temp)
    if not np.isfinite(list(direct.values())).all():
        raise ValueError("Moisture features contain missing or non-finite values.")
    if abs(direct["wet_product_feed_rate"]) < 1e-12:
        raise ValueError("wet_product_feed_rate must be non-zero for air_per_feed.")

    direct.update(
        {
            "temperature_drop": (
                direct["dryer_air_temperature"] - direct["final_product_temp"]
            ),
            "air_product_delta": (
                direct["dryer_air_temperature"]
                - direct["product_inlet_temperature"]
            ),
            "air_per_feed": (
                direct["air_flow_rate"] / direct["wet_product_feed_rate"]
            ),
            "steam_temp_interaction": (
                direct["steam_pressure"] * direct["dryer_air_temperature"]
            ),
            "heating_index": (
                direct["residence_time"] * direct["dryer_air_temperature"]
            ),
        }
    )
    return {name: direct[name] for name in MOISTURE_FEATURE_NAMES}


def _series_stats(
    values: np.ndarray,
    minutes_elapsed: np.ndarray,
    short_delta_mask_recent: np.ndarray,
    short_delta_mask_before: np.ndarray,
) -> dict[str, float]:
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0

    if len(values) > 1:
        slope_per_min = float(np.polyfit(minutes_elapsed, values, 1)[0])
    else:
        slope_per_min = 0.0

    if short_delta_mask_recent.any() and short_delta_mask_before.any():
        delta_short = float(
            np.mean(values[short_delta_mask_recent])
            - np.mean(values[short_delta_mask_before])
        )
    else:
        delta_short = 0.0

    cv = std / abs(mean) if abs(mean) > 1e-9 else 0.0

    return {
        "mean": mean,
        "std": std,
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "median": float(np.median(values)),
        "last": float(values[-1]),
        "range": float(np.max(values) - np.min(values)),
        "slope_per_min": slope_per_min,
        "delta_short": delta_short,
        "cv": cv,
    }


def compute_window_features(window: pd.DataFrame) -> dict[str, float]:
    """Aggregate one chronological process window into a feature mapping.

    ``window`` must contain ``Timestamp`` plus the nine process variables,
    already restricted to the intended time span and sorted ascending.
    """

    if window.empty:
        raise ValueError("Cannot compute features for an empty window.")

    missing = [
        name
        for name in ["Timestamp", *PROCESS_VARIABLES]
        if name not in window.columns
    ]
    if missing:
        raise ValueError(f"Window is missing required columns: {missing}")

    timestamps = pd.to_datetime(window["Timestamp"])
    if not timestamps.is_monotonic_increasing:
        raise ValueError("Window rows must be sorted chronologically.")

    minutes_elapsed = (
        (timestamps - timestamps.iloc[0]).dt.total_seconds().to_numpy() / 60.0
    )
    window_end_minutes = minutes_elapsed[-1]
    recent_mask = minutes_elapsed > window_end_minutes - SHORT_DELTA_MINUTES
    before_mask = (
        ~recent_mask
        & (minutes_elapsed > window_end_minutes - 2.0 * SHORT_DELTA_MINUTES)
    )

    features: dict[str, float] = {}
    series_cache: dict[str, np.ndarray] = {}

    for variable in PROCESS_VARIABLES:
        values = pd.to_numeric(window[variable], errors="coerce").to_numpy(
            dtype=float
        )
        if not np.isfinite(values).all():
            raise ValueError(
                f"Window contains missing or non-finite values for "
                f"{variable!r}."
            )
        series_cache[variable] = values
        stats = _series_stats(values, minutes_elapsed, recent_mask, before_mask)
        prefix = RAW_TO_SNAKE[variable]
        for suffix, value in stats.items():
            features[f"{prefix}__{suffix}"] = value

    feed = series_cache["Wet Product Feed Rate"]
    if np.abs(feed).min() < 1e-12:
        raise ValueError(
            "Wet Product Feed Rate must be non-zero inside the window."
        )

    derived = {
        "thermal_load": series_cache["Steam Pressure"]
        * series_cache["Dryer Air Temperature"],
        "air_per_feed": series_cache["Air Flow Rate"] / feed,
        "steam_per_feed": series_cache["Steam Pressure"] / feed,
        "air_product_delta": series_cache["Dryer Air Temperature"]
        - series_cache["Product Inlet Temperature"],
        "cooler_delta": series_cache["Dryer Air Temperature"]
        - series_cache["Cooler Air Temperature"],
        "thermal_exposure": series_cache["Residence Time"]
        * series_cache["Dryer Air Temperature"],
    }
    for name, values in derived.items():
        features[f"{name}__mean"] = float(np.mean(values))
        features[f"{name}__last"] = float(values[-1])

    stability_terms = []
    for variable in _STABILITY_VARIABLES:
        values = series_cache[variable]
        mean = np.mean(values)
        std = np.std(values, ddof=1) if len(values) > 1 else 0.0
        if abs(mean) > 1e-9:
            stability_terms.append(std / abs(mean))
    features["process_stability_index"] = (
        float(np.mean(stability_terms)) if stability_terms else 0.0
    )

    ordered = {name: features[name] for name in WINDOW_FEATURE_NAMES}
    if not np.isfinite(list(ordered.values())).all():
        raise ValueError("Window features contain non-finite values.")

    return ordered
