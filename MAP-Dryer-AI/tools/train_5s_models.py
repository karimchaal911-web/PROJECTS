"""Run the active canonical 92-day training pipeline outside Jupyter.

Notebook 03 calls the same implementation, so this command cannot create a
separate runtime model or revert to the deprecated 101/103-feature contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from canonical_pipeline import (  # noqa: E402
    audit_canonical_dataset,
    build_feature_handoff,
    train_anomaly_and_diagnosis,
    train_final_model,
    validate_runtime_contract,
)


TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15


def chronological_split(n_rows: int) -> tuple[slice, slice, slice]:
    """Return the project's chronological 70/15/15 split slices."""
    train_end = int(round(n_rows * TRAIN_FRACTION))
    validation_end = int(
        round(n_rows * (TRAIN_FRACTION + VALIDATION_FRACTION))
    )
    return (
        slice(0, train_end),
        slice(train_end, validation_end),
        slice(validation_end, n_rows),
    )


def evaluation_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Compute the finite regression metrics used by legacy 5-second tests."""
    actual_values = np.asarray(actual, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    residuals = predicted_values - actual_values
    denominator = max(
        float(np.sum((actual_values - np.mean(actual_values)) ** 2)), 1e-12
    )
    return {
        "mae": float(np.mean(np.abs(residuals))),
        "rmse": float(np.sqrt(np.mean(residuals**2))),
        "r2": float(1.0 - np.sum(residuals**2) / denominator),
        "bias": float(np.mean(residuals)),
        "max_abs_error": float(np.max(np.abs(residuals))),
        "n": int(len(actual_values)),
    }


def main() -> None:
    audit = audit_canonical_dataset()
    _, handoff = build_feature_handoff()
    _, evaluation = train_final_model()
    anomaly = train_anomaly_and_diagnosis()
    checks = validate_runtime_contract()
    print(f"Process rows: {audit['process_rows']:,}")
    print(f"Laboratory samples: {audit['laboratory_samples']:,}")
    print(f"Supervised rows: {handoff['supervised_rows']:,}")
    print(f"Selected model: {evaluation['selected_model']}")
    print(f"Feature count: {evaluation['feature_count']}")
    print(f"TEST metrics: {evaluation['metrics']['test']}")
    print(f"Anomaly model: {anomaly['selected_model']}")
    print(f"Anomaly feature count: {anomaly['feature_count']}")
    print(f"Runtime checks: {checks}")


if __name__ == "__main__":
    main()
