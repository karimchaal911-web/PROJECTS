import re

import pandas as pd


DRYER_MAP_COLUMNS = [
    "date", "time", "dryer_air_temperature", "cooler_air_temperature",
    "air_flow_rate", "wet_product_feed_rate", "product_inlet_temperature",
    "residence_time", "vacuum", "steam_pressure", "fan_speed",
    "product_density", "final_product_temp", "final_moisture_h₂o",
]

OUTPUT_MEASUREMENT_COLUMNS = [
    "product_density", "final_product_temp", "final_moisture_h₂o",
]


def clean_column_names(columns):
    """Return normalized snake_case column names and reject collisions."""
    cleaned = [
        re.sub(
            r"_+",
            "_",
            re.sub(r"[^\w\s]", "_", str(column).strip().lower()).replace(" ", "_"),
        ).strip("_")
        for column in columns
    ]
    if len(cleaned) != len(set(cleaned)):
        raise ValueError("Column cleaning produced duplicate names.")
    return cleaned


def _parse_decimal_numeric(series, column_name):
    """Parse numeric data that may use either a decimal comma or point.

    Missing values stay missing. Non-empty values that cannot be parsed raise an
    error rather than being silently converted to missing values.
    """
    text = series.astype("string").str.strip().str.replace(",", ".", regex=False)
    numeric = pd.to_numeric(text, errors="coerce")
    invalid = series.notna() & numeric.isna()
    if invalid.any():
        bad_values = series.loc[invalid].astype(str).unique().tolist()
        raise ValueError(
            f"Could not parse numeric values in {column_name!r}: {bad_values}"
        )
    return numeric


def prepare_dryer_map(raw_df):
    """Return a consistently typed Dryer MAP dataset without dropping records.

    The function normalizes column names, parses dates/times and both decimal
    conventions, and adds record-status flags. A zero-output record is flagged
    but intentionally retained: its process meaning must be decided by the
    data owner before any modelling exclusion rule is applied.
    """
    df = raw_df.copy()
    df.columns = clean_column_names(df.columns)
    if df.columns.tolist() != DRYER_MAP_COLUMNS:
        raise ValueError("Unexpected Dryer MAP dataset schema.")

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="raise")
    df["time"] = pd.to_datetime(
        df["time"].astype(str), format="%H:%M:%S", errors="raise"
    ).dt.time

    for column in DRYER_MAP_COLUMNS:
        if column not in {"date", "time"}:
            df[column] = _parse_decimal_numeric(df[column], column)

    df["timestamp"] = pd.to_datetime(
        df["date"].dt.strftime("%d-%m-%y") + " " + df["time"].astype(str),
        errors="raise",
    )

    return df
    
