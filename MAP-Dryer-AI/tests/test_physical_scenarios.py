import unittest

from anomaly.scoring import canonical_anomaly_score
from diagnosis.engine import diagnose_anomaly
from diagnosis.scenarios import build_physical_scenarios
from tests._fixtures import build_fixture


class PhysicalScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normal, cls.configuration, cls.profile, cls.scaler, cls.model, cls.threshold = build_fixture()
        cls.scenarios = build_physical_scenarios(cls.profile)

    def diagnose(self, scenario_id):
        scenario = self.scenarios[scenario_id]
        score = float(
            canonical_anomaly_score(
                self.model, self.scaler.transform(scenario.current.to_frame().T)
            )[0]
        )
        self.assertGreaterEqual(score, self.threshold, f"{scenario_id} was not detected")
        event = diagnose_anomaly(
            timestamp=f"2026-01-01T{int(scenario_id[1:]):02d}:00:00",
            anomaly=True,
            anomaly_score=score,
            threshold=self.threshold,
            x_current=scenario.current,
            history_df=scenario.history,
            model=self.model,
            scaler=self.scaler,
            reference_profile=self.profile,
            feature_metadata=self.configuration["feature_metadata"],
            subsystem_config=self.configuration["subsystems"],
            rule_config=self.configuration["rules"],
            threshold_config=self.configuration["thresholds"],
            config_versions=self.configuration["versions"],
        )
        return scenario, event

    def test_all_scenarios_return_expected_rule(self):
        for scenario_id in sorted(self.scenarios):
            with self.subTest(scenario=scenario_id):
                scenario, event = self.diagnose(scenario_id)
                rule_ids = [result.rule_id for result in event.diagnoses]
                self.assertIn(scenario.expected_rule_id, rule_ids)

    def test_instrumentation_jump_outranks_process_failure(self):
        _, event = self.diagnose("S06")
        self.assertEqual(event.diagnoses[0].rule_id, "D06")

    def test_stuck_sensor_ranks_first(self):
        _, event = self.diagnose("S07")
        self.assertEqual(event.diagnoses[0].rule_id, "D07")


if __name__ == "__main__":
    unittest.main()
