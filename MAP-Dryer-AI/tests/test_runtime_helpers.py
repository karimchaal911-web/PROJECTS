import unittest

import numpy as np
import pandas as pd

from anomaly.alarms import attach_pcs7_hybrid_alarm_state, evaluate_pcs7_limits
from anomaly.persistence import apply_persistence_logic
from anomaly.thresholds import calibrate_conformal_threshold
from features.engineering import RAW_PROCESS_FEATURES, recompute_engineered_features
from models.regression import calculate_regression_metrics


class RuntimeHelperTests(unittest.TestCase):
    def test_shared_feature_engineering(self):
        values = {feature: 1.0 for feature in RAW_PROCESS_FEATURES}
        values.update(
            dryer_air_temperature=140.0,
            final_product_temp=40.0,
            product_inlet_temperature=50.0,
            air_flow_rate=24.0,
            wet_product_feed_rate=8.0,
            steam_pressure=5.0,
            residence_time=20.0,
        )
        engineered = recompute_engineered_features(pd.DataFrame([values]))
        self.assertEqual(engineered.loc[0, "temperature_drop"], 100.0)
        self.assertEqual(engineered.loc[0, "air_product_delta"], 90.0)
        self.assertEqual(engineered.loc[0, "air_per_feed"], 3.0)
        self.assertEqual(engineered.loc[0, "steam_temp_interaction"], 700.0)
        self.assertEqual(engineered.loc[0, "heating_index"], 2800.0)

    def test_finite_sample_threshold(self):
        threshold, rank = calibrate_conformal_threshold([1, 2, 3, 4], 0.25)
        self.assertEqual(rank, 4)
        self.assertEqual(threshold, 4.0)

    def test_persistence_resets_after_a_sampling_gap(self):
        score_table = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    [
                        "2026-01-01 00:00",
                        "2026-01-01 02:00",
                        "2026-01-01 04:00",
                        "2026-01-01 10:00",
                    ]
                ),
                "Split": ["Validation"] * 4,
                "Raw anomaly flag": [True, False, True, True],
            }
        )
        result = apply_persistence_logic(
            score_table,
            expected_sample_interval=pd.Timedelta(hours=2),
        )
        self.assertEqual(result["Persistent alarm"].tolist(), [False, False, True, False])
        self.assertEqual(result["Cadence segment"].tolist(), [1, 1, 1, 2])

    def test_pcs7_and_ml_alarm_priority(self):
        process_data = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2026-01-01 00:00"]),
                "air_flow_rate": [10.0],
            }
        )
        limits = {
            "air_flow_rate": {"LL": 11.0, "L": 12.0, "H": 20.0, "HH": 21.0}
        }
        pcs7 = evaluate_pcs7_limits(process_data, limits, ["air_flow_rate"])
        score_table = pd.DataFrame(
            {
                "timestamp": process_data["timestamp"],
                "Raw anomaly flag": [True],
                "Persistent alarm": [True],
            }
        )
        combined = attach_pcs7_hybrid_alarm_state(score_table, pcs7, 4)
        self.assertEqual(combined.loc[0, "Combined severity level"], 5)
        self.assertIn("persistent ML anomaly", combined.loc[0, "Combined alarm state"])

    def test_regression_metrics(self):
        metrics = calculate_regression_metrics([1.0, 2.0], [1.0, 2.0])
        self.assertTrue(np.isclose(metrics["RMSE"], 0.0))
        self.assertTrue(np.isclose(metrics["R2"], 1.0))


if __name__ == "__main__":
    unittest.main()
