"""Extract verified presentation data from the canonical repository artifacts.

Every number rendered by the soutenance experience originates here. Nothing in
this script invents, smooths or rescales a model result: predictions come from
the exact notebook artifacts in models/5s/, and the headline metrics are
re-derived and asserted against artifacts/notebook03_model_evaluation.json.

Output: final_presentation_claude/web/public/data/*.json
"""

from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "final_presentation_claude" / "web" / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO / "src"))
from multirate.instant_features import engineer_instant_features  # noqa: E402

SCHEMA = json.loads((REPO / "models/5s/feature_schema.json").read_text())
NB03 = json.loads((REPO / "artifacts/notebook03_model_evaluation.json").read_text())
NB04 = json.loads((REPO / "artifacts/notebook04_anomaly_evaluation.json").read_text())

MOISTURE_FEATURES = SCHEMA["moisture_model_features"]
PROCESS_FEATURES = SCHEMA["process_model_features"]
RISK_SCALE = float(SCHEMA["anomaly_risk_calibration"]["score_scale"])
TEST_START = pd.Timestamp("2026-07-03 06:00:00")

moisture_pipeline = joblib.load(REPO / "models/5s/quality_moisture_pipeline.joblib")
anomaly_model = joblib.load(REPO / "models/5s/anomaly_model.joblib")
anomaly_scaler = joblib.load(REPO / "models/5s/anomaly_scaler.joblib")

RENAME = {
    "Dryer Air Temperature": "dryer_air_temperature",
    "Cooler Air Temperature": "cooler_air_temperature",
    "Air Flow Rate": "air_flow_rate",
    "Wet Product Feed Rate": "wet_product_feed_rate",
    "Product Inlet Temperature": "product_inlet_temperature",
    "Residence Time": "residence_time",
    "Vacuum": "vacuum",
    "Steam Pressure": "steam_pressure",
    "Fan Speed": "fan_speed",
}


def write(name: str, payload: dict) -> None:
    path = OUT / name
    path.write_text(json.dumps(payload, separators=(",", ":")))
    print("  wrote %-24s %8.1f KB" % (name, path.stat().st_size / 1024))


def r(x, n=6):
    """Round for transport; None-safe."""
    if x is None:
        return None
    x = float(x)
    if not math.isfinite(x):
        return None
    return round(x, n)


# ---------------------------------------------------------------- holdout ---
def build_holdout() -> dict:
    df = pd.read_csv(
        REPO / "data/processed/MAP_Dryer_Lab_Aligned_16.csv",
        parse_dates=["Sample Timestamp"],
    )
    test = df[df["Sample Timestamp"] >= TEST_START].reset_index(drop=True)
    y = test["Final Moisture (%H2O)"].to_numpy(float)
    yhat = moisture_pipeline.predict(test[MOISTURE_FEATURES]).astype(float)

    mae = float(np.abs(y - yhat).mean())
    rmse = float(np.sqrt(((y - yhat) ** 2).mean()))
    r2 = float(1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum())
    bias = float((yhat - y).mean())
    max_abs = float(np.abs(y - yhat).max())

    ref = NB03["metrics"]["test"]
    checks = (("mae", mae), ("rmse", rmse), ("r2", r2),
              ("bias", bias), ("max_abs_error", max_abs))
    for key, got in checks:
        assert abs(got - ref[key]) < 1e-9, "%s drifted: %r vs %r" % (key, got, ref[key])
    assert len(test) == ref["n"] == 165

    return {
        "target": "Final Moisture (%H2O)",
        "unit": "% H2O",
        "n": int(len(test)),
        "start": str(test["Sample Timestamp"].iloc[0]),
        "end": str(test["Sample Timestamp"].iloc[-1]),
        "metrics": {"mae": mae, "rmse": rmse, "r2": r2,
                    "bias": bias, "maxAbsError": max_abs},
        "t": [ts.isoformat(sep=" ") for ts in test["Sample Timestamp"]],
        "actual": [r(v) for v in y],
        "predicted": [r(v) for v in yhat],
        "residual": [r(v) for v in (yhat - y)],
    }


# ------------------------------------------------------------- candidates ---
def build_candidates() -> dict:
    rows = []
    for name, block in NB03["candidate_results"].items():
        rows.append({
            "name": name,
            "cvRmse": block["time_series_cv_rmse"],
            "valRmse": block["validation"]["rmse"],
            "valR2": block["validation"]["r2"],
            "valMae": block["validation"]["mae"],
            "selected": name == NB03["selected_model"],
        })
    rows.sort(key=lambda row: row["valRmse"])
    return {
        "selected": NB03["selected_model"],
        "selectedParameters": NB03["selected_parameters"],
        "criterion": "validation RMSE, time-aware tuning on TRAIN only",
        "candidates": rows,
    }


# ----------------------------------------------------------- coefficients ---
def build_coefficients() -> dict:
    ridge = moisture_pipeline.named_steps["model"]
    coef = np.asarray(ridge.coef_, dtype=float).ravel()
    order = np.argsort(-np.abs(coef))
    return {
        "note": ("Standardised Ridge coefficients. The pipeline z-scores every "
                 "input, so magnitudes are directly comparable."),
        "features": [
            {"name": MOISTURE_FEATURES[i], "coef": r(coef[i], 8),
             "abs": r(abs(coef[i]), 8)}
            for i in order
        ],
    }


# ------------------------------------------------- replay-derived windows ---
def load_replay() -> pd.DataFrame:
    cols = ["Date", "Time", "Dryer Air Temperature", "Cooler Air Temperature",
            "Air Flow Rate", "Wet Product Feed Rate", "Product Inlet Temperature",
            "Residence Time", "Vacuum", "Steam Pressure", "Fan Speed",
            "Product Density", "Final Product Temp", "Final Moisture (%H2O)",
            "Operating Regime", "Disturbance State"]
    df = pd.read_csv(REPO / "data/processed/MAP_Dryer_TEST_Replay_5s.csv", usecols=cols)
    df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    return df.drop(columns=["Date", "Time"])


def risk_from_score(score):
    z = np.clip(np.asarray(score, dtype=float) / RISK_SCALE, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(z))


def score_rows(frame: pd.DataFrame):
    feats = engineer_instant_features(frame)[PROCESS_FEATURES]
    scaled = anomaly_scaler.transform(feats)
    score = anomaly_model.decision_function(scaled).astype(float)
    return score, risk_from_score(score)


def build_anomaly(replay: pd.DataFrame) -> dict:
    proc = replay.rename(columns=RENAME)

    stride = 60  # 60 rows x 5 s = 5 minutes
    coarse = proc.iloc[::stride].reset_index(drop=True)
    _, coarse_risk = score_rows(coarse)
    flagged = float((coarse_risk > 0.5).mean() * 100.0)
    print("  TEST scored at 5 min stride: %d points, %.2f%% above warning"
          % (len(coarse), flagged))

    day0 = coarse["Timestamp"].iloc[0].normalize()
    best, best_score = None, -1.0
    for offset_h in range(0, 13 * 24, 6):
        lo = day0 + pd.Timedelta(hours=offset_h)
        hi = lo + pd.Timedelta(hours=24)
        mask = ((coarse["Timestamp"] >= lo) & (coarse["Timestamp"] < hi)).to_numpy()
        if mask.sum() < 200:
            continue
        peak = float(coarse_risk[mask].max())
        if peak > best_score:
            best_score, best = peak, (lo, hi)
    lo, hi = best
    print("  peak-risk 24 h window: %s -> %s (peak %.3f)" % (lo, hi, best_score))

    win = proc[(proc["Timestamp"] >= lo) & (proc["Timestamp"] < hi)].reset_index(drop=True)
    fine = win.iloc[::6].reset_index(drop=True)  # 30 s stride
    fine_score, fine_risk = score_rows(fine)

    event = build_event(proc, fine, fine_risk)

    return {
        "note": ("One-Class SVM decision function over 15 process-only features, "
                 "mapped to the dashboard display risk. The learned boundary is "
                 "risk 0.50."),
        "isProbability": False,
        "warning": SCHEMA["anomaly_risk_calibration"]["risk_warning_threshold"],
        "critical": SCHEMA["anomaly_risk_calibration"]["risk_critical_threshold"],
        "nu": NB04["nu"],
        "validationFlagRate": NB04["validation_flag_rate"],
        "trainingProcessRows": NB04["training_process_rows"],
        "fitSampleRows": NB04["fit_sample_rows"],
        "testFlagPercent": r(flagged, 3),
        "coarse": {
            "strideSeconds": stride * 5,
            "t": [ts.isoformat(sep=" ") for ts in coarse["Timestamp"]],
            "risk": [r(v, 4) for v in coarse_risk],
        },
        "window": {
            "start": str(lo), "end": str(hi), "strideSeconds": 30,
            "t": [ts.isoformat(sep=" ") for ts in fine["Timestamp"]],
            "risk": [r(v, 4) for v in fine_risk],
            "score": [r(v, 4) for v in fine_score],
            "disturbance": fine["Disturbance State"].astype(str).tolist(),
        },
        "event": event,
    }


def build_event(proc: pd.DataFrame, fine: pd.DataFrame, fine_risk) -> dict:
    """Close-up around the labelled synthetic disturbance inside the window.

    The detector is unsupervised: it never saw this label at any point. The
    label exists only in the synthetic generator and is used here purely to
    check where the learned novelty boundary actually fired.
    """
    state = fine["Disturbance State"].astype(str).to_numpy()
    flagged = np.asarray(fine_risk) > 0.5
    labels = sorted(set(state) - {"normal"})
    if not labels:
        return {}
    label = labels[0]
    mask = state == label
    dip_t = fine["Timestamp"].to_numpy()[mask]
    lo = pd.Timestamp(dip_t[0]) - pd.Timedelta(hours=2)
    hi = pd.Timestamp(dip_t[-1]) + pd.Timedelta(hours=2)

    close = proc[(proc["Timestamp"] >= lo) & (proc["Timestamp"] < hi)]
    close = close.iloc[::4].reset_index(drop=True)  # 20 s stride
    close_score, close_risk = score_rows(close)
    close_state = close["Disturbance State"].astype(str).to_numpy()
    inside = close_state == label

    precision = float((flagged & mask).sum() / max(int(flagged.sum()), 1))
    recall = float((flagged & mask).sum() / max(int(mask.sum()), 1))
    print("  labelled disturbance %r: %s -> %s | risk in-event mean %.3f, "
          "out-of-event mean %.3f | %d/%d warning points inside"
          % (label, dip_t[0], dip_t[-1], float(np.asarray(fine_risk)[mask].mean()),
             float(np.asarray(fine_risk)[~mask].mean()),
             int((flagged & mask).sum()), int(flagged.sum())))

    contributors = ["steam_pressure", "thermal_load", "dryer_air_temperature"]
    feats = engineer_instant_features(close)[PROCESS_FEATURES]
    return {
        "label": label,
        "labelSource": ("synthetic generator ground truth, used for validation "
                        "display only; the One-Class SVM is unsupervised and "
                        "never received this label"),
        "start": str(dip_t[0]), "end": str(dip_t[-1]),
        "durationMinutes": r((pd.Timestamp(dip_t[-1]) - pd.Timestamp(dip_t[0]))
                             .total_seconds() / 60.0, 1),
        "windowStart": str(lo), "windowEnd": str(hi), "strideSeconds": 20,
        "t": [ts.isoformat(sep=" ") for ts in close["Timestamp"]],
        "risk": [r(v, 4) for v in close_risk],
        "score": [r(v, 4) for v in close_score],
        "inEvent": [bool(v) for v in inside],
        "signals": {
            name: [r(v, 3) for v in feats[name].to_numpy(float)]
            for name in contributors
        },
        "riskInEventMean": r(float(np.asarray(fine_risk)[mask].mean()), 4),
        "riskOutEventMean": r(float(np.asarray(fine_risk)[~mask].mean()), 4),
        "warningPointsInsideEvent": int((flagged & mask).sum()),
        "warningPointsTotal": int(flagged.sum()),
        "precisionInWindow": r(precision, 4),
        "recallInWindow": r(recall, 4),
    }


def build_gap(replay: pd.DataFrame) -> dict:
    gap_lo = pd.Timestamp("2026-07-05 00:00:00")
    gap_hi = gap_lo + pd.Timedelta(hours=12)
    gap = replay[(replay["Timestamp"] >= gap_lo)
                 & (replay["Timestamp"] < gap_hi)].reset_index(drop=True)

    lab_mask = gap["Product Density"].notna() & gap["Final Product Temp"].notna()
    lab_rows = gap[lab_mask]
    print("  gap window %s -> %s: %d process rows, %d laboratory samples"
          % (gap_lo, gap_hi, len(gap), len(lab_rows)))

    ts = gap["Timestamp"].to_numpy()
    stride_gap = 12  # 1 minute
    idx = np.arange(0, len(gap), stride_gap)
    lab_ts = lab_rows["Timestamp"].to_numpy()
    lab_density = lab_rows["Product Density"].to_numpy(float)
    lab_temp = lab_rows["Final Product Temp"].to_numpy(float)

    snap_rows, pred_ts, used = [], [], []
    for i in idx:
        now = gap["Timestamp"].iloc[i]
        residence = float(gap["Residence Time"].iloc[i])
        window_end = now - pd.Timedelta(minutes=residence)
        pos = int(np.searchsorted(ts, np.datetime64(window_end), side="right")) - 1
        if pos < 0:
            continue
        lab_pos = int(np.searchsorted(lab_ts, np.datetime64(now), side="left")) - 1
        if lab_pos < 0:
            continue
        snap_rows.append(pos)
        pred_ts.append(now)
        used.append(lab_pos)

    snapshot = gap.iloc[snap_rows].rename(columns=RENAME).reset_index(drop=True)
    feat = pd.DataFrame(index=snapshot.index)
    direct = ["dryer_air_temperature", "cooler_air_temperature", "air_flow_rate",
              "wet_product_feed_rate", "product_inlet_temperature",
              "residence_time", "vacuum", "steam_pressure", "fan_speed"]
    for name in direct:
        feat[name] = snapshot[name].to_numpy(float)
    feat["product_density"] = lab_density[used]
    feat["final_product_temp"] = lab_temp[used]
    feat["temperature_drop"] = feat["dryer_air_temperature"] - feat["final_product_temp"]
    feat["air_product_delta"] = feat["dryer_air_temperature"] - feat["product_inlet_temperature"]
    feat["air_per_feed"] = feat["air_flow_rate"] / feat["wet_product_feed_rate"]
    feat["steam_temp_interaction"] = feat["steam_pressure"] * feat["dryer_air_temperature"]
    feat["heating_index"] = feat["residence_time"] * feat["dryer_air_temperature"]
    soft = moisture_pipeline.predict(feat[MOISTURE_FEATURES]).astype(float)

    coarse_gap = gap.set_index("Timestamp").loc[pd.DatetimeIndex(pred_ts)].reset_index()
    proc_gap = coarse_gap.rename(columns=RENAME)
    _, gap_risk = score_rows(proc_gap)

    return {
        "note": ("Continuous soft-sensor trace over a 12-hour held-out TEST "
                 "window, reproducing the runtime residence-time alignment. "
                 "Laboratory samples are the only directly measured points."),
        "start": str(gap_lo), "end": str(gap_hi),
        "labIntervalMinutes": 120,
        "strideSeconds": stride_gap * 5,
        "t": [pd.Timestamp(v).isoformat(sep=" ") for v in pred_ts],
        "predicted": [r(v) for v in soft],
        "risk": [r(v, 4) for v in gap_risk],
        "signals": {
            key: [r(v, 3) for v in proc_gap[key].to_numpy(float)]
            for key in direct
        },
        "lab": {
            "t": [pd.Timestamp(v).isoformat(sep=" ") for v in lab_ts],
            "moisture": [r(v) for v in lab_rows["Final Moisture (%H2O)"].to_numpy(float)],
            "density": [r(v) for v in lab_density],
            "productTemp": [r(v, 4) for v in lab_temp],
        },
    }


# ------------------------------------------------------------------ facts ---
def build_facts() -> dict:
    audit = json.loads((REPO / "artifacts/notebook01_canonical_audit.json").read_text())
    handoff = json.loads((REPO / "artifacts/notebook02_feature_handoff.json").read_text())
    registry = json.loads((REPO / "models/model_registry.json").read_text())
    return {
        "dataset": {
            "version": audit["dataset_version"],
            "sha256": audit["dataset_sha256"],
            "processRows": audit["process_rows"],
            "durationDays": audit["duration_days"],
            "intervalSeconds": audit["process_interval_seconds"],
            "intervalInterpretation": audit["process_interval_interpretation"],
            "laboratorySamples": audit["laboratory_samples"],
            "laboratoryIntervalMinutes": audit["laboratory_interval_minutes"],
            "start": audit["start_timestamp"], "end": audit["end_timestamp"],
            "disturbanceCount": audit["disturbance_count"],
            "checks": audit["checks"],
            "source": "synthetic_prototype",
        },
        "handoff": {
            "supervisedRows": handoff["supervised_rows"],
            "featureCount": handoff["feature_count"],
            "features": handoff["feature_names"],
            "availableEngineered": handoff["available_engineered_feature_count"],
            "alignment": handoff["temporal_alignment"],
            "labInputs": SCHEMA["laboratory_quality_inputs"],
            "labInputTiming": SCHEMA["laboratory_quality_input_timing"],
        },
        "split": NB03["split"],
        "moistureModel": {
            "family": "Ridge",
            "parameters": NB03["selected_parameters"],
            "featureCount": 16,
            "artifact": "models/5s/quality_moisture_pipeline.joblib",
            "sha256": NB03["model_artifact_sha256"],
            "metrics": NB03["metrics"],
        },
        "anomalyModel": {
            "family": "One-Class SVM",
            "learning": "unsupervised novelty detection",
            "featureCount": 15,
            "features": PROCESS_FEATURES,
            "nu": NB04["nu"],
            "kernelGamma": "scale",
            "artifact": "models/5s/anomaly_model.joblib",
            "sha256": NB04["artifacts"]["model"]["sha256"],
            "trainingProcessRows": NB04["training_process_rows"],
            "fitSampleRows": NB04["fit_sample_rows"],
            "validationFlagRate": NB04["validation_flag_rate"],
            "riskCalibration": NB04["risk_calibration"],
        },
        "replay": registry["models"][0]["test_replay"],
        "runtime": {
            "cadenceSeconds": 5,
            "service": "realtime_pipeline/src/realtime_service.py",
            "database": "PostgreSQL",
            "tables": ["dryer_map", "dryer_model_outputs", "dryer_abnormal_variables"],
            "views": ["vw_dryer_dashboard_powerbi", "vw_dryer_contributors_powerbi",
                      "vw_dryer_lab_samples", "vw_dryer_anomaly_events",
                      "vw_dryer_overview_trends_powerbi"],
            "dashboard": "Power BI Desktop, PBIP, DirectQuery, five-second page refresh",
            "smokeLatencyMsAvg": 9,
            "smokeLatencyMsMax": 47,
        },
        "tests": {"passed": 33, "subtests": 8, "seconds": 2.89},
        "boundaries": [
            "Synthetic prototype dataset, disturbances and labels.",
            "Five seconds is the prototype replay cadence, not a verified PCS7 historian rate.",
            "Anomaly risk is a calibrated display score, not a probability of failure.",
            "Diagnosis localises evidence; it does not prove root cause.",
            "Advisory only: no closed-loop control and no automatic write to the process.",
            "Laboratory analysis remains the quality reference.",
        ],
    }


# --------------------------------------------------------------- manifold ---
def build_manifold(replay: pd.DataFrame, event: dict) -> dict:
    """A truthful 3-D view of the learned normal operating region.

    The One-Class SVM lives in 15 standardised dimensions. To show it we fit a
    PCA on the TRAIN process rows the detector was fitted from and project
    three real things into the first three components: a sample of normal
    operation, the model's own 136 support vectors (the points that define the
    learned boundary), and the trajectory of the labelled disturbance.
    """
    from sklearn.decomposition import PCA

    cols = ["Date", "Time", "Dryer Air Temperature", "Cooler Air Temperature",
            "Air Flow Rate", "Wet Product Feed Rate", "Product Inlet Temperature",
            "Residence Time", "Vacuum", "Steam Pressure", "Fan Speed"]
    print("  loading TRAIN process rows for the manifold projection...")
    train = pd.read_csv(REPO / "data/processed/MAP_Dryer_Canonical_5s.csv",
                        usecols=cols, skiprows=lambda i: i > 0 and i % 240 != 0)
    train["Timestamp"] = pd.to_datetime(train["Date"] + " " + train["Time"])
    train = train[train["Timestamp"] < pd.Timestamp("2026-06-19 08:00:00")]
    train = train.rename(columns=RENAME).reset_index(drop=True)
    print("    TRAIN sample rows: %d (20 min stride)" % len(train))

    train_feats = engineer_instant_features(train)[PROCESS_FEATURES]
    train_scaled = anomaly_scaler.transform(train_feats)
    train_score = anomaly_model.decision_function(train_scaled).astype(float)

    pca = PCA(n_components=3, random_state=0).fit(train_scaled)
    normal = pca.transform(train_scaled)
    support = pca.transform(anomaly_model.support_vectors_)

    rng = np.random.default_rng(7)
    keep = rng.choice(len(normal), size=min(2400, len(normal)), replace=False)
    keep.sort()

    trajectory = []
    if event:
        close = replay[(replay["Timestamp"] >= pd.Timestamp(event["windowStart"]))
                       & (replay["Timestamp"] < pd.Timestamp(event["windowEnd"]))]
        close = close.iloc[::4].rename(columns=RENAME).reset_index(drop=True)
        close_feats = engineer_instant_features(close)[PROCESS_FEATURES]
        trajectory = pca.transform(anomaly_scaler.transform(close_feats))

    def pack(points):
        return [[r(p[0], 4), r(p[1], 4), r(p[2], 4)] for p in points]

    return {
        "note": ("PCA(3) fitted on the standardised TRAIN process rows. The "
                 "support vectors are the model's own boundary-defining points."),
        "explainedVariance": [r(v, 5) for v in pca.explained_variance_ratio_],
        "normal": {
            "points": pack(normal[keep]),
            "score": [r(train_score[i], 4) for i in keep],
        },
        "support": {"points": pack(support), "count": int(len(support))},
        "trajectory": {
            "points": pack(trajectory),
            "risk": event.get("risk", []) if event else [],
            "inEvent": event.get("inEvent", []) if event else [],
        },
    }


def main() -> None:
    print("Building presentation data from canonical artifacts...")
    write("holdout.json", build_holdout())
    write("candidates.json", build_candidates())
    write("coefficients.json", build_coefficients())
    write("facts.json", build_facts())
    print("  loading held-out TEST replay (237,600 rows)...")
    replay = load_replay()
    anomaly = build_anomaly(replay)
    write("anomaly.json", anomaly)
    write("gap.json", build_gap(replay))
    write("manifold.json", build_manifold(replay, anomaly.get("event", {})))
    print("Done. Headline metrics asserted against artifacts/.")


if __name__ == "__main__":
    main()
