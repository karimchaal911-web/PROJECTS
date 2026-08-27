"""Extend the Power BI semantic model for the 5-second multi-rate upgrade.

Idempotently patches the TMDL definition:

* appends the new physical view columns (Anomaly Risk, model/version
  metadata, Latest Lab context, validated-error fields) to
  ``vw_dryer_dashboard_powerbi.tmdl``;
* appends the "5S EXTENSION" measure block: lab context, validation,
  freshness (LIVE/DELAYED/STALE), risk intensity, centralized heatmap
  color measures, per-variable status/color/delta measures for the five
  critical process-variable cards, and trend series;
* writes the two new DirectQuery tables ``vw_dryer_lab_samples`` and
  ``vw_dryer_anomaly_events`` (with selected-event and row-color
  measures);
* adds the events → contributors relationship.

Per-variable normal bands are model constants taken from
``models/5s/reference_profile.json`` (training-period quantiles), and the
moisture target band is the rounded p10–p90 of the training laboratory
results — documented constants, not fabricated data.

Everything between the sentinel markers is replaced on rerun.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_DIR = (
    PROJECT_ROOT
    / "POWERBI DASHBOARD"
    / "MAP Dryer AI Dashboard.SemanticModel"
    / "definition"
)
TABLES_DIR = SEMANTIC_DIR / "tables"
DASHBOARD_TMDL = TABLES_DIR / "vw_dryer_dashboard_powerbi.tmdl"
RELATIONSHIPS_TMDL = SEMANTIC_DIR / "relationships.tmdl"
REFERENCE_PROFILE = PROJECT_ROOT / "models" / "5s" / "reference_profile.json"

BEGIN_MARK = "\t/// ===== BEGIN 5S EXTENSION (generated) ====="
END_MARK = "\t/// ===== END 5S EXTENSION (generated) ====="

# Reference palette (mirrors the dashboard template).
GREEN = "#087C5B"
GREEN_SURFACE = "#E7F4EF"
AMBER = "#B26A00"          # readable amber text
AMBER_SURFACE = "#FFF0D5"
AMBER_SURFACE_2 = "#FDE7C8"
RED = "#C83F45"
RED_TEXT = "#C83F45"
RED_SURFACE = "#FBE2E3"
GRAY_SURFACE = "#E5E9E7"
TEXT = "#17231F"
TEXT_2 = "#66756F"
WHITE = "#FFFFFF"

TARGET_BAND_LOW = 0.07018   # rounded p10 of canonical laboratory moisture
TARGET_BAND_HIGH = 0.08074  # rounded p90 of canonical laboratory moisture
MOISTURE_WARNING_LOW = 0.06904   # rounded p05
MOISTURE_WARNING_HIGH = 0.08188  # rounded p95

DASH = "vw_dryer_dashboard_powerbi"
LAB = "vw_dryer_lab_samples"
EVENTS = "vw_dryer_anomaly_events"


def tag(*parts: str) -> str:
    """Deterministic lineage tag so reruns do not churn the files."""

    return str(
        uuid.uuid5(uuid.NAMESPACE_URL, "map-dryer-5s/" + "/".join(parts))
    )


def measure(
    name: str,
    dax: str,
    folder: str,
    fmt: str | None = None,
    owner: str = DASH,
) -> str:
    lines = dax.strip().splitlines()
    if len(lines) == 1:
        head = f"\tmeasure '{name}' = {lines[0].strip()}"
        body = ""
    else:
        head = f"\tmeasure '{name}' ="
        body = "\n" + "\n".join(f"\t\t\t{line}" for line in lines)
    out = head + body + "\n"
    if fmt:
        out += f"\t\tformatString: {fmt}\n"
    out += f"\t\tdisplayFolder: {folder}\n"
    out += f"\t\tlineageTag: {tag(owner, 'measure', name)}\n"
    return out


def column(
    name: str,
    source: str,
    data_type: str,
    owner: str,
    fmt: str | None = None,
    hidden: bool = False,
) -> str:
    quoted = f"'{name}'" if any(c in name for c in " ()%") else name
    out = f"\tcolumn {quoted}\n"
    out += f"\t\tdataType: {data_type}\n"
    if fmt:
        out += f"\t\tformatString: {fmt}\n"
    if hidden:
        out += "\t\tisHidden\n"
    out += f"\t\tlineageTag: {tag(owner, 'column', name)}\n"
    out += "\t\tsummarizeBy: none\n"
    out += f"\t\tsourceColumn: {source}\n"
    return out


# --------------------------------------------------------------------------
# Dashboard-table extension: columns
# --------------------------------------------------------------------------

NEW_DASHBOARD_COLUMNS = [
    column("Anomaly Risk", "Anomaly Risk", "double", DASH, "0.000"),
    column("Model Version", "Model Version", "string", DASH),
    column(
        "Feature Schema Version", "Feature Schema Version", "string", DASH
    ),
    column(
        "Inference Timestamp",
        "Inference Timestamp",
        "dateTime",
        DASH,
        "yyyy-mm-dd hh:nn:ss",
    ),
    column(
        "Inference Latency Ms", "Inference Latency Ms", "double", DASH, "0"
    ),
    column(
        "Latest Lab Sample Timestamp",
        "Latest Lab Sample Timestamp",
        "dateTime",
        DASH,
        "yyyy-mm-dd hh:nn:ss",
    ),
    column(
        "Latest Lab Product Density",
        "Latest Lab Product Density",
        "double",
        DASH,
        "0.0000",
    ),
    column(
        "Latest Lab Final Product Temp",
        "Latest Lab Final Product Temp",
        "double",
        DASH,
        "0.0",
    ),
    column(
        "Latest Lab Final Moisture",
        "Latest Lab Final Moisture",
        "double",
        DASH,
        "0.0000",
    ),
    column("Lab Result Age Min", "Lab Result Age Min", "double", DASH, "0.0"),
    column("Lab Sample Available", "Lab Sample Available", "boolean", DASH),
    column("Is Lab Sample", "Is Lab Sample", "boolean", DASH),
    column(
        "Validated Moisture Error",
        "Validated Moisture Error",
        "double",
        DASH,
        "+0.0000;-0.0000;0.0000",
    ),
    column(
        "Validated Absolute Error",
        "Validated Absolute Error",
        "double",
        DASH,
        "0.0000",
    ),
]

# --------------------------------------------------------------------------
# Dashboard-table extension: measures
# --------------------------------------------------------------------------

F_LAB = "08 Lab Context (5s)"
F_VAL = "09 Validation (5s)"
F_STATE = "10 Risk & Status (5s)"
F_COLOR = "11 Heatmap Colors (5s)"
F_TREND = "12 Trend Series (5s)"
F_VARS = "13 Critical Variables (5s)"

M = []

# --- 08 Lab context -------------------------------------------------------
M.append(measure(
    "Lab Last Sample Timestamp",
    f"CALCULATE ( MAX ( '{LAB}'[Sample Timestamp] ), "
    f"REMOVEFILTERS ( '{LAB}' ) )",
    F_LAB, "yyyy-mm-dd hh:nn:ss",
))
M.append(measure(
    "Lab Last Moisture",
    f"""VAR t = [Lab Last Sample Timestamp]
RETURN
    CALCULATE (
        AVERAGE ( '{LAB}'[Laboratory Moisture] ),
        REMOVEFILTERS ( '{LAB}' ),
        '{LAB}'[Sample Timestamp] = t
    )""",
    F_LAB, "0.000000",
))
M.append(measure(
    "Lab Last Moisture Display",
    'IF ( ISBLANK ( [Lab Last Moisture] ), "—", '
    'FORMAT ( [Lab Last Moisture], "0.000000" ) & " %" )',
    F_LAB,
))
M.append(measure(
    "Lab Result Age Minutes",
    """IF (
    ISBLANK ( [Lab Last Sample Timestamp] ) || ISBLANK ( [Latest Timestamp] ),
    BLANK (),
    DATEDIFF ( [Lab Last Sample Timestamp], [Latest Timestamp], SECOND ) / 60.0
)""",
    F_LAB, "0.0",
))
M.append(measure(
    "Lab Age Display",
    'IF ( ISBLANK ( [Lab Result Age Minutes] ), "no laboratory result", '
    '"Lab age " & FORMAT ( [Lab Result Age Minutes], "0" ) & " min" )',
    F_LAB,
))
M.append(measure(
    "Lab Sample Time Display",
    'IF ( ISBLANK ( [Lab Last Sample Timestamp] ), "—", '
    '"Sampled " & FORMAT ( [Lab Last Sample Timestamp], "hh:nn" ) & " · " '
    '& FORMAT ( [Lab Result Age Minutes], "0" ) & " min ago" )',
    F_LAB,
))

# --- 09 Validation --------------------------------------------------------
M.append(measure(
    "Validated Error Timestamp",
    f"""CALCULATE (
    MAX ( '{LAB}'[Sample Timestamp] ),
    REMOVEFILTERS ( '{LAB}' ),
    NOT ISBLANK ( '{LAB}'[Validated Absolute Error] )
)""",
    F_VAL, "yyyy-mm-dd hh:nn:ss",
))
M.append(measure(
    "Validated Error Latest",
    f"""VAR t = [Validated Error Timestamp]
RETURN
    IF (
        ISBLANK ( t ),
        BLANK (),
        CALCULATE (
            AVERAGE ( '{LAB}'[Validated Absolute Error] ),
            REMOVEFILTERS ( '{LAB}' ),
            '{LAB}'[Sample Timestamp] = t
        )
    )""",
    F_VAL, "0.000000",
))
M.append(measure(
    "Validated Error Display",
    'IF ( ISBLANK ( [Validated Error Latest] ), '
    '"Awaiting next laboratory result", '
    'FORMAT ( [Validated Error Latest], "0.000000" ) & " %" )',
    F_VAL,
))
M.append(measure(
    "Validated Error Caption",
    'IF ( ISBLANK ( [Validated Error Latest] ), "No validated comparison yet", '
    '"Validated at " & FORMAT ( [Validated Error Timestamp], "hh:nn" ) )',
    F_VAL,
))

# --- 10 Risk & status -----------------------------------------------------
M.append(measure(
    "Latest Anomaly Risk",
    f"""VAR t = [Latest Timestamp]
RETURN
    CALCULATE (
        AVERAGE ( '{DASH}'[Anomaly Risk] ),
        '{DASH}'[Timestamp] = t
    )""",
    F_STATE, "0.000",
))
M.append(measure(
    "Risk Intensity", "COALESCE ( [Latest Anomaly Risk], 0 )",
    F_STATE, "0.000",
))
M.append(measure(
    "Latest Anomaly Risk Display",
    'FORMAT ( [Risk Intensity], "0.00" )', F_STATE,
))
M.append(measure(
    "Predicted Now Timestamp",
    f"""CALCULATE (
    MAX ( '{DASH}'[Timestamp] ),
    NOT ISBLANK ( '{DASH}'[Predicted Moisture] )
)""",
    F_STATE, "yyyy-mm-dd hh:nn:ss",
))
M.append(measure(
    "Predicted Now",
    f"""VAR t = [Predicted Now Timestamp]
RETURN
    IF (
        ISBLANK ( t ),
        BLANK (),
        CALCULATE (
            AVERAGE ( '{DASH}'[Predicted Moisture] ),
            '{DASH}'[Timestamp] = t
        )
    )""",
    F_STATE, "0.000000",
))
M.append(measure(
    "Predicted Now Display",
    'IF ( ISBLANK ( [Predicted Now] ), "—", '
    'FORMAT ( [Predicted Now], "0.000000" ) & " %" )',
    F_STATE,
))
M.append(measure(
    "Predicted Now Caption",
    'IF ( ISBLANK ( [Predicted Now Timestamp] ), '
    '"No prediction yet", '
    '"Updated " & FORMAT ( [Predicted Now Timestamp], "hh:nn:ss" ) )',
    F_STATE,
))
M.append(measure(
    "Data Age Minutes (Now)",
    """IF (
    ISBLANK ( [Latest Timestamp] ),
    BLANK (),
    DATEDIFF ( [Latest Timestamp], NOW (), SECOND ) / 60.0
)""",
    F_STATE, "0.0",
))
# Freshness is judged by when the last row ARRIVED (Inference Timestamp,
# wall clock), not by the process timestamp it carries: the replay emits
# historical plant timestamps, so process-time age says nothing about
# whether the pipeline is alive.
M.append(measure(
    "Ingest Age Minutes (Now)",
    f"""VAR t =
    CALCULATE (
        MAX ( '{DASH}'[Inference Timestamp] ),
        REMOVEFILTERS ( '{DASH}' )
    )
RETURN
    IF (
        ISBLANK ( t ),
        BLANK (),
        DATEDIFF ( t, NOW (), SECOND ) / 60.0
    )""",
    F_STATE, "0.0",
))
M.append(measure(
    "Freshness Status",
    """VAR age = [Ingest Age Minutes (Now)]
RETURN
    IF (
        ISBLANK ( age ), "NO DATA",
        IF ( age <= 2, "LIVE", IF ( age <= 10, "DELAYED", "STALE" ) )
    )""",
    F_STATE,
))
M.append(measure(
    "Freshness Pill Label",
    'SWITCH ( [Freshness Status], "LIVE", "LIVE DATA", "DELAYED", '
    '"DELAYED", "STALE", "STALE", "NO DATA" )',
    F_STATE,
))
M.append(measure(
    "Freshness Detail Display",
    'IF ( ISBLANK ( [Latest Timestamp] ), "no data received", '
    '"Latest " & FORMAT ( [Latest Timestamp], "yyyy-mm-dd hh:nn:ss" ) '
    '& " · ingested " & FORMAT ( [Ingest Age Minutes (Now)], "0" ) '
    '& " min ago" )',
    F_STATE,
))
M.append(measure("Refresh Pill Label", '"AUTO 60 SEC"', F_STATE))
M.append(measure(
    "Operating Status",
    f"""VAR t = [Latest Timestamp]
VAR latestStatus =
    CALCULATE ( MAX ( '{DASH}'[Anomaly Status] ), '{DASH}'[Timestamp] = t )
RETURN
    IF (
        [Freshness Status] = "STALE" || [Freshness Status] = "NO DATA",
        "STALE",
        IF (
            latestStatus = "ANOMALY",
            "ANOMALY",
            IF ( [Risk Intensity] >= 0.35, "WATCH", "NORMAL" )
        )
    )""",
    F_STATE,
))
M.append(measure(
    "Operating Status Caption",
    'SWITCH ( [Operating Status], "ANOMALY", "Requires verification", '
    '"WATCH", "Monitor closely", "STALE", "Data not current", '
    '"Stable operation" )',
    F_STATE,
))
M.append(measure(
    "Severity Caption",
    'IF ( [Operating Status] = "ANOMALY", [Latest Subsystem], "—" )',
    F_STATE,
))
M.append(measure(
    "Model Version Display",
    f"""VAR t = [Latest Timestamp]
VAR v =
    CALCULATE ( MAX ( '{DASH}'[Model Version] ), '{DASH}'[Timestamp] = t )
VAR s =
    CALCULATE (
        MAX ( '{DASH}'[Feature Schema Version] ),
        '{DASH}'[Timestamp] = t
    )
RETURN
    IF ( ISBLANK ( v ), "—", v & " · " & s )""",
    F_STATE,
))

# --- 11 Centralized heatmap colors ---------------------------------------
M.append(measure(
    "Risk Band",
    """VAR r = [Risk Intensity]
RETURN
    IF ( r < 0.2, 0, IF ( r < 0.35, 1, IF ( r < 0.5, 2,
        IF ( r < 0.65, 3, IF ( r < 0.8, 4, 5 ) ) ) ) )""",
    F_COLOR, "0",
))
M.append(measure(
    "Card BG (Risk)",
    f"""SWITCH ( [Risk Band],
    0, "{WHITE}", 1, "{GREEN_SURFACE}", 2, "{AMBER_SURFACE}",
    3, "{AMBER_SURFACE_2}", 4, "{RED_SURFACE}", "{RED}" )""",
    F_COLOR,
))
M.append(measure(
    "Card FG (Risk)",
    f'IF ( [Risk Band] >= 5, "{WHITE}", "{TEXT}" )', F_COLOR,
))
M.append(measure(
    "Status BG (Latest)",
    f"""SWITCH ( [Operating Status],
    "NORMAL", "{GREEN_SURFACE}", "WATCH", "{AMBER_SURFACE}",
    "ANOMALY", "{RED_SURFACE}", "STALE", "{GRAY_SURFACE}", "{WHITE}" )""",
    F_COLOR,
))
M.append(measure(
    "Status FG (Latest)",
    f"""SWITCH ( [Operating Status],
    "NORMAL", "{GREEN}", "WATCH", "{AMBER}",
    "ANOMALY", "{RED_TEXT}", "STALE", "{TEXT_2}", "{TEXT}" )""",
    F_COLOR,
))
M.append(measure(
    "Severity BG (Latest)",
    f"""SWITCH ( UPPER ( [Latest Severity] ),
    "NORMAL", "{GREEN_SURFACE}", "LOW", "{AMBER_SURFACE}",
    "MEDIUM", "{AMBER_SURFACE_2}", "HIGH", "{RED_SURFACE}",
    "CRITICAL", "{RED}", "DATA_QUALITY", "{GRAY_SURFACE}", "{WHITE}" )""",
    F_COLOR,
))
M.append(measure(
    "Severity FG (Latest)",
    f"""SWITCH ( UPPER ( [Latest Severity] ),
    "NORMAL", "{GREEN}", "LOW", "{AMBER}", "MEDIUM", "{AMBER}",
    "HIGH", "{RED_TEXT}", "CRITICAL", "{WHITE}", "{TEXT_2}" )""",
    F_COLOR,
))
M.append(measure(
    "Freshness Pill BG",
    f"""SWITCH ( [Freshness Status],
    "LIVE", "{GREEN_SURFACE}", "DELAYED", "{AMBER_SURFACE}",
    "{RED_SURFACE}" )""",
    F_COLOR,
))
M.append(measure(
    "Freshness Pill FG",
    f"""SWITCH ( [Freshness Status],
    "LIVE", "{GREEN}", "DELAYED", "{AMBER}", "{RED_TEXT}" )""",
    F_COLOR,
))
M.append(measure(
    "Error Card BG",
    f"""VAR e = [Validated Error Latest]
RETURN
    IF ( ISBLANK ( e ), "{WHITE}",
        IF ( e <= 0.05, "{GREEN_SURFACE}",
            IF ( e <= 0.10, "{AMBER_SURFACE}", "{RED_SURFACE}" ) ) )""",
    F_COLOR,
))
M.append(measure(
    "Error Card FG",
    f"""VAR e = [Validated Error Latest]
RETURN
    IF ( ISBLANK ( e ), "{TEXT_2}",
        IF ( e <= 0.05, "{GREEN}",
            IF ( e <= 0.10, "{AMBER}", "{RED_TEXT}" ) ) )""",
    F_COLOR,
))
M.append(measure(
    "Predicted Card BG",
    f"""VAR v = [Predicted Now]
RETURN
    IF ( ISBLANK ( v ), "{WHITE}",
        IF ( v >= [Target Band Low] && v <= [Target Band High],
            "{GREEN_SURFACE}",
            IF ( v >= {MOISTURE_WARNING_LOW} && v <= {MOISTURE_WARNING_HIGH}, "{AMBER_SURFACE}",
                "{RED_SURFACE}" ) ) )""",
    F_COLOR,
))
M.append(measure(
    "Lab Card BG",
    f"""VAR v = [Lab Last Moisture]
RETURN
    IF ( ISBLANK ( v ), "{WHITE}",
        IF ( v >= [Target Band Low] && v <= [Target Band High],
            "{GREEN_SURFACE}",
            IF ( v >= {MOISTURE_WARNING_LOW} && v <= {MOISTURE_WARNING_HIGH}, "{AMBER_SURFACE}",
                "{RED_SURFACE}" ) ) )""",
    F_COLOR,
))
M.append(measure(
    "Risk Gauge Color",
    f"""SWITCH ( [Risk Band],
    0, "{GREEN}", 1, "{GREEN}", 2, "#F2A12E", 3, "#F2A12E",
    4, "#DF5558", "{RED}" )""",
    F_COLOR,
))
M.append(measure("Risk Gauge Remainder", "1 - [Risk Intensity]", F_COLOR, "0.000"))

# --- 12 Trend series ------------------------------------------------------
M.append(measure("Target Band Low", str(TARGET_BAND_LOW), F_TREND, "0.00000"))
M.append(measure("Target Band High", str(TARGET_BAND_HIGH), F_TREND, "0.00000"))
M.append(measure(
    "Moisture Lab Markers",
    f"""CALCULATE (
    AVERAGE ( '{DASH}'[Laboratory Moisture] ),
    '{DASH}'[Is Lab Sample] = TRUE ()
)""",
    F_TREND, "0.000000",
))
M.append(measure(
    "Risk (Trend)", f"AVERAGE ( '{DASH}'[Anomaly Risk] )", F_TREND, "0.000",
))
M.append(measure(
    "Risk (Anomalous)",
    f"""CALCULATE (
    AVERAGE ( '{DASH}'[Anomaly Risk] ),
    '{DASH}'[Anomaly Status] = "ANOMALY"
)""",
    F_TREND, "0.000",
))
M.append(measure("Warning Threshold", "0.5", F_TREND, "0.0"))
M.append(measure("Critical Threshold", "0.8", F_TREND, "0.0"))
for trend_name, trend_col in [
    ("Steam Pressure (Trend)", "Steam Pressure"),
    ("Air Flow (Trend)", "Air Flow Rate"),
    ("Feed Rate (Trend)", "Wet Product Feed Rate"),
    ("Dryer Temp (Trend)", "Dryer Air Temperature"),
    ("Vacuum (Trend)", "Vacuum"),
    ("Fan Speed (Trend)", "Fan Speed"),
]:
    M.append(measure(
        trend_name, f"AVERAGE ( '{DASH}'[{trend_col}] )", F_TREND, "0.00",
    ))
M.append(measure(
    "Timeline Selected Marker",
    # Must respect the chart's Timestamp axis context: overriding it with
    # CALCULATE(Timestamp = t) returns the same value for EVERY axis
    # point and draws a solid horizontal line across the whole timeline.
    # Emitting only at the matching axis point yields a single marker.
    f"""VAR t = [Selected Event Peak Timestamp]
RETURN
    IF (
        MAX ( '{DASH}'[Timestamp] ) = t,
        AVERAGE ( '{DASH}'[Anomaly Risk] )
    )""",
    F_TREND, "0.000",
))

# --- 13 Critical variable cards ------------------------------------------
with REFERENCE_PROFILE.open("r", encoding="utf-8") as file:
    _profile = json.load(file)


def _bands(feature: str) -> dict[str, float]:
    stats = _profile["statistics"][feature]
    return {k: float(stats[k]) for k in ("q01", "q05", "q95", "q99")}


CRITICAL_VARIABLES = [
    # (short, tmdl column, latest measure, unit, value format, profile key)
    ("DAT", "Dryer Air Temperature", "Latest Dryer Air Temperature",
     "°C", "0.0", "dryer_air_temperature"),
    ("Feed", "Wet Product Feed Rate", "Latest Wet Product Feed Rate",
     "m³/h", "0.0", "wet_product_feed_rate"),
    ("Steam", "Steam Pressure", "Latest Steam Pressure",
     "bar", "0.00", "steam_pressure"),
    ("Airflow", "Air Flow Rate", "Latest Air Flow Rate",
     "m³/h", "#,0", "air_flow_rate"),
    ("Vacuum", "Vacuum", "Latest Vacuum",
     "mmH2O", "0.0", "vacuum"),
]

for short, col_name, latest_ref, unit, fmt, profile_key in CRITICAL_VARIABLES:
    b = _bands(profile_key)
    M.append(measure(
        f"{short} Status",
        f"""VAR v = [{latest_ref}]
RETURN
    IF ( ISBLANK ( v ), "NO DATA",
        IF ( v >= {b['q05']:.4f} && v <= {b['q95']:.4f}, "NORMAL",
            IF ( v >= {b['q01']:.4f} && v <= {b['q99']:.4f}, "WATCH",
                "HIGH" ) ) )""",
        F_VARS,
    ))
    M.append(measure(
        f"{short} Card BG",
        f"""SWITCH ( [{short} Status],
    "NORMAL", "{GREEN_SURFACE}", "WATCH", "{AMBER_SURFACE}",
    "HIGH", "{RED_SURFACE}", "{WHITE}" )""",
        F_COLOR,
    ))
    M.append(measure(
        f"{short} Card FG",
        f"""SWITCH ( [{short} Status],
    "NORMAL", "{GREEN}", "WATCH", "{AMBER}", "HIGH", "{RED_TEXT}",
    "{TEXT_2}" )""",
        F_COLOR,
    ))
    M.append(measure(
        f"{short} Value Display",
        f'IF ( ISBLANK ( [{latest_ref}] ), "—", '
        f'FORMAT ( [{latest_ref}], "{fmt}" ) & " {unit}" )',
        F_VARS,
    ))
    M.append(measure(
        f"{short} Delta 5m",
        f"""VAR t = [Latest Timestamp]
VAR prev = t - TIME ( 0, 5, 0 )
VAR previousValue =
    CALCULATE (
        AVERAGE ( '{DASH}'[{col_name}] ),
        '{DASH}'[Timestamp] = prev
    )
RETURN
    IF (
        ISBLANK ( previousValue ),
        BLANK (),
        [{latest_ref}] - previousValue
    )""",
        F_VARS, "+0.00;-0.00;0.00",
    ))
    M.append(measure(
        f"{short} Delta Display",
        f"""VAR d = [{short} Delta 5m]
VAR deltaText =
    IF (
        ISBLANK ( d ),
        "Δ —",
        "Δ " & IF ( d >= 0, "+", "" ) & FORMAT ( d, "0.0" )
    )
RETURN
    deltaText & "   " & [{short} Status]""",
        F_VARS,
    ))
    M.append(measure(
        f"{short} Stats Tooltip",
        f""""min " & FORMAT ( MIN ( '{DASH}'[{col_name}] ), "{fmt}" )
    & " · max " & FORMAT ( MAX ( '{DASH}'[{col_name}] ), "{fmt}" )
    & " · mean " & FORMAT ( AVERAGE ( '{DASH}'[{col_name}] ), "{fmt}" )
    & " · σ " & FORMAT ( STDEV.P ( '{DASH}'[{col_name}] ), "{fmt}" )""",
        F_VARS,
    ))

# TMDL treats /// lines as object DESCRIPTIONS that must sit directly on
# the object they describe — a blank line in between (or a trailing
# description with no object) makes Power BI fail with
# "InvalidLineType ... an object-description must be followed by the
# actual object". The BEGIN sentinel therefore attaches to the first
# generated column and the END sentinel to the partition that follows.
DASHBOARD_EXTENSION = (
    BEGIN_MARK
    + "\n\t/// Generated by tools/generate_powerbi_semantic.py — edit the\n"
    + "\t/// generator, not this block. Normal bands are training-period\n"
    + "\t/// quantiles from models/5s/reference_profile.json.\n"
    + "\n".join(NEW_DASHBOARD_COLUMNS)
    + "\n"
    + "\n".join(M)
    + END_MARK
    + "\n"
)

# --------------------------------------------------------------------------
# New table: vw_dryer_lab_samples
# --------------------------------------------------------------------------

LAB_COLUMNS = [
    column("Sample Timestamp", "Sample Timestamp", "dateTime", LAB,
           "yyyy-mm-dd hh:nn:ss"),
    column("Product Density", "Product Density", "double", LAB, "0.0000"),
    column("Final Product Temp", "Final Product Temp", "double", LAB, "0.0"),
    column("Laboratory Moisture", "Laboratory Moisture", "double", LAB,
           "0.0000"),
    column("Predicted Moisture At Sample", "Predicted Moisture At Sample",
           "double", LAB, "0.0000"),
    column("Validated Error", "Validated Error", "double", LAB,
           "+0.0000;-0.0000;0.0000"),
    column("Validated Absolute Error", "Validated Absolute Error", "double",
           LAB, "0.0000"),
    column("Previous Sample Timestamp", "Previous Sample Timestamp",
           "dateTime", LAB, "yyyy-mm-dd hh:nn:ss", hidden=True),
]

LAB_MEASURES = [
    measure("Lab Sample Count", f"COUNTROWS ( '{LAB}' )", F_LAB, "#,0",
            owner=LAB),
    measure(
        "Lab MAE (Window)",
        f"AVERAGE ( '{LAB}'[Validated Absolute Error] )",
        F_VAL, "0.0000", owner=LAB,
    ),
]

LAB_TABLE = f"""/// Actual laboratory samples (one row per real analysis) with the
/// validated model prediction at each sample. Populated by the SQL view
/// vw_dryer_lab_samples; row count equals laboratory analyses, never
/// process rows.
table {LAB}
\tlineageTag: {tag(LAB, 'table')}

{chr(10).join(LAB_MEASURES)}
{chr(10).join(LAB_COLUMNS)}
\tpartition {LAB} = m
\t\tmode: directQuery
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = PostgreSQL.Database(DB_Server, DB_Database),
\t\t\t\t    Data = Source{{[Schema = "public", Item = "{LAB}"]}}[Data]
\t\t\t\tin
\t\t\t\t    Data

\tannotation PBI_ResultType = Table
"""

# --------------------------------------------------------------------------
# New table: vw_dryer_anomaly_events
# --------------------------------------------------------------------------

F_EVENTS = "14 Events (5s)"

EVENT_COLUMNS = [
    column("Event ID", "Event ID", "int64", EVENTS, "0"),
    column("Event Start", "Event Start", "dateTime", EVENTS,
           "yyyy-mm-dd hh:nn:ss"),
    column("Event End", "Event End", "dateTime", EVENTS,
           "yyyy-mm-dd hh:nn:ss"),
    column("Duration Min", "Duration Min", "double", EVENTS, "0.0"),
    column("Rows In Event", "Rows In Event", "int64", EVENTS, "0"),
    column("Peak Timestamp", "Peak Timestamp", "dateTime", EVENTS,
           "yyyy-mm-dd hh:nn:ss"),
    column("Peak Anomaly Score", "Peak Anomaly Score", "double", EVENTS,
           "0.000000"),
    column("Peak Anomaly Risk", "Peak Anomaly Risk", "double", EVENTS,
           "0.000"),
    column("Severity", "Severity", "string", EVENTS),
    column("Subsystem", "Subsystem", "string", EVENTS),
    column("Diagnosis", "Diagnosis", "string", EVENTS),
    column("Possible Causes", "Possible Causes", "string", EVENTS),
    column("Recommended Verification", "Recommended Verification", "string",
           EVENTS),
    column("Predicted Moisture At Peak", "Predicted Moisture At Peak",
           "double", EVENTS, "0.0000"),
]


def event_lookup(name: str, target_column: str, fmt: str | None,
                 wrap: str | None = None) -> str:
    dax = f"""VAR t = [Selected Event Peak Timestamp]
RETURN
    CALCULATE (
        MAX ( '{EVENTS}'[{target_column}] ),
        REMOVEFILTERS ( '{EVENTS}' ),
        '{EVENTS}'[Peak Timestamp] = t
    )"""
    if wrap:
        dax = wrap.replace("__X__", f"( {dax} )")
    return measure(name, dax, F_EVENTS, fmt, owner=EVENTS)


EVENT_MEASURES = [
    measure("Events Count", f"COUNTROWS ( '{EVENTS}' )", F_EVENTS, "#,0",
            owner=EVENTS),
    measure(
        "Events High Count",
        f"CALCULATE ( COUNTROWS ( '{EVENTS}' ), "
        f"'{EVENTS}'[Severity] = \"HIGH\" )",
        F_EVENTS, "#,0", owner=EVENTS,
    ),
    measure(
        "Events Medium Count",
        f"CALCULATE ( COUNTROWS ( '{EVENTS}' ), "
        f"'{EVENTS}'[Severity] = \"MEDIUM\" )",
        F_EVENTS, "#,0", owner=EVENTS,
    ),
    measure(
        "Events Low Count",
        f"CALCULATE ( COUNTROWS ( '{EVENTS}' ), "
        f"'{EVENTS}'[Severity] = \"LOW\" )",
        F_EVENTS, "#,0", owner=EVENTS,
    ),
    measure(
        "Events Empty State",
        'IF ( COALESCE ( [Events Count], 0 ) = 0, '
        '"No abnormal events in the selected window.", "" )',
        F_EVENTS, owner=EVENTS,
    ),
    measure(
        "Selected Event Peak Timestamp",
        f"""VAR s = SELECTEDVALUE ( '{EVENTS}'[Peak Timestamp] )
RETURN
    IF (
        ISBLANK ( s ),
        CALCULATE (
            MAX ( '{EVENTS}'[Peak Timestamp] ),
            ALLSELECTED ( '{EVENTS}' )
        ),
        s
    )""",
        F_EVENTS, "yyyy-mm-dd hh:nn:ss", owner=EVENTS,
    ),
    event_lookup("Event Sel Severity", "Severity", None),
    event_lookup("Event Sel Subsystem", "Subsystem", None),
    event_lookup("Event Sel Diagnosis", "Diagnosis", None),
    event_lookup("Event Sel Causes", "Possible Causes", None),
    event_lookup("Event Sel Verification", "Recommended Verification", None),
    event_lookup(
        "Event Sel Time Display", "Peak Timestamp", None,
        wrap='IF ( ISBLANK ( __X__ ), "No event selected", '
             'FORMAT ( __X__, "yyyy-mm-dd hh:nn:ss" ) )',
    ),
    event_lookup(
        "Event Sel Duration Display", "Duration Min", None,
        wrap='IF ( ISBLANK ( __X__ ), "—", FORMAT ( __X__, "0.0" ) '
             '& " min" )',
    ),
    event_lookup(
        "Event Sel Peak Risk Display", "Peak Anomaly Risk", None,
        wrap='IF ( ISBLANK ( __X__ ), "—", FORMAT ( __X__, "0.00" ) )',
    ),
    event_lookup(
        "Event Sel Moisture Display", "Predicted Moisture At Peak", None,
        wrap='IF ( ISBLANK ( __X__ ), "—", FORMAT ( __X__, "0.00" ) '
             '& " % predicted" )',
    ),
    measure(
        "Event Sel Lab Context",
        f"""VAR t = [Selected Event Peak Timestamp]
VAR labT =
    CALCULATE (
        MAX ( '{LAB}'[Sample Timestamp] ),
        REMOVEFILTERS ( '{LAB}' ),
        '{LAB}'[Sample Timestamp] <= t
    )
VAR labV =
    CALCULATE (
        AVERAGE ( '{LAB}'[Laboratory Moisture] ),
        REMOVEFILTERS ( '{LAB}' ),
        '{LAB}'[Sample Timestamp] = labT
    )
RETURN
    IF (
        ISBLANK ( labV ),
        "No laboratory result before this event",
        FORMAT ( labV, "0.00" ) & " % lab at "
            & FORMAT ( labT, "hh:nn" )
    )""",
        F_EVENTS, owner=EVENTS,
    ),
    measure(
        "Event Sel Severity Pill BG",
        f"""SWITCH ( UPPER ( [Event Sel Severity] ),
    "HIGH", "{RED_SURFACE}", "MEDIUM", "{AMBER_SURFACE_2}",
    "LOW", "{AMBER_SURFACE}", "CRITICAL", "{RED}", "{GREEN_SURFACE}" )""",
        F_COLOR, owner=EVENTS,
    ),
    measure(
        "Event Sel Severity Pill FG",
        f"""SWITCH ( UPPER ( [Event Sel Severity] ),
    "HIGH", "{RED_TEXT}", "MEDIUM", "{AMBER}", "LOW", "{AMBER}",
    "CRITICAL", "{WHITE}", "{GREEN}" )""",
        F_COLOR, owner=EVENTS,
    ),
    measure(
        "Event Row BG",
        f"""SWITCH ( UPPER ( MAX ( '{EVENTS}'[Severity] ) ),
    "HIGH", "{RED_SURFACE}", "MEDIUM", "{AMBER_SURFACE_2}",
    "LOW", "{AMBER_SURFACE}", "CRITICAL", "{RED}", "{WHITE}" )""",
        F_COLOR, owner=EVENTS,
    ),
    measure(
        "Event Row FG",
        f"""SWITCH ( UPPER ( MAX ( '{EVENTS}'[Severity] ) ),
    "HIGH", "{RED_TEXT}", "MEDIUM", "{AMBER}", "LOW", "{AMBER}",
    "CRITICAL", "{WHITE}", "{TEXT}" )""",
        F_COLOR, owner=EVENTS,
    ),
]

EVENTS_TABLE = f"""/// Operator-facing anomaly events: consecutive anomalous 5-second rows
/// grouped by the SQL view vw_dryer_anomaly_events (gap tolerance 30 s).
/// Severity/subsystem/diagnosis come from each event's peak-risk row.
table {EVENTS}
\tlineageTag: {tag(EVENTS, 'table')}

{chr(10).join(EVENT_MEASURES)}
{chr(10).join(EVENT_COLUMNS)}
\tpartition {EVENTS} = m
\t\tmode: directQuery
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = PostgreSQL.Database(DB_Server, DB_Database),
\t\t\t\t    Data = Source{{[Schema = "public", Item = "{EVENTS}"]}}[Data]
\t\t\t\tin
\t\t\t\t    Data

\tannotation PBI_ResultType = Table
"""

# Relationships cannot carry /// descriptions at all (TOM relationships
# have no Description property), so the generated block is anchored on
# the relationship name instead of sentinel comment lines.
RELATIONSHIP_ANCHOR = "relationship events-to-contributors"
RELATIONSHIP_BLOCK = f"""{RELATIONSHIP_ANCHOR}
\tfromColumn: vw_dryer_contributors_powerbi.Timestamp
\ttoColumn: vw_dryer_anomaly_events.'Peak Timestamp'
"""

_LEGACY_RELATIONSHIP_SENTINELS = (
    "/// ===== BEGIN 5S EXTENSION (generated) =====\n",
    "/// ===== END 5S EXTENSION (generated) =====\n",
    "/// ===== BEGIN 5S EXTENSION (generated) =====",
    "/// ===== END 5S EXTENSION (generated) =====",
)


def patch_relationships(text: str) -> str:
    """Idempotently (re)write the generated relationship.

    The generated relationship is always the last object in
    relationships.tmdl; everything from its anchor line to the end of the
    file is replaced. Legacy sentinel lines from older generator versions
    are stripped first.
    """

    for sentinel in _LEGACY_RELATIONSHIP_SENTINELS:
        text = text.replace(sentinel, "")
    if RELATIONSHIP_ANCHOR in text:
        text = text[: text.index(RELATIONSHIP_ANCHOR)]
    return text.rstrip("\n") + "\n\n" + RELATIONSHIP_BLOCK


def replace_block(text: str, block: str, begin: str, end: str,
                  insert_before: str | None = None) -> str:
    if begin in text:
        head, rest = text.split(begin, 1)
        _, tail = rest.split(end, 1)
        tail = tail.lstrip("\n")
        return head + block + tail
    if insert_before is not None and insert_before in text:
        index = text.index(insert_before)
        return text[:index] + block + text[index:]
    return text.rstrip("\n") + "\n\n" + block


def main() -> None:
    dashboard = DASHBOARD_TMDL.read_text(encoding="utf-8")
    dashboard = replace_block(
        dashboard,
        DASHBOARD_EXTENSION,
        BEGIN_MARK,
        END_MARK,
        insert_before="\tpartition vw_dryer_dashboard_powerbi = m",
    )
    DASHBOARD_TMDL.write_text(dashboard, encoding="utf-8")
    print(f"Patched {DASHBOARD_TMDL.name}")

    (TABLES_DIR / f"{LAB}.tmdl").write_text(LAB_TABLE, encoding="utf-8")
    print(f"Wrote {LAB}.tmdl")
    (TABLES_DIR / f"{EVENTS}.tmdl").write_text(EVENTS_TABLE, encoding="utf-8")
    print(f"Wrote {EVENTS}.tmdl")

    relationships = patch_relationships(
        RELATIONSHIPS_TMDL.read_text(encoding="utf-8")
    )
    RELATIONSHIPS_TMDL.write_text(relationships, encoding="utf-8")
    print(f"Patched {RELATIONSHIPS_TMDL.name}")

    print(
        f"\nAdded {len(NEW_DASHBOARD_COLUMNS)} columns and "
        f"{len(M)} dashboard measures, {len(LAB_MEASURES)} lab measures, "
        f"{len(EVENT_MEASURES)} event measures."
    )


if __name__ == "__main__":
    main()
