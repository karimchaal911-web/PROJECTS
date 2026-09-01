"""Restore the canonical 92-day dataset from its versioned XZ archive.

The canonical CSV is 235 MB, which exceeds GitHub's 100 MB per-file limit, so
the repository ships `data/raw/MAP_Dryer_Canonical_5s_deterministic.csv.xz`
(≈40 MB) instead. This script expands it and verifies the result against the
SHA-256 recorded in `data/processed/MAP_Dryer_Canonical_5s.manifest.json`.

The dataset is user-supplied and deterministic: nothing in this repository can
regenerate it, so the archive is the project's only copy of record.

Two paths are written because both are referenced by code and they hold
identical bytes:

    data/raw/MAP_Dryer_Canonical_5s_deterministic.csv   supplied source of record
    data/processed/MAP_Dryer_Canonical_5s.csv           canonical analytical path

Usage:

    python tools/restore_canonical_dataset.py           # expand if missing
    python tools/restore_canonical_dataset.py --force   # expand even if present
    python tools/restore_canonical_dataset.py --check   # verify only, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "MAP_Dryer_Canonical_5s_deterministic.csv.xz"
)
RAW_CSV = ARCHIVE.with_suffix("")
PROCESSED_CSV = (
    PROJECT_ROOT / "data" / "processed" / "MAP_Dryer_Canonical_5s.csv"
)
MANIFEST = PROCESSED_CSV.with_suffix(".manifest.json")

CHUNK = 1 << 22


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_sha256() -> str:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Canonical manifest not found: {MANIFEST}")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["dataset_sha256"]


def expand(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(ARCHIVE, "rb") as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target, CHUNK)


def report(path: Path, expected: str) -> bool:
    if not path.exists():
        print(f"  MISSING  {path.relative_to(PROJECT_ROOT)}")
        return False
    actual = sha256_file(path)
    ok = actual == expected
    size_mb = path.stat().st_size / 1048576
    print(
        f"  {'OK      ' if ok else 'MISMATCH'} "
        f"{path.relative_to(PROJECT_ROOT)}  ({size_mb:.1f} MB)"
    )
    if not ok:
        print(f"           expected {expected}\n           actual   {actual}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="expand even if the CSV already exists",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify existing files only; write nothing",
    )
    args = parser.parse_args()

    expected = expected_sha256()
    targets = (RAW_CSV, PROCESSED_CSV)

    if args.check:
        print("Verifying canonical dataset against the manifest:")
        return 0 if all(report(path, expected) for path in targets) else 1

    if not ARCHIVE.exists():
        print(f"Archive not found: {ARCHIVE}", file=sys.stderr)
        return 1

    for path in targets:
        if path.exists() and not args.force:
            print(f"  present, skipping  {path.relative_to(PROJECT_ROOT)}")
            continue
        print(f"  expanding -> {path.relative_to(PROJECT_ROOT)} ...", flush=True)
        expand(path)

    print("Verifying against the manifest:")
    if not all(report(path, expected) for path in targets):
        print(
            "Restored dataset does not match the manifest hash.",
            file=sys.stderr,
        )
        return 1
    print("Canonical dataset restored and verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
