"""Time alignment between the 5-second process stream and laboratory data.

Two deliberately different alignments exist:

1. **Dashboard alignment** (``align_lab_for_dashboard``) — a backward as-of
   join so every process row can *display* the latest known laboratory
   result together with its age. Carried-forward values are labelled as
   such and are never used as model targets.

2. **Training alignment** (``build_training_matrix``) — one supervised row
   per actual laboratory sample. The product analysed at ``t_lab`` left the
   dryer earlier: material needs the dryer residence time plus a
   configurable downstream transport delay to reach the sampling point, so
   the feature window ends at::

       effective_end = t_lab − residence_time(t_lab) − transport_delay

   and starts ``window_minutes`` before that. Residence time is taken from
   the latest process observation at or before ``t_lab`` (never a future
   value). No process row after ``effective_end`` can leak into a feature
   window, and no laboratory value is interpolated, back-filled, or
   duplicated across process rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from multirate.preprocessing import (
    PROCESS_VARIABLES,
    QUALITY_VARIABLES,
)
from multirate.window_features import (
    WINDOW_FEATURE_NAMES,
    compute_window_features,
)


DEFAULT_WINDOW_MINUTES = 30.0
DEFAULT_TRANSPORT_DELAY_MINUTES = 0.0
DEFAULT_MIN_WINDOW_COVERAGE = 0.8

LAB_DISPLAY_COLUMNS = {
    "Sample Timestamp": "Latest Lab Sample Timestamp",
    "Product Density": "Latest Lab Product Density",
    "Final Product Temp": "Latest Lab Final Product Temp",
    "Final Moisture (%H2O)": "Latest Lab Final Moisture",
}


@dataclass
class TrainingAlignmentResult:
    """Supervised matrix plus an auditable account of every lab sample."""

    features: pd.DataFrame
    targets: pd.DataFrame
    window_info: pd.DataFrame
    skipped: list[tuple[pd.Timestamp, str]] = field(default_factory=list)


def align_lab_for_dashboard(
    process: pd.DataFrame,
    lab: pd.DataFrame,
) -> pd.DataFrame:
    """Attach the latest known laboratory result to each process row.

    Display-only. Adds ``Latest Lab *`` columns, ``Lab Result Age (min)``
    and ``Lab Sample Available``; rows before the first laboratory sample
    stay empty rather than borrowing a future result.
    """

    process_sorted = process.sort_values("Timestamp", kind="stable")
    lab_sorted = lab.sort_values("Sample Timestamp", kind="stable")

    joined = pd.merge_asof(
        process_sorted,
        lab_sorted.rename(columns=LAB_DISPLAY_COLUMNS),
        left_on="Timestamp",
        right_on="Latest Lab Sample Timestamp",
        direction="backward",
    )

    age = (
        joined["Timestamp"] - joined["Latest Lab Sample Timestamp"]
    ).dt.total_seconds() / 60.0
    joined["Lab Result Age (min)"] = age
    joined["Lab Sample Available"] = joined[
        "Latest Lab Sample Timestamp"
    ].notna()

    return joined


def effective_window_end(
    lab_timestamp: pd.Timestamp,
    residence_time_minutes: float,
    transport_delay_minutes: float = DEFAULT_TRANSPORT_DELAY_MINUTES,
) -> pd.Timestamp:
    """End of the process window that influenced a laboratory sample."""

    if residence_time_minutes < 0 or transport_delay_minutes < 0:
        raise ValueError(
            "Residence time and transport delay must be non-negative."
        )

    return lab_timestamp - pd.Timedelta(
        minutes=residence_time_minutes + transport_delay_minutes
    )


def _residence_time_asof(
    process: pd.DataFrame,
    lab_timestamp: pd.Timestamp,
) -> float | None:
    """Residence time from the latest process row at or before the sample."""

    earlier = process.loc[process["Timestamp"] <= lab_timestamp]
    if earlier.empty:
        return None
    value = earlier["Residence Time"].iloc[-1]
    return None if pd.isna(value) else float(value)


def build_training_matrix(
    process: pd.DataFrame,
    lab: pd.DataFrame,
    window_minutes: float = DEFAULT_WINDOW_MINUTES,
    transport_delay_minutes: float = DEFAULT_TRANSPORT_DELAY_MINUTES,
    expected_interval_seconds: int = 5,
    min_window_coverage: float = DEFAULT_MIN_WINDOW_COVERAGE,
) -> TrainingAlignmentResult:
    """One supervised row per actual laboratory sample.

    X = aggregated process-window features ending before the sample left
    the dryer; y = the three sparse laboratory targets. Samples without
    enough process history (e.g. the first sample of a campaign) are
    skipped and reported, never fabricated.
    """

    if window_minutes <= 0:
        raise ValueError("window_minutes must be positive.")

    process_sorted = (
        process.sort_values("Timestamp", kind="stable").reset_index(drop=True)
    )
    lab_sorted = (
        lab.sort_values("Sample Timestamp", kind="stable").reset_index(
            drop=True
        )
    )

    expected_rows = window_minutes * 60.0 / expected_interval_seconds

    feature_rows: list[dict[str, float]] = []
    info_rows: list[dict[str, object]] = []
    skipped: list[tuple[pd.Timestamp, str]] = []

    for lab_timestamp in lab_sorted["Sample Timestamp"]:
        residence = _residence_time_asof(process_sorted, lab_timestamp)
        if residence is None:
            skipped.append(
                (lab_timestamp, "no process data at or before the sample")
            )
            continue

        window_end = effective_window_end(
            lab_timestamp, residence, transport_delay_minutes
        )
        window_start = window_end - pd.Timedelta(minutes=window_minutes)

        in_window = process_sorted.loc[
            (process_sorted["Timestamp"] > window_start)
            & (process_sorted["Timestamp"] <= window_end)
        ]

        coverage = len(in_window) / expected_rows
        if coverage < min_window_coverage:
            skipped.append(
                (
                    lab_timestamp,
                    f"window coverage {coverage:.2f} below "
                    f"{min_window_coverage:.2f}",
                )
            )
            continue

        try:
            features = compute_window_features(
                in_window[["Timestamp", *PROCESS_VARIABLES]]
            )
        except ValueError as error:
            skipped.append((lab_timestamp, str(error)))
            continue

        feature_rows.append(features)
        info_rows.append(
            {
                "Sample Timestamp": lab_timestamp,
                "Residence Time (min)": residence,
                "Transport Delay (min)": transport_delay_minutes,
                "Window Start": window_start,
                "Window End": window_end,
                "Window Rows": len(in_window),
                "Window Coverage": coverage,
            }
        )

    if info_rows:
        sample_index = pd.DatetimeIndex(
            [row["Sample Timestamp"] for row in info_rows],
            name="Sample Timestamp",
        )
        aligned_lab = lab_sorted.set_index("Sample Timestamp").loc[
            sample_index
        ]
        targets = aligned_lab[QUALITY_VARIABLES].copy()
        features = pd.DataFrame(
            feature_rows,
            index=sample_index,
            columns=WINDOW_FEATURE_NAMES,
        )
        window_info = pd.DataFrame(info_rows).set_index("Sample Timestamp")
    else:
        sample_index = pd.DatetimeIndex([], name="Sample Timestamp")
        features = pd.DataFrame(columns=WINDOW_FEATURE_NAMES)
        targets = pd.DataFrame(columns=QUALITY_VARIABLES)
        window_info = pd.DataFrame()

    return TrainingAlignmentResult(
        features=features,
        targets=targets,
        window_info=window_info,
        skipped=skipped,
    )
