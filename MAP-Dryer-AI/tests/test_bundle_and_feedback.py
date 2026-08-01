import csv
import json
import tempfile
import unittest
from pathlib import Path

from diagnosis.bundle import save_diagnostic_bundle_metadata
from diagnosis.engine import diagnose_anomaly
from diagnosis.feedback import append_operator_feedback
from tests._fixtures import build_fixture


class BundleAndFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normal, cls.configuration, cls.profile, cls.scaler, cls.model, cls.threshold = build_fixture()

    def test_bundle_contains_versions_and_score_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            target = save_diagnostic_bundle_metadata(
                Path(directory) / "bundle.json",
                detector_name="One-Class SVM",
                detector_parameters={"gamma": "scale", "nu": 0.02},
                anomaly_threshold=self.threshold,
                model_features=list(self.normal.columns),
                reference_profile=self.profile,
                config_versions=self.configuration["versions"],
                config_hashes=self.configuration["hashes"],
                diagnostic_version="diag_v1.0",
            )
            payload = json.loads(target.read_text())
        self.assertEqual(payload["detector"]["score_contract"], "higher_is_more_abnormal")
        self.assertEqual(len(payload["config_versions"]), 4)

    def test_feedback_is_append_only_and_has_stable_columns(self):
        event = diagnose_anomaly(
            timestamp="2026-01-01T00:00:00",
            anomaly=False,
            anomaly_score=self.threshold - 0.1,
            threshold=self.threshold,
            x_current=None,
            history_df=None,
            model=object(),
            scaler=object(),
            reference_profile=self.profile,
            feature_metadata=self.configuration["feature_metadata"],
            subsystem_config=self.configuration["subsystems"],
            rule_config=self.configuration["rules"],
            threshold_config=self.configuration["thresholds"],
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "feedback.csv"
            append_operator_feedback(target, event, operator_status="UNKNOWN")
            append_operator_feedback(target, event, operator_status="REJECTED")
            with target.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["operator_status"], "UNKNOWN")
        self.assertEqual(rows[1]["operator_status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
