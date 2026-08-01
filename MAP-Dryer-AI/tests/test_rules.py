import copy
import unittest

from diagnosis.rules import evaluate_diagnostic_rules
from diagnosis.schemas import FeatureEvidence, TemporalPattern
from tests._fixtures import build_fixture


def item(feature, direction, attribution=0.2):
    z = 3.0 if direction == "HIGH" else -3.0 if direction == "LOW" else 0.0
    return FeatureEvidence(
        feature=feature,
        direction=direction,
        current_value=1.0,
        reference_median=0.0,
        robust_z=z,
        robust_deviation=abs(z),
        counterfactual_contribution=attribution,
        attribution=attribution,
    )


class RuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.configuration, _, _, _, _ = build_fixture()

    def evaluate(self, evidence, patterns=(), rules=None):
        return evaluate_diagnostic_rules(
            evidence,
            patterns,
            {"drying_air_exhaust": 0.8, "thermal_system": 0.1, "instrumentation": 0.1},
            rules or self.configuration["rules"],
            self.configuration["thresholds"],
        )

    def test_d01_matches_airflow_pattern(self):
        results = self.evaluate(
            [
                item("air_flow_rate", "LOW"),
                item("air_per_feed", "LOW"),
                item("fan_speed", "LOW"),
            ]
        )
        self.assertEqual(results[0].rule_id, "D01")

    def test_contradiction_lowers_confidence(self):
        custom_rules = {
            "version": "test",
            "rules": [
                {
                    "id": "T01",
                    "subsystem": "drying_air_exhaust",
                    "diagnosis": "Test probable diagnosis",
                    "required": ["fan_speed:LOW"],
                    "supporting": [],
                    "contradictions": ["air_flow_rate:HIGH"],
                    "temporal": [],
                    "suspected_causes": [],
                    "recommended_checks": [],
                }
            ],
        }
        no_conflict = self.evaluate([item("fan_speed", "LOW")], rules=custom_rules)[0]
        conflict = self.evaluate(
            [item("fan_speed", "LOW"), item("air_flow_rate", "HIGH")],
            rules=custom_rules,
        )[0]
        self.assertLess(conflict.confidence, no_conflict.confidence)

    def test_instrumentation_guard_discounts_process_rule(self):
        pattern = TemporalPattern(
            feature="air_flow_rate",
            pattern="ISOLATED_JUMP",
            strength=1.0,
            direction="LOW",
            evidence="isolated",
            window_observations=6,
        )
        results = self.evaluate(
            [item("air_flow_rate", "LOW"), item("air_per_feed", "LOW")],
            [pattern],
        )
        d01 = next(result for result in results if result.rule_id == "D01")
        self.assertTrue(d01.instrumentation_discount_applied)


if __name__ == "__main__":
    unittest.main()
