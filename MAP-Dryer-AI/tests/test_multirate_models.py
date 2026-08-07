"""Model and inference-service tests for the 5-second prototype."""

import importlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from multirate.instant_features import (
    PROCESS_MODEL_FEATURES,
    engineer_instant_features,
)
from multirate.preprocessing import PROCESS_VARIABLES, build_process_table
from multirate.window_features import (
    WINDOW_FEATURE_NAMES,
    compute_window_features,
)
from tests.test_multirate_preprocessing import make_raw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_5S = PROJECT_ROOT / "models" / "5s"
TOOLS_DIR = PROJECT_ROOT / "tools"


def make_window(n_rows=360, seed=23) -> pd.DataFrame:
    raw = make_raw(n_rows=n_rows, lab_every=n_rows * 2, seed=seed)
    process, _ = build_process_table(raw)
    return process[["Timestamp", *PROCESS_VARIABLES]]


class WindowFeatureContractTests(unittest.TestCase):
    def test_training_feature_schema_equals_inference_schema(self):
        features = compute_window_features(make_window())
        self.assertEqual(list(features.keys()), WINDOW_FEATURE_NAMES)
        self.assertTrue(np.isfinite(list(features.values())).all())

    def test_unsorted_window_is_rejected(self):
        window = make_window().iloc[::-1].reset_index(drop=True)
        with self.assertRaisesRegex(ValueError, "chronologically"):
            compute_window_features(window)

    def test_missing_column_is_rejected(self):
        window = make_window().drop(columns=["Steam Pressure"])
        with self.assertRaisesRegex(ValueError, "Steam Pressure"):
            compute_window_features(window)

    def test_missing_values_are_rejected(self):
        window = make_window()
        window.loc[5, "Vacuum"] = np.nan
        with self.assertRaisesRegex(ValueError, "Vacuum"):
            compute_window_features(window)

    def test_empty_window_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_window_features(make_window().iloc[:0])


class InstantFeatureTests(unittest.TestCase):
    def test_instant_features_do_not_need_laboratory_values(self):
        window = make_window(n_rows=3)
        features = engineer_instant_features(window[PROCESS_VARIABLES])
        self.assertEqual(list(features.columns), PROCESS_MODEL_FEATURES)

    def test_invalid_schema_is_rejected_clearly(self):
        window = make_window(n_rows=3)
        with self.assertRaisesRegex(ValueError, "Missing process variables"):
            engineer_instant_features(
                window[PROCESS_VARIABLES].drop(columns=["Fan Speed"])
            )

    def test_non_finite_input_is_rejected(self):
        frame = make_window(n_rows=3)[PROCESS_VARIABLES].copy()
        frame.loc[1, "Steam Pressure"] = np.nan
        with self.assertRaises(ValueError):
            engineer_instant_features(frame)


class ChronologicalSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        cls.train_module = importlib.import_module("train_5s_models")

    def test_split_is_chronological_and_disjoint(self):
        train, validation, test = self.train_module.chronological_split(100)
        self.assertEqual(train, slice(0, 70))
        self.assertEqual(validation, slice(70, 85))
        self.assertEqual(test, slice(85, 100))

    def test_metrics_are_finite(self):
        actual = np.array([1.0, 2.0, 3.0, 4.0])
        predicted = np.array([1.1, 1.9, 3.2, 3.8])
        metrics = self.train_module.evaluation_metrics(actual, predicted)
        for key in ("mae", "rmse", "r2", "bias", "max_abs_error"):
            self.assertTrue(np.isfinite(metrics[key]), key)


@unittest.skipUnless(
    (MODELS_5S / "feature_schema.json").exists(),
    "models/5s artifacts not trained yet (run tools/train_5s_models.py)",
)
class SavedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import joblib

        with (MODELS_5S / "feature_schema.json").open(
            encoding="utf-8"
        ) as file:
            cls.schema = json.load(file)
        cls.moisture = joblib.load(
            MODELS_5S / "quality_moisture_pipeline.joblib"
        )
        cls.anomaly_model = joblib.load(MODELS_5S / "anomaly_model.joblib")
        cls.anomaly_scaler = joblib.load(MODELS_5S / "anomaly_scaler.joblib")

    def test_saved_schema_matches_current_feature_code(self):
        self.assertEqual(
            self.schema["window_feature_names"], WINDOW_FEATURE_NAMES
        )
        self.assertEqual(
            self.schema["process_model_features"], PROCESS_MODEL_FEATURES
        )
        self.assertEqual(self.schema["process_interval_seconds"], 5)

    def test_versions_are_recorded(self):
        self.assertTrue(self.schema["model_version"])
        self.assertTrue(self.schema["feature_schema_version"])

    def test_reloaded_quality_pipeline_predicts_a_valid_row(self):
        features = compute_window_features(make_window())
        frame = pd.DataFrame([features], columns=WINDOW_FEATURE_NAMES)
        prediction = float(self.moisture.predict(frame)[0])
        self.assertTrue(np.isfinite(prediction))

    def test_anomaly_inference_works_without_laboratory_values(self):
        window = make_window(n_rows=4)
        instant = engineer_instant_features(window[PROCESS_VARIABLES])
        scaled = self.anomaly_scaler.transform(instant)
        scores = self.anomaly_model.decision_function(scaled)
        labels = self.anomaly_model.predict(scaled)
        self.assertTrue(np.isfinite(scores).all())
        self.assertTrue(set(labels).issubset({-1, 1}))

    def test_training_report_metrics_are_finite(self):
        with (MODELS_5S / "training_report.json").open(
            encoding="utf-8"
        ) as file:
            report = json.load(file)
        for target in ("moisture", "density", "product_temp"):
            test_metrics = report["quality"][target]["test"]
            for key in ("mae", "rmse", "r2", "bias", "max_abs_error"):
                self.assertTrue(
                    np.isfinite(test_metrics[key]), f"{target}.{key}"
                )


class RealtimeServiceHelperTests(unittest.TestCase):
    """Pure-Python behavior of the 5-second service (no database)."""

    @classmethod
    def setUpClass(cls):
        pipeline_src = PROJECT_ROOT / "realtime_pipeline" / "src"
        if str(pipeline_src) not in sys.path:
            sys.path.insert(0, str(pipeline_src))
        cls.service = importlib.import_module("realtime_service")

    def _artifacts_stub(self, prediction=1.83):
        class _Pipe:
            def predict(self, frame):
                return np.array([prediction])

        return self.service.Artifacts(
            moisture_pipeline=_Pipe(),
            anomaly_model=None,
            anomaly_scaler=None,
            reference_profile={},
            feature_schema={
                "model_version": "test",
                "feature_schema_version": "test",
                "quality_window_minutes": 10.0,
                "anomaly_risk_calibration": {"score_scale": 1.0},
            },
        )

    def test_prediction_produced_for_a_valid_row_with_history(self):
        buffer = make_window(n_rows=720)  # 60 min of 5-second history
        row_timestamp = buffer["Timestamp"].iloc[-1]
        quality = self.service.predict_moisture(
            buffer, row_timestamp, self._artifacts_stub(), 0.0
        )
        self.assertIsNone(quality.reason)
        self.assertAlmostEqual(quality.predicted_moisture, 1.83)

    def test_insufficient_history_yields_no_prediction_with_reason(self):
        buffer = make_window(n_rows=60)  # only 5 minutes of history
        row_timestamp = buffer["Timestamp"].iloc[-1]
        quality = self.service.predict_moisture(
            buffer, row_timestamp, self._artifacts_stub(), 0.0
        )
        self.assertIsNone(quality.predicted_moisture)
        self.assertIn("insufficient process history", quality.reason)

    def test_missing_residence_time_rejects_the_row(self):
        buffer = make_window(n_rows=720).copy()
        buffer.loc[buffer.index[-1], "Residence Time"] = np.nan
        row_timestamp = buffer["Timestamp"].iloc[-1]
        quality = self.service.predict_moisture(
            buffer, row_timestamp, self._artifacts_stub(), 0.0
        )
        self.assertIsNone(quality.predicted_moisture)
        self.assertEqual(quality.reason, "residence time missing")

    def test_anomaly_risk_calibration_maps_boundary_to_half(self):
        self.assertAlmostEqual(
            self.service.anomaly_risk_from_score(0.0, 1.0), 0.5
        )
        self.assertLess(self.service.anomaly_risk_from_score(3.0, 1.0), 0.1)
        self.assertGreater(
            self.service.anomaly_risk_from_score(-3.0, 1.0), 0.9
        )

    def test_resume_position_processes_each_timestamp_exactly_once(self):
        source = make_window(n_rows=100)
        latest_processed = source["Timestamp"].iloc[41]
        next_position = int(
            source["Timestamp"].searchsorted(latest_processed, side="right")
        )
        self.assertEqual(next_position, 42)
        # Replaying from the resume point never repeats a timestamp.
        replayed = source["Timestamp"].iloc[next_position:]
        self.assertTrue((replayed > latest_processed).all())
        self.assertEqual(
            len(replayed) + next_position, len(source)
        )


if __name__ == "__main__":
    unittest.main()
