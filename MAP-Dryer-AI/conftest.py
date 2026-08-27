"""Pytest path setup: make src/ and the pipeline scripts importable."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for entry in (ROOT, ROOT / "src", ROOT / "realtime_pipeline" / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
