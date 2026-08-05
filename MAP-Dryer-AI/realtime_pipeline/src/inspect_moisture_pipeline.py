from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Any

import joblib
import sklearn
from dotenv import load_dotenv
from sklearn.exceptions import InconsistentVersionWarning


# ================================================================
# CONFIGURATION
# ================================================================

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PIPELINE_ROOT / ".env"

load_dotenv(ENV_FILE)


# ================================================================
# ENVIRONMENT AND PATH HELPERS
# ================================================================

def require_env(name: str) -> str:
    """Return a required environment variable."""

    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing environment variable: {name}"
        )

    return value.strip()


def resolve_pipeline_path(environment_name: str) -> Path:
    """Resolve a path relative to the realtime_pipeline folder."""

    path = Path(
        require_env(environment_name)
    )

    if not path.is_absolute():
        path = PIPELINE_ROOT / path

    return path.resolve()


# ================================================================
# INSPECTION HELPERS
# ================================================================

def safe_attribute(
    object_value: Any,
    attribute_name: str,
) -> Any:
    """Read an attribute without failing."""

    try:
        return getattr(
            object_value,
            attribute_name,
        )
    except Exception:
        return None


def print_feature_names(
    title: str,
    feature_names: Any,
) -> None:
    """Print an ordered feature-name collection."""

    if feature_names is None:
        print(f"{title}: NOT STORED")
        return

    feature_list = list(feature_names)

    print(f"{title}: {len(feature_list)}")

    for index, feature_name in enumerate(
        feature_list,
        start=1,
    ):
        print(
            f"  {index:02d}. {feature_name!r}"
        )


def inspect_pipeline_steps(model: Any) -> None:
    """Inspect sklearn Pipeline steps when present."""

    named_steps = safe_attribute(
        model,
        "named_steps",
    )

    if not named_steps:
        print("\nPipeline steps: NOT AVAILABLE")
        return

    print("\nPipeline steps:")

    for step_name, step_object in named_steps.items():
        print(
            f"- {step_name}: "
            f"{type(step_object).__module__}."
            f"{type(step_object).__name__}"
        )

        step_features = safe_attribute(
            step_object,
            "feature_names_in_",
        )

        if step_features is not None:
            print_feature_names(
                f"  {step_name} feature names",
                step_features,
            )

        step_count = safe_attribute(
            step_object,
            "n_features_in_",
        )

        if step_count is not None:
            print(
                f"  {step_name} n_features_in_: "
                f"{step_count}"
            )


# ================================================================
# MAIN INSPECTION
# ================================================================

def inspect_moisture_pipeline() -> None:
    model_path = resolve_pipeline_path(
        "MOISTURE_MODEL"
    )

    print("MOISTURE PIPELINE INSPECTION")
    print("=" * 72)
    print(
        "Current scikit-learn version:",
        sklearn.__version__,
    )
    print("Artifact path:", model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Moisture artifact not found:\n{model_path}"
        )

    captured_version_warning = None

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter(
            "always",
            InconsistentVersionWarning,
        )

        moisture_pipeline = joblib.load(
            model_path
        )

        for warning in captured:
            if isinstance(
                warning.message,
                InconsistentVersionWarning,
            ):
                captured_version_warning = (
                    warning.message
                )

    print(
        "\nArtifact type:",
        f"{type(moisture_pipeline).__module__}."
        f"{type(moisture_pipeline).__name__}",
    )

    if captured_version_warning is None:
        print(
            "Version compatibility warning: NONE"
        )
    else:
        training_version = getattr(
            captured_version_warning,
            "original_sklearn_version",
            "UNKNOWN",
        )

        print(
            "Model training scikit-learn version:",
            training_version,
        )

        print(
            "WARNING: deployment and training versions "
            "must match."
        )

    top_level_features = safe_attribute(
        moisture_pipeline,
        "feature_names_in_",
    )

    top_level_count = safe_attribute(
        moisture_pipeline,
        "n_features_in_",
    )

    print_feature_names(
        "\nTop-level expected features",
        top_level_features,
    )

    print(
        "Top-level n_features_in_:",
        top_level_count
        if top_level_count is not None
        else "NOT STORED",
    )

    inspect_pipeline_steps(
        moisture_pipeline
    )

    final_estimator = safe_attribute(
        moisture_pipeline,
        "_final_estimator",
    )

    if final_estimator is not None:
        print(
            "\nFinal estimator:",
            f"{type(final_estimator).__module__}."
            f"{type(final_estimator).__name__}",
        )

        final_features = safe_attribute(
            final_estimator,
            "feature_names_in_",
        )

        print_feature_names(
            "Final-estimator expected features",
            final_features,
        )

        final_count = safe_attribute(
            final_estimator,
            "n_features_in_",
        )

        print(
            "Final-estimator n_features_in_:",
            final_count
            if final_count is not None
            else "NOT STORED",
        )

    if not hasattr(
        moisture_pipeline,
        "predict",
    ):
        raise TypeError(
            "The moisture artifact has no predict() method."
        )

    forbidden_names = {
        "Final Moisture (%H2O)",
        "final_moisture",
        "final_moisture_pct",
        "reference_final_moisture",
    }

    if top_level_features is not None:
        feature_strings = {
            str(feature)
            for feature in top_level_features
        }

        forbidden_present = (
            feature_strings
            & forbidden_names
        )

        if forbidden_present:
            raise ValueError(
                "DATA LEAKAGE DETECTED: the moisture target "
                "appears among model inputs:\n"
                f"{sorted(forbidden_present)}"
            )

    print("\nMoisture predict() method: AVAILABLE")
    print(
        "Target leakage check:",
        "PASS"
        if top_level_features is not None
        else "MANUAL VERIFICATION REQUIRED",
    )

    print("\nMOISTURE PIPELINE INSPECTION: SUCCESS")


if __name__ == "__main__":
    try:
        inspect_moisture_pipeline()

    except Exception as error:
        print(
            "\nMOISTURE PIPELINE INSPECTION: FAILED",
            file=sys.stderr,
        )

        print(
            repr(error),
            file=sys.stderr,
        )

        sys.exit(1)