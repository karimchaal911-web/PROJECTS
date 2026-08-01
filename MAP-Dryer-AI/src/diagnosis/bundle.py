"""Versioned deployment metadata for detector-plus-diagnosis bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .reference_profile import ReferenceProfile


def save_diagnostic_bundle_metadata(
    path: str | Path,
    *,
    detector_name: str,
    detector_parameters: dict[str, Any],
    anomaly_threshold: float,
    model_features: list[str],
    reference_profile: ReferenceProfile,
    config_versions: dict[str, str],
    config_hashes: dict[str, str],
    diagnostic_version: str,
) -> Path:
    payload = {
        "bundle_schema": "map_dryer_diagnostic_bundle_v1.0",
        "detector": {
            "name": detector_name,
            "parameters": detector_parameters,
            "score_contract": "higher_is_more_abnormal",
            "anomaly_threshold": float(anomaly_threshold),
        },
        "model_features": list(model_features),
        "reference_profile": reference_profile.as_dict(),
        "diagnostic_version": diagnostic_version,
        "config_versions": dict(config_versions),
        "config_hashes_sha256": dict(config_hashes),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return target
