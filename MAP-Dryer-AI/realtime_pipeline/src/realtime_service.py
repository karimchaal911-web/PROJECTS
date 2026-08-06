"""5-second incremental real-time service for the MAP dryer prototype.

Replays the 5-second dashboard CSV as if it were the plant historian:

* one new observation per cycle, resumed **incrementally** from the latest
  ``Timestamp`` already present in PostgreSQL (idempotent upserts — a
  retried row can never duplicate);
* the anomaly model and diagnosis run on every 5-second row from
  process-only instant features (no laboratory values needed);
* the quality model predicts Final Moisture on every row from a rolling
  process-window whose end is shifted back by the dryer residence time
  plus a configurable transport delay — exactly the alignment used in
  training (``multirate.alignment``);
* prediction error is validated only when a row carries a real laboratory
  result; between samples the dashboard shows the last validated error;
* all models are loaded once at startup; the database connection is
  reused, with bounded reconnect-and-retry on transient failures;
* every cycle logs its latency and warns when it exceeds the 5-second
  budget; a stale-data warning is raised when no new source row is
  available for ``STALE_AFTER_SECONDS``.

Timestamps are naive plant-local time end-to-end (CSV → Python →
PostgreSQL ``Date``/``Time`` columns → Power BI). No timezone conversion
is performed anywhere.

Configuration (``realtime_pipeline/.env``):

    SOURCE_CSV_5S           source CSV (default: the copied dashboard file)
    POLL_INTERVAL_SECONDS   cycle budget, default 5
    REPLAY_SPEED            pacing divisor: 1 = real time, 60 = 60x faster,
                            0 = as fast as possible (bulk catch-up)
    MAX_CYCLES              optional bounded run (0 = unlimited)
    EXIT_WHEN_EXHAUSTED     end instead of idling when the CSV is finished
    STALE_AFTER_SECONDS     freshness threshold, default 30
    TRANSPORT_DELAY_MINUTES extra lag after residence time, default 0
    MODELS_5S_DIR           artifact directory (default ../models/5s)
    REPLAY_FROM_START       ignore the database resume point and replay the
                            whole CSV; safe because every write is an
                            idempotent upsert keyed on (Date, Time)
"""

from __future__ import annotations

import json
import math
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import psycopg
from dotenv import load_dotenv

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PIPELINE_ROOT.parent
ENV_PATH = PIPELINE_ROOT / ".env"
load_dotenv(ENV_PATH)

for entry in (str(PROJECT_ROOT), str(PROJECT_ROOT / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from diagnosis_engine import diagnose_event, load_reference_profile  # noqa: E402
from multirate import (  # noqa: E402
    PROCESS_VARIABLES,
    QUALITY_VARIABLES,
    build_lab_table,
    build_process_table,
    compute_window_features,
    engineer_instant_features,
    load_raw_source,
)
from multirate.alignment import effective_window_end  # noqa: E402
from multirate.window_features import WINDOW_FEATURE_NAMES  # noqa: E402


STORE_MOISTURE_SQL = "SELECT public.upsert_moisture_output(%s, %s, %s, %s);"
STORE_ANOMALY_SQL = (
    "SELECT public.upsert_anomaly_output(%s, %s, %s, %s, %s);"
)
STORE_DIAGNOSIS_SQL = (
    "SELECT public.upsert_diagnosis_output(%s, %s, %s, %s, %s, %s, %s, %s);"
)
INSERT_PROCESS_SQL = (
    "SELECT public.insert_dryer_observation("
    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
)
UPDATE_METADATA_SQL = """
UPDATE public.dryer_model_outputs
SET "Anomaly Risk" = %s,
    "Model Version" = %s,
    "Feature Schema Version" = %s,
    "Inference Timestamp" = %s,
    "Inference Latency Ms" = %s
WHERE "Date" = %s AND "Time" = %s;
"""
DELETE_CONTRIBUTORS_SQL = """
DELETE FROM public.dryer_abnormal_variables
WHERE event_date = %s AND event_time = %s;
"""
INSERT_CONTRIBUTOR_SQL = """
INSERT INTO public.dryer_abnormal_variables (
    event_date, event_time, contribution_rank, feature_name,
    observed_value, reference_center, reference_scale,
    lower_normal_limit, upper_normal_limit, signed_deviation,
    deviation_percent, contribution_score, deviation_direction,
    is_direct_process_feature, variable_severity
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""
LATEST_TIMESTAMP_SQL = """
SELECT MAX("Date" + "Time") FROM public.dryer_map;
"""

DB_RETRY_ATTEMPTS = 5
DB_RETRY_BACKOFF_SECONDS = 2.0


@dataclass
class ServiceConfig:
    source_csv: Path
    poll_interval_seconds: float
    replay_speed: float
    max_cycles: int
    exit_when_exhausted: bool
    stale_after_seconds: float
    transport_delay_minutes: float
    models_dir: Path
    replay_from_start: bool


@dataclass
class Artifacts:
    moisture_pipeline: Any
    anomaly_model: Any
    anomaly_scaler: Any
    reference_profile: dict[str, Any]
    feature_schema: dict[str, Any]

    @property
    def model_version(self) -> str:
        return str(self.feature_schema["model_version"])

    @property
    def feature_schema_version(self) -> str:
        return str(self.feature_schema["feature_schema_version"])

    @property
    def window_minutes(self) -> float:
        return float(self.feature_schema["quality_window_minutes"])

    @property
    def risk_scale(self) -> float:
        return float(
            self.feature_schema["anomaly_risk_calibration"]["score_scale"]
        )


class GracefulExit(Exception):
    """Raised when a shutdown signal arrives between cycles."""


def _env_float(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = float(raw)
    if value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}.")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable {name!r} in {ENV_PATH}."
        )
    return value.strip()


def load_config() -> ServiceConfig:
    source_default = str(
        PROJECT_ROOT
        / "resources"
        / "prototype_data"
        / "MAP_Dryer_5s_Dashboard_Original_Columns.csv"
    )
    source_csv = Path(os.getenv("SOURCE_CSV_5S", source_default).strip())
    if not source_csv.is_absolute():
        source_csv = PIPELINE_ROOT / source_csv

    models_dir = Path(
        os.getenv("MODELS_5S_DIR", str(PROJECT_ROOT / "models" / "5s")).strip()
    )
    if not models_dir.is_absolute():
        models_dir = PIPELINE_ROOT / models_dir

    return ServiceConfig(
        source_csv=source_csv.resolve(),
        poll_interval_seconds=_env_float("POLL_INTERVAL_SECONDS", 5.0, 0.1),
        replay_speed=_env_float("REPLAY_SPEED", 1.0, 0.0),
        max_cycles=int(_env_float("MAX_CYCLES", 0.0)),
        exit_when_exhausted=_env_bool("EXIT_WHEN_EXHAUSTED", True),
        stale_after_seconds=_env_float("STALE_AFTER_SECONDS", 30.0, 1.0),
        transport_delay_minutes=_env_float("TRANSPORT_DELAY_MINUTES", 0.0),
        models_dir=models_dir.resolve(),
        replay_from_start=_env_bool("REPLAY_FROM_START", False),
    )


def load_artifacts(models_dir: Path) -> Artifacts:
    def _load(name: str) -> Any:
        path = models_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Model artifact was not found:\n{path}")
        return joblib.load(path)

    schema_path = models_dir / "feature_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(
            f"feature_schema.json was not found in {models_dir}."
        )
    with schema_path.open("r", encoding="utf-8") as file:
        feature_schema = json.load(file)

    if feature_schema["window_feature_names"] != WINDOW_FEATURE_NAMES:
        raise RuntimeError(
            "Saved window-feature schema does not match the current "
            "multirate.window_features implementation. Retrain with "
            "tools/train_5s_models.py before serving."
        )

    return Artifacts(
        moisture_pipeline=_load("quality_moisture_pipeline.joblib"),
        anomaly_model=_load("anomaly_model.joblib"),
        anomaly_scaler=_load("anomaly_scaler.joblib"),
        reference_profile=load_reference_profile(
            models_dir / "reference_profile.json"
        ),
        feature_schema=feature_schema,
    )


def build_connection() -> psycopg.Connection[Any]:
    # autocommit=True is required: without it the startup SELECT opens an
    # implicit transaction, connection.transaction() only nests savepoints
    # inside it, and nothing is ever committed. With autocommit=True each
    # connection.transaction() block is a real atomic BEGIN/COMMIT.
    return psycopg.connect(
        f"host={require_env('DB_HOST')} "
        f"port={require_env('DB_PORT')} "
        f"dbname={require_env('DB_NAME')} "
        f"user={require_env('DB_USER')} "
        f"password={require_env('DB_PASSWORD')}",
        autocommit=True,
    )


def nullable_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    converted = float(value)
    return converted if math.isfinite(converted) else None


def anomaly_risk_from_score(score: float, scale: float) -> float:
    """Calibrated 0-1 display risk; the SVM boundary (0) maps to 0.5."""

    return 1.0 / (1.0 + math.exp(min(max(score / scale, -60.0), 60.0)))


@dataclass
class QualityPrediction:
    predicted_moisture: float | None
    reason: str | None
    window_rows: int


def predict_moisture(
    buffer: pd.DataFrame,
    row_timestamp: pd.Timestamp,
    artifacts: Artifacts,
    transport_delay_minutes: float,
) -> QualityPrediction:
    """Window-feature moisture prediction with the training alignment.

    The window ends at ``now − residence_time − transport_delay`` so the
    prediction describes the product reaching the sampling point now.
    """

    residence = nullable_float(buffer["Residence Time"].iloc[-1])
    if residence is None:
        return QualityPrediction(None, "residence time missing", 0)

    window_minutes = artifacts.window_minutes
    window_end = effective_window_end(
        row_timestamp, residence, transport_delay_minutes
    )
    window_start = window_end - pd.Timedelta(minutes=window_minutes)

    in_window = buffer.loc[
        (buffer["Timestamp"] > window_start)
        & (buffer["Timestamp"] <= window_end)
    ]

    expected_rows = window_minutes * 60.0 / 5.0
    if len(in_window) < 0.8 * expected_rows:
        return QualityPrediction(
            None,
            f"insufficient process history ({len(in_window)}/"
            f"{int(expected_rows)} rows in the aligned window)",
            len(in_window),
        )

    features = compute_window_features(
        in_window[["Timestamp", *PROCESS_VARIABLES]]
    )
    frame = pd.DataFrame([features], columns=WINDOW_FEATURE_NAMES)
    predicted = float(artifacts.moisture_pipeline.predict(frame)[0])
    if not math.isfinite(predicted):
        return QualityPrediction(None, "non-finite prediction", len(in_window))
    return QualityPrediction(predicted, None, len(in_window))


@dataclass
class InferenceOutput:
    predicted_moisture: float | None
    prediction_note: str | None
    anomaly_score: float | None
    anomaly_risk: float | None
    anomaly_detected: bool | None
    severity: str
    likely_subsystem: str
    probable_diagnosis: str
    possible_causes: str
    diagnosis_confidence: float | None
    recommended_verification: str
    contributors: tuple[Any, ...]


def run_row_inference(
    source_row: pd.Series,
    buffer: pd.DataFrame,
    artifacts: Artifacts,
    config: ServiceConfig,
) -> InferenceOutput:
    row_timestamp = source_row["Timestamp"]

    try:
        instant = engineer_instant_features(
            source_row[PROCESS_VARIABLES].to_frame().T
        )
    except ValueError as error:
        # Reject the row explicitly instead of producing an invalid result.
        return InferenceOutput(
            predicted_moisture=None,
            prediction_note=str(error),
            anomaly_score=None,
            anomaly_risk=None,
            anomaly_detected=None,
            severity="DATA_QUALITY",
            likely_subsystem="Data acquisition and measurement",
            probable_diagnosis="Incomplete or invalid model input",
            possible_causes=str(error),
            diagnosis_confidence=None,
            recommended_verification=(
                "Verify the missing or invalid process measurement and "
                "restore a valid observation before interpreting outputs."
            ),
            contributors=(),
        )

    scaled = artifacts.anomaly_scaler.transform(instant)
    anomaly_score = float(artifacts.anomaly_model.decision_function(scaled)[0])
    anomaly_detected = int(artifacts.anomaly_model.predict(scaled)[0]) == -1
    risk = anomaly_risk_from_score(anomaly_score, artifacts.risk_scale)

    diagnosis = diagnose_event(
        model_features=instant,
        anomaly_detected=anomaly_detected,
        reference_profile=artifacts.reference_profile,
    )

    quality = predict_moisture(
        buffer, row_timestamp, artifacts, config.transport_delay_minutes
    )

    return InferenceOutput(
        predicted_moisture=quality.predicted_moisture,
        prediction_note=quality.reason,
        anomaly_score=anomaly_score,
        anomaly_risk=risk,
        anomaly_detected=anomaly_detected,
        severity=diagnosis.severity,
        likely_subsystem=diagnosis.likely_subsystem,
        probable_diagnosis=diagnosis.probable_diagnosis,
        possible_causes=diagnosis.possible_causes,
        diagnosis_confidence=diagnosis.diagnosis_confidence,
        recommended_verification=diagnosis.recommended_verification,
        contributors=(
            tuple(diagnosis.direct_contributors) if anomaly_detected else ()
        ),
    )


def persist_row(
    connection: psycopg.Connection[Any],
    source_row: pd.Series,
    inference: InferenceOutput,
    artifacts: Artifacts,
    latency_ms: float,
) -> None:
    timestamp: pd.Timestamp = source_row["Timestamp"]
    event_date = timestamp.date()
    event_time = timestamp.time().replace(microsecond=0)

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_PROCESS_SQL,
                (
                    event_date,
                    event_time,
                    *(
                        nullable_float(source_row[column])
                        for column in PROCESS_VARIABLES
                    ),
                    *(
                        nullable_float(source_row[column])
                        for column in QUALITY_VARIABLES
                    ),
                ),
            )
            cursor.fetchone()

            cursor.execute(
                STORE_MOISTURE_SQL,
                (
                    event_date,
                    event_time,
                    inference.predicted_moisture,
                    None,
                ),
            )
            cursor.fetchone()

            cursor.execute(
                STORE_ANOMALY_SQL,
                (
                    event_date,
                    event_time,
                    inference.anomaly_score,
                    inference.anomaly_detected,
                    inference.severity,
                ),
            )
            cursor.fetchone()

            cursor.execute(
                STORE_DIAGNOSIS_SQL,
                (
                    event_date,
                    event_time,
                    inference.severity,
                    inference.likely_subsystem,
                    inference.probable_diagnosis,
                    inference.possible_causes,
                    inference.diagnosis_confidence,
                    inference.recommended_verification,
                ),
            )
            cursor.fetchone()

            cursor.execute(
                UPDATE_METADATA_SQL,
                (
                    inference.anomaly_risk,
                    artifacts.model_version,
                    artifacts.feature_schema_version,
                    datetime.now().replace(microsecond=0),
                    latency_ms,
                    event_date,
                    event_time,
                ),
            )

            cursor.execute(
                DELETE_CONTRIBUTORS_SQL, (event_date, event_time)
            )
            for rank, contributor in enumerate(
                inference.contributors, start=1
            ):
                cursor.execute(
                    INSERT_CONTRIBUTOR_SQL,
                    (
                        event_date,
                        event_time,
                        rank,
                        contributor.feature_name,
                        contributor.observed_value,
                        contributor.reference_center,
                        contributor.reference_scale,
                        contributor.lower_normal_limit,
                        contributor.upper_normal_limit,
                        contributor.signed_deviation,
                        contributor.deviation_percent,
                        contributor.contribution_score,
                        contributor.direction,
                        contributor.is_direct_process_feature,
                        contributor.variable_severity,
                    ),
                )


def persist_with_retry(
    connection: psycopg.Connection[Any],
    source_row: pd.Series,
    inference: InferenceOutput,
    artifacts: Artifacts,
    latency_ms: float,
) -> psycopg.Connection[Any]:
    """Persist one row, reconnecting on transient database failures."""

    for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
        try:
            persist_row(
                connection, source_row, inference, artifacts, latency_ms
            )
            return connection
        except psycopg.OperationalError as error:
            print(
                f"  Database failure (attempt {attempt}/"
                f"{DB_RETRY_ATTEMPTS}): {error!r}",
                file=sys.stderr,
            )
            try:
                connection.close()
            except Exception:
                pass
            if attempt == DB_RETRY_ATTEMPTS:
                raise
            time.sleep(DB_RETRY_BACKOFF_SECONDS * attempt)
            connection = build_connection()
    return connection


def load_source(config: ServiceConfig) -> pd.DataFrame:
    raw = load_raw_source(config.source_csv)
    process, report = build_process_table(raw)
    lab = build_lab_table(raw)

    if report.gap_count:
        print(
            f"WARNING: source has {report.gap_count} gaps "
            f"({report.missing_interval_rows} missing 5-second rows)."
        )

    # Re-attach the sparse laboratory values to their process rows so the
    # database insert carries them only where a real analysis exists.
    merged = process.merge(
        lab.rename(columns={"Sample Timestamp": "Timestamp"}),
        on="Timestamp",
        how="left",
    )
    print(
        f"Source: {len(merged):,} process rows | "
        f"{int(merged['Final Moisture (%H2O)'].notna().sum())} lab samples | "
        f"{merged['Timestamp'].min()} .. {merged['Timestamp'].max()}"
    )
    return merged


def main() -> None:
    config = load_config()
    print("MAP DRYER 5-SECOND REAL-TIME SERVICE")
    print("=" * 72)
    print(f"Environment:      {ENV_PATH}")
    print(f"Source CSV:       {config.source_csv}")
    print(f"Models:           {config.models_dir}")
    print(f"Poll interval:    {config.poll_interval_seconds:g} s")
    print(
        "Replay speed:     "
        + (
            "max (no pacing)"
            if config.replay_speed == 0
            else f"{config.replay_speed:g}x"
        )
    )
    print(f"Transport delay:  {config.transport_delay_minutes:g} min")
    print("Timestamps:       naive plant-local time (documented, no TZ)")

    artifacts = load_artifacts(config.models_dir)
    print(
        f"Model version:    {artifacts.model_version} / "
        f"{artifacts.feature_schema_version}"
    )

    source = load_source(config)

    shutdown_requested = False

    def _request_shutdown(signum: int, frame: Any) -> None:
        nonlocal shutdown_requested
        shutdown_requested = True

    signal.signal(signal.SIGINT, _request_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _request_shutdown)

    connection = build_connection()

    with connection.cursor() as cursor:
        cursor.execute(LATEST_TIMESTAMP_SQL)
        latest_processed = cursor.fetchone()[0]

    if config.replay_from_start:
        print(
            "REPLAY_FROM_START=true: replaying the whole CSV; existing "
            "rows at the same timestamps are overwritten by upsert."
        )
        latest_processed = None

    if latest_processed is None:
        next_position = 0
    else:
        latest_processed = pd.Timestamp(latest_processed)
        next_position = int(
            source["Timestamp"].searchsorted(latest_processed, side="right")
        )
    print(
        f"Resuming after:   {latest_processed} "
        f"(source position {next_position:,}/{len(source):,})\n"
    )

    # Rolling history for window features: residence (~25 min) + window
    # (30 min) + margin. Seeded from already-processed source rows so a
    # restart keeps predicting immediately.
    buffer_minutes = (
        artifacts.window_minutes + config.transport_delay_minutes + 45.0
    )
    buffer_rows = int(buffer_minutes * 60 / 5)
    buffer = source.iloc[max(0, next_position - buffer_rows):next_position][
        ["Timestamp", *PROCESS_VARIABLES]
    ].copy()

    cycles = 0
    latencies: list[float] = []
    lab_rows_seen = 0
    anomaly_rows = 0
    last_new_row_wall_time = time.monotonic()
    stale_announced = False

    try:
        while not shutdown_requested:
            if config.max_cycles and cycles >= config.max_cycles:
                print(f"\nReached MAX_CYCLES={config.max_cycles}; stopping.")
                break

            if next_position >= len(source):
                if config.exit_when_exhausted:
                    print("\nSource CSV exhausted; exiting gracefully.")
                    break
                idle_seconds = time.monotonic() - last_new_row_wall_time
                if (
                    idle_seconds > config.stale_after_seconds
                    and not stale_announced
                ):
                    print(
                        f"STALE DATA: no new source row for "
                        f"{idle_seconds:.0f}s (threshold "
                        f"{config.stale_after_seconds:g}s)."
                    )
                    stale_announced = True
                time.sleep(config.poll_interval_seconds)
                continue

            cycle_started = time.monotonic()
            source_row = source.iloc[next_position]

            buffer = pd.concat(
                [
                    buffer,
                    source_row[["Timestamp", *PROCESS_VARIABLES]]
                    .to_frame()
                    .T,
                ],
                ignore_index=True,
            ).tail(buffer_rows)

            inference = run_row_inference(
                source_row, buffer, artifacts, config
            )

            latency_ms = (time.monotonic() - cycle_started) * 1000.0
            connection = persist_with_retry(
                connection, source_row, inference, artifacts, latency_ms
            )

            total_latency = time.monotonic() - cycle_started
            latencies.append(total_latency)
            cycles += 1
            next_position += 1
            last_new_row_wall_time = time.monotonic()
            stale_announced = False

            is_lab_row = pd.notna(source_row["Final Moisture (%H2O)"])
            if is_lab_row:
                lab_rows_seen += 1
            if inference.anomaly_detected:
                anomaly_rows += 1

            if (
                cycles <= 5
                or cycles % 500 == 0
                or is_lab_row
                or inference.anomaly_detected
            ):
                validated = ""
                if is_lab_row and inference.predicted_moisture is not None:
                    error = inference.predicted_moisture - float(
                        source_row["Final Moisture (%H2O)"]
                    )
                    validated = f" | LAB validated_err={error:+.4f}"
                predicted_display = (
                    f"{inference.predicted_moisture:.4f}"
                    if inference.predicted_moisture is not None
                    else f"NULL ({inference.prediction_note})"
                )
                print(
                    f"[{source_row['Timestamp']}] row "
                    f"{next_position:,}/{len(source):,} | "
                    f"pred={predicted_display} | "
                    f"risk={inference.anomaly_risk:.3f} | "
                    f"severity={inference.severity} | "
                    f"{total_latency * 1000:.0f} ms{validated}"
                    if inference.anomaly_risk is not None
                    else f"[{source_row['Timestamp']}] row "
                    f"{next_position:,} | DATA_QUALITY | "
                    f"{total_latency * 1000:.0f} ms"
                )

            if total_latency > config.poll_interval_seconds:
                print(
                    f"WARNING: cycle took {total_latency:.2f}s — longer "
                    f"than the {config.poll_interval_seconds:g}s budget."
                )

            if config.replay_speed > 0:
                target = config.poll_interval_seconds / config.replay_speed
                time.sleep(max(0.0, target - total_latency))

    finally:
        try:
            connection.close()
        except Exception:
            pass

    if latencies:
        print("\nRUN SUMMARY")
        print(f"  Cycles processed:   {cycles:,}")
        print(f"  Laboratory rows:    {lab_rows_seen}")
        print(f"  Anomalous rows:     {anomaly_rows}")
        print(
            f"  Latency avg/max:    {sum(latencies) / len(latencies) * 1000:.0f}"
            f" / {max(latencies) * 1000:.0f} ms"
        )
    if shutdown_requested:
        print("Service stopped by shutdown signal.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nREAL-TIME SERVICE FAILED", file=sys.stderr)
        print(repr(error), file=sys.stderr)
        sys.exit(1)
