import unittest

import numpy as np

from anomaly.scoring import canonical_anomaly_score, is_anomaly
from tests._fixtures import build_fixture


class CanonicalScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normal, _, _, cls.scaler, cls.model, cls.threshold = build_fixture()

    def test_score_is_negative_native_score(self):
        scaled = self.scaler.transform(self.normal.iloc[:8])
        expected = -self.model.score_samples(scaled)
        actual = canonical_anomaly_score(self.model, scaled)
        np.testing.assert_allclose(actual, expected)

    def test_extreme_point_scores_above_normal_median(self):
        extreme = self.normal.iloc[[0]].copy()
        extreme.loc[:, "air_flow_rate"] -= 10.0
        extreme.loc[:, "fan_speed"] -= 400.0
        extreme_score = canonical_anomaly_score(
            self.model, self.scaler.transform(extreme)
        )[0]
        normal_scores = canonical_anomaly_score(
            self.model, self.scaler.transform(self.normal.iloc[:100])
        )
        self.assertGreater(extreme_score, float(np.median(normal_scores)))
        self.assertTrue(is_anomaly(extreme_score, self.threshold))


if __name__ == "__main__":
    unittest.main()
