"""Explainable diagnostic layer for MAP dryer anomaly events."""

from .attribution import localize_anomaly
from .config import load_diagnostic_configuration
from .engine import diagnose_anomaly, format_operator_report
from .reference_profile import build_reference_profile
from .rules import evaluate_diagnostic_rules
from .subsystems import score_subsystems
from .temporal import analyze_temporal_patterns

__all__ = [
    "analyze_temporal_patterns",
    "build_reference_profile",
    "diagnose_anomaly",
    "evaluate_diagnostic_rules",
    "format_operator_report",
    "load_diagnostic_configuration",
    "localize_anomaly",
    "score_subsystems",
]
