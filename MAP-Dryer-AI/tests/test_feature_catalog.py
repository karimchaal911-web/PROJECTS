import unittest
from pathlib import Path

from data.feature_catalog import (
    feature_axis_label,
    load_feature_catalog,
    select_feature_catalog,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FeatureCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_feature_catalog(
            PROJECT_ROOT / "config" / "data_dictionary.yaml"
        )

    def test_all_pipeline_fields_are_documented(self):
        expected = {
            "date",
            "time",
            "timestamp",
            "dryer_air_temperature",
            "cooler_air_temperature",
            "air_flow_rate",
            "wet_product_feed_rate",
            "product_inlet_temperature",
            "residence_time",
            "vacuum",
            "steam_pressure",
            "fan_speed",
            "product_density",
            "final_product_temp",
            "final_moisture_h₂o",
            "temperature_drop",
            "air_product_delta",
            "air_per_feed",
            "steam_temp_interaction",
            "heating_index",
        }
        self.assertEqual(expected, set(self.catalog.index))

    def test_supplied_engineering_units_are_explicit(self):
        expected_units = {
            "air_flow_rate": "m³/h",
            "wet_product_feed_rate": "m³/h",
            "vacuum": "mmH2O",
            "steam_pressure": "bar",
            "fan_speed": "rpm",
            "air_per_feed": "dimensionless ratio",
            "steam_temp_interaction": "bar · °C",
        }
        for feature, unit in expected_units.items():
            self.assertEqual(self.catalog.loc[feature, "unit"], unit)

        self.assertIn(
            "more-negative values mean stronger depressure",
            self.catalog.loc["vacuum", "interpretation"],
        )

    def test_selection_and_axis_label_preserve_units(self):
        selected = select_feature_catalog(
            self.catalog,
            ["dryer_air_temperature", "final_moisture_h₂o"],
        )
        self.assertEqual(list(selected.index), ["dryer_air_temperature", "final_moisture_h₂o"])
        self.assertEqual(
            feature_axis_label(self.catalog, "final_moisture_h₂o"),
            "Final moisture (% H2O)",
        )


if __name__ == "__main__":
    unittest.main()
