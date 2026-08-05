from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


CRITICALITY_WEIGHTS: dict[str, float] = {
    "high": 1.25,
    "medium": 1.00,
    "low": 0.75,
}

SUBSYSTEM_DISPLAY_NAMES: dict[str, str] = {
    "drying_air_exhaust": "Drying-air and exhaust circuit",
    "thermal_system": "Thermal system",
    "feed_loading": "Feed-loading system",
    "cooling_system": "Cooling system",
}


# Cautious prototype advisory rules. These are not confirmed root-cause,
# safety, alarm, trip, or automatic-control rules.
DIAGNOSIS_RULES: dict[tuple[str, str], dict[str, Any]] = {
    ("air_supply", "LOW"): {
        "diagnosis": "Insufficient drying-air supply",
        "causes": [
            "Reduced fan performance",
            "Air-path restriction",
            "Abnormal damper or control position",
            "Air-flow measurement issue",
        ],
        "verification": (
            "Inspect fan speed and operating condition, air-flow measurement, "
            "damper position, and pressure drop across the drying-air circuit."
        ),
    },
    ("air_supply", "HIGH"): {
        "diagnosis": "Excessive drying-air delivery",
        "causes": [
            "Excessive fan speed",
            "Damper opened beyond the intended position",
            "Air-flow control-loop deviation",
            "Air-flow sensor bias",
        ],
        "verification": (
            "Verify fan-speed command, damper position, air-flow controller "
            "output, and air-flow instrument calibration."
        ),
    },
    ("exhaust_pressure", "HIGH"): {
        "diagnosis": "Insufficient dryer draft or vacuum",
        "causes": [
            "Reduced exhaust-fan performance",
            "Restriction in the exhaust path",
            "Filter or dust-separation pressure loss",
            "Vacuum measurement issue",
        ],
        "verification": (
            "Inspect exhaust-fan operation, vacuum measurement, filter "
            "condition, dust-separation equipment, and exhaust pressure drop."
        ),
    },
    ("exhaust_pressure", "LOW"): {
        "diagnosis": "Excessive dryer suction",
        "causes": [
            "Excessive exhaust-fan demand",
            "Abnormal damper position",
            "Vacuum-control deviation",
            "Vacuum instrument bias",
        ],
        "verification": (
            "Check exhaust-fan demand, damper position, vacuum-control output, "
            "air leakage, and vacuum transmitter condition."
        ),
    },
    ("dryer_temperature", "LOW"): {
        "diagnosis": "Insufficient dryer thermal condition",
        "causes": [
            "Reduced steam or heating supply",
            "Excessive product or air loading",
            "Heat-transfer degradation",
            "Temperature measurement issue",
        ],
        "verification": (
            "Compare dryer temperature with steam pressure, feed rate, air "
            "flow, residence time, and temperature-instrument status."
        ),
    },
    ("dryer_temperature", "HIGH"): {
        "diagnosis": "Elevated dryer thermal condition",
        "causes": [
            "Excessive steam or heating input",
            "Reduced product loading",
            "Air-flow imbalance",
            "Temperature-controller or sensor deviation",
        ],
        "verification": (
            "Verify steam supply, feed loading, air flow, temperature "
            "controller output, and dryer-temperature measurement."
        ),
    },
    ("steam_supply", "LOW"): {
        "diagnosis": "Insufficient steam supply",
        "causes": [
            "Low upstream steam pressure",
            "Control-valve restriction",
            "Steam-demand limitation",
            "Pressure measurement issue",
        ],
        "verification": (
            "Inspect upstream steam pressure, valve position, steam "
            "availability, pressure loss, and pressure-instrument status."
        ),
    },
    ("steam_supply", "HIGH"): {
        "diagnosis": "Elevated steam supply",
        "causes": [
            "Excessive steam-valve opening",
            "Steam-pressure controller deviation",
            "Downstream demand reduction",
            "Pressure measurement bias",
        ],
        "verification": (
            "Verify steam-valve position, controller output, downstream "
            "thermal response, and steam-pressure measurement."
        ),
    },
    ("feed_loading", "HIGH"): {
        "diagnosis": "Elevated wet-product loading",
        "causes": [
            "High feeder output",
            "Feed-control deviation",
            "Wet-product density or composition variation",
            "Feed-flow measurement issue",
        ],
        "verification": (
            "Inspect feeder speed, wet-product flow measurement, feed density, "
            "hopper condition, and feed-control output."
        ),
    },
    ("feed_loading", "LOW"): {
        "diagnosis": "Reduced or unstable wet-product loading",
        "causes": [
            "Feed starvation",
            "Hopper bridging or restriction",
            "Reduced feeder performance",
            "Feed-flow measurement issue",
        ],
        "verification": (
            "Inspect hopper level and bridging, feeder operation, feed-path "
            "restrictions, and wet-product flow measurement."
        ),
    },
    ("cooler_temperature", "HIGH"): {
        "diagnosis": "Insufficient product cooling",
        "causes": [
            "Reduced cooling-air supply",
            "High dryer outlet thermal load",
            "Cooling-path restriction",
            "Temperature measurement issue",
        ],
        "verification": (
            "Inspect cooler air flow, cooling-fan condition, product "
            "temperature trend, cooler restrictions, and temperature measurement."
        ),
    },
    ("cooler_temperature", "LOW"): {
        "diagnosis": "Unusually low cooler-air temperature",
        "causes": [
            "Ambient or cooling-air condition change",
            "Excessive cooling-air delivery",
            "Reduced dryer thermal load",
            "Temperature sensor bias",
        ],
        "verification": (
            "Compare cooler-air temperature with ambient conditions, cooling-air "
            "delivery, final-product temperature, and sensor status."
        ),
    },
    ("final_product_temperature", "HIGH"): {
        "diagnosis": "Elevated final-product temperature",
        "causes": [
            "Insufficient cooling",
            "Excessive dryer heat input",
            "Reduced cooling residence time",
            "Product-temperature measurement issue",
        ],
        "verification": (
            "Check cooler operation, dryer thermal condition, residence time, "
            "product loading, and final-product temperature sensor."
        ),
    },
    ("final_product_temperature", "LOW"): {
        "diagnosis": "Low final-product temperature",
        "causes": [
            "Reduced dryer thermal input",
            "Excessive cooling",
            "Low product loading",
            "Product-temperature sensor bias",
        ],
        "verification": (
            "Compare final-product temperature with dryer temperature, steam "
            "pressure, cooling conditions, feed loading, and sensor status."
        ),
    },
    ("air_to_feed_balance", "LOW"): {
        "diagnosis": "Insufficient air-to-feed ratio",
        "causes": [
            "Reduced drying-air flow",
            "Elevated wet-product feed",
            "Fan or damper limitation",
            "Air-flow or feed-flow measurement issue",
        ],
        "verification": (
            "Compare air flow with wet-product feed, fan speed, damper position, "
            "and both flow instruments."
        ),
    },
    ("air_to_feed_balance", "HIGH"): {
        "diagnosis": "Elevated air-to-feed ratio",
        "causes": [
            "Excessive drying-air flow",
            "Reduced wet-product feed",
            "Air-flow control deviation",
            "Feed-flow or air-flow measurement issue",
        ],
        "verification": (
            "Compare air flow with feed loading and inspect fan, damper, "
            "air-flow control, feeder operation, and flow instruments."
        ),
    },
    ("thermal_energy", "LOW"): {
        "diagnosis": "Reduced combined thermal-energy condition",
        "causes": [
            "Low steam pressure",
            "Low dryer-air temperature",
            "Heat-transfer limitation",
            "Thermal measurement issue",
        ],
        "verification": (
            "Inspect steam pressure, dryer-air temperature, heating equipment, "
            "heat-transfer condition, and related instruments."
        ),
    },
    ("thermal_energy", "HIGH"): {
        "diagnosis": "Elevated combined thermal-energy condition",
        "causes": [
            "High steam pressure",
            "High dryer-air temperature",
            "Excessive heating demand",
            "Thermal control or measurement deviation",
        ],
        "verification": (
            "Inspect steam pressure, dryer-air temperature, heating control "
            "output, feed loading, and thermal instruments."
        ),
    },
    ("thermal_exposure", "LOW"): {
        "diagnosis": "Insufficient product thermal exposure",
        "causes": [
            "Reduced residence time",
            "Low dryer temperature",
            "Excessive product throughput",
            "Residence-time calculation issue",
        ],
        "verification": (
            "Verify residence time, dryer temperature, product flow, equipment "
            "loading, and the residence-time calculation."
        ),
    },
    ("thermal_exposure", "HIGH"): {
        "diagnosis": "Elevated product thermal exposure",
        "causes": [
            "Extended residence time",
            "High dryer temperature",
            "Reduced product throughput",
            "Residence-time calculation issue",
        ],
        "verification": (
            "Verify residence time, dryer temperature, feed loading, equipment "
            "speed, and the residence-time calculation."
        ),
    },
}


@dataclass(frozen=True)
class VariableContribution:
    feature_name: str
    observed_value: float
    reference_center: float
    reference_scale: float
    lower_normal_limit: float
    upper_normal_limit: float
    signed_deviation: float
    deviation_percent: float | None
    contribution_score: float
    direction: str
    variable_severity: str
    is_direct_process_feature: bool
    criticality: str
    explanation_group: str
    subsystems: tuple[str, ...]
    unit: str | None


@dataclass(frozen=True)
class DiagnosisResult:
    severity: str
    likely_subsystem: str
    probable_diagnosis: str
    possible_causes: str
    recommended_verification: str
    diagnosis_confidence: float | None
    direct_contributors: tuple[VariableContribution, ...]


def load_reference_profile(profile_path: Path) -> dict[str, Any]:
    """Load and validate the reference-profile JSON."""

    if not profile_path.exists():
        raise FileNotFoundError(
            f"Reference profile not found:\n{profile_path}"
        )

    with profile_path.open("r", encoding="utf-8") as file:
        reference_profile = json.load(file)

    required_keys = {
        "feature_metadata",
        "feature_names",
        "statistics",
        "profile_version",
        "training_rows",
    }

    missing_keys = required_keys - set(reference_profile)

    if missing_keys:
        raise ValueError(
            "Reference profile is missing keys: "
            f"{sorted(missing_keys)}"
        )

    feature_names = list(reference_profile["feature_names"])
    statistics = reference_profile["statistics"]
    metadata = reference_profile["feature_metadata"]

    missing_statistics = [
        feature_name
        for feature_name in feature_names
        if feature_name not in statistics
    ]

    missing_metadata = [
        feature_name
        for feature_name in feature_names
        if feature_name not in metadata
    ]

    if missing_statistics:
        raise ValueError(
            f"Missing feature statistics: {missing_statistics}"
        )

    if missing_metadata:
        raise ValueError(
            f"Missing feature metadata: {missing_metadata}"
        )

    return reference_profile


def _robust_scale(statistics: dict[str, Any]) -> float:
    """Return a stable robust scale derived from MAD and IQR."""

    mad = abs(float(statistics["mad"]))
    iqr = abs(float(statistics["iqr"]))

    mad_scale = 1.4826 * mad
    iqr_scale = iqr / 1.349 if iqr > 0 else 0.0

    return max(mad_scale, iqr_scale, 1e-12)


def _direction_and_severity(
    value: float,
    statistics: dict[str, Any],
) -> tuple[str, str]:
    q01 = float(statistics["q01"])
    q05 = float(statistics["q05"])
    q95 = float(statistics["q95"])
    q99 = float(statistics["q99"])

    if q05 <= value <= q95:
        return "NORMAL", "NORMAL"

    direction = "LOW" if value < q05 else "HIGH"

    if q01 <= value <= q99:
        return direction, "MEDIUM"

    return direction, "HIGH"


def _create_contribution(
    feature_name: str,
    observed_value: float,
    statistics: dict[str, Any],
    metadata: dict[str, Any],
) -> VariableContribution:
    center = float(statistics["median"])
    scale = _robust_scale(statistics)
    lower_limit = float(statistics["q05"])
    upper_limit = float(statistics["q95"])
    signed_deviation = observed_value - center

    if abs(center) > 1e-12:
        deviation_percent = signed_deviation / abs(center) * 100.0
    else:
        deviation_percent = None

    direction, variable_severity = _direction_and_severity(
        observed_value,
        statistics,
    )

    criticality = str(metadata.get("criticality", "medium")).lower()
    criticality_weight = CRITICALITY_WEIGHTS.get(criticality, 1.0)
    robust_distance = abs(signed_deviation) / scale
    contribution_score = robust_distance * criticality_weight

    return VariableContribution(
        feature_name=feature_name,
        observed_value=observed_value,
        reference_center=center,
        reference_scale=scale,
        lower_normal_limit=lower_limit,
        upper_normal_limit=upper_limit,
        signed_deviation=signed_deviation,
        deviation_percent=deviation_percent,
        contribution_score=contribution_score,
        direction=direction,
        variable_severity=variable_severity,
        is_direct_process_feature=metadata.get("kind") == "raw",
        criticality=criticality,
        explanation_group=str(
            metadata.get("explanation_group", "unknown")
        ),
        subsystems=tuple(metadata.get("subsystems", [])),
        unit=metadata.get("unit"),
    )


def _select_event_severity(
    anomaly_detected: bool,
    direct_abnormal: list[VariableContribution],
) -> str:
    """
    Assign a prototype operational severity.

    CRITICAL is intentionally not assigned because this profile contains
    statistical limits, not approved safety, alarm, or trip limits.
    """

    if not anomaly_detected:
        return "NORMAL"

    if not direct_abnormal:
        return "LOW"

    high_count = sum(
        contribution.variable_severity == "HIGH"
        for contribution in direct_abnormal
    )

    if high_count >= 1:
        return "HIGH"

    if len(direct_abnormal) >= 2:
        return "MEDIUM"

    return "LOW"


def _select_likely_subsystem(
    abnormal_contributions: list[VariableContribution],
) -> str:
    if not abnormal_contributions:
        return "No subsystem identified"

    subsystem_scores: dict[str, float] = {}

    for contribution in abnormal_contributions:
        if not contribution.subsystems:
            continue

        allocated_score = (
            contribution.contribution_score
            / len(contribution.subsystems)
        )

        for subsystem in contribution.subsystems:
            subsystem_scores[subsystem] = (
                subsystem_scores.get(subsystem, 0.0)
                + allocated_score
            )

    if not subsystem_scores:
        return "No subsystem identified"

    selected_subsystem = max(
        subsystem_scores,
        key=subsystem_scores.get,
    )

    return SUBSYSTEM_DISPLAY_NAMES.get(
        selected_subsystem,
        selected_subsystem.replace("_", " ").title(),
    )


def _build_diagnosis_text(
    top_contributor: VariableContribution | None,
    likely_subsystem: str,
    anomaly_detected: bool,
) -> tuple[str, str, str]:
    if not anomaly_detected:
        return (
            "No active anomaly",
            "No anomaly-related cause list is generated.",
            (
                "Continue normal monitoring and verify data freshness "
                "and instrument quality."
            ),
        )

    if top_contributor is None:
        return (
            "Anomaly detected without a dominant direct-variable deviation",
            (
                "The anomaly may result from a multivariable interaction, "
                "an engineered feature, an operating-regime transition, "
                "or data-quality behaviour."
            ),
            (
                "Review synchronized process trends, engineered-feature "
                "values, the model score, and measurement quality before "
                "taking operational action."
            ),
        )

    rule = DIAGNOSIS_RULES.get(
        (
            top_contributor.explanation_group,
            top_contributor.direction,
        )
    )

    if rule is None:
        return (
            (
                f"Abnormal "
                f"{top_contributor.explanation_group.replace('_', ' ')} "
                f"condition associated with {likely_subsystem}"
            ),
            (
                "Possible process disturbance, control deviation, equipment "
                "performance change, or measurement issue."
            ),
            (
                f"Inspect {top_contributor.feature_name.replace('_', ' ')}, "
                "its related controller and equipment, associated process "
                "measurements, and instrument status."
            ),
        )

    possible_causes = "; ".join(
        str(cause)
        for cause in rule["causes"]
    )

    return (
        str(rule["diagnosis"]),
        possible_causes,
        str(rule["verification"]),
    )


def diagnose_event(
    model_features: pd.DataFrame,
    anomaly_detected: bool,
    reference_profile: dict[str, Any],
    top_n_direct: int = 4,
) -> DiagnosisResult:
    """
    Rank abnormal variables and produce a cautious diagnosis.

    Engineered features participate in subsystem voting, but only raw
    process variables are returned as operator-facing contributors.
    """

    if len(model_features) != 1:
        raise ValueError(
            "diagnose_event() expects exactly one observation."
        )

    if top_n_direct < 1:
        raise ValueError("top_n_direct must be at least 1.")

    feature_names = list(reference_profile["feature_names"])

    missing_features = [
        feature_name
        for feature_name in feature_names
        if feature_name not in model_features.columns
    ]

    if missing_features:
        raise ValueError(
            f"Model-feature DataFrame is missing: {missing_features}"
        )

    all_contributions: list[VariableContribution] = []

    for feature_name in feature_names:
        observed_value = float(
            model_features.iloc[0][feature_name]
        )

        if not math.isfinite(observed_value):
            raise ValueError(
                f"Feature {feature_name!r} is not finite."
            )

        contribution = _create_contribution(
            feature_name=feature_name,
            observed_value=observed_value,
            statistics=reference_profile["statistics"][feature_name],
            metadata=reference_profile["feature_metadata"][feature_name],
        )

        all_contributions.append(contribution)

    abnormal_contributions = [
        contribution
        for contribution in all_contributions
        if contribution.direction != "NORMAL"
    ]

    abnormal_contributions.sort(
        key=lambda item: item.contribution_score,
        reverse=True,
    )

    direct_abnormal = [
        contribution
        for contribution in abnormal_contributions
        if contribution.is_direct_process_feature
    ][:top_n_direct]

    severity = _select_event_severity(
        anomaly_detected=anomaly_detected,
        direct_abnormal=direct_abnormal,
    )

    likely_subsystem = (
        _select_likely_subsystem(abnormal_contributions)
        if anomaly_detected
        else "Normal operation"
    )

    top_contributor = (
        direct_abnormal[0]
        if direct_abnormal
        else None
    )

    (
        probable_diagnosis,
        possible_causes,
        recommended_verification,
    ) = _build_diagnosis_text(
        top_contributor=top_contributor,
        likely_subsystem=likely_subsystem,
        anomaly_detected=anomaly_detected,
    )

    return DiagnosisResult(
        severity=severity,
        likely_subsystem=likely_subsystem,
        probable_diagnosis=probable_diagnosis,
        possible_causes=possible_causes,
        recommended_verification=recommended_verification,
        diagnosis_confidence=None,
        direct_contributors=tuple(direct_abnormal),
    )