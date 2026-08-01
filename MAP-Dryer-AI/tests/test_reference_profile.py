import json
import tempfile
import unittest
from pathlib import Path

from diagnosis.reference_profile import ReferenceProfile, build_reference_profile
from tests._fixtures import build_fixture


class ReferenceProfileTests(unittest.TestCase):
    def test_profile_is_train_only_and_serializable(self):
        normal, configuration, _, _, _, _ = build_fixture()
        train = normal.iloc[:300]
        profile = build_reference_profile(train, configuration["feature_metadata"])
        self.assertEqual(profile.training_rows, 300)
        self.assertAlmostEqual(
            profile.statistics["air_flow_rate"]["median"],
            float(train["air_flow_rate"].median()),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = profile.save(Path(directory) / "profile.json")
            restored = ReferenceProfile.from_dict(json.loads(path.read_text()))
        self.assertEqual(restored.as_dict(), profile.as_dict())


if __name__ == "__main__":
    unittest.main()
