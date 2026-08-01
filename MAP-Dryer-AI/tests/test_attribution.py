import unittest

from diagnosis.attribution import localize_anomaly
from diagnosis.scenarios import recompute_engineered_features
from tests._fixtures import build_fixture


class AttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normal, cls.configuration, cls.profile, cls.scaler, cls.model, _ = build_fixture()

    def test_airflow_disturbance_localizes_airflow_group(self):
        current = self.normal.iloc[[0]].copy()
        current.loc[:, "air_flow_rate"] -= 5.0
        current = recompute_engineered_features(current)
        evidence = localize_anomaly(
            current.iloc[0],
            self.model,
            self.scaler,
            self.profile,
            self.configuration["feature_metadata"],
            self.configuration["thresholds"],
            top_n=None,
        )
        self.assertAlmostEqual(sum(item.attribution for item in evidence), 1.0)
        top_features = {item.feature for item in evidence[:5]}
        self.assertIn("air_flow_rate", top_features)
        airflow = next(item for item in evidence if item.feature == "air_flow_rate")
        self.assertEqual(airflow.direction, "LOW")
        self.assertGreater(airflow.counterfactual_contribution, 0.0)


if __name__ == "__main__":
    unittest.main()
