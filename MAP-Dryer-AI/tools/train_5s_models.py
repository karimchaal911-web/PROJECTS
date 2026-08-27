"""Run the active canonical 92-day training pipeline outside Jupyter.

Notebook 03 calls the same implementation, so this command cannot create a
separate runtime model or revert to the deprecated 101/103-feature contract.
"""

from __future__ import annotations

import sys
from pathlib import Path


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
