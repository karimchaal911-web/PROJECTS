import unittest

from diagnosis.schemas import FeatureEvidence, TemporalPattern
from diagnosis.subsystems import score_subsystems
from tests._fixtures import build_fixture


def evidence(feature, attribution, subsystems):
    return FeatureEvidence(
        feature=feature,
        direction="LOW",
        current_value=0.0,
        reference_median=1.0,
        robust_z=-3.0,
        robust_deviation=3.0,
        counterfactual_contribution=attribution,
        attribution=attribution,
        subsystems=tuple(subsystems),
    )


class SubsystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.configuration, _, _, _, _ = build_fixture()

    def test_feature_memberships_are_not_double_counted(self):
        scores = score_subsystems(
            [
                evidence("air_flow_rate", 0.60, ["drying_air_exhaust"]),
                evidence("air_per_feed", 0.40, ["drying_air_exhaust", "feed_loading"]),
            ],
            self.configuration["subsystems"],
        )
        self.assertAlmostEqual(sum(scores.values()), 1.0)
        self.assertGreater(scores["drying_air_exhaust"], scores["feed_loading"])

    def test_instrumentation_pattern_adds_instrumentation_evidence(self):
        pattern = TemporalPattern(
            feature="fan_speed",
            pattern="STUCK",
            strength=1.0,
            direction="UNCHANGED",
            evidence="test",
            window_observations=6,
        )
        scores = score_subsystems(
            [evidence("fan_speed", 1.0, ["drying_air_exhaust"])],
            self.configuration["subsystems"],
            [pattern],
        )
        self.assertAlmostEqual(sum(scores.values()), 1.0)
        self.assertEqual(max(scores, key=scores.get), "drying_air_exhaust")
        self.assertGreater(scores["instrumentation"], 0.0)


if __name__ == "__main__":
    unittest.main()
