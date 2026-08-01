from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from anomaly.scoring import canonical_anomaly_score
from diagnosis.config import load_diagnostic_configuration
from diagnosis.reference_profile import build_reference_profile
from diagnosis.scenarios import RAW_FEATURES, recompute_engineered_features


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_fixture(seed: int = 17):
    rng = np.random.default_rng(seed)
    centers = {
        "dryer_air_temperature": 140.0,
        "cooler_air_temperature": 25.0,
        "air_flow_rate": 24.0,
        "wet_product_feed_rate": 10.1,
        "product_inlet_temperature": 47.5,
        "residence_time": 20.5,
        "vacuum": -1.1,
        "steam_pressure": 4.8,
        "fan_speed": 1270.0,
        "product_density": 1.025,
        "final_product_temp": 43.0,
    }
    scales = {
        "dryer_air_temperature": 0.8,
        "cooler_air_temperature": 1.8,
        "air_flow_rate": 0.7,
        "wet_product_feed_rate": 0.25,
        "product_inlet_temperature": 1.0,
        "residence_time": 0.45,
        "vacuum": 0.22,
        "steam_pressure": 0.12,
        "fan_speed": 28.0,
        "product_density": 0.004,
        "final_product_temp": 1.4,
    }
    raw = pd.DataFrame(
        {
            feature: rng.normal(centers[feature], scales[feature], size=480)
            for feature in RAW_FEATURES
        }
    )
    normal = recompute_engineered_features(raw)
    configuration = load_diagnostic_configuration(PROJECT_ROOT / "config")
    feature_names = list(configuration["feature_metadata"]["features"])
    normal = normal.loc[:, feature_names]
    profile = build_reference_profile(normal, configuration["feature_metadata"])
    scaler = StandardScaler().fit(normal)
    scaled = scaler.transform(normal)
    model = OneClassSVM(kernel="rbf", gamma="scale", nu=0.02).fit(scaled)
    scores = canonical_anomaly_score(model, scaled)
    threshold = float(np.quantile(scores, 0.99))
    return normal, configuration, profile, scaler, model, threshold
