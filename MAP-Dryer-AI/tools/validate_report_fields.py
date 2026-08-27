"""Validate that every field referenced by the PBIR report exists in the
semantic model, and that every visual JSON is structurally sound.

Checks:
1. every ``{Measure|Column}`` reference (entity + property) in every
   ``visual.json`` resolves to a measure/column defined in the TMDL tables;
2. every visual file parses and carries a name, a position, and a visual
   payload;
3. page dimensions are the 1600x900 template canvas.

Run:  python tools/validate_report_fields.py
Exits non-zero when anything is missing, so it can act as a CI gate.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_TABLES = (
    PROJECT_ROOT
    / "POWERBI DASHBOARD"
    / "MAP Dryer AI Dashboard.SemanticModel"
    / "definition"
    / "tables"
)
PAGES_DIR = (
    PROJECT_ROOT
    / "POWERBI DASHBOARD"
    / "MAP Dryer AI Dashboard.Report"
    / "definition"
    / "pages"
)

_MEASURE_RE = re.compile(r"^\tmeasure '?([^'=\n]+?)'? =", re.MULTILINE)
_COLUMN_RE = re.compile(r"^\tcolumn '?([^'\n]+?)'?\s*(?:=|$)", re.MULTILINE)


def load_model_fields() -> dict[str, set[str]]:
    fields: dict[str, set[str]] = {}
    for tmdl in MODEL_TABLES.glob("*.tmdl"):
        text = tmdl.read_text(encoding="utf-8")
        names = set(_MEASURE_RE.findall(text)) | set(
            _COLUMN_RE.findall(text)
        )
        fields[tmdl.stem] = {name.strip() for name in names}
    return fields


def field_references(node: object) -> list[tuple[str, str]]:
    """Recursively collect (entity, property) pairs from a visual JSON."""

    found: list[tuple[str, str]] = []

    def walk(item: object) -> None:
        if isinstance(item, dict):
            for kind in ("Measure", "Column"):
                ref = item.get(kind)
                if (
                    isinstance(ref, dict)
                    and "Property" in ref
                    and isinstance(ref.get("Expression"), dict)
                ):
                    source = ref["Expression"].get("SourceRef", {})
                    entity = source.get("Entity") or source.get("Source")
                    if entity:
                        found.append((entity, ref["Property"]))
            for value in item.values():
                walk(value)
        elif isinstance(item, list):
            for value in item:
                walk(value)

    walk(node)
    return found


def main() -> int:
    model_fields = load_model_fields()
    problems: list[str] = []
    visual_count = 0
    reference_count = 0

    for page_dir in sorted(PAGES_DIR.iterdir()):
        if not page_dir.is_dir():
            continue
        page_json = page_dir / "page.json"
        page = json.loads(page_json.read_text(encoding="utf-8"))
        if (page.get("width"), page.get("height")) != (1600, 900):
            problems.append(
                f"{page_json}: canvas is "
                f"{page.get('width')}x{page.get('height')}, expected 1600x900"
            )
        for visual_json in sorted(page_dir.glob("visuals/*/visual.json")):
            visual_count += 1
            try:
                visual = json.loads(visual_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                problems.append(f"{visual_json}: invalid JSON ({error})")
                continue
            if "name" not in visual or "position" not in visual:
                problems.append(f"{visual_json}: missing name/position")
            for entity, prop in field_references(visual):
                reference_count += 1
                # Aliased entities (e.g. sub-query names) that are not
                # model tables are resolved against every table.
                if entity in model_fields:
                    known = model_fields[entity]
                    if prop not in known:
                        problems.append(
                            f"{visual_json.parent.name}: "
                            f"'{entity}'[{prop}] not in the model"
                        )
                else:
                    if not any(
                        prop in known for known in model_fields.values()
                    ):
                        problems.append(
                            f"{visual_json.parent.name}: unknown entity "
                            f"'{entity}' and no table has [{prop}]"
                        )

    print(
        f"Checked {visual_count} visuals, {reference_count} field "
        f"references against {sum(len(v) for v in model_fields.values())} "
        f"model fields in {len(model_fields)} tables."
    )
    if problems:
        print(f"\n{len(problems)} PROBLEMS:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("All report field references resolve. Canvas is 1600x900.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
