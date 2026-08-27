"""Execute canonical Notebooks 01-04 sequentially and save outputs in place."""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    PROJECT_ROOT / "notebooks" / "01_Data_Exploration.ipynb",
    PROJECT_ROOT / "notebooks" / "02_Feature_Engineering.ipynb",
    PROJECT_ROOT / "notebooks" / "03_Model1_SoftSensor.ipynb",
    PROJECT_ROOT / "notebooks" / "04_Model2_AnomalyDetection&Diagnosis.ipynb",
]


def main() -> None:
    for path in NOTEBOOKS:
        print(f"Executing {path.relative_to(PROJECT_ROOT)}", flush=True)
        notebook = nbformat.read(path, as_version=4)
        executor = ExecutePreprocessor(timeout=3600, kernel_name="python3")
        executor.preprocess(
            notebook,
            {"metadata": {"path": str(PROJECT_ROOT)}},
        )
        nbformat.write(notebook, path)
        print(f"Saved {path.relative_to(PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
