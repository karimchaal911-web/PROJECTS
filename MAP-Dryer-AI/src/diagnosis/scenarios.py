"""Coherent physical scenarios for diagnostic acceptance testing."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from features.engineering import RAW_PROCESS_FEATURES, recompute_engineered_features

from .reference_profile import ReferenceProfile


RAW_FEATURES = list(RAW_PROCESS_FEATURES)


@dataclass(frozen=True)
class PhysicalScenario:
    scenario_id: str
    name: str
    expected_rule_id: str
    history: pd.DataFrame

    @property
    def current(self) -> pd.Series:
        return self.history.iloc[-1]


def _scale(profile: ReferenceProfile, feature: str) -> float:
    return max(float(profile.statistics[feature]["iqr"]), 1e-6)


def _baseline_history(
    profile: ReferenceProfile, observations: int
) -> pd.DataFrame:
    rows = []
    for row_index in range(observations):
        row = {}
        for feature_index, feature in enumerate(RAW_FEATURES):
            median = float(profile.statistics[feature]["median"])
            variation = 0.04 * _scale(profile, feature) * np.sin(
                (row_index + 1) * (feature_index + 2) * 0.71
            )
            row[feature] = median + variation
        rows.append(row)
    return pd.DataFrame(rows)


def build_physical_scenarios(
    reference_profile: ReferenceProfile,
    observations: int = 6,
) -> dict[str, PhysicalScenario]:
    """Alter raw measurements first, then recompute all engineered indicators."""

    if observations < 6:
        raise ValueError("Physical diagnostic scenarios require at least 6 observations.")
    scenarios: dict[str, PhysicalScenario] = {}

    airflow = _baseline_history(reference_profile, observations)
    for offset, multiplier in zip(range(observations - 3, observations), [2.0, 3.0, 4.0]):
        airflow.loc[offset, "air_flow_rate"] -= multiplier * _scale(reference_profile, "air_flow_rate")
        airflow.loc[offset, "fan_speed"] -= 0.75 * multiplier * _scale(reference_profile, "fan_speed")
        airflow.loc[offset, "vacuum"] += 0.50 * multiplier * _scale(reference_profile, "vacuum")
    scenarios["S01"] = PhysicalScenario(
        "S01", "Airflow loss", "D01", recompute_engineered_features(airflow)
    )

    steam = _baseline_history(reference_profile, observations)
    for offset, multiplier in zip(range(observations - 3, observations), [2.0, 3.0, 4.0]):
        steam.loc[offset, "steam_pressure"] -= multiplier * _scale(reference_profile, "steam_pressure")
        steam.loc[offset, "dryer_air_temperature"] -= multiplier * _scale(reference_profile, "dryer_air_temperature")
        steam.loc[offset, "final_product_temp"] -= 0.60 * multiplier * _scale(reference_profile, "final_product_temp")
    scenarios["S02"] = PhysicalScenario(
        "S02", "Steam loss", "D02", recompute_engineered_features(steam)
    )

    overload = _baseline_history(reference_profile, observations)
    for offset, multiplier in zip(range(observations - 3, observations), [2.5, 3.5, 5.0]):
        overload.loc[offset, "wet_product_feed_rate"] += multiplier * _scale(reference_profile, "wet_product_feed_rate")
        overload.loc[offset, "residence_time"] -= 0.50 * multiplier * _scale(reference_profile, "residence_time")
    scenarios["S03"] = PhysicalScenario(
        "S03", "Feed overload", "D03", recompute_engineered_features(overload)
    )

    cooling = _baseline_history(reference_profile, observations)
    for offset, multiplier in zip(range(observations - 3, observations), [2.0, 3.0, 4.0]):
        cooling.loc[offset, "cooler_air_temperature"] += multiplier * _scale(reference_profile, "cooler_air_temperature")
        cooling.loc[offset, "final_product_temp"] += multiplier * _scale(reference_profile, "final_product_temp")
    scenarios["S04"] = PhysicalScenario(
        "S04", "Cooling degradation", "D04", recompute_engineered_features(cooling)
    )

    exhaust = _baseline_history(reference_profile, observations)
    for offset, multiplier in zip(range(observations - 3, observations), [2.5, 3.75, 5.0]):
        exhaust.loc[offset, "vacuum"] -= multiplier * _scale(reference_profile, "vacuum")
        exhaust.loc[offset, "air_flow_rate"] -= 0.75 * multiplier * _scale(reference_profile, "air_flow_rate")
        exhaust.loc[offset, "fan_speed"] -= 0.50 * multiplier * _scale(reference_profile, "fan_speed")
    scenarios["S05"] = PhysicalScenario(
        "S05", "Exhaust restriction", "D05", recompute_engineered_features(exhaust)
    )

    sensor_jump = _baseline_history(reference_profile, observations)
    sensor_jump.loc[observations - 1, "dryer_air_temperature"] += 7.0 * _scale(
        reference_profile, "dryer_air_temperature"
    )
    scenarios["S06"] = PhysicalScenario(
        "S06",
        "Temperature sensor jump",
        "D06",
        recompute_engineered_features(sensor_jump),
    )

    stuck = _baseline_history(reference_profile, observations)
    stuck_value = (
        float(reference_profile.statistics["fan_speed"]["median"])
        - 4.0 * _scale(reference_profile, "fan_speed")
    )
    stuck.loc[:, "fan_speed"] = stuck_value
    air_center = float(reference_profile.statistics["air_flow_rate"]["median"])
    air_scale = _scale(reference_profile, "air_flow_rate")
    stuck.loc[:, "air_flow_rate"] = air_center + np.linspace(-0.8, 0.8, observations) * air_scale
    scenarios["S07"] = PhysicalScenario(
        "S07", "Stuck fan-speed signal", "D07", recompute_engineered_features(stuck)
    )

    oscillation = _baseline_history(reference_profile, observations)
    signs = np.array([1.0, -1.0] * ((observations + 1) // 2))[:observations]
    for feature, amplitude in {
        "air_flow_rate": 3.0,
        "fan_speed": 2.5,
        "vacuum": 2.5,
        "dryer_air_temperature": 2.0,
    }.items():
        center = float(reference_profile.statistics[feature]["median"])
        oscillation.loc[:, feature] = center + signs * amplitude * _scale(
            reference_profile, feature
        )
    scenarios["S08"] = PhysicalScenario(
        "S08", "Oscillatory control", "D08", recompute_engineered_features(oscillation)
    )

    ordered_features = list(reference_profile.feature_names)
    return {
        scenario_id: PhysicalScenario(
            scenario.scenario_id,
            scenario.name,
            scenario.expected_rule_id,
            scenario.history.loc[:, ordered_features],
        )
        for scenario_id, scenario in scenarios.items()
    }
