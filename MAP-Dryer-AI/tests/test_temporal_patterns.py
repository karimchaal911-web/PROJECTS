import unittest

from diagnosis.scenarios import build_physical_scenarios
from diagnosis.temporal import analyze_temporal_patterns
from tests._fixtures import build_fixture


class TemporalPatternTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.configuration, cls.profile, _, _, _ = build_fixture()
        cls.scenarios = build_physical_scenarios(cls.profile)

    def patterns_for(self, scenario_id):
        return analyze_temporal_patterns(
            self.scenarios[scenario_id].history,
            self.profile,
            self.configuration["thresholds"],
        )

    def test_airflow_loss_has_drop_or_drift(self):
        patterns = self.patterns_for("S01")
        labels = {(item.feature, item.pattern) for item in patterns}
        self.assertTrue(
            ("air_flow_rate", "SUDDEN_DROP") in labels
            or ("air_flow_rate", "DRIFT") in labels
        )

    def test_sensor_jump_is_isolated(self):
        patterns = self.patterns_for("S06")
        labels = {(item.feature, item.pattern) for item in patterns}
        self.assertIn(("dryer_air_temperature", "ISOLATED_JUMP"), labels)

    def test_stuck_sensor_is_detected(self):
        patterns = self.patterns_for("S07")
        labels = {(item.feature, item.pattern) for item in patterns}
        self.assertIn(("fan_speed", "STUCK"), labels)

    def test_oscillation_is_detected(self):
        patterns = self.patterns_for("S08")
        self.assertTrue(any(item.pattern == "OSCILLATION" for item in patterns))


if __name__ == "__main__":
    unittest.main()
