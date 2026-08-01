"""PCS7-style prototype limit checks and hybrid alarm state logic."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


LIMIT_ORDER = ("LL", "L", "H", "HH")


def evaluate_pcs7_limits(
    process_data: pd.DataFrame,
    feature_limits: Mapping[str, Mapping[str, float | str | None]],
    direct_process_features: Sequence[str],
) -> pd.DataFrame:
    """Evaluate LL/L/H/HH prototype rules in original feature units."""

    features = list(direct_process_features)
    missing = [feature for feature in features if feature not in process_data]
    if missing:
        raise KeyError(f"Process features required by limit checks are missing: {missing}")
    missing_configs = [feature for feature in features if feature not in feature_limits]
    if missing_configs:
        raise KeyError(f"Limit configurations are missing: {missing_configs}")

    limit_results = process_data[["timestamp"]].reset_index(drop=True).copy()
    state_columns: list[str] = []
    configured_limit_count = 0

    for feature in features:
        limits = feature_limits[feature]
        configured_limit_count += sum(limits.get(name) is not None for name in LIMIT_ORDER)
        values = process_data[feature].reset_index(drop=True)
        state_column = f"{feature} PCS7 state"
        state_columns.append(state_column)
        if all(limits.get(name) is None for name in LIMIT_ORDER):
            state = np.full(len(values), "Not configured", dtype=object)
        else:
            state = np.full(len(values), "Within configured limits", dtype=object)
            if limits.get("L") is not None:
                state[values < limits["L"]] = "L warning"
            if limits.get("H") is not None:
                state[values > limits["H"]] = "H warning"
            if limits.get("LL") is not None:
                state[values <= limits["LL"]] = "LL critical"
            if limits.get("HH") is not None:
                state[values >= limits["HH"]] = "HH critical"
        limit_results[state_column] = state

    warning_mask = limit_results[state_columns].isin(["L warning", "H warning"])
    critical_mask = limit_results[state_columns].isin(["LL critical", "HH critical"])
    limit_results["PCS7 warning count"] = warning_mask.sum(axis=1)
    limit_results["PCS7 critical count"] = critical_mask.sum(axis=1)
    limit_results["PCS7 breach count"] = (
        limit_results["PCS7 warning count"] + limit_results["PCS7 critical count"]
    )
    limit_results["PCS7 rule breach"] = limit_results["PCS7 breach count"] > 0

    breached_feature_labels = []
    for row_index in range(len(limit_results)):
        row_breaches = []
        for feature, state_column in zip(features, state_columns):
            feature_state = limit_results.at[row_index, state_column]
            if feature_state not in ["Not configured", "Within configured limits"]:
                row_breaches.append(f"{feature}: {feature_state}")
        breached_feature_labels.append("; ".join(row_breaches))
    limit_results["PCS7 breached features"] = breached_feature_labels

    if configured_limit_count == 0:
        limit_results["PCS7 limit status"] = "Not configured"
    else:
        limit_results["PCS7 limit status"] = np.select(
            [
                limit_results["PCS7 critical count"] > 0,
                limit_results["PCS7 warning count"] > 0,
            ],
            ["Critical", "Warning"],
            default="Within configured limits",
        )
    return limit_results


def attach_pcs7_hybrid_alarm_state(
    score_table: pd.DataFrame,
    pcs7_limit_results: pd.DataFrame,
    configured_limit_count: int,
) -> pd.DataFrame:
    """Combine PCS7-style limit states with raw and persistent ML states."""

    pcs7_columns = [
        "timestamp",
        "PCS7 warning count",
        "PCS7 critical count",
        "PCS7 breach count",
        "PCS7 rule breach",
        "PCS7 breached features",
        "PCS7 limit status",
    ]
    hybrid_table = score_table.merge(
        pcs7_limit_results[pcs7_columns],
        on="timestamp",
        how="left",
        validate="one_to_one",
    )
    pcs7_critical = hybrid_table["PCS7 critical count"] > 0
    pcs7_warning = hybrid_table["PCS7 warning count"] > 0
    persistent_ml = hybrid_table["Persistent alarm"]
    raw_ml = hybrid_table["Raw anomaly flag"]
    default_state = (
        "No active alert (PCS7 limits not configured)"
        if configured_limit_count == 0
        else "Normal within configured PCS7 limits"
    )
    hybrid_table["Combined alarm state"] = np.select(
        [
            pcs7_critical & persistent_ml,
            pcs7_critical,
            pcs7_warning & persistent_ml,
            pcs7_warning,
            persistent_ml,
            raw_ml,
        ],
        [
            "Critical: PCS7 limit + persistent ML anomaly",
            "Critical: PCS7 limit",
            "High: PCS7 warning + persistent ML anomaly",
            "Warning: PCS7 limit",
            "Advisory: persistent ML anomaly",
            "Review: raw ML candidate",
        ],
        default=default_state,
    )
    hybrid_table["Combined severity level"] = np.select(
        [
            pcs7_critical & persistent_ml,
            pcs7_critical,
            pcs7_warning & persistent_ml,
            pcs7_warning,
            persistent_ml,
            raw_ml,
        ],
        [5, 5, 4, 3, 2, 1],
        default=0,
    ).astype(int)
    return hybrid_table.sort_values("timestamp", kind="stable").reset_index(drop=True)
