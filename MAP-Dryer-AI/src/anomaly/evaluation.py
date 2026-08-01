"""Detector-comparison summaries."""

from __future__ import annotations

import pandas as pd


def detector_comparison_row(
    detector_name: str,
    score_table: pd.DataFrame,
    threshold: float,
    synthetic_detection_rates: pd.Series,
) -> dict[str, float | str | int]:
    """Build one comparable detector summary row."""

    split_tables = {
        split_name: score_table.loc[score_table["Split"] == split_name]
        for split_name in ["Reference", "Validation", "Testing"]
    }
    missing = [name for name, table in split_tables.items() if table.empty]
    if missing:
        raise ValueError(f"Detector comparison splits are empty: {missing}")
    return {
        "Detector": detector_name,
        "Validation threshold": float(threshold),
        "Reference candidate rate (%)": float(
            100 * split_tables["Reference"]["Raw anomaly flag"].mean()
        ),
        "Validation candidate rate (%)": float(
            100 * split_tables["Validation"]["Raw anomaly flag"].mean()
        ),
        "Validation persistent episodes": int(
            split_tables["Validation"]["Alarm episode"].nunique()
        ),
        "Worst synthetic detection rate (%)": float(
            100 * synthetic_detection_rates.min()
        ),
        "Mean synthetic detection rate (%)": float(
            100 * synthetic_detection_rates.mean()
        ),
        "Test candidate rate (%) - descriptive": float(
            100 * split_tables["Testing"]["Raw anomaly flag"].mean()
        ),
        "Test persistent episodes - descriptive": int(
            split_tables["Testing"]["Alarm episode"].nunique()
        ),
    }
