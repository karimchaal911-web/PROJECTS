"""Alignment tests: dashboard as-of join and lab-aligned training windows."""

import unittest

import numpy as np
import pandas as pd

from multirate.alignment import (
    align_lab_for_dashboard,
    build_training_matrix,
    effective_window_end,
)
from multirate.preprocessing import (
    QUALITY_VARIABLES,
    build_lab_table,
    build_process_table,
)
from multirate.window_features import WINDOW_FEATURE_NAMES
from tests.test_multirate_preprocessing import make_raw


def build_tables(n_rows=4320, lab_every=720, seed=5):
    """5-second process table + lab table (lab spacing = lab_every rows)."""

    raw = make_raw(n_rows=n_rows, lab_every=lab_every, seed=seed)
    process, _ = build_process_table(raw)
    lab = build_lab_table(raw)
    return process, lab


class DashboardAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.process, cls.lab = build_tables()
        cls.joined = align_lab_for_dashboard(cls.process, cls.lab)

    def test_rows_before_first_lab_sample_have_no_lab_context(self):
        first_lab = self.lab["Sample Timestamp"].iloc[0]
        before = self.joined.loc[self.joined["Timestamp"] < first_lab]
        self.assertFalse(before["Lab Sample Available"].any())
        self.assertTrue(
            before["Latest Lab Final Moisture"].isna().all()
        )

    def test_no_future_laboratory_result_is_attached(self):
        available = self.joined.loc[self.joined["Lab Sample Available"]]
        self.assertTrue(
            (
                available["Latest Lab Sample Timestamp"]
                <= available["Timestamp"]
            ).all()
        )

    def test_lab_age_is_minutes_since_the_attached_sample(self):
        available = self.joined.loc[self.joined["Lab Sample Available"]]
        expected = (
            available["Timestamp"] - available["Latest Lab Sample Timestamp"]
        ).dt.total_seconds() / 60.0
        np.testing.assert_allclose(
            available["Lab Result Age (min)"], expected
        )
        # Age grows monotonically between two consecutive samples.
        first_lab = self.lab["Sample Timestamp"].iloc[0]
        second_lab = self.lab["Sample Timestamp"].iloc[1]
        between = self.joined.loc[
            (self.joined["Timestamp"] >= first_lab)
            & (self.joined["Timestamp"] < second_lab)
        ]
        self.assertTrue(
            between["Lab Result Age (min)"].is_monotonic_increasing
        )

    def test_latest_lab_value_is_constant_between_samples(self):
        first_lab = self.lab["Sample Timestamp"].iloc[0]
        second_lab = self.lab["Sample Timestamp"].iloc[1]
        between = self.joined.loc[
            (self.joined["Timestamp"] >= first_lab)
            & (self.joined["Timestamp"] < second_lab)
        ]
        self.assertEqual(between["Latest Lab Final Moisture"].nunique(), 1)
        self.assertAlmostEqual(
            float(between["Latest Lab Final Moisture"].iloc[0]),
            float(self.lab["Final Moisture (%H2O)"].iloc[0]),
        )


class TrainingAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.process, cls.lab = build_tables()
        cls.window_minutes = 10.0
        cls.transport_delay = 2.0
        cls.result = build_training_matrix(
            cls.process,
            cls.lab,
            window_minutes=cls.window_minutes,
            transport_delay_minutes=cls.transport_delay,
        )

    def test_effective_window_end_applies_residence_time_shift(self):
        lab_timestamp = pd.Timestamp("2026-07-01 12:00:00")
        end = effective_window_end(lab_timestamp, 24.5, 2.0)
        self.assertEqual(
            end, lab_timestamp - pd.Timedelta(minutes=26.5)
        )
        with self.assertRaises(ValueError):
            effective_window_end(lab_timestamp, -1.0, 0.0)

    def test_one_supervised_row_per_actual_laboratory_sample(self):
        self.assertEqual(
            len(self.result.features) + len(self.result.skipped),
            len(self.lab),
        )
        # Every retained row corresponds to exactly one real sample.
        self.assertTrue(
            self.result.features.index.isin(
                self.lab["Sample Timestamp"]
            ).all()
        )
        self.assertFalse(self.result.features.index.duplicated().any())

    def test_window_boundaries_respect_residence_and_transport_shift(self):
        info = self.result.window_info
        for sample_timestamp, row in info.iterrows():
            expected_end = sample_timestamp - pd.Timedelta(
                minutes=row["Residence Time (min)"] + self.transport_delay
            )
            self.assertEqual(row["Window End"], expected_end)
            self.assertEqual(
                row["Window Start"],
                expected_end - pd.Timedelta(minutes=self.window_minutes),
            )

    def test_no_future_process_data_enters_a_feature_window(self):
        info = self.result.window_info
        for sample_timestamp, row in info.iterrows():
            # Window ends strictly before the sample time (residence > 0).
            self.assertLess(row["Window End"], sample_timestamp)
            in_window = self.process.loc[
                (self.process["Timestamp"] > row["Window Start"])
                & (self.process["Timestamp"] <= row["Window End"])
            ]
            self.assertEqual(len(in_window), row["Window Rows"])
            self.assertLess(
                in_window["Timestamp"].max(), sample_timestamp
            )

    def test_targets_are_the_actual_sparse_lab_values(self):
        lab_indexed = self.lab.set_index("Sample Timestamp")
        for sample_timestamp in self.result.targets.index:
            for column in QUALITY_VARIABLES:
                self.assertAlmostEqual(
                    float(self.result.targets.loc[sample_timestamp, column]),
                    float(lab_indexed.loc[sample_timestamp, column]),
                    msg=f"{column} must never be interpolated or filled",
                )

    def test_feature_schema_matches_window_feature_names(self):
        self.assertEqual(
            list(self.result.features.columns), WINDOW_FEATURE_NAMES
        )
        self.assertTrue(
            np.isfinite(self.result.features.to_numpy(dtype=float)).all()
        )

    def test_sample_without_enough_history_is_skipped_not_fabricated(self):
        # A lab sample 1 minute into the campaign cannot have a full
        # residence-shifted window: it must be reported, never invented.
        early_lab = pd.DataFrame(
            {
                "Sample Timestamp": [
                    self.process["Timestamp"].iloc[12],
                ],
                "Product Density": [1.02],
                "Final Product Temp": [43.0],
                "Final Moisture (%H2O)": [1.8],
            }
        )
        result = build_training_matrix(
            self.process,
            early_lab,
            window_minutes=self.window_minutes,
            transport_delay_minutes=self.transport_delay,
        )
        self.assertEqual(len(result.features), 0)
        self.assertEqual(len(result.skipped), 1)


if __name__ == "__main__":
    unittest.main()
