"""Build and validate the isolated two-day Power BI demonstration replay.

The canonical 92-day dataset, notebooks, model artifacts, and reported metrics
are read-only inputs.  This script copies the final two complete calendar days
and injects measured multivariate residual profiles from anomaly families that
already exist in the canonical data.  It never writes model outputs into the
CSV and never trains or modifies a model.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
REALTIME_SRC = PROJECT_ROOT / "realtime_pipeline" / "src"
for entry in (str(SRC_DIR), str(REALTIME_SRC)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from multirate import (  # noqa: E402
    PROCESS_MODEL_FEATURES,
    PROCESS_VARIABLES,
    QUALITY_VARIABLES,
    RAW_SOURCE_COLUMNS,
    build_lab_table,
    build_process_table,
    build_timestamp,
    engineer_instant_features,
)
from realtime_service import load_artifacts, predict_moisture  # noqa: E402


CANONICAL_PATH = (
    PROJECT_ROOT / "data" / "raw" / "MAP_Dryer_Canonical_5s_deterministic.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "resources" / "dashboard_demo"
OUTPUT_PATH = OUTPUT_DIR / "MAP_Dryer_Dashboard_Demo_5s.csv"
WARMUP_PATH = OUTPUT_DIR / "MAP_Dryer_Dashboard_Warmup_5s.csv"
SCENARIO_PATH = OUTPUT_DIR / "MAP_Dryer_Dashboard_Demo_Scenarios.csv"
AUDIT_PATH = OUTPUT_DIR / "MAP_Dryer_Dashboard_Demo_Audit.json"
MODELS_DIR = PROJECT_ROOT / "models" / "5s"

CANONICAL_COLUMNS = [
    *RAW_SOURCE_COLUMNS,
    "Operating Regime",
    "Disturbance State",
    "Data Source",
]

PROTECTED_PATHS = [
    CANONICAL_PATH,
    PROJECT_ROOT / "data" / "processed" / "MAP_Dryer_Canonical_5s.csv",
    PROJECT_ROOT / "data" / "processed" / "MAP_Dryer_TEST_Replay_5s.csv",
    PROJECT_ROOT / "notebooks" / "01_Data_Exploration.ipynb",
    PROJECT_ROOT / "notebooks" / "02_Feature_Engineering.ipynb",
    PROJECT_ROOT / "notebooks" / "03_Model1_SoftSensor.ipynb",
    PROJECT_ROOT / "notebooks" / "04_Model2_AnomalyDetection&Diagnosis.ipynb",
]

PROFILE_BASELINE_MINUTES = 10
PROFILE_SMOOTHING_ROWS = 13  # 65 seconds on the five-second grid.
WARMUP_MINUTES = 180

SCENARIO_DIRECTION_RULES = {
    "steam_dip": {
        "Steam Pressure": -1,
        "Dryer Air Temperature": -1,
    },
    "airflow_restriction": {
        "Air Flow Rate": -1,
        "Vacuum": -1,
    },
    "cooling_loss": {
        "Cooler Air Temperature": 1,
    },
    "fan_speed_dip": {
        "Fan Speed": -1,
        "Air Flow Rate": -1,
        "Vacuum": -1,
        "Dryer Air Temperature": -1,
    },
    "feed_surge": {
        "Wet Product Feed Rate": 1,
        "Air Flow Rate": 1,
        "Fan Speed": 1,
        "Steam Pressure": 1,
        "Dryer Air Temperature": -1,
        "Vacuum": 1,
        "Residence Time": -1,
    },
}


@dataclass(frozen=True)
class EpisodeSpec:
    scenario_id: str
    scenario_type: str
    source_start: str
    target_start: str
    severity: str
    amplitude_multiplier: float
    affected_features: tuple[str, ...]


EPISODES = (
    EpisodeSpec(
        "DEMO_01_STEAM_MILD",
        "steam_dip",
        "2026-04-19 05:00:00",
        "2026-07-15 05:00:00",
        "mild",
        0.85,
        ("Steam Pressure", "Dryer Air Temperature"),
    ),
    EpisodeSpec(
        "DEMO_02_AIRFLOW_MODERATE",
        "airflow_restriction",
        "2026-04-23 08:00:00",
        "2026-07-15 08:00:00",
        "moderate",
        1.00,
        ("Air Flow Rate", "Vacuum"),
    ),
    EpisodeSpec(
        "DEMO_03_FAN_MODERATE",
        "fan_speed_dip",
        "2026-06-10 14:00:00",
        "2026-07-15 14:00:00",
        "moderate",
        1.00,
        ("Fan Speed", "Air Flow Rate", "Vacuum", "Dryer Air Temperature"),
    ),
    EpisodeSpec(
        "DEMO_04_FEED_MODERATE",
        "feed_surge",
        "2026-05-05 17:00:00",
        "2026-07-15 17:00:00",
        "moderate",
        1.00,
        (
            "Wet Product Feed Rate",
            "Air Flow Rate",
            "Fan Speed",
            "Steam Pressure",
            "Dryer Air Temperature",
            "Vacuum",
            "Residence Time",
        ),
    ),
    EpisodeSpec(
        "DEMO_05_STEAM_SEVERE",
        "steam_dip",
        "2026-07-08 05:00:00",
        "2026-07-16 05:00:00",
        "severe",
        1.15,
        ("Steam Pressure", "Dryer Air Temperature"),
    ),
    EpisodeSpec(
        "DEMO_06_COOLING_MODERATE",
        "cooling_loss",
        "2026-05-17 11:00:00",
        "2026-07-16 09:00:00",
        "moderate",
        0.85,
        ("Cooler Air Temperature",),
    ),
    EpisodeSpec(
        "DEMO_07_FAN_SEVERE",
        "fan_speed_dip",
        "2026-06-30 14:00:00",
        "2026-07-16 14:00:00",
        "severe",
        1.15,
        ("Fan Speed", "Air Flow Rate", "Vacuum", "Dryer Air Temperature"),
    ),
    EpisodeSpec(
        "DEMO_08_FEED_SEVERE",
        "feed_surge",
        "2026-07-04 17:00:00",
        "2026-07-16 18:00:00",
        "severe",
        1.15,
        (
            "Wet Product Feed Rate",
            "Air Flow Rate",
            "Fan Speed",
            "Steam Pressure",
            "Dryer Air Temperature",
            "Vacuum",
            "Residence Time",
        ),
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(PROJECT_ROOT)): sha256_file(path)
        for path in PROTECTED_PATHS
    }


def contiguous_episodes(
    timestamps: pd.Series, state: pd.Series
) -> list[dict[str, object]]:
    groups = state.ne(state.shift()).cumsum()
    episodes: list[dict[str, object]] = []
    for _, indexes in state.loc[state.ne("normal")].groupby(groups).groups.items():
        positions = list(indexes)
        start = pd.Timestamp(timestamps.loc[positions[0]])
        end = pd.Timestamp(timestamps.loc[positions[-1]])
        episodes.append(
            {
                "scenario_type": str(state.loc[positions[0]]),
                "start_timestamp": str(start),
                "end_timestamp": str(end),
                "duration_minutes": len(positions) * 5.0 / 60.0,
                "rows": len(positions),
            }
        )
    return episodes


def source_episode_positions(
    canonical: pd.DataFrame,
    timestamps: pd.Series,
    spec: EpisodeSpec,
) -> np.ndarray:
    start = pd.Timestamp(spec.source_start)
    matches = np.flatnonzero(timestamps.to_numpy() == start.to_datetime64())
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one source row at {start}; found {len(matches)}."
        )
    first = int(matches[0])
    if canonical.loc[first, "Disturbance State"] != spec.scenario_type:
        raise RuntimeError(
            f"{spec.scenario_id} source is not labelled {spec.scenario_type}."
        )
    last = first
    while (
        last + 1 < len(canonical)
        and canonical.loc[last + 1, "Disturbance State"] == spec.scenario_type
    ):
        last += 1
    return np.arange(first, last + 1)


def measured_residual_profile(
    canonical: pd.DataFrame,
    source_positions: np.ndarray,
    features: tuple[str, ...],
) -> pd.DataFrame:
    baseline_rows = int(PROFILE_BASELINE_MINUTES * 60 / 5)
    first, last = int(source_positions[0]), int(source_positions[-1])
    before = canonical.iloc[max(0, first - baseline_rows):first]
    after = canonical.iloc[last + 1:last + 1 + baseline_rows]
    if len(before) != baseline_rows or len(after) != baseline_rows:
        raise RuntimeError("A source episode lacks the required baseline context.")

    start_baseline = before.loc[:, features].median()
    end_baseline = after.loc[:, features].median()
    alpha = np.linspace(0.0, 1.0, len(source_positions))[:, None]
    baseline = (
        start_baseline.to_numpy()[None, :] * (1.0 - alpha)
        + end_baseline.to_numpy()[None, :] * alpha
    )
    source_values = canonical.loc[source_positions, features].to_numpy(dtype=float)
    residual = pd.DataFrame(source_values - baseline, columns=features)
    residual = residual.rolling(
        PROFILE_SMOOTHING_ROWS, center=True, min_periods=1
    ).mean()

    # Remove any small baseline offset at the exact boundaries.  The source
    # ramp/hold/recovery shape remains, while the injected target has no jump.
    endpoint_line = (
        residual.iloc[0].to_numpy()[None, :] * (1.0 - alpha)
        + residual.iloc[-1].to_numpy()[None, :] * alpha
    )
    return residual - endpoint_line


def build_demo(canonical: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    timestamps = build_timestamp(canonical)
    canonical_episode_inventory = contiguous_episodes(
        timestamps,
        canonical["Disturbance State"].fillna("normal").astype(str),
    )
    final_day = timestamps.max().normalize()
    first_day = final_day - pd.Timedelta(days=1)
    final_mask = timestamps.between(
        first_day, final_day + pd.Timedelta(days=1) - pd.Timedelta(seconds=5)
    )
    demo = canonical.loc[final_mask].copy().reset_index(drop=True)
    demo_timestamps = build_timestamp(demo)
    source_period = canonical.loc[final_mask].copy().reset_index(drop=True)

    existing = contiguous_episodes(
        demo_timestamps,
        demo["Disturbance State"].fillna("normal").astype(str),
    )
    scenario_rows: list[dict[str, object]] = []

    for spec in EPISODES:
        source_positions = source_episode_positions(canonical, timestamps, spec)
        profile = measured_residual_profile(
            canonical, source_positions, spec.affected_features
        )
        target_start = pd.Timestamp(spec.target_start)
        target_end = target_start + pd.Timedelta(
            seconds=5 * (len(source_positions) - 1)
        )
        target_mask = demo_timestamps.between(target_start, target_end)
        target_positions = np.flatnonzero(target_mask.to_numpy())
        if len(target_positions) != len(source_positions):
            raise RuntimeError(
                f"{spec.scenario_id} target has {len(target_positions)} rows; "
                f"expected {len(source_positions)}."
            )
        if not demo.loc[target_positions, "Disturbance State"].eq("normal").all():
            raise RuntimeError(f"{spec.scenario_id} overlaps an existing episode.")

        original = demo.loc[target_positions, spec.affected_features].to_numpy(
            dtype=float
        )
        applied_delta = spec.amplitude_multiplier * profile.to_numpy()
        injected = original + applied_delta
        demo.loc[target_positions, spec.affected_features] = injected
        demo.loc[target_positions, "Disturbance State"] = spec.scenario_type

        core_start = int(0.25 * len(target_positions))
        core_end = max(int(0.75 * len(target_positions)), core_start + 1)
        core_median = pd.Series(
            np.median(applied_delta[core_start:core_end], axis=0),
            index=spec.affected_features,
        )
        rules = SCENARIO_DIRECTION_RULES[spec.scenario_type]
        physics_violations = [
            feature
            for feature, direction in rules.items()
            if float(core_median[feature]) * direction <= 0.0
        ]
        if physics_violations:
            raise RuntimeError(
                f"{spec.scenario_id} violates audited directions for "
                f"{physics_violations}."
            )
        boundary_delta = float(
            np.max(np.abs(applied_delta[[0, -1], :]))
        )
        if boundary_delta > 1e-9:
            raise RuntimeError(
                f"{spec.scenario_id} does not meet the unchanged baseline "
                "at both episode boundaries."
            )

        source_end = pd.Timestamp(timestamps.loc[int(source_positions[-1])])
        scenario_rows.append(
            {
                "Scenario_ID": spec.scenario_id,
                "Scenario_Type": spec.scenario_type,
                "Start_Timestamp": str(target_start),
                "End_Timestamp": str(target_end),
                "Duration_Minutes": len(target_positions) * 5.0 / 60.0,
                "Severity": spec.severity,
                "Amplitude_Multiplier": spec.amplitude_multiplier,
                "Affected_Features": "; ".join(spec.affected_features),
                "Source_Scenario": (
                    f"{spec.scenario_type}: {spec.source_start} -> {source_end}"
                ),
                "Source_Profile": "measured ramp-hold-recovery residual",
                "Applied_Core_Median_Deltas": json.dumps(
                    {name: float(core_median[name]) for name in spec.affected_features},
                    separators=(",", ":"),
                ),
                "Boundary_Max_Absolute_Delta": boundary_delta,
                "Physics_Check": "PASS",
                "Injected_For_Dashboard_Demo": True,
            }
        )

    demo["Data Source"] = "synthetic_prototype_dashboard_demo"
    scenario_table = pd.DataFrame(scenario_rows)

    non_episode = demo["Disturbance State"].eq("normal")
    normal_values_preserved = bool(
        demo.loc[non_episode, PROCESS_VARIABLES]
        .reset_index(drop=True)
        .equals(
            source_period.loc[non_episode, PROCESS_VARIABLES].reset_index(drop=True)
        )
    )
    quality_values_preserved = bool(
        demo.loc[:, QUALITY_VARIABLES].equals(source_period.loc[:, QUALITY_VARIABLES])
    )
    metadata = {
        "source_start": str(demo_timestamps.min()),
        "source_end": str(demo_timestamps.max()),
        "source_rows": int(len(demo)),
        "canonical_scenario_types": sorted(
            {str(row["scenario_type"]) for row in canonical_episode_inventory}
        ),
        "canonical_episode_count": len(canonical_episode_inventory),
        "canonical_episode_counts_by_type": {
            scenario_type: sum(
                row["scenario_type"] == scenario_type
                for row in canonical_episode_inventory
            )
            for scenario_type in sorted(
                {str(row["scenario_type"]) for row in canonical_episode_inventory}
            )
        },
        "existing_episodes": existing,
        "existing_episode_count_in_source_period": len(existing),
        "normal_process_rows_preserved": normal_values_preserved,
        "laboratory_values_preserved": quality_values_preserved,
    }
    return demo, scenario_table, metadata


def build_warmup_context(
    canonical: pd.DataFrame, demo: pd.DataFrame
) -> pd.DataFrame:
    """Copy hidden pre-replay history without changing any canonical values."""

    canonical_timestamps = build_timestamp(canonical)
    demo_start = pd.Timestamp(build_timestamp(demo).min())
    warmup_start = demo_start - pd.Timedelta(minutes=WARMUP_MINUTES)
    warmup_end = demo_start - pd.Timedelta(seconds=5)
    mask = canonical_timestamps.between(warmup_start, warmup_end)
    return canonical.loc[mask, CANONICAL_COLUMNS].copy().reset_index(drop=True)


def validate_warmup_context(
    warmup: pd.DataFrame, demo: pd.DataFrame
) -> dict[str, object]:
    """Prove the hidden context supports prediction on the first visible row."""

    expected_rows = WARMUP_MINUTES * 60 // 5
    timestamps = build_timestamp(warmup)
    demo_start = pd.Timestamp(build_timestamp(demo).min())
    if list(warmup.columns) != CANONICAL_COLUMNS:
        raise RuntimeError("Warm-up column order differs from canonical.")
    if len(warmup) != expected_rows:
        raise RuntimeError(
            f"Expected {expected_rows:,} warm-up rows; found {len(warmup):,}."
        )
    if timestamps.iloc[-1] != demo_start - pd.Timedelta(seconds=5):
        raise RuntimeError("Warm-up does not end one interval before replay start.")
    if timestamps.diff().dropna().ne(pd.Timedelta(seconds=5)).any():
        raise RuntimeError("Warm-up does not have a continuous five-second grid.")

    raw_warmup = warmup.loc[:, RAW_SOURCE_COLUMNS]
    warmup_process, report = build_process_table(raw_warmup)
    if report.gap_count:
        raise RuntimeError("Warm-up preprocessing found unexpected gaps.")
    warmup_lab = build_lab_table(raw_warmup)
    history = warmup_process.merge(
        warmup_lab.rename(columns={"Sample Timestamp": "Timestamp"}),
        on="Timestamp",
        how="left",
    )

    first_raw = demo.loc[[0], RAW_SOURCE_COLUMNS]
    first_process, first_report = build_process_table(first_raw)
    if first_report.gap_count:
        raise RuntimeError("First replay row failed process preprocessing.")
    first_lab = build_lab_table(first_raw)
    first_row = first_process.merge(
        first_lab.rename(columns={"Sample Timestamp": "Timestamp"}),
        on="Timestamp",
        how="left",
    ).iloc[0]
    buffer = pd.concat(
        [
            history.loc[:, ["Timestamp", *PROCESS_VARIABLES, *QUALITY_VARIABLES]],
            first_row[["Timestamp", *PROCESS_VARIABLES, *QUALITY_VARIABLES]]
            .to_frame()
            .T,
        ],
        ignore_index=True,
    )
    result = predict_moisture(
        buffer,
        pd.Timestamp(first_row["Timestamp"]),
        load_artifacts(MODELS_DIR),
        0.0,
    )
    if result.predicted_moisture is None:
        raise RuntimeError(
            "Warm-up did not produce a first-row moisture prediction: "
            f"{result.reason}"
        )

    prior_lab_rows = int(
        (
            history["Product Density"].notna()
            & history["Final Product Temp"].notna()
        ).sum()
    )
    return {
        "purpose": "in-memory soft-sensor context only; never replayed or persisted",
        "row_count": int(len(warmup)),
        "timestamp_start": str(timestamps.iloc[0]),
        "timestamp_end": str(timestamps.iloc[-1]),
        "ends_before_visible_replay": bool(timestamps.iloc[-1] < demo_start),
        "prior_complete_lab_rows": prior_lab_rows,
        "first_visible_timestamp": str(first_row["Timestamp"]),
        "first_visible_prediction_available": True,
        "first_visible_predicted_moisture": float(result.predicted_moisture),
        "hidden_rows_written_to_database": False,
    }


def validate_dataset(
    canonical: pd.DataFrame,
    demo: pd.DataFrame,
    scenario_table: pd.DataFrame,
) -> dict:
    if list(demo.columns) != CANONICAL_COLUMNS:
        raise RuntimeError("Dashboard fork column order differs from canonical.")
    if len(demo) != 2 * 24 * 60 * 60 // 5:
        raise RuntimeError(f"Expected 34,560 rows; found {len(demo):,}.")

    timestamps = build_timestamp(demo)
    deltas = timestamps.diff().dropna()
    duplicate_count = int(timestamps.duplicated().sum())
    gap_count = int(deltas.ne(pd.Timedelta(seconds=5)).sum())
    if duplicate_count or gap_count or not timestamps.is_monotonic_increasing:
        raise RuntimeError("Dashboard fork does not have a unique five-second grid.")
    if demo.loc[:, PROCESS_VARIABLES].isna().any().any():
        raise RuntimeError("Dashboard fork has missing process values.")

    canonical_min = canonical.loc[:, PROCESS_VARIABLES].min()
    canonical_max = canonical.loc[:, PROCESS_VARIABLES].max()
    below = demo.loc[:, PROCESS_VARIABLES].lt(canonical_min).sum()
    above = demo.loc[:, PROCESS_VARIABLES].gt(canonical_max).sum()
    outside = {
        column: int(below[column] + above[column])
        for column in PROCESS_VARIABLES
        if below[column] + above[column]
    }
    if outside:
        raise RuntimeError(
            "Injected values exceed the canonical physical envelope: "
            f"{outside}"
        )

    state = demo["Disturbance State"].fillna("normal").astype(str)
    episodes = contiguous_episodes(timestamps, state)
    injected_rows = int(state.ne("normal").sum())
    expected_types = {spec.scenario_type for spec in EPISODES}
    if not set(state.unique()).issubset(expected_types | {"normal"}):
        raise RuntimeError("Dashboard fork contains an unknown scenario family.")
    if len(scenario_table) != len(EPISODES):
        raise RuntimeError("Not every configured episode was written to metadata.")
    if not scenario_table["Physics_Check"].eq("PASS").all():
        raise RuntimeError("At least one episode failed the physics-direction audit.")

    ordered_starts = pd.to_datetime(scenario_table["Start_Timestamp"])
    ordered_ends = pd.to_datetime(scenario_table["End_Timestamp"])
    gaps = (
        ordered_starts.iloc[1:].reset_index(drop=True)
        - ordered_ends.iloc[:-1].reset_index(drop=True)
        - pd.Timedelta(seconds=5)
    )

    return {
        "row_count": int(len(demo)),
        "column_count": int(len(demo.columns)),
        "timestamp_start": str(timestamps.iloc[0]),
        "timestamp_end": str(timestamps.iloc[-1]),
        "timestamp_interval_seconds": 5,
        "duplicate_timestamps": duplicate_count,
        "unexpected_intervals": gap_count,
        "required_features_present": True,
        "feature_order_matches_canonical": True,
        "process_missing_values": 0,
        "values_outside_canonical_envelope": outside,
        "episodes": episodes,
        "episode_count": len(episodes),
        "physics_checks_passed": int(scenario_table["Physics_Check"].eq("PASS").sum()),
        "minimum_normal_gap_minutes": float(gaps.min().total_seconds() / 60.0),
        "injected_rows": injected_rows,
        "injected_row_percentage": 100.0 * injected_rows / len(demo),
        "normal_row_percentage": 100.0 * (len(demo) - injected_rows) / len(demo),
    }


def validate_model_behavior(
    demo: pd.DataFrame, scenario_table: pd.DataFrame
) -> dict:
    process, process_report = build_process_table(demo.loc[:, RAW_SOURCE_COLUMNS])
    if process_report.gap_count:
        raise RuntimeError("Existing preprocessing found gaps in the demo fork.")

    features = engineer_instant_features(process.loc[:, PROCESS_VARIABLES])
    scaler = joblib.load(MODELS_DIR / "anomaly_scaler.joblib")
    model = joblib.load(MODELS_DIR / "anomaly_model.joblib")
    if list(scaler.feature_names_in_) != PROCESS_MODEL_FEATURES:
        raise RuntimeError("Anomaly scaler feature contract is not current.")
    scaled = scaler.transform(features.loc[:, PROCESS_MODEL_FEATURES])
    scores = model.decision_function(scaled)
    flags = np.asarray(model.predict(scaled)) == -1

    with (MODELS_DIR / "feature_schema.json").open(encoding="utf-8") as file:
        schema = json.load(file)
    risk_scale = float(schema["anomaly_risk_calibration"]["score_scale"])
    risks = 1.0 / (1.0 + np.exp(np.clip(scores / risk_scale, -60.0, 60.0)))
    timestamps = build_timestamp(demo)
    state = demo["Disturbance State"].fillna("normal").astype(str).to_numpy()

    episode_metrics: list[dict[str, object]] = []
    for row in scenario_table.to_dict(orient="records"):
        mask = timestamps.between(
            pd.Timestamp(row["Start_Timestamp"]),
            pd.Timestamp(row["End_Timestamp"]),
        ).to_numpy()
        episode_metrics.append(
            {
                "scenario_id": row["Scenario_ID"],
                "scenario_type": row["Scenario_Type"],
                "severity": row["Severity"],
                "rows": int(mask.sum()),
                "model_flag_rate": float(np.mean(flags[mask])),
                "peak_anomaly_risk": float(np.max(risks[mask])),
                "minimum_decision_score": float(np.min(scores[mask])),
                "detector_responded": bool(
                    np.mean(flags[mask]) >= 0.05 or np.max(risks[mask]) >= 0.8
                ),
            }
        )

    normal_mask = state == "normal"
    episode_mask = ~normal_mask

    artifacts = load_artifacts(MODELS_DIR)
    lab = build_lab_table(demo.loc[:, RAW_SOURCE_COLUMNS])
    replay = process.merge(
        lab.rename(columns={"Sample Timestamp": "Timestamp"}),
        on="Timestamp",
        how="left",
    )
    moisture_checks: list[dict[str, object]] = []
    for row in scenario_table.to_dict(orient="records"):
        start = pd.Timestamp(row["Start_Timestamp"])
        end = pd.Timestamp(row["End_Timestamp"])
        midpoint = start + (end - start) / 2
        position = int(replay["Timestamp"].searchsorted(midpoint, side="left"))
        buffer = replay.iloc[:position + 1][
            ["Timestamp", *PROCESS_VARIABLES, *QUALITY_VARIABLES]
        ]
        result = predict_moisture(
            buffer,
            pd.Timestamp(replay.loc[position, "Timestamp"]),
            artifacts,
            0.0,
        )
        moisture_checks.append(
            {
                "scenario_id": row["Scenario_ID"],
                "timestamp": str(replay.loc[position, "Timestamp"]),
                "prediction_available": result.predicted_moisture is not None,
                "predicted_moisture": result.predicted_moisture,
                "reason": result.reason,
            }
        )

    responded = sum(bool(row["detector_responded"]) for row in episode_metrics)
    predictions_available = sum(
        bool(row["prediction_available"]) for row in moisture_checks
    )
    return {
        "model_version": artifacts.model_version,
        "feature_schema_version": artifacts.feature_schema_version,
        "anomaly_feature_count": len(PROCESS_MODEL_FEATURES),
        "inference_rows": int(len(features)),
        "overall_model_flag_rate": float(np.mean(flags)),
        "normal_period_model_flag_rate": float(np.mean(flags[normal_mask])),
        "injected_period_model_flag_rate": float(np.mean(flags[episode_mask])),
        "episodes_with_detector_response": responded,
        "episode_count": len(episode_metrics),
        "episode_metrics": episode_metrics,
        "moisture_predictions_available": predictions_available,
        "moisture_prediction_checks": moisture_checks,
        "model_inference_pass": bool(
            responded >= 6 and predictions_available == len(moisture_checks)
        ),
    }


def write_csv_atomic(dataframe: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    dataframe.to_csv(
        temporary,
        index=False,
        encoding="utf-8",
        float_format="%.6f",
        na_rep="",
        lineterminator="\n",
    )
    temporary.replace(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    protected_before = protected_hashes()
    canonical = pd.read_csv(CANONICAL_PATH, encoding="utf-8-sig")
    canonical.columns = [str(column).strip() for column in canonical.columns]
    if list(canonical.columns) != CANONICAL_COLUMNS:
        raise RuntimeError("Canonical column order differs from the audited contract.")

    demo, scenario_table, source_metadata = build_demo(canonical)
    warmup = build_warmup_context(canonical, demo)
    warmup_validation = validate_warmup_context(warmup, demo)
    dataset_validation = validate_dataset(canonical, demo, scenario_table)
    model_validation = validate_model_behavior(demo, scenario_table)

    write_csv_atomic(demo, OUTPUT_PATH)
    write_csv_atomic(warmup, WARMUP_PATH)
    write_csv_atomic(scenario_table, SCENARIO_PATH)
    protected_after = protected_hashes()
    if protected_before != protected_after:
        raise RuntimeError("A protected canonical dataset or notebook changed.")

    audit = {
        "audit_version": "dashboard_demo_v1.0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "dashboard demonstration/scenario replay only",
        "original_source_dataset": str(CANONICAL_PATH.relative_to(PROJECT_ROOT)),
        "dashboard_fork": str(OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "warmup_context": str(WARMUP_PATH.relative_to(PROJECT_ROOT)),
        "scenario_sidecar": str(SCENARIO_PATH.relative_to(PROJECT_ROOT)),
        "source_metadata": source_metadata,
        "warmup_validation": {
            **warmup_validation,
            "sha256": sha256_file(WARMUP_PATH),
        },
        "dataset_validation": dataset_validation,
        "model_validation": model_validation,
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "protected_assets_unchanged": protected_before == protected_after,
        "notebooks_modified": False,
        "canonical_datasets_modified": False,
        "model_retraining_performed": False,
        "model_evaluation_metrics_recomputed": False,
        "quality_reference_values_modified": False,
        "model_outputs_written_to_demo_csv": False,
    }
    with AUDIT_PATH.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(audit, file, indent=2, ensure_ascii=False)
        file.write("\n")

    print(f"Dashboard fork: {OUTPUT_PATH}")
    print(f"Hidden warm-up: {WARMUP_PATH}")
    print(f"Scenario sidecar: {SCENARIO_PATH}")
    print(f"Rows: {dataset_validation['row_count']:,}")
    print(
        "Episodes: "
        f"{dataset_validation['episode_count']} | injected rows: "
        f"{dataset_validation['injected_row_percentage']:.2f}%"
    )
    print(
        "Detector response: "
        f"{model_validation['episodes_with_detector_response']}/"
        f"{model_validation['episode_count']} episodes | "
        f"normal flag rate {model_validation['normal_period_model_flag_rate']:.2%}"
    )
    print(
        "Moisture inference: "
        f"{model_validation['moisture_predictions_available']}/"
        f"{model_validation['episode_count']} checks available"
    )
    print(
        "First visible prediction: "
        f"{warmup_validation['first_visible_predicted_moisture']:.6f} "
        "(hidden context only)"
    )
    print(f"Protected assets unchanged: {protected_before == protected_after}")
    if not model_validation["model_inference_pass"]:
        raise RuntimeError(
            "The unchanged trained pipeline did not respond to enough injected "
            "episodes; inspect the audit before changing scenario amplitudes."
        )


if __name__ == "__main__":
    main()
