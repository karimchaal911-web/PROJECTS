"""Data-contract tests for the 5-second multi-rate preprocessing."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from multirate.preprocessing import (
    PROCESS_VARIABLES,
    QUALITY_VARIABLES,
    RAW_SOURCE_COLUMNS,
    build_lab_table,
    build_process_table,
    build_timestamp,
    load_raw_source,
)


def make_raw(
    n_rows: int = 720,
    lab_every: int = 360,
    start: str = "2026-07-01 08:00:00",
    seed: int = 11,
) -> pd.DataFrame:
    """Synthetic raw frame with the exact plant columns and sparse labs."""

    index = pd.date_range(start, periods=n_rows, freq="5s")
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "Date": index.strftime("%Y-%m-%d"),
            "Time": index.strftime("%H:%M:%S"),
            "Dryer Air Temperature": rng.normal(128.0, 1.0, n_rows),
            "Cooler Air Temperature": rng.normal(25.0, 0.8, n_rows),
            "Air Flow Rate": rng.normal(24.0, 0.5, n_rows),
            "Wet Product Feed Rate": rng.normal(18.5, 0.4, n_rows),
            "Product Inlet Temperature": rng.normal(47.0, 0.9, n_rows),
            "Residence Time": rng.normal(24.6, 0.3, n_rows),
            "Vacuum": rng.normal(-31.0, 1.1, n_rows),
            "Steam Pressure": rng.normal(5.2, 0.15, n_rows),
            "Fan Speed": rng.normal(1270.0, 20.0, n_rows),
        }
    )
    for column in QUALITY_VARIABLES:
        frame[column] = np.nan
    lab_positions = list(range(lab_every, n_rows, lab_every))
    frame.loc[lab_positions, "Product Density"] = rng.normal(
        1.025, 0.003, len(lab_positions)
    )
    frame.loc[lab_positions, "Final Product Temp"] = rng.normal(
        43.0, 1.0, len(lab_positions)
    )
    frame.loc[lab_positions, "Final Moisture (%H2O)"] = rng.normal(
        1.8, 0.05, len(lab_positions)
    )
    return frame.loc[:, RAW_SOURCE_COLUMNS]


class RawSchemaTests(unittest.TestCase):
    def test_exact_expected_raw_column_names_accepted(self):
        raw = make_raw(n_rows=24, lab_every=12)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            raw.to_csv(path, index=False)
            loaded = load_raw_source(path)
        self.assertEqual(list(loaded.columns), RAW_SOURCE_COLUMNS)

    def test_missing_required_column_is_rejected(self):
        raw = make_raw(n_rows=24, lab_every=12).drop(columns=["Steam Pressure"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            raw.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "Steam Pressure"):
                load_raw_source(path)

    def test_timestamp_generation_is_valid(self):
        raw = make_raw(n_rows=24, lab_every=12)
        timestamps = build_timestamp(raw)
        self.assertFalse(timestamps.isna().any())
        self.assertEqual(
            timestamps.iloc[1] - timestamps.iloc[0], pd.Timedelta(seconds=5)
        )

    def test_unparseable_timestamp_is_rejected(self):
        raw = make_raw(n_rows=24, lab_every=12)
        raw.loc[3, "Time"] = "not-a-time"
        with self.assertRaises(ValueError):
            build_timestamp(raw)


class ProcessTableTests(unittest.TestCase):
    def test_chronological_sorting_of_shuffled_input(self):
        raw = make_raw(n_rows=120, lab_every=60)
        shuffled = raw.sample(frac=1.0, random_state=3).reset_index(drop=True)
        process, report = build_process_table(shuffled)
        self.assertTrue(process["Timestamp"].is_monotonic_increasing)
        self.assertEqual(report.gap_count, 0)

    def test_duplicate_timestamps_removed_first_wins(self):
        raw = make_raw(n_rows=60, lab_every=30)
        duplicated = pd.concat([raw, raw.iloc[[10]]], ignore_index=True)
        original_value = raw.loc[10, "Dryer Air Temperature"]
        process, report = build_process_table(duplicated)
        self.assertEqual(report.duplicate_timestamps_removed, 1)
        self.assertEqual(len(process), 60)
        self.assertAlmostEqual(
            float(process.loc[10, "Dryer Air Temperature"]),
            float(original_value),
        )

    def test_five_second_interval_is_validated_and_gaps_reported(self):
        raw = make_raw(n_rows=120, lab_every=60)
        with_gap = raw.drop(index=[40, 41, 42]).reset_index(drop=True)
        process, report = build_process_table(with_gap)
        self.assertEqual(report.gap_count, 1)
        self.assertEqual(report.missing_interval_rows, 3)
        # The real gap is preserved: no rows are invented.
        self.assertEqual(len(process), 117)
        self.assertFalse(process["filled_from_previous"].any())

    def test_process_variables_are_numeric(self):
        raw = make_raw(n_rows=24, lab_every=12).astype(
            {"Vacuum": str, "Fan Speed": str}
        )
        process, _ = build_process_table(raw)
        for column in PROCESS_VARIABLES:
            self.assertTrue(
                pd.api.types.is_numeric_dtype(process[column]), column
            )

    def test_short_gap_fill_uses_only_the_previous_value(self):
        raw = make_raw(n_rows=120, lab_every=60)
        with_gaps = raw.drop(index=[30, 31, 80, 81, 82, 83]).reset_index(
            drop=True
        )
        process, report = build_process_table(
            with_gaps, short_gap_fill_limit_intervals=2
        )
        # Only the 2-row gap is filled; the 4-row gap stays open.
        self.assertEqual(report.filled_rows, 2)
        filled = process.loc[process["filled_from_previous"]]
        self.assertEqual(len(filled), 2)
        previous_value = float(
            process.loc[
                process["Timestamp"]
                == filled["Timestamp"].min() - pd.Timedelta(seconds=5),
                "Dryer Air Temperature",
            ].iloc[0]
        )
        # Last-value hold from the row before the gap, never the row after.
        self.assertTrue(
            (filled["Dryer Air Temperature"] == previous_value).all()
        )


class LabTableTests(unittest.TestCase):
    def test_row_count_matches_actual_laboratory_samples(self):
        raw = make_raw(n_rows=720, lab_every=360)
        lab = build_lab_table(raw)
        self.assertEqual(len(lab), 1)  # positions 360 only (720 exclusive)
        raw_2 = make_raw(n_rows=1500, lab_every=360)
        self.assertEqual(len(build_lab_table(raw_2)), 4)

    def test_quality_blanks_between_samples_are_preserved(self):
        raw = make_raw(n_rows=720, lab_every=360)
        process, _ = build_process_table(raw)
        # The process table never carries quality columns at all.
        for column in QUALITY_VARIABLES:
            self.assertNotIn(column, process.columns)
        # And the raw quality columns keep their structural blanks.
        self.assertEqual(int(raw["Final Moisture (%H2O)"].notna().sum()), 1)

    def test_lab_spacing_is_about_two_hours_in_prototype_shape(self):
        raw = make_raw(n_rows=4320, lab_every=1440)  # lab every 2 h at 5 s
        lab = build_lab_table(raw)
        spacing = lab["Sample Timestamp"].diff().dropna()
        self.assertTrue((spacing == pd.Timedelta(hours=2)).all())


if __name__ == "__main__":
    unittest.main()
