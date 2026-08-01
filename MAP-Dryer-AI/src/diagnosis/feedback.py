"""Append-only operator feedback records for future supervised learning."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .schemas import DiagnosticEvent


FEEDBACK_COLUMNS = [
    "event_id",
    "timestamp",
    "model_anomaly_score",
    "predicted_subsystem",
    "predicted_diagnosis",
    "predicted_confidence",
    "operator_status",
    "confirmed_fault_category",
    "confirmed_root_cause",
    "maintenance_action",
    "process_action",
    "quality_impact",
    "lab_moisture_after_event",
    "notes",
]


def append_operator_feedback(
    path: str | Path,
    event: DiagnosticEvent,
    *,
    operator_status: str,
    confirmed_fault_category: str | None = None,
    confirmed_root_cause: str | None = None,
    maintenance_action: str | None = None,
    process_action: str | None = None,
    quality_impact: str | None = None,
    lab_moisture_after_event: float | None = None,
    notes: str | None = None,
) -> Path:
    status = operator_status.upper()
    if status not in {"CONFIRMED", "REJECTED", "UNKNOWN"}:
        raise ValueError("operator_status must be CONFIRMED, REJECTED, or UNKNOWN.")
    primary = event.diagnoses[0] if event.diagnoses else None
    row: dict[str, Any] = {
        "event_id": event.event_id,
        "timestamp": event.as_dict()["timestamp"],
        "model_anomaly_score": event.anomaly_score,
        "predicted_subsystem": event.primary_subsystem,
        "predicted_diagnosis": primary.diagnosis if primary else None,
        "predicted_confidence": primary.confidence if primary else None,
        "operator_status": status,
        "confirmed_fault_category": confirmed_fault_category,
        "confirmed_root_cause": confirmed_root_cause,
        "maintenance_action": maintenance_action,
        "process_action": process_action,
        "quality_impact": quality_impact,
        "lab_moisture_after_event": lab_moisture_after_event,
        "notes": notes,
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_header = not target.exists()
    with target.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FEEDBACK_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return target
