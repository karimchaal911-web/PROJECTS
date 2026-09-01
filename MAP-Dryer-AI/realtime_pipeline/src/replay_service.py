from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import psycopg
from dotenv import load_dotenv

from anomaly_features import engineer_anomaly_features
from diagnosis_engine import diagnose_event, load_reference_profile


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PIPELINE_ROOT / ".env"
load_dotenv(ENV_PATH)


SOURCE_COLUMNS = [
    "Date",
    "Time",
    "Dryer Air Temperature",
    "Cooler Air Temperature",
    "Air Flow Rate",
    "Wet Product Feed Rate",
    "Product Inlet Temperature",
    "Residence Time",
    "Vacuum",
    "Steam Pressure",
    "Fan Speed",
    "Product Density",
    "Final Product Temp",
    "Final Moisture (%H2O)",
]

MODEL_RAW_COLUMNS = {
    "dryer_air_temperature": "Dryer Air Temperature",
    "cooler_air_temperature": "Cooler Air Temperature",
    "air_flow_rate": "Air Flow Rate",
    "wet_product_feed_rate": "Wet Product Feed Rate",
    "product_inlet_temperature": "Product Inlet Temperature",
    "residence_time": "Residence Time",
    "vacuum": "Vacuum",
    "steam_pressure": "Steam Pressure",
    "fan_speed": "Fan Speed",
    "product_density": "Product Density",
    "final_product_temp": "Final Product Temp",
}


INSERT_PROCESS_SQL = """
SELECT public.insert_dryer_observation(
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s
);
"""

STORE_MOISTURE_SQL = """
SELECT public.upsert_moisture_output(
    %s, %s, %s, %s
);
"""

STORE_ANOMALY_SQL = """
SELECT public.upsert_anomaly_output(
    %s, %s, %s, %s, %s
);
"""

STORE_DIAGNOSIS_SQL = """
SELECT public.upsert_diagnosis_output(
    %s, %s, %s, %s, %s, %s, %s, %s
);
"""

DELETE_CONTRIBUTORS_SQL = """
DELETE FROM public.dryer_abnormal_variables
WHERE event_date = %s
  AND event_time = %s;
"""

INSERT_CONTRIBUTOR_SQL = """
INSERT INTO public.dryer_abnormal_variables (
    event_date,
    event_time,
    contribution_rank,
    feature_name,
    observed_value,
    reference_center,
    reference_scale,
    lower_normal_limit,
    upper_normal_limit,
    signed_deviation,
    deviation_percent,
    contribution_score,
    deviation_direction,
    is_direct_process_feature,
    variable_severity
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s
);
"""

LATEST_TIMESTAMP_SQL = """
SELECT
    d."Date",
    d."Time"
FROM public.dryer_map AS d
ORDER BY
    d."Date" DESC,
    d."Time" DESC
LIMIT 1;
"""

SERVICE_METRICS_SQL = """
SELECT
    (SELECT COUNT(*) FROM public.dryer_map) AS process_rows,
    (SELECT COUNT(*) FROM public.dryer_model_outputs) AS output_rows,
    (
        SELECT COUNT(*)
        FROM public.dryer_map AS d
        LEFT JOIN public.dryer_model_outputs AS m
            ON d."Date" = m."Date"
           AND d."Time" = m."Time"
        WHERE m."Date" IS NULL
    ) AS missing_output_rows,
    (
        SELECT COUNT(*)
        FROM public.dryer_model_outputs
        WHERE "Severity" = 'DATA_QUALITY'
    ) AS data_quality_rows;
"""


@dataclass(frozen=True)
class InferenceResult:
    predicted_moisture: float | None
    prediction_confidence: float | None
    anomaly_score: float | None
    anomaly_detected: bool | None
    severity: str
    likely_subsystem: str
    probable_diagnosis: str
    possible_causes: str
    diagnosis_confidence: float | None
    recommended_verification: str
    contributors: tuple[Any, ...]
    warning: str | None


@dataclass(frozen=True)
class CycleResult:
    source_index: int
    event_timestamp: datetime
    inference: InferenceResult
    process_count: int
    output_count: int
    missing_count: int
    data_quality_count: int


def require_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable {name!r} in {ENV_PATH}."
        )

    return value.strip()


def optional_positive_float_env(
    name: str,
    default: float,
) -> float:
    raw_value = os.getenv(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = float(raw_value)
    except ValueError as error:
        raise RuntimeError(
            f"Environment variable {name!r} must be numeric."
        ) from error

    if value <= 0:
        raise RuntimeError(
            f"Environment variable {name!r} must be greater than zero."
        )

    return value


def resolve_configured_path(
    env_name: str,
    default_relative_path: str | None = None,
) -> Path:
    configured_value = os.getenv(env_name)

    if configured_value is None or not configured_value.strip():
        if default_relative_path is None:
            raise RuntimeError(
                f"Missing environment variable {env_name!r}."
            )
        configured_value = default_relative_path

    path = Path(configured_value.strip())

    if not path.is_absolute():
        path = PIPELINE_ROOT / path

    return path.resolve()


def build_connection_string() -> str:
    return (
        f"host={require_env('DB_HOST')} "
        f"port={require_env('DB_PORT')} "
        f"dbname={require_env('DB_NAME')} "
        f"user={require_env('DB_USER')} "
        f"password={require_env('DB_PASSWORD')}"
    )


def load_artifact(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Model artifact was not found:\n{path}")

    return joblib.load(path)


def normalize_source_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]

    duplicate_columns = normalized.columns[
        normalized.columns.duplicated()
    ].tolist()

    if duplicate_columns:
        raise ValueError(
            "The source file contains duplicate column names after "
            f"whitespace normalization: {duplicate_columns}"
        )

    missing_columns = [
        column
        for column in SOURCE_COLUMNS
        if column not in normalized.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Source file is missing required columns: {missing_columns}"
        )

    return normalized.loc[:, SOURCE_COLUMNS].copy()


def load_source_data(source_path: Path) -> pd.DataFrame:
    if not source_path.exists():
        raise FileNotFoundError(f"Source CSV was not found:\n{source_path}")

    dataframe = pd.read_csv(source_path)
    dataframe = normalize_source_columns(dataframe)

    source_timestamp = pd.to_datetime(
        dataframe["Date"].astype(str).str.strip()
        + " "
        + dataframe["Time"].astype(str).str.strip(),
        format="%d/%m/%Y %H:%M",
        errors="coerce",
    )

    invalid_timestamp_count = int(source_timestamp.isna().sum())

    if invalid_timestamp_count:
        raise ValueError(
            "Source CSV contains "
            f"{invalid_timestamp_count} invalid Date/Time combinations."
        )

    numeric_columns = [
        column
        for column in SOURCE_COLUMNS
        if column not in {"Date", "Time"}
    ]

    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    dataframe["_source_timestamp"] = source_timestamp
    dataframe.sort_values("_source_timestamp", inplace=True)
    dataframe.reset_index(drop=True, inplace=True)

    if dataframe.empty:
        raise ValueError("Source CSV contains no observations.")

    return dataframe


def nullable_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None

    converted = float(value)

    if not math.isfinite(converted):
        return None

    return converted


def build_raw_model_features(
    source_row: pd.Series,
) -> pd.DataFrame:
    values: dict[str, float] = {}
    missing_features: list[str] = []

    for model_name, source_name in MODEL_RAW_COLUMNS.items():
        value = nullable_float(source_row[source_name])

        if value is None:
            missing_features.append(model_name)
        else:
            values[model_name] = value

    if missing_features:
        raise ValueError(
            "Missing or non-finite model inputs: "
            + ", ".join(missing_features)
        )

    if values["wet_product_feed_rate"] == 0:
        raise ValueError(
            "wet_product_feed_rate is zero; air_per_feed cannot be calculated."
        )

    return pd.DataFrame([values])


def build_model_features(
    source_row: pd.Series,
    reference_profile: dict[str, Any],
) -> pd.DataFrame:
    raw_features = build_raw_model_features(source_row)
    model_features = engineer_anomaly_features(raw_features)

    expected_features = list(reference_profile["feature_names"])
    missing_features = [
        feature
        for feature in expected_features
        if feature not in model_features.columns
    ]

    if missing_features:
        raise ValueError(
            "Engineered model data is missing features: "
            f"{missing_features}"
        )

    model_features = model_features.loc[:, expected_features].copy()

    numeric_values = model_features.to_numpy(dtype=float)

    if not np.isfinite(numeric_values).all():
        raise ValueError(
            "Engineered model features contain NaN or infinite values."
        )

    return model_features


def scalar_from_array(
    value: Any,
    label: str,
) -> float:
    array = np.asarray(value).reshape(-1)

    if array.size != 1:
        raise RuntimeError(
            f"{label} returned {array.size} values; exactly one was expected."
        )

    result = float(array[0])

    if not math.isfinite(result):
        raise RuntimeError(f"{label} returned a non-finite value.")

    return result


def build_data_quality_result(error: ValueError) -> InferenceResult:
    message = str(error)

    return InferenceResult(
        predicted_moisture=None,
        prediction_confidence=None,
        anomaly_score=None,
        anomaly_detected=None,
        severity="DATA_QUALITY",
        likely_subsystem="Data acquisition and measurement",
        probable_diagnosis="Incomplete or invalid model input",
        possible_causes=message,
        diagnosis_confidence=None,
        recommended_verification=(
            "Verify the missing or invalid process measurement, confirm the "
            "instrument status, and restore a valid synchronized observation "
            "before interpreting model outputs."
        ),
        contributors=(),
        warning=message,
    )


def run_inference(
    source_row: pd.Series,
    moisture_pipeline: Any,
    anomaly_model: Any,
    anomaly_scaler: Any,
    reference_profile: dict[str, Any],
) -> InferenceResult:
    try:
        model_features = build_model_features(
            source_row=source_row,
            reference_profile=reference_profile,
        )
    except ValueError as error:
        return build_data_quality_result(error)

    predicted_moisture = scalar_from_array(
        moisture_pipeline.predict(model_features),
        "Moisture pipeline",
    )

    scaled_features = anomaly_scaler.transform(model_features)

    anomaly_prediction = int(
        round(
            scalar_from_array(
                anomaly_model.predict(scaled_features),
                "Anomaly model prediction",
            )
        )
    )

    if anomaly_prediction not in {-1, 1}:
        raise RuntimeError(
            "One-Class SVM prediction must be -1 or 1, "
            f"but received {anomaly_prediction}."
        )

    anomaly_score = scalar_from_array(
        anomaly_model.decision_function(scaled_features),
        "Anomaly decision function",
    )

    anomaly_detected = anomaly_prediction == -1

    diagnosis = diagnose_event(
        model_features=model_features,
        anomaly_detected=anomaly_detected,
        reference_profile=reference_profile,
    )

    contributors = (
        diagnosis.direct_contributors
        if anomaly_detected
        else ()
    )

    return InferenceResult(
        predicted_moisture=predicted_moisture,
        prediction_confidence=None,
        anomaly_score=anomaly_score,
        anomaly_detected=anomaly_detected,
        severity=diagnosis.severity,
        likely_subsystem=diagnosis.likely_subsystem,
        probable_diagnosis=diagnosis.probable_diagnosis,
        possible_causes=diagnosis.possible_causes,
        diagnosis_confidence=diagnosis.diagnosis_confidence,
        recommended_verification=diagnosis.recommended_verification,
        contributors=tuple(contributors),
        warning=None,
    )


def process_parameters(
    source_row: pd.Series,
    event_timestamp: datetime,
) -> tuple[Any, ...]:
    event_time = event_timestamp.time().replace(microsecond=0)

    return (
        event_timestamp.date(),
        event_time,
        nullable_float(source_row["Dryer Air Temperature"]),
        nullable_float(source_row["Cooler Air Temperature"]),
        nullable_float(source_row["Air Flow Rate"]),
        nullable_float(source_row["Wet Product Feed Rate"]),
        nullable_float(source_row["Product Inlet Temperature"]),
        nullable_float(source_row["Residence Time"]),
        nullable_float(source_row["Vacuum"]),
        nullable_float(source_row["Steam Pressure"]),
        nullable_float(source_row["Fan Speed"]),
        nullable_float(source_row["Product Density"]),
        nullable_float(source_row["Final Product Temp"]),
        nullable_float(source_row["Final Moisture (%H2O)"]),
    )


def persist_complete_cycle(
    connection: psycopg.Connection[Any],
    source_row: pd.Series,
    event_timestamp: datetime,
    inference: InferenceResult,
) -> None:
    event_date = event_timestamp.date()
    event_time = event_timestamp.time().replace(microsecond=0)

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_PROCESS_SQL,
                process_parameters(source_row, event_timestamp),
            )
            cursor.fetchone()

            cursor.execute(
                STORE_MOISTURE_SQL,
                (
                    event_date,
                    event_time,
                    inference.predicted_moisture,
                    inference.prediction_confidence,
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
                DELETE_CONTRIBUTORS_SQL,
                (event_date, event_time),
            )

            for rank, contributor in enumerate(
                inference.contributors,
                start=1,
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


def get_service_metrics(
    connection: psycopg.Connection[Any],
) -> tuple[int, int, int, int]:
    with connection.cursor() as cursor:
        cursor.execute(SERVICE_METRICS_SQL)
        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Could not read service metrics from PostgreSQL.")

    return tuple(int(value) for value in row)  # type: ignore[return-value]


def get_initial_replay_state(
    connection: psycopg.Connection[Any],
    source_row_count: int,
) -> tuple[int, datetime]:
    with connection.cursor() as cursor:
        cursor.execute(LATEST_TIMESTAMP_SQL)
        latest_row = cursor.fetchone()

    process_count, _, _, _ = get_service_metrics(connection)
    source_index = process_count % source_row_count

    if latest_row is None:
        next_timestamp = datetime.now().replace(
            second=0,
            microsecond=0,
        )
    else:
        latest_timestamp = datetime.combine(
            latest_row[0],
            latest_row[1],
        )
        next_timestamp = latest_timestamp + timedelta(minutes=1)

    return source_index, next_timestamp


def execute_cycle(
    connection: psycopg.Connection[Any],
    dataframe: pd.DataFrame,
    source_index: int,
    event_timestamp: datetime,
    moisture_pipeline: Any,
    anomaly_model: Any,
    anomaly_scaler: Any,
    reference_profile: dict[str, Any],
) -> CycleResult:
    source_row = dataframe.iloc[source_index]

    inference = run_inference(
        source_row=source_row,
        moisture_pipeline=moisture_pipeline,
        anomaly_model=anomaly_model,
        anomaly_scaler=anomaly_scaler,
        reference_profile=reference_profile,
    )

    persist_complete_cycle(
        connection=connection,
        source_row=source_row,
        event_timestamp=event_timestamp,
        inference=inference,
    )

    (
        process_count,
        output_count,
        missing_count,
        data_quality_count,
    ) = get_service_metrics(connection)

    return CycleResult(
        source_index=source_index,
        event_timestamp=event_timestamp,
        inference=inference,
        process_count=process_count,
        output_count=output_count,
        missing_count=missing_count,
        data_quality_count=data_quality_count,
    )


def format_optional_float(
    value: float | None,
    digits: int = 6,
) -> str:
    if value is None:
        return "NULL"

    return f"{value:.{digits}f}"


def print_cycle_result(
    result: CycleResult,
    source_row_count: int,
) -> None:
    detected_display = (
        "NULL"
        if result.inference.anomaly_detected is None
        else str(result.inference.anomaly_detected)
    )

    print(
        f"[{result.event_timestamp:%Y-%m-%d %H:%M:%S}] "
        f"CSV row {result.source_index + 1:,}/{source_row_count:,} | "
        f"moisture={format_optional_float(result.inference.predicted_moisture, 8)} | "
        f"score={format_optional_float(result.inference.anomaly_score, 8)} | "
        f"anomaly={detected_display} | "
        f"severity={result.inference.severity} | "
        f"contributors={len(result.inference.contributors)} | "
        f"process={result.process_count} | "
        f"outputs={result.output_count} | "
        f"missing={result.missing_count} | "
        f"data_quality={result.data_quality_count}"
    )

    if result.inference.warning:
        print(f"  Warning: {result.inference.warning}")


def run_replay_service() -> None:
    source_path = resolve_configured_path(
        "SOURCE_CSV",
        "data/dryerMAP_dashboard_1min_original_features_only.csv",
    )
    moisture_model_path = resolve_configured_path("MOISTURE_MODEL")
    anomaly_model_path = resolve_configured_path("ANOMALY_MODEL")
    anomaly_scaler_path = resolve_configured_path("ANOMALY_SCALER")
    reference_profile_path = resolve_configured_path("REFERENCE_PROFILE")
    replay_interval_seconds = optional_positive_float_env(
        "REPLAY_INTERVAL_SECONDS",
        60.0,
    )

    dataframe = load_source_data(source_path)
    moisture_pipeline = load_artifact(moisture_model_path)
    anomaly_model = load_artifact(anomaly_model_path)
    anomaly_scaler = load_artifact(anomaly_scaler_path)
    reference_profile = load_reference_profile(reference_profile_path)

    print("MAP DRYER REAL-TIME REPLAY SERVICE")
    print("=" * 72)
    print(f"Environment:       {ENV_PATH}")
    print(f"Source CSV:        {source_path}")
    print(f"Source rows:       {len(dataframe):,}")
    print(f"Moisture model:    {moisture_model_path}")
    print(f"Anomaly model:     {anomaly_model_path}")
    print(f"Anomaly scaler:    {anomaly_scaler_path}")
    print(f"Reference profile: {reference_profile_path}")
    print(f"Replay interval:   {replay_interval_seconds:g} seconds")
    print("Press Ctrl+C to stop.\n")

    connection_string = build_connection_string()

    with psycopg.connect(
        connection_string,
        autocommit=True,
    ) as connection:
        source_index, next_event_timestamp = get_initial_replay_state(
            connection=connection,
            source_row_count=len(dataframe),
        )

        while True:
            cycle_started_at = time.monotonic()

            try:
                result = execute_cycle(
                    connection=connection,
                    dataframe=dataframe,
                    source_index=source_index,
                    event_timestamp=next_event_timestamp,
                    moisture_pipeline=moisture_pipeline,
                    anomaly_model=anomaly_model,
                    anomaly_scaler=anomaly_scaler,
                    reference_profile=reference_profile,
                )

                print_cycle_result(
                    result=result,
                    source_row_count=len(dataframe),
                )

                source_index = (source_index + 1) % len(dataframe)
                next_event_timestamp += timedelta(minutes=1)

            except KeyboardInterrupt:
                raise

            except Exception as error:
                print(
                    "\nREPLAY CYCLE FAILED",
                    file=sys.stderr,
                )
                print(
                    f"Timestamp: {next_event_timestamp:%Y-%m-%d %H:%M:%S}",
                    file=sys.stderr,
                )
                print(repr(error), file=sys.stderr)
                print(
                    "The transaction was rolled back. The same source row "
                    "will be retried after the interval.\n",
                    file=sys.stderr,
                )

            elapsed_seconds = time.monotonic() - cycle_started_at
            sleep_seconds = max(
                0.0,
                replay_interval_seconds - elapsed_seconds,
            )
            time.sleep(sleep_seconds)


def main() -> None:
    if os.getenv("ENABLE_LEGACY_1MIN_REPLAY", "false").strip().lower() != "true":
        print(
            "replay_service.py is the superseded one-minute writer. Its rows "
            "are incompatible with the five-second dashboard schema and are "
            "filtered out of every Power BI view. The supported service "
            "is realtime_pipeline/src/realtime_service.py, started by "
            "RUN_FINAL_DEMO.ps1. "
            "Set ENABLE_LEGACY_1MIN_REPLAY=true to run it anyway.",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        run_replay_service()

    except KeyboardInterrupt:
        print("\nReplay service stopped by user.")

    except Exception as error:
        print("\nREPLAY SERVICE FAILED", file=sys.stderr)
        print(repr(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()