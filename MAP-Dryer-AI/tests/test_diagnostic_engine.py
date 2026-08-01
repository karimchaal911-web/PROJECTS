import json
import unittest

from anomaly.scoring import canonical_anomaly_score
from diagnosis.engine import diagnose_anomaly, format_operator_report
from diagnosis.scenarios import build_physical_scenarios
from tests._fixtures import build_fixture


class DiagnosticEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normal, cls.configuration, cls.profile, cls.scaler, cls.model, cls.threshold = build_fixture()
        cls.scenario = build_physical_scenarios(cls.profile)["S01"]

    def call(self, **overrides):
        current = self.scenario.current
        score = float(
            canonical_anomaly_score(
                self.model, self.scaler.transform(current.to_frame().T)
            )[0]
        )
        kwargs = dict(
            timestamp="2026-07-21T14:32:00",
            anomaly=True,
            anomaly_score=score,
            threshold=self.threshold,
            x_current=current,
            history_df=self.scenario.history,
            model=self.model,
            scaler=self.scaler,
            reference_profile=self.profile,
            feature_metadata=self.configuration["feature_metadata"],
            subsystem_config=self.configuration["subsystems"],
            rule_config=self.configuration["rules"],
            threshold_config=self.configuration["thresholds"],
            config_versions=self.configuration["versions"],
        )
        kwargs.update(overrides)
        return diagnose_anomaly(**kwargs)

    def test_normal_observation_bypasses_diagnosis(self):
        event = self.call(
            anomaly=False,
            x_current=None,
            history_df=None,
            model=object(),
            scaler=object(),
        )
        self.assertFalse(event.anomaly)
        self.assertEqual(event.primary_subsystem, "monitoring_only")
        self.assertFalse(event.diagnoses)

    def test_anomaly_event_is_deterministic_and_serializable(self):
        first = self.call()
        second = self.call()
        self.assertEqual(first.event_id, second.event_id)
        json.dumps(first.as_dict())
        self.assertEqual(first.diagnoses[0].rule_id, "D01")
        report = format_operator_report(first)
        self.assertIn("Probable diagnosis", report)
        self.assertNotIn("confirmed root cause", report.lower())


if __name__ == "__main__":
    unittest.main()
