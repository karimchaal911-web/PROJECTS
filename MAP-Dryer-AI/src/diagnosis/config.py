"""Versioned configuration loading and validation for diagnosis."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml


CONFIG_FILENAMES = {
    "feature_metadata": "feature_metadata.yaml",
    "subsystems": "subsystems.yaml",
    "thresholds": "diagnostic_thresholds.yaml",
    "rules": "diagnosis_rules.yaml",
}


def load_yaml(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Diagnostic configuration not found: {source}")
    with source.open("r", encoding="utf-8") as stream:
        payload = yaml.safe_load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"Configuration must contain a mapping: {source}")
    if not payload.get("version"):
        raise ValueError(f"Configuration is missing a version: {source}")
    return payload


def load_diagnostic_configuration(config_dir: str | Path) -> dict[str, Any]:
    directory = Path(config_dir)
    configuration = {
        key: load_yaml(directory / filename)
        for key, filename in CONFIG_FILENAMES.items()
    }
    feature_names = set(configuration["feature_metadata"].get("features", {}))
    if not feature_names:
        raise ValueError("Feature metadata must define at least one feature.")

    subsystem_names = set(configuration["subsystems"].get("subsystems", {}))
    for feature, metadata in configuration["feature_metadata"]["features"].items():
        unknown = set(metadata.get("subsystems", [])) - subsystem_names
        if unknown:
            raise ValueError(
                f"Feature {feature} references unknown subsystems: {sorted(unknown)}"
            )

    rule_ids = [rule.get("id") for rule in configuration["rules"].get("rules", [])]
    if len(rule_ids) != len(set(rule_ids)) or any(not rule_id for rule_id in rule_ids):
        raise ValueError("Diagnostic rule IDs must be present and unique.")

    configuration["versions"] = {
        key: str(value["version"])
        for key, value in configuration.items()
        if key != "versions"
    }
    configuration["hashes"] = {
        key: hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        for key, filename in CONFIG_FILENAMES.items()
    }
    return configuration


def validate_model_features(
    model_features: list[str] | tuple[str, ...], feature_metadata: dict[str, Any]
) -> None:
    configured = list(feature_metadata.get("features", {}))
    expected = list(model_features)
    missing = sorted(set(expected) - set(configured))
    extra = sorted(set(configured) - set(expected))
    if missing or extra:
        raise ValueError(
            f"Feature metadata mismatch. Missing={missing}; unexpected={extra}."
        )
