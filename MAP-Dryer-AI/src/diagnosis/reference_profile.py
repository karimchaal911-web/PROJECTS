"""Train-only robust reference statistics for anomaly diagnosis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ReferenceProfile:
    feature_names: tuple[str, ...]
    statistics: dict[str, dict[str, float]]
    feature_metadata: dict[str, dict[str, Any]]
    training_rows: int
    profile_version: str = "reference_profile_v1.0"

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_version": self.profile_version,
            "training_rows": self.training_rows,
            "feature_names": list(self.feature_names),
            "statistics": self.statistics,
            "feature_metadata": self.feature_metadata,
        }

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.as_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return target

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceProfile":
        return cls(
            feature_names=tuple(payload["feature_names"]),
            statistics=payload["statistics"],
            feature_metadata=payload["feature_metadata"],
            training_rows=int(payload["training_rows"]),
            profile_version=str(payload.get("profile_version", "reference_profile_v1.0")),
        )


def _finite_numeric_frame(data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError("Normal-reference data must be a non-empty DataFrame.")
    numeric = data.apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("Normal-reference data contains missing or non-finite values.")
    return numeric


def build_reference_profile(
    X_normal: pd.DataFrame,
    feature_metadata: dict[str, Any],
) -> ReferenceProfile:
    """Build robust statistics exclusively from the supplied normal training rows."""

    normal = _finite_numeric_frame(X_normal)
    metadata_payload = feature_metadata.get("features", feature_metadata)
    missing = sorted(set(normal.columns) - set(metadata_payload))
    if missing:
        raise ValueError(f"Reference features lack metadata: {missing}")

    statistics: dict[str, dict[str, float]] = {}
    for feature in normal.columns:
        values = normal[feature]
        q01, q05, q25, q50, q75, q95, q99 = values.quantile(
            [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
        )
        absolute_deviation = (values - q50).abs()
        deltas = values.diff().dropna()
        if deltas.empty:
            delta_median = delta_iqr = delta_mad = 0.0
        else:
            delta_q25, delta_median, delta_q75 = deltas.quantile(
                [0.25, 0.50, 0.75]
            )
            delta_iqr = float(delta_q75 - delta_q25)
            delta_mad = float((deltas - delta_median).abs().median())
        statistics[feature] = {
            "median": float(q50),
            "q01": float(q01),
            "q05": float(q05),
            "q25": float(q25),
            "q75": float(q75),
            "q95": float(q95),
            "q99": float(q99),
            "iqr": float(q75 - q25),
            "mad": float(absolute_deviation.median()),
            "delta_median": float(delta_median),
            "delta_iqr": float(delta_iqr),
            "delta_mad": float(delta_mad),
        }

    selected_metadata = {
        feature: dict(metadata_payload[feature]) for feature in normal.columns
    }
    return ReferenceProfile(
        feature_names=tuple(str(column) for column in normal.columns),
        statistics=statistics,
        feature_metadata=selected_metadata,
        training_rows=len(normal),
    )
