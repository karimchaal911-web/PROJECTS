"""Shared MAP dryer feature names, units, and interpretation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


REQUIRED_FIELDS = {
    "display_name",
    "unit",
    "unit_status",
    "role",
    "interpretation",
}


def load_feature_catalog(path: str | Path) -> pd.DataFrame:
    """Load and validate the versioned YAML data dictionary."""

    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), dict):
        raise ValueError("The data dictionary must contain a features mapping.")

    rows = payload["features"]
    missing_fields = {
        feature: sorted(REQUIRED_FIELDS - set(details))
        for feature, details in rows.items()
        if REQUIRED_FIELDS - set(details)
    }
    if missing_fields:
        raise ValueError(f"Data-dictionary entries are incomplete: {missing_fields}")

    catalog = pd.DataFrame.from_dict(rows, orient="index")
    catalog.index.name = "feature"

    catalog.attrs["version"] = str(payload.get("version", "unversioned"))
    catalog.attrs["dataset_status"] = str(payload.get("dataset_status", "unknown"))
    catalog.attrs["unit_policy"] = str(payload.get("unit_policy", ""))
    return catalog


def select_feature_catalog(
    catalog: pd.DataFrame,
    features: Iterable[str],
) -> pd.DataFrame:
    """Return an ordered catalog view and reject undocumented features."""

    ordered = list(features)

    # If a requested feature is not present, allow ascii-subscripted names
    # (e.g., final_moisture_h2o) to map to the canonical unicode name
    # (final_moisture_h₂o) so notebooks that cleaned CSV headers work without
    # changing the canonical data dictionary.
    def _to_subscript(name: str) -> str:
        trans = str.maketrans({
            '0': '\u2080', '1': '\u2081', '2': '\u2082', '3': '\u2083',
            '4': '\u2084', '5': '\u2085', '6': '\u2086', '7': '\u2087',
            '8': '\u2088', '9': '\u2089'
        })
        return name.translate(trans)

    resolved = []
    missing = []
    for feature in ordered:
        if feature in catalog.index:
            resolved.append(feature)
        else:
            alt = _to_subscript(feature)
            if alt in catalog.index:
                resolved.append(alt)
            else:
                missing.append(feature)
    if missing:
        raise KeyError(f"Features missing from the data dictionary: {missing}")

    return catalog.loc[
        resolved,
        [
            "display_name",
            "unit",
            "unit_status",
            "role",
            "interpretation",
        ],
    ].copy()


def feature_axis_label(catalog: pd.DataFrame, feature: str) -> str:
    """Return a readable axis label containing the documented unit."""

    if feature not in catalog.index:
        raise KeyError(f"Feature missing from the data dictionary: {feature}")
    row = catalog.loc[feature]
    return f"{row['display_name']} ({row['unit']})"
