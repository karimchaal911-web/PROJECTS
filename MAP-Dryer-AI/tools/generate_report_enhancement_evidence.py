"""Generate reproducible evidence used by the enhanced internship report.

This script is deliberately read-only with respect to the canonical datasets,
notebooks, and governed model artifacts.  It adds an independent report audit:

* last-laboratory-moisture persistence versus the frozen Ridge artifact;
* residual and split-conformal pilot diagnostics;
* held-out synthetic disturbance response for the frozen One-Class SVM;
* a controlled sensitivity study for ``nu``;
* an accelerated full held-out analytical replay benchmark;
* a feature/formula/unit audit; and
* a comparison between the manifest disturbance catalogue and the labels that
  are actually embedded in the canonical CSV.

Run from the project root:

    $env:PYTHONPATH="src"
    python tools/generate_report_enhancement_evidence.py
"""

from __future__ import annotations

import json
import math
import shutil
import time
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from anomaly.persistence import apply_persistence_logic
from multirate.instant_features import engineer_instant_features


ROOT = Path(__file__).resolve().parents[1]
ALIGNED = ROOT / "data" / "processed" / "MAP_Dryer_Lab_Aligned_16.csv"
CANONICAL = ROOT / "data" / "processed" / "MAP_Dryer_Canonical_5s.csv"
MANIFEST = CANONICAL.with_suffix(".manifest.json")
TEST_REPLAY = ROOT / "data" / "processed" / "MAP_Dryer_TEST_Replay_5s.csv"
MODEL_DIR = ROOT / "models" / "5s"
DASHBOARD_AUDIT = (
    ROOT
    / "resources"
    / "dashboard_demo"
    / "MAP_Dryer_Dashboard_Demo_Audit.json"
)

EVIDENCE_DIR = ROOT / "final_report" / "evidence"
FIGURE_DIR = ROOT / "final_report" / "figures" / "plots"
SCREENSHOT_DIR = ROOT / "final_report" / "figures" / "screenshots"
FINAL_DASHBOARD_IMAGE_DIR = ROOT / "final_presentation_claude" / "web" / "public" / "img"
METRICS_PATH = EVIDENCE_DIR / "report_enhancement_metrics.json"
FEATURE_AUDIT_PATH = EVIDENCE_DIR / "feature_unit_audit.csv"

TARGET = "Final Moisture (%H2O)"
PROCESS = [
    "Dryer Air Temperature",
    "Cooler Air Temperature",
    "Air Flow Rate",
    "Wet Product Feed Rate",
    "Product Inlet Temperature",
    "Residence Time",
    "Vacuum",
    "Steam Pressure",
    "Fan Speed",
]
QUALITY = ["Product Density", "Final Product Temp", TARGET]
TRAIN_END = pd.Timestamp("2026-06-19 08:00:00")
VALIDATION_END = pd.Timestamp("2026-07-03 04:00:00")
TEST_START = pd.Timestamp("2026-07-03 06:00:00")
RISK_SCALE = 2.7968971418305486

COLORS = {
    "green": "#0F766E",
    "blue": "#135D8C",
    "orange": "#D98E04",
    "red": "#D64545",
    "ink": "#17231F",
    "gray": "#6B7C76",
    "pale": "#E8F3EF",
}


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | int]:
    residual = predicted - actual
    return {
        "n": int(len(actual)),
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
        "bias": float(residual.mean()),
        "max_abs_error": float(np.abs(residual).max()),
    }


def _read_replay(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(
        frame["Date"].astype(str) + " " + frame["Time"].astype(str)
    )
    return frame


def _plot_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#CAD8D3",
            "axes.labelcolor": COLORS["ink"],
            "axes.titlecolor": COLORS["ink"],
            "xtick.color": COLORS["gray"],
            "ytick.color": COLORS["gray"],
            "grid.color": "#DDE8E4",
            "grid.alpha": 0.7,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def soft_sensor_evidence() -> dict[str, Any]:
    aligned = pd.read_csv(ALIGNED, parse_dates=["Sample Timestamp"])
    features = aligned.drop(columns=["Sample Timestamp", TARGET])
    actual = aligned[TARGET].to_numpy(dtype=float)
    train_end = round(len(aligned) * 0.70)
    test_start = round(len(aligned) * 0.85)

    frozen = joblib.load(MODEL_DIR / "quality_moisture_pipeline.joblib")
    ridge_prediction = frozen.predict(features.iloc[test_start:])
    test_actual = actual[test_start:]
    persistence_prediction = actual[test_start - 1 : -1]

    ridge_metrics = _metrics(test_actual, ridge_prediction)
    persistence_metrics = _metrics(test_actual, persistence_prediction)
    residual = ridge_prediction - test_actual
    residual_series = pd.Series(residual)
    residual_stats = {
        "mean": float(residual.mean()),
        "median": float(np.median(residual)),
        "standard_deviation": float(np.std(residual, ddof=1)),
        "q05": float(np.quantile(residual, 0.05)),
        "q95": float(np.quantile(residual, 0.95)),
        "underprediction_rate": float(np.mean(residual < 0)),
        "overprediction_rate": float(np.mean(residual > 0)),
        "durbin_watson": float(
            np.sum(np.diff(residual) ** 2) / np.sum(residual**2)
        ),
        "autocorrelation": {
            str(lag): float(residual_series.autocorr(lag))
            for lag in (1, 2, 3, 6, 12)
        },
        "absolute_residual_fitted_correlation": float(
            np.corrcoef(np.abs(residual), ridge_prediction)[0, 1]
        ),
    }

    # Independent uncertainty pilot: fit on TRAIN, calibrate on the later
    # VALIDATION block, and evaluate once on TEST.  This is not attached to the
    # final TRAIN+VALIDATION artifact and is labelled accordingly in the report.
    pilot = Pipeline(
        [("scaler", StandardScaler()), ("model", Ridge(alpha=10.0))]
    ).fit(features.iloc[:train_end], actual[:train_end])
    validation_residual = np.abs(
        pilot.predict(features.iloc[train_end:test_start])
        - actual[train_end:test_start]
    )
    pilot_test_prediction = pilot.predict(features.iloc[test_start:])
    conformal: dict[str, Any] = {
        "method": (
            "split-conformal pilot: TRAIN fit, VALIDATION calibration, TEST audit"
        ),
        "model_scope": "independent uncertainty pilot; not the final refitted artifact",
        "test_metrics": _metrics(test_actual, pilot_test_prediction),
        "intervals": {},
    }
    for nominal_coverage in (0.90, 0.95):
        alpha = 1.0 - nominal_coverage
        level = math.ceil((len(validation_residual) + 1) * (1 - alpha)) / len(
            validation_residual
        )
        half_width = float(
            np.quantile(validation_residual, level, method="higher")
        )
        covered = np.abs(test_actual - pilot_test_prediction) <= half_width
        conformal["intervals"][f"{int(nominal_coverage * 100)}"] = {
            "nominal_coverage": nominal_coverage,
            "empirical_test_coverage": float(covered.mean()),
            "half_width_percentage_points": half_width,
            "mean_width_percentage_points": 2 * half_width,
        }

    fig, axes = plt.subplots(2, 2, figsize=(12.4, 7.5))
    x = np.arange(len(test_actual))
    axes[0, 0].plot(x, test_actual, color=COLORS["ink"], lw=1.4, label="Laboratory")
    axes[0, 0].plot(
        x, ridge_prediction, color=COLORS["green"], lw=1.3, label="Ridge"
    )
    axes[0, 0].set_title("Untouched TEST chronology")
    axes[0, 0].set_ylabel("Moisture (% H$_2$O)")
    axes[0, 0].legend(frameon=False, ncol=2)
    axes[0, 0].grid(True)

    labels = ["Persistence", "Ridge"]
    mae = [persistence_metrics["mae"], ridge_metrics["mae"]]
    rmse = [persistence_metrics["rmse"], ridge_metrics["rmse"]]
    xpos = np.arange(2)
    width = 0.34
    axes[0, 1].bar(
        xpos - width / 2, mae, width, color=COLORS["orange"], label="MAE"
    )
    axes[0, 1].bar(
        xpos + width / 2, rmse, width, color=COLORS["blue"], label="RMSE"
    )
    axes[0, 1].set_xticks(xpos, labels)
    axes[0, 1].set_title("Baseline comparison")
    axes[0, 1].set_ylabel("Percentage points")
    axes[0, 1].legend(frameon=False)
    axes[0, 1].grid(True, axis="y")

    axes[1, 0].axhline(0, color=COLORS["gray"], lw=0.9)
    axes[1, 0].plot(x, residual, color=COLORS["blue"], lw=1.0)
    axes[1, 0].set_title("Ridge residuals (prediction - laboratory)")
    axes[1, 0].set_xlabel("Chronological TEST sample")
    axes[1, 0].set_ylabel("Percentage points")
    axes[1, 0].grid(True)

    axes[1, 1].hist(
        residual, bins=22, color=COLORS["green"], alpha=0.86, edgecolor="white"
    )
    axes[1, 1].axvline(0, color=COLORS["ink"], lw=1.0)
    axes[1, 1].set_title("Residual distribution")
    axes[1, 1].set_xlabel("Prediction - laboratory (percentage points)")
    axes[1, 1].set_ylabel("Count")
    axes[1, 1].grid(True, axis="y")
    fig.suptitle(
        "Soft-sensor evidence: persistence baseline and residual behaviour",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(
        FIGURE_DIR / "soft_sensor_baseline_residuals.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)

    return {
        "split": {
            "train_rows": train_end,
            "validation_rows": test_start - train_end,
            "test_rows": len(aligned) - test_start,
        },
        "ridge": ridge_metrics,
        "last_lab_persistence": persistence_metrics,
        "ridge_improvement_over_persistence": {
            "mae_fraction": float(1 - ridge_metrics["mae"] / persistence_metrics["mae"]),
            "rmse_fraction": float(
                1 - ridge_metrics["rmse"] / persistence_metrics["rmse"]
            ),
        },
        "residuals": residual_stats,
        "uncertainty_pilot": conformal,
    }


def _group_labelled_episodes(frame: pd.DataFrame) -> pd.DataFrame:
    abnormal = frame.loc[
        frame["Disturbance State"].astype(str).str.lower().ne("normal"),
        ["timestamp", "Disturbance State"],
    ].copy()
    abnormal["new_episode"] = (
        abnormal["Disturbance State"].ne(abnormal["Disturbance State"].shift())
        | abnormal["timestamp"].diff().gt(pd.Timedelta(seconds=5))
    )
    abnormal["episode"] = abnormal["new_episode"].cumsum()
    return (
        abnormal.groupby(["episode", "Disturbance State"], sort=True)["timestamp"]
        .agg(start="min", end="max", rows="size")
        .reset_index()
    )


def anomaly_evidence() -> tuple[dict[str, Any], pd.DataFrame, np.ndarray, np.ndarray]:
    replay = _read_replay(TEST_REPLAY)
    instant = engineer_instant_features(replay[PROCESS])
    scaler = joblib.load(MODEL_DIR / "anomaly_scaler.joblib")
    detector = joblib.load(MODEL_DIR / "anomaly_model.joblib")
    scaled = scaler.transform(instant)
    decision = detector.decision_function(scaled)
    raw_flag = decision < 0
    risk = 1.0 / (1.0 + np.exp(np.clip(decision / RISK_SCALE, -60.0, 60.0)))
    designed = replay["Disturbance State"].astype(str).str.lower().ne("normal").to_numpy()

    persistence_input = pd.DataFrame(
        {
            "timestamp": replay["timestamp"],
            "Split": "Testing",
            "Raw anomaly flag": raw_flag,
        }
    )
    persistent = apply_persistence_logic(
        persistence_input,
        expected_sample_interval=pd.Timedelta(seconds=5),
        window_observations=3,
        minimum_candidates=2,
    )["Persistent alarm"].to_numpy(dtype=bool)

    flagged_times = replay.loc[raw_flag, ["timestamp"]].copy()
    flagged_times["new_event"] = (
        flagged_times["timestamp"].diff().gt(pd.Timedelta(seconds=30))
        | flagged_times["timestamp"].diff().isna()
    )
    flagged_times["event"] = flagged_times["new_event"].cumsum()
    grouped_events = (
        flagged_times.groupby("event")["timestamp"]
        .agg(start="min", end="max", rows="size")
        .reset_index()
    )
    grouped_events["overlaps_designed_episode"] = grouped_events.apply(
        lambda row: bool(
            (
                (replay["timestamp"] >= row["start"])
                & (replay["timestamp"] <= row["end"])
                & designed
            ).any()
        ),
        axis=1,
    )

    replay_eval = replay[["timestamp", "Disturbance State"]].copy()
    replay_eval["raw_flag"] = raw_flag
    replay_eval["persistent_flag"] = persistent
    replay_eval["risk"] = risk
    scenario_table = (
        replay_eval.groupby("Disturbance State", sort=False)
        .agg(
            rows=("raw_flag", "size"),
            raw_flag_rate=("raw_flag", "mean"),
            persistent_flag_rate=("persistent_flag", "mean"),
            peak_display_risk=("risk", "max"),
        )
        .reset_index()
    )
    scenario_rows: list[dict[str, Any]] = []
    for state, group in replay_eval.loc[
        replay_eval["Disturbance State"].ne("normal")
    ].groupby("Disturbance State", sort=False):
        first_raw = group.loc[group["raw_flag"], "timestamp"].min()
        first_persistent = group.loc[group["persistent_flag"], "timestamp"].min()
        start = group["timestamp"].min()
        scenario_rows.append(
            {
                "scenario": state,
                "start": str(start),
                "end": str(group["timestamp"].max()),
                "rows": int(len(group)),
                "raw_flag_rate": float(group["raw_flag"].mean()),
                "persistent_flag_rate": float(group["persistent_flag"].mean()),
                "first_raw_detection_delay_seconds": (
                    float((first_raw - start).total_seconds())
                    if pd.notna(first_raw)
                    else None
                ),
                "first_persistent_detection_delay_seconds": (
                    float((first_persistent - start).total_seconds())
                    if pd.notna(first_persistent)
                    else None
                ),
                "peak_display_risk": float(group["risk"].max()),
            }
        )

    result = {
        "scope": "held-out chronological TEST synthetic labels only",
        "rows": int(len(replay)),
        "designed_disturbance_rows": int(designed.sum()),
        "designed_episode_count": int(
            len(_group_labelled_episodes(replay))
        ),
        "raw_flag_rows": int(raw_flag.sum()),
        "raw_flag_rate": float(raw_flag.mean()),
        "normal_row_flag_rate": float(raw_flag[~designed].mean()),
        "designed_row_recall": float(raw_flag[designed].mean()),
        "designed_row_precision": float(designed[raw_flag].mean()),
        "persistent_flag_rate": float(persistent.mean()),
        "persistent_normal_row_flag_rate": float(persistent[~designed].mean()),
        "persistent_designed_row_recall": float(persistent[designed].mean()),
        "persistent_designed_row_precision": float(designed[persistent].mean()),
        "grouped_candidate_events_30s": int(len(grouped_events)),
        "grouped_events_overlapping_designed": int(
            grouped_events["overlaps_designed_episode"].sum()
        ),
        "scenario_response": scenario_rows,
        "interpretation": (
            "Designed synthetic disturbance recall is not plant fault recall; "
            "normal-row flags are not confirmed false alarms."
        ),
    }

    fig, axes = plt.subplots(2, 1, figsize=(12.4, 7.1), sharex=True)
    axes[0].plot(replay["timestamp"], decision, color=COLORS["blue"], lw=0.7)
    axes[0].axhline(0, color=COLORS["red"], lw=1.0, label="OCSVM boundary")
    axes[0].set_ylabel("Decision function")
    axes[0].set_title("Frozen One-Class SVM on the chronological TEST replay")
    axes[0].grid(True)
    axes[0].legend(frameon=False)
    axes[1].plot(replay["timestamp"], risk, color=COLORS["green"], lw=0.8)
    axes[1].axhline(0.5, color=COLORS["orange"], lw=1.0, ls="--")
    axes[1].set_ylabel("Display risk (not probability)")
    axes[1].set_xlabel("Prototype timestamp")
    axes[1].grid(True)
    for _, episode in _group_labelled_episodes(replay).iterrows():
        for axis in axes:
            axis.axvspan(
                episode["start"], episode["end"], color=COLORS["red"], alpha=0.13
            )
    fig.tight_layout()
    fig.savefig(
        FIGURE_DIR / "anomaly_holdout_validation.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)

    scenario_plot = scenario_table.loc[
        scenario_table["Disturbance State"].ne("normal")
    ].copy()
    fig, axis = plt.subplots(figsize=(9.6, 4.7))
    xpos = np.arange(len(scenario_plot))
    axis.bar(
        xpos,
        100 * scenario_plot["raw_flag_rate"],
        color=[COLORS["orange"], COLORS["blue"], COLORS["green"]],
    )
    axis.set_xticks(xpos, scenario_plot["Disturbance State"].str.replace("_", " "))
    axis.set_ylabel("Flagged rows (%)")
    axis.set_ylim(0, 100)
    axis.set_title("Response to the three designed episodes in held-out TEST")
    axis.grid(True, axis="y")
    for index, value in enumerate(100 * scenario_plot["raw_flag_rate"]):
        axis.text(index, value + 2.2, f"{value:.1f}%", ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(
        FIGURE_DIR / "anomaly_scenario_response.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)

    return result, replay, raw_flag, decision


def _load_canonical_for_audit() -> pd.DataFrame:
    usecols = ["Date", "Time", "Disturbance State", *PROCESS, *QUALITY]
    frame = pd.read_csv(CANONICAL, usecols=usecols)
    frame["timestamp"] = pd.to_datetime(
        frame["Date"].astype(str) + " " + frame["Time"].astype(str)
    )
    return frame


def dataset_label_audit(canonical: pd.DataFrame) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    episodes = _group_labelled_episodes(canonical)
    counts = episodes["Disturbance State"].value_counts().to_dict()
    return {
        "embedded_label_episode_count": int(len(episodes)),
        "embedded_label_counts_by_type": {key: int(value) for key, value in counts.items()},
        "manifest_catalogue_count": int(len(manifest.get("disturbances", []))),
        "catalogue_matches_embedded_labels": bool(
            len(episodes) == len(manifest.get("disturbances", []))
        ),
        "generator_provenance": {
            "generator_version": manifest.get("generator_version"),
            "configuration_path": manifest.get("configuration_path"),
            "random_seed": manifest.get("random_seed"),
            "source_filename": manifest.get("source_filename"),
        },
        "report_rule": (
            "Use direct CSV label audit for scenario counts; treat the manifest "
            "disturbance catalogue as stale metadata and do not infer missing "
            "generator equations."
        ),
    }


def nu_sensitivity(canonical: pd.DataFrame) -> dict[str, Any]:
    train_positions = np.flatnonzero(canonical["timestamp"].le(TRAIN_END).to_numpy())
    validation_positions = np.flatnonzero(
        (
            canonical["timestamp"].gt(TRAIN_END)
            & canonical["timestamp"].le(VALIDATION_END)
        ).to_numpy()
    )
    test_positions = np.flatnonzero(canonical["timestamp"].ge(TEST_START).to_numpy())

    train_stride = max(len(train_positions) // 6000, 1)
    validation_stride = max(len(validation_positions) // 20000, 1)
    fit_positions = train_positions[::train_stride][:6000]
    check_positions = validation_positions[::validation_stride][:20000]
    diagnostic_test_positions = test_positions[::12]  # one-minute diagnostic sample

    scaler = joblib.load(MODEL_DIR / "anomaly_scaler.joblib")
    fit_scaled = scaler.transform(
        engineer_instant_features(canonical.iloc[fit_positions][PROCESS])
    )
    validation_scaled = scaler.transform(
        engineer_instant_features(canonical.iloc[check_positions][PROCESS])
    )
    diagnostic_test = canonical.iloc[diagnostic_test_positions]
    diagnostic_test_scaled = scaler.transform(
        engineer_instant_features(diagnostic_test[PROCESS])
    )
    labels = diagnostic_test["Disturbance State"].astype(str).to_numpy()

    rows: list[dict[str, Any]] = []
    for nu in (0.005, 0.01, 0.02, 0.03, 0.05):
        model = OneClassSVM(kernel="rbf", gamma="scale", nu=nu).fit(fit_scaled)
        validation_flag = model.predict(validation_scaled) == -1
        test_flag = model.predict(diagnostic_test_scaled) == -1
        row: dict[str, Any] = {
            "nu": nu,
            "validation_flag_rate": float(validation_flag.mean()),
            "test_normal_flag_rate": float(test_flag[labels == "normal"].mean()),
        }
        for scenario in ("feed_surge", "steam_dip", "airflow_restriction"):
            row[f"{scenario}_recall"] = float(
                test_flag[labels == scenario].mean()
            )
        rows.append(row)

    table = pd.DataFrame(rows)
    fig, axis = plt.subplots(figsize=(9.7, 5.1))
    axis.plot(
        table["nu"],
        100 * table["test_normal_flag_rate"],
        marker="o",
        color=COLORS["gray"],
        label="Normal rows flagged",
    )
    axis.plot(
        table["nu"],
        100 * table["steam_dip_recall"],
        marker="o",
        color=COLORS["orange"],
        label="Steam-dip recall",
    )
    axis.plot(
        table["nu"],
        100 * table["airflow_restriction_recall"],
        marker="o",
        color=COLORS["blue"],
        label="Airflow-restriction recall",
    )
    axis.plot(
        table["nu"],
        100 * table["feed_surge_recall"],
        marker="o",
        color=COLORS["red"],
        label="Feed-surge recall",
    )
    axis.axvline(0.02, color=COLORS["green"], ls="--", lw=1.1, label="Selected $\\nu$")
    axis.set_xlabel("One-Class SVM $\\nu$")
    axis.set_ylabel("Rows flagged / detected (%)")
    axis.set_ylim(-3, 100)
    axis.set_title("Sensitivity study on a one-minute sample of held-out TEST")
    axis.grid(True)
    axis.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(
        FIGURE_DIR / "anomaly_nu_sensitivity.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)

    return {
        "fit_rows": int(len(fit_positions)),
        "validation_rows": int(len(check_positions)),
        "test_sample_rows": int(len(diagnostic_test_positions)),
        "test_sample_cadence_seconds": 60,
        "controlled_variables": (
            "same scaler, deterministic fit sample, RBF kernel and gamma='scale'"
        ),
        "results": rows,
    }


def accelerated_analytical_replay(
    canonical: pd.DataFrame, test_replay: pd.DataFrame
) -> dict[str, Any]:
    """Benchmark both frozen models over every held-out five-second row.

    The benchmark is intentionally database-free and batch-accelerated.  It
    measures feature construction and both model paths, not PostgreSQL writes,
    diagnosis text generation, Power BI queries, or deliberate five-second
    pacing.
    """

    moisture_model = joblib.load(MODEL_DIR / "quality_moisture_pipeline.joblib")
    anomaly_model = joblib.load(MODEL_DIR / "anomaly_model.joblib")
    anomaly_scaler = joblib.load(MODEL_DIR / "anomaly_scaler.joblib")

    source_timestamps = canonical["timestamp"].to_numpy(dtype="datetime64[ns]")
    replay_timestamps = test_replay["timestamp"].to_numpy(dtype="datetime64[ns]")
    effective = replay_timestamps - pd.to_timedelta(
        test_replay["Residence Time"].to_numpy(dtype=float), unit="m"
    ).to_numpy()
    snapshot_positions = np.searchsorted(source_timestamps, effective, side="right") - 1

    laboratory = canonical.loc[
        canonical["Product Density"].notna()
        & canonical["Final Product Temp"].notna(),
        ["timestamp", "Product Density", "Final Product Temp"],
    ]
    lab_timestamps = laboratory["timestamp"].to_numpy(dtype="datetime64[ns]")
    prior_lab_positions = np.searchsorted(
        lab_timestamps, replay_timestamps, side="left"
    ) - 1
    if (snapshot_positions < 0).any() or (prior_lab_positions < 0).any():
        raise RuntimeError("Full replay benchmark does not have sufficient history.")

    chunk_size = 20_000
    chunk_seconds: list[float] = []
    anomaly_flags = 0
    moisture_count = 0
    started = time.perf_counter()
    for start in range(0, len(test_replay), chunk_size):
        stop = min(start + chunk_size, len(test_replay))
        chunk_started = time.perf_counter()
        replay_chunk = test_replay.iloc[start:stop]
        instant = engineer_instant_features(replay_chunk[PROCESS])
        scaled = anomaly_scaler.transform(instant)
        anomaly_flags += int((anomaly_model.predict(scaled) == -1).sum())

        positions = snapshot_positions[start:stop]
        snapshot = canonical.iloc[positions]
        previous_lab = laboratory.iloc[prior_lab_positions[start:stop]]
        moisture_features = pd.DataFrame(
            {
                "dryer_air_temperature": snapshot["Dryer Air Temperature"].to_numpy(),
                "cooler_air_temperature": snapshot["Cooler Air Temperature"].to_numpy(),
                "air_flow_rate": snapshot["Air Flow Rate"].to_numpy(),
                "wet_product_feed_rate": snapshot["Wet Product Feed Rate"].to_numpy(),
                "product_inlet_temperature": snapshot["Product Inlet Temperature"].to_numpy(),
                "residence_time": snapshot["Residence Time"].to_numpy(),
                "vacuum": snapshot["Vacuum"].to_numpy(),
                "steam_pressure": snapshot["Steam Pressure"].to_numpy(),
                "fan_speed": snapshot["Fan Speed"].to_numpy(),
                "product_density": previous_lab["Product Density"].to_numpy(),
                "final_product_temp": previous_lab["Final Product Temp"].to_numpy(),
            }
        )
        moisture_features["temperature_drop"] = (
            moisture_features["dryer_air_temperature"]
            - moisture_features["final_product_temp"]
        )
        moisture_features["air_product_delta"] = (
            moisture_features["dryer_air_temperature"]
            - moisture_features["product_inlet_temperature"]
        )
        moisture_features["air_per_feed"] = (
            moisture_features["air_flow_rate"]
            / moisture_features["wet_product_feed_rate"]
        )
        moisture_features["steam_temp_interaction"] = (
            moisture_features["steam_pressure"]
            * moisture_features["dryer_air_temperature"]
        )
        moisture_features["heating_index"] = (
            moisture_features["residence_time"]
            * moisture_features["dryer_air_temperature"]
        )
        prediction = moisture_model.predict(moisture_features)
        moisture_count += int(np.isfinite(prediction).sum())
        chunk_seconds.append(time.perf_counter() - chunk_started)

    elapsed = time.perf_counter() - started
    per_row_ms = 1000 * np.asarray(chunk_seconds) / np.asarray(
        [
            min(chunk_size, len(test_replay) - start)
            for start in range(0, len(test_replay), chunk_size)
        ]
    )
    return {
        "scope": (
            "batch-accelerated analytics only; excludes database, diagnosis text, "
            "Power BI, source transport and deliberate pacing"
        ),
        "rows": int(len(test_replay)),
        "moisture_predictions": int(moisture_count),
        "anomaly_flags": int(anomaly_flags),
        "chunk_size": chunk_size,
        "chunks": int(len(chunk_seconds)),
        "wall_seconds": float(elapsed),
        "throughput_rows_per_second": float(len(test_replay) / elapsed),
        "normalized_chunk_latency_ms_per_row": {
            "mean": float(per_row_ms.mean()),
            "p50": float(np.quantile(per_row_ms, 0.50)),
            "p95": float(np.quantile(per_row_ms, 0.95)),
            "p99": float(np.quantile(per_row_ms, 0.99)),
            "max": float(per_row_ms.max()),
        },
    }


def dashboard_demonstration_evidence() -> dict[str, Any]:
    if not DASHBOARD_AUDIT.exists():
        return {"available": False}
    payload = json.loads(DASHBOARD_AUDIT.read_text(encoding="utf-8"))
    model = payload["model_validation"]
    return {
        "available": True,
        "purpose": payload["purpose"],
        "source_rows": payload["source_metadata"]["source_rows"],
        "injected_episode_count": payload["dataset_validation"]["episode_count"],
        "normal_rows_preserved": payload["source_metadata"]["normal_process_rows_preserved"],
        "laboratory_values_preserved": payload["source_metadata"]["laboratory_values_preserved"],
        "normal_period_model_flag_rate": model["normal_period_model_flag_rate"],
        "injected_period_model_flag_rate": model["injected_period_model_flag_rate"],
        "episodes_with_detector_response": model["episodes_with_detector_response"],
        "episode_count": model["episode_count"],
        "interpretation": (
            "Dedicated dashboard demonstration fork; not canonical TEST evidence "
            "and not a plant fault benchmark."
        ),
    }


def write_feature_unit_audit() -> None:
    rows = [
        ("dryer_air_temperature", "both", "direct process", "-", "degC", "prototype unit; reconcile plant tag"),
        ("cooler_air_temperature", "both", "direct process", "-", "degC", "prototype unit; reconcile plant tag"),
        ("air_flow_rate", "both", "direct process", "-", "m3/h", "defined repository convention"),
        ("wet_product_feed_rate", "both", "direct process", "-", "m3/h", "volumetric prototype convention; confirm plant basis"),
        ("product_inlet_temperature", "both", "direct process", "-", "degC", "prototype unit; reconcile plant tag"),
        ("residence_time", "both", "direct process", "-", "min", "prototype estimate; not parcel tracking"),
        ("vacuum", "both", "direct process", "-", "mmH2O", "canonical file is positive-valued; confirm plant polarity"),
        ("steam_pressure", "both", "direct process", "-", "bar", "defined repository convention"),
        ("fan_speed", "both", "direct process", "-", "rpm", "defined repository convention"),
        ("product_density", "moisture", "strictly previous lab", "-", "kg/L", "carried context, not a current fast measurement"),
        ("final_product_temp", "moisture", "strictly previous lab", "-", "degC", "carried context, not a current fast measurement"),
        ("temperature_drop", "moisture", "derived", "dryer_air_temperature - final_product_temp", "delta degC", "uses prior laboratory product temperature"),
        ("air_product_delta", "both", "derived", "dryer_air_temperature - product_inlet_temperature", "delta degC", "temperature-difference proxy"),
        ("cooler_delta", "anomaly", "derived", "dryer_air_temperature - cooler_air_temperature", "delta degC", "path temperature proxy"),
        ("air_per_feed", "both", "derived", "air_flow_rate / wet_product_feed_rate", "ratio", "dimensionless only under the shared volumetric convention"),
        ("steam_per_feed", "anomaly", "derived", "steam_pressure / wet_product_feed_rate", "bar/(m3/h)", "heuristic loading proxy"),
        ("steam_temp_interaction", "moisture", "derived", "steam_pressure * dryer_air_temperature", "bar*degC", "statistical interaction, not heat duty"),
        ("thermal_load", "anomaly", "derived", "steam_pressure * dryer_air_temperature", "bar*degC", "historical name; not heat duty"),
        ("heating_index", "moisture", "derived", "residence_time * dryer_air_temperature", "min*degC", "exposure proxy, not energy"),
        ("thermal_exposure", "anomaly", "derived", "residence_time * dryer_air_temperature", "min*degC", "exposure proxy, not energy"),
    ]
    pd.DataFrame(
        rows,
        columns=["feature", "used_by", "source", "formula", "unit", "limitation"],
    ).to_csv(FEATURE_AUDIT_PATH, index=False)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # Keep the report self-contained while using the current, manually refined
    # dashboard captures (higher numeric precision and final spacing).
    for name in ("powerbi_overview.png", "powerbi_diagnostics.png"):
        shutil.copy2(FINAL_DASHBOARD_IMAGE_DIR / name, SCREENSHOT_DIR / name)
    _plot_style()

    soft_sensor = soft_sensor_evidence()
    anomaly, test_replay, _, _ = anomaly_evidence()
    canonical = _load_canonical_for_audit()
    labels = dataset_label_audit(canonical)
    sensitivity = nu_sensitivity(canonical)
    replay = accelerated_analytical_replay(canonical, test_replay)
    dashboard = dashboard_demonstration_evidence()
    write_feature_unit_audit()

    payload = {
        "created_at": pd.Timestamp.now().isoformat(),
        "evidence_scope": (
            "independent report audit; canonical datasets and governed model "
            "artifacts were read but not modified"
        ),
        "soft_sensor": soft_sensor,
        "anomaly_detector": anomaly,
        "nu_sensitivity": sensitivity,
        "accelerated_analytical_replay": replay,
        "dataset_label_audit": labels,
        "dashboard_demonstration": dashboard,
    }
    METRICS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {METRICS_PATH.relative_to(ROOT)}")
    print(f"Wrote {FEATURE_AUDIT_PATH.relative_to(ROOT)}")
    print(
        "Soft sensor TEST RMSE: "
        f"{soft_sensor['ridge']['rmse']:.7f} versus persistence "
        f"{soft_sensor['last_lab_persistence']['rmse']:.7f}"
    )
    print(
        "Anomaly TEST designed-row recall / normal-row flag rate: "
        f"{anomaly['designed_row_recall']:.3%} / "
        f"{anomaly['normal_row_flag_rate']:.3%}"
    )
    print(
        "Accelerated analytical replay: "
        f"{replay['rows']:,} rows in {replay['wall_seconds']:.2f} s"
    )


if __name__ == "__main__":
    main()
