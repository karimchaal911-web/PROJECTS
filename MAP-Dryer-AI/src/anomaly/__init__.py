"""Reusable anomaly detection, threshold, persistence, and alarm helpers."""

from .alarms import attach_pcs7_hybrid_alarm_state, evaluate_pcs7_limits
from .evaluation import detector_comparison_row
from .persistence import apply_persistence_logic
from .preprocessing import build_scaled_feature_table
from .scenarios import build_synthetic_validation_scenario
from .scoring import build_anomaly_score_table, canonical_anomaly_score, is_anomaly
from .thresholds import calibrate_conformal_threshold, candidate_rate

__all__ = [
    "apply_persistence_logic",
    "attach_pcs7_hybrid_alarm_state",
    "build_anomaly_score_table",
    "build_scaled_feature_table",
    "build_synthetic_validation_scenario",
    "calibrate_conformal_threshold",
    "candidate_rate",
    "canonical_anomaly_score",
    "detector_comparison_row",
    "evaluate_pcs7_limits",
    "is_anomaly",
]
