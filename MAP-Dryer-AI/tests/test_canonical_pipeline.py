import json
import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
for entry in (PROJECT_ROOT / "src", PROJECT_ROOT / "realtime_pipeline" / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from canonical_pipeline import (  # noqa: E402
    AUDIT_PATH,
    ANOMALY_EVALUATION_PATH,
    EVALUATION_PATH,
    FEATURE_SCHEMA_PATH,
    HANDOFF_PATH,
    MODEL_REGISTRY_PATH,
    MOISTURE_FEATURE_NAMES,
    MOISTURE_MODEL_PATH,
    TEST_REPLAY_PATH,
    validate_runtime_contract,
)
from multirate import PROCESS_VARIABLES, QUALITY_VARIABLES  # noqa: E402
from realtime_service import load_artifacts, predict_moisture  # noqa: E402


class CanonicalPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.handoff = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
        cls.evaluation = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))
        cls.anomaly_evaluation = json.loads(
            ANOMALY_EVALUATION_PATH.read_text(encoding="utf-8")
        )
        cls.schema = json.loads(FEATURE_SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.registry = json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_dataset_and_multirate_contract(self):
        self.assertEqual(self.audit["duration_days"], 92.0)
        self.assertEqual(self.audit["process_rows"], 1_589_760)
        self.assertEqual(self.audit["laboratory_samples"], 1_104)
        self.assertEqual(self.audit["laboratory_interval_minutes"], 120)
        self.assertTrue(all(self.audit["checks"].values()))

    def test_final_feature_contract_is_exactly_16_original_features(self):
        self.assertEqual(self.handoff["feature_count"], 16)
        self.assertEqual(self.handoff["feature_names"], MOISTURE_FEATURE_NAMES)
        self.assertEqual(
            self.handoff["quality_fields_used_as_model_inputs"],
            ["product_density", "final_product_temp"],
        )
        self.assertEqual(
            self.handoff["quality_input_causality"],
            "most recent strictly previous laboratory sample",
        )
        self.assertEqual(self.schema["expected_feature_count"], 16)

    def test_split_is_chronological_and_complete(self):
        split = self.evaluation["split"]
        self.assertEqual(split["strategy"], "chronological TRAIN -> VALIDATION -> TEST")
        self.assertEqual(
            split["train"]["rows"]
            + split["validation"]["rows"]
            + split["test"]["rows"],
            self.evaluation["supervised_rows"],
        )
        self.assertLess(split["train"]["end_timestamp"], split["validation"]["start_timestamp"])
        self.assertLess(split["validation"]["end_timestamp"], split["test"]["start_timestamp"])
        self.assertTrue(split["time_series_cross_validation"]["used"])

    def test_runtime_loads_exact_notebook03_and_notebook04_artifacts(self):
        checks = validate_runtime_contract()
        self.assertTrue(all(checks.values()))
        self.assertTrue(MOISTURE_MODEL_PATH.exists())
        self.assertTrue(self.registry["models"][0]["runtime_uses_exact_notebook03_artifact"])
        self.assertTrue(
            self.anomaly_evaluation["runtime_loads_exact_notebook04_artifacts"]
        )
        self.assertEqual(
            self.anomaly_evaluation["depends_on"],
            "artifacts\\notebook03_model_evaluation.json",
        )

    def test_held_out_replay_and_one_runtime_prediction(self):
        preview = pd.read_csv(TEST_REPLAY_PATH, nrows=1_500)
        self.assertTrue((preview["Replay Partition"] == "test").all())
        timestamps = pd.to_datetime(
            preview["Date"] + " " + preview["Time"],
            format="%Y-%m-%d %H:%M:%S",
        )
        preview.insert(0, "Timestamp", timestamps)
        artifacts = load_artifacts(PROJECT_ROOT / "models" / "5s")
        buffer = preview.loc[
            :, ["Timestamp", *PROCESS_VARIABLES, *QUALITY_VARIABLES]
        ]
        prediction = predict_moisture(
            buffer,
            buffer["Timestamp"].iloc[-1],
            artifacts,
            transport_delay_minutes=0.0,
        )
        self.assertIsNone(prediction.reason)
        self.assertIsNotNone(prediction.predicted_moisture)


if __name__ == "__main__":
    unittest.main()
