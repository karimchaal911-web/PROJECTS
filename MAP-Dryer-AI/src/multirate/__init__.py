"""Multi-rate MAP dryer data handling.

The 5-second prototype datasets carry two asynchronous streams in one file:

* nine process variables sampled every 5 seconds, and
* three laboratory quality variables that only exist when a laboratory
  sample was analysed (about every two hours). Blank quality cells between
  samples are intentional structural missing values, never failures.

This package splits the raw file into an explicit process table and an
explicit laboratory table, aligns them for two different purposes
(dashboard display via a backward as-of join, model training via
residence-time-shifted process snapshots), and centralizes every engineered
feature formula used by both training and real-time inference.
"""

from multirate.preprocessing import (
    PROCESS_INTERVAL_SECONDS,
    PROCESS_VARIABLES,
    QUALITY_VARIABLES,
    RAW_SOURCE_COLUMNS,
    RAW_TO_SNAKE,
    ProcessTableReport,
    build_lab_table,
    build_process_table,
    build_timestamp,
    load_raw_source,
)
from multirate.alignment import (
    TrainingAlignmentResult,
    align_lab_for_dashboard,
    build_training_matrix,
    effective_window_end,
)
from multirate.instant_features import (
    INSTANT_ENGINEERED_FEATURES,
    PROCESS_MODEL_FEATURES,
    engineer_instant_features,
)
from multirate.window_features import (
    MOISTURE_FEATURE_NAMES,
    WINDOW_FEATURE_NAMES,
    compute_moisture_features,
    compute_window_features,
)

__all__ = [
    "PROCESS_INTERVAL_SECONDS",
    "PROCESS_VARIABLES",
    "QUALITY_VARIABLES",
    "RAW_SOURCE_COLUMNS",
    "RAW_TO_SNAKE",
    "ProcessTableReport",
    "TrainingAlignmentResult",
    "INSTANT_ENGINEERED_FEATURES",
    "PROCESS_MODEL_FEATURES",
    "MOISTURE_FEATURE_NAMES",
    "WINDOW_FEATURE_NAMES",
    "align_lab_for_dashboard",
    "build_lab_table",
    "build_process_table",
    "build_timestamp",
    "build_training_matrix",
    "compute_moisture_features",
    "compute_window_features",
    "effective_window_end",
    "engineer_instant_features",
    "load_raw_source",
]
