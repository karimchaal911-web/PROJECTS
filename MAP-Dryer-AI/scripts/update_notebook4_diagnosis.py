"""Integrate the modular diagnosis demonstration into Notebook 4."""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "04_Model2_AnomalyDetection&Diagnosis.ipynb"
TAG = "diagnosis-layer-v1"


def tagged(cell):
    cell.metadata.setdefault("tags", []).append(TAG)
    return cell


def make_persistence_gap_aware(notebook) -> None:
    """Reset row-based persistence at real sampling gaps instead of failing."""

    for cell in notebook.cells:
        if cell.cell_type != "code" or not cell.source.startswith(
            "PERSISTENCE_WINDOW_OBSERVATIONS = 3"
        ):
            continue
        strict_guard = '''if not (observed_intervals == EXPECTED_SAMPLE_INTERVAL).all():
    raise ValueError(
        "Persistence by observation count requires a regular sampling interval."
    )'''
        gap_guard = '''CADENCE_GAP_TOLERANCE = 1.5
irregular_interval_count = int(
    (observed_intervals > EXPECTED_SAMPLE_INTERVAL * CADENCE_GAP_TOLERANCE).sum()
)
if irregular_interval_count:
    print(
        f"Detected {irregular_interval_count} sampling gaps; persistence state "
        "will reset at each gap."
    )'''
        if strict_guard in cell.source:
            cell.source = cell.source.replace(strict_guard, gap_guard)

        sort_line = '''    alarm_table = score_table.sort_values("timestamp", kind="stable").copy()
    alarm_table["Candidates in persistence window"] = ('''
        gap_aware_sort = '''    alarm_table = score_table.sort_values("timestamp", kind="stable").copy()
    split_boundary = alarm_table["Split"].ne(alarm_table["Split"].shift())
    cadence_gap = alarm_table["timestamp"].diff().gt(
        EXPECTED_SAMPLE_INTERVAL * CADENCE_GAP_TOLERANCE
    )
    alarm_table["Cadence segment"] = (split_boundary | cadence_gap).cumsum()
    alarm_table["Candidates in persistence window"] = ('''
        if sort_line in cell.source:
            cell.source = cell.source.replace(sort_line, gap_aware_sort)
        cell.source = cell.source.replace(
            'alarm_table.groupby("Split", sort=False)["Raw anomaly flag"]',
            'alarm_table.groupby(["Split", "Cadence segment"], sort=False)["Raw anomaly flag"]',
        )
        cell.source = cell.source.replace(
            'previous_alarm_state = alarm_table.groupby("Split", sort=False)[\n        "Persistent alarm"\n    ].shift(fill_value=False)',
            'previous_alarm_state = alarm_table.groupby(\n        ["Split", "Cadence segment"], sort=False\n    )["Persistent alarm"].shift(fill_value=False)',
        )
        return
    raise RuntimeError("Notebook persistence cell was not found.")


def main() -> None:
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    make_persistence_gap_aware(notebook)
    notebook.cells[0].source = notebook.cells[0].source.replace(
        "# Notebook 04: Model 2 — Anomaly Detection",
        "# Notebook 04: Model 2 — Anomaly Detection and Diagnosis",
    )

    retained = []
    for cell in notebook.cells:
        if TAG not in cell.metadata.get("tags", []):
            retained.append(cell)
    notebook.cells = retained

    next_task_index = next(
        (
            index
            for index, cell in enumerate(notebook.cells)
            if cell.cell_type == "markdown"
            and cell.source.lstrip().startswith("## Next task")
        ),
        len(notebook.cells),
    )

    diagnosis_cells = [
        tagged(
            new_markdown_cell(
                """## 28-29. Configure the diagnostic layer and build the train-only reference profile

The detector remains unchanged. The diagnostic branch loads versioned feature, subsystem, rule, and threshold configuration, then builds robust medians, IQR/MAD values, quantiles, and temporal delta statistics from the same chronological `X_normal_reference` used to fit the detector. Delayed laboratory moisture is excluded from all online inputs.

Diagnostic language is deliberately cautious: diagnoses are **probable**, causes are **suspected**, and no mechanical root cause is treated as confirmed without operator or maintenance evidence."""
            )
        ),
        tagged(
            new_code_cell(
                """from anomaly.scoring import canonical_anomaly_score
from diagnosis.bundle import save_diagnostic_bundle_metadata
from diagnosis.config import (
    load_diagnostic_configuration,
    validate_model_features,
)
from diagnosis.engine import diagnose_anomaly, format_operator_report
from diagnosis.reference_profile import build_reference_profile
from diagnosis.scenarios import build_physical_scenarios

DIAGNOSTIC_CONFIG_DIR = PROJECT_ROOT / "config"
DIAGNOSIS_FIGURE_OUTPUT_DIR = FIGURES_DIR / "05_Model3_Process_Diagnosis"
DIAGNOSIS_FIGURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

diagnostic_configuration = load_diagnostic_configuration(
    DIAGNOSTIC_CONFIG_DIR
)
validate_model_features(
    MODEL_FEATURES,
    diagnostic_configuration["feature_metadata"],
)
reference_profile = build_reference_profile(
    X_normal_reference,
    diagnostic_configuration["feature_metadata"],
)

feature_metadata_table = (
    pd.DataFrame.from_dict(
        diagnostic_configuration["feature_metadata"]["features"],
        orient="index",
    )
    .rename_axis("Feature")
    .loc[MODEL_FEATURES]
)
reference_profile_table = pd.DataFrame(reference_profile.statistics).T[
    ["median", "iqr", "mad", "q05", "q95", "delta_iqr"]
]

display(feature_metadata_table)
display(reference_profile_table.round(4))
print("Diagnostic configuration versions:", diagnostic_configuration["versions"])
print("Reference-profile rows (training only):", reference_profile.training_rows)"""
            )
        ),
        tagged(
            new_markdown_cell(
                """## 30-34. Verify localization, temporal, subsystem, rule, confidence, severity, and instrumentation contracts

The reusable modules apply two complementary localization signals: robust deviation from train-only medians/IQRs and counterfactual One-Class SVM sensitivity. Feature attributions are normalized, mapped to physical subsystems without double counting, combined with recent temporal patterns, and evaluated through the configured D01-D08 rules. Diagnostic confidence describes rule agreement; severity is a separate model-based operational indicator and is not a safety classification.

The check below proves that the canonical scoring helper reproduces the notebook's existing OCSVM scores exactly. Diagnosis therefore adds no retuning or detector-output change."""
            )
        ),
        tagged(
            new_code_cell(
                """ocsvm_scaled_timeline = pd.concat(
    [X_train_scaled, X_validation_scaled, X_test_scaled],
    axis=0,
).sort_index()
canonical_ocsvm_scores = canonical_anomaly_score(
    one_class_svm_model,
    ocsvm_scaled_timeline[MODEL_FEATURES],
)
stored_ocsvm_scores = (
    one_class_svm_score_results
    .sort_values("timestamp", kind="stable")["Anomaly score"]
    .to_numpy()
)
if not np.allclose(canonical_ocsvm_scores, stored_ocsvm_scores):
    raise AssertionError(
        "The diagnosis score adapter changed the existing OCSVM score contract."
    )

diagnostic_contract = pd.Series(
    {
        "Detector preserved": "Tuned One-Class SVM",
        "Score convention": "Higher score = more abnormal",
        "Detector score equality": True,
        "Feature localization": "40% robust deviation + 60% counterfactual sensitivity",
        "Configured diagnostic rules": len(
            diagnostic_configuration["rules"]["rules"]
        ),
        "Instrumentation guard": "Enabled",
        "Lab moisture used online": False,
    },
    name="Diagnostic contract",
)
display(diagnostic_contract.to_frame())"""
            )
        ),
        tagged(
            new_markdown_cell(
                """## 35. Diagnose persistent validation/test episodes and produce operator-safe events

One representative observation is selected per persistent alarm episode: the observation with the highest OCSVM anomaly score. The engine uses only history available at that timestamp. It returns a stable `DiagnosticEvent` with ranked evidence, subsystem scores, temporal patterns, probable diagnoses, suspected causes, recommended checks, severity, confidence, configuration versions, and empty operator-confirmation fields."""
            )
        ),
        tagged(
            new_code_cell(
                """import json

diagnostic_score_results = one_class_svm_score_results.copy()
episode_rows = diagnostic_score_results.loc[
    diagnostic_score_results["Persistent alarm"]
    & diagnostic_score_results["Split"].isin(["Validation", "Testing"])
    & diagnostic_score_results["Alarm episode"].notna()
].copy()

if episode_rows.empty:
    representative_rows = diagnostic_score_results.loc[
        diagnostic_score_results["Raw anomaly flag"]
        & diagnostic_score_results["Split"].isin(["Validation", "Testing"])
    ].copy()
else:
    representative_indices = episode_rows.groupby(
        ["Split", "Alarm episode"], sort=False
    )["Anomaly score"].idxmax()
    representative_rows = diagnostic_score_results.loc[
        representative_indices
    ].sort_values("timestamp", kind="stable")

history_window = int(
    diagnostic_configuration["thresholds"]["temporal"]["history_window"]
)
diagnostic_events = []
for _, representative in representative_rows.iterrows():
    event_timestamp = pd.Timestamp(representative["timestamp"])
    history = ordered_anomaly_data.loc[
        ordered_anomaly_data["timestamp"] <= event_timestamp,
        MODEL_FEATURES,
    ].tail(history_window)
    current = history.iloc[-1]
    pcs7_row = pcs7_limit_results.loc[
        pcs7_limit_results["timestamp"] == event_timestamp
    ].iloc[0]
    lab_moisture = dryerMAP_model.loc[
        dryerMAP_model["timestamp"] == event_timestamp,
        "final_moisture_h₂o",
    ].iloc[0]
    diagnostic_events.append(
        diagnose_anomaly(
            timestamp=event_timestamp,
            anomaly=True,
            anomaly_score=representative["Anomaly score"],
            threshold=ONE_CLASS_SVM_THRESHOLD,
            x_current=current,
            history_df=history,
            model=one_class_svm_model,
            scaler=anomaly_scaler,
            reference_profile=reference_profile,
            feature_metadata=diagnostic_configuration["feature_metadata"],
            subsystem_config=diagnostic_configuration["subsystems"],
            rule_config=diagnostic_configuration["rules"],
            threshold_config=diagnostic_configuration["thresholds"],
            config_versions=diagnostic_configuration["versions"],
            approved_limit_crossing=(
                PCS7_LIMITS_APPROVED and bool(pcs7_row["PCS7 rule breach"])
            ),
            lab_moisture_after_event=float(lab_moisture),
            notes="Retrospective prototype diagnosis; operator evidence unavailable.",
        )
    )

diagnostic_event_summary = pd.DataFrame(
    [
        {
            "Event ID": event.event_id,
            "Timestamp": event.timestamp,
            "Severity": event.severity,
            "Primary subsystem": event.primary_subsystem,
            "Probable diagnosis": (
                event.diagnoses[0].diagnosis
                if event.diagnoses
                else "Insufficient diagnostic evidence"
            ),
            "Confidence": (
                event.diagnoses[0].confidence if event.diagnoses else np.nan
            ),
            "Top feature": (
                event.top_features[0].feature if event.top_features else None
            ),
            "Retrospective lab moisture": event.lab_moisture_after_event,
            "Operator status": event.operator_status,
        }
        for event in diagnostic_events
    ]
)
display(diagnostic_event_summary.round({"Confidence": 3}))
for event in diagnostic_events:
    print(format_operator_report(event))
    print()

if diagnostic_events:
    first_event_evidence = pd.DataFrame(
        [item.as_dict() for item in diagnostic_events[0].top_features]
    )
    display(first_event_evidence.round(4))

    subsystem_score_table = pd.DataFrame(
        [event.subsystem_scores for event in diagnostic_events],
        index=[
            f"E{event_index + 1} | {pd.Timestamp(event.timestamp):%Y-%m-%d}"
            for event_index, event in enumerate(diagnostic_events)
        ],
    ).fillna(0.0)
    subsystem_display_names = {
        name: details["display_name"]
        for name, details in diagnostic_configuration["subsystems"][
            "subsystems"
        ].items()
    }
    subsystem_score_table = subsystem_score_table.rename(
        columns=subsystem_display_names
    )
    axis = subsystem_score_table.plot(
        kind="bar",
        figsize=(12, 6),
        width=0.8,
    )
    axis.set_title("MAP Dryer: Diagnostic Subsystem Scores by Alarm Episode")
    axis.set_xlabel("Diagnostic event")
    axis.set_ylabel("Normalized subsystem score")
    axis.set_ylim(0, 1)
    axis.tick_params(axis="x", rotation=15)
    axis.grid(axis="y", alpha=0.2)
    axis.legend(title="Subsystem", bbox_to_anchor=(1.02, 1), loc="upper left")
    axis.figure.tight_layout()
    axis.figure.savefig(
        DIAGNOSIS_FIGURE_OUTPUT_DIR / "01_episode_subsystem_scores.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.show()"""
            )
        ),
        tagged(
            new_markdown_cell(
                """## 36. Run coherent physical scenarios and the deterministic unit suite

The eight scenarios modify raw process measurements first, recompute all engineered features, apply the unchanged OCSVM detector, and then invoke diagnosis. Acceptance requires every scenario to be detected and its expected D01-D08 rule to be returned; isolated temperature jumps and stuck signals must resolve to instrumentation diagnoses."""
            )
        ),
        tagged(
            new_code_cell(
                """import os
import subprocess

physical_scenarios = build_physical_scenarios(reference_profile)
scenario_rows = []
for scenario_id, scenario in physical_scenarios.items():
    scenario_score = float(
        canonical_anomaly_score(
            one_class_svm_model,
            anomaly_scaler.transform(
                scenario.current.to_frame().T[MODEL_FEATURES]
            ),
        )[0]
    )
    detected = scenario_score >= ONE_CLASS_SVM_THRESHOLD
    scenario_event = diagnose_anomaly(
        timestamp=pd.Timestamp("2030-01-01")
        + pd.Timedelta(hours=2 * int(scenario_id[1:])),
        anomaly=detected,
        anomaly_score=scenario_score,
        threshold=ONE_CLASS_SVM_THRESHOLD,
        x_current=scenario.current,
        history_df=scenario.history,
        model=one_class_svm_model,
        scaler=anomaly_scaler,
        reference_profile=reference_profile,
        feature_metadata=diagnostic_configuration["feature_metadata"],
        subsystem_config=diagnostic_configuration["subsystems"],
        rule_config=diagnostic_configuration["rules"],
        threshold_config=diagnostic_configuration["thresholds"],
        config_versions=diagnostic_configuration["versions"],
    )
    returned_rules = [result.rule_id for result in scenario_event.diagnoses]
    scenario_rows.append(
        {
            "Scenario": scenario_id,
            "Injected behavior": scenario.name,
            "Anomaly score": scenario_score,
            "Detected": detected,
            "Expected rule": scenario.expected_rule_id,
            "Top returned rule": returned_rules[0] if returned_rules else None,
            "Expected rule returned": scenario.expected_rule_id in returned_rules,
        }
    )

scenario_acceptance = pd.DataFrame(scenario_rows).set_index("Scenario")
if not scenario_acceptance["Detected"].all():
    raise AssertionError("At least one physical scenario was not detected by OCSVM.")
if not scenario_acceptance["Expected rule returned"].all():
    raise AssertionError("At least one physical scenario missed its expected rule.")
if scenario_acceptance.loc["S06", "Top returned rule"] != "D06":
    raise AssertionError("Instrumentation jump did not outrank process-fault rules.")
if scenario_acceptance.loc["S07", "Top returned rule"] != "D07":
    raise AssertionError("Stuck-sensor diagnosis did not rank first.")
display(scenario_acceptance.round({"Anomaly score": 4}))

acceptance_plot = scenario_acceptance[
    ["Detected", "Expected rule returned"]
].astype(int).T
acceptance_plot.index = ["Detector raised anomaly", "Expected rule returned"]
figure, axis = plt.subplots(figsize=(12, 3.2))
sns.heatmap(
    acceptance_plot,
    annot=acceptance_plot.replace({1: "PASS", 0: "FAIL"}),
    fmt="",
    cmap=sns.color_palette(["#c0392b", "#2e8b57"], as_cmap=True),
    vmin=0,
    vmax=1,
    cbar=False,
    linewidths=1,
    linecolor="white",
    ax=axis,
)
axis.set_title("MAP Dryer: Physical Diagnostic Scenario Acceptance")
axis.set_xlabel("Physical scenario")
axis.set_ylabel("")
axis.tick_params(axis="x", rotation=0)
axis.tick_params(axis="y", rotation=0)
figure.tight_layout()
figure.savefig(
    DIAGNOSIS_FIGURE_OUTPUT_DIR / "02_physical_scenario_acceptance.png",
    dpi=300,
    bbox_inches="tight",
)
plt.show()

test_environment = os.environ.copy()
test_environment["PYTHONPATH"] = str(SRC_DIR)
unit_test_run = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
    cwd=PROJECT_ROOT,
    env=test_environment,
    capture_output=True,
    text=True,
    check=False,
)
print(unit_test_run.stdout)
print(unit_test_run.stderr)
if unit_test_run.returncode != 0:
    raise AssertionError("The deterministic diagnostic unit suite failed.")"""
            )
        ),
        tagged(
            new_markdown_cell(
                """## 37-38. Retrospective evidence, event export, and versioned deployment metadata

Laboratory moisture is attached only after diagnosis as retrospective evidence; it never enters model fitting, scoring, localization, rules, or severity. Operator and maintenance labels are not yet available, so the probable diagnoses remain unconfirmed. The final cell exports JSON events and a metadata bundle containing the detector score contract, threshold, train-only profile, exact feature order, configuration versions, and configuration hashes."""
            )
        ),
        tagged(
            new_code_cell(
                """DIAGNOSTIC_MODEL_OUTPUT_DIR = PROJECT_ROOT / "models" / "diagnosis"
DIAGNOSTIC_MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

diagnostic_events_path = (
    DIAGNOSTIC_MODEL_OUTPUT_DIR
    / "validation_test_diagnostic_events.diag_v1.0.json"
)
diagnostic_events_path.write_text(
    json.dumps(
        [event.as_dict() for event in diagnostic_events],
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)

diagnostic_bundle_path = save_diagnostic_bundle_metadata(
    DIAGNOSTIC_MODEL_OUTPUT_DIR / "diagnostic_bundle_metadata.diag_v1.0.json",
    detector_name="Tuned One-Class SVM",
    detector_parameters=best_one_class_svm_parameters,
    anomaly_threshold=ONE_CLASS_SVM_THRESHOLD,
    model_features=MODEL_FEATURES,
    reference_profile=reference_profile,
    config_versions=diagnostic_configuration["versions"],
    config_hashes=diagnostic_configuration["hashes"],
    diagnostic_version=diagnostic_configuration["thresholds"][
        "diagnostic_version"
    ],
)
feedback_template_path = (
    PROJECT_ROOT / "data" / "reference" / "diagnostic_event_history_template.csv"
)

deployment_outputs = pd.Series(
    {
        "Diagnostic events JSON": diagnostic_events_path,
        "Diagnostic bundle metadata": diagnostic_bundle_path,
        "Operator feedback template": feedback_template_path,
        "Configuration versions": diagnostic_configuration["versions"],
        "Reference rows": reference_profile.training_rows,
        "Lab moisture used online": False,
        "Confirmed event labels available": False,
    },
    name="Deployment output",
)
display(deployment_outputs.to_frame())"""
            )
        ),
        tagged(
            new_markdown_cell(
                """## Diagnostic-layer status and required next evidence

The modular diagnostic layer now satisfies the specification's implementation scope: unchanged OCSVM detection, train-only profiling, dual-signal localization, normalized subsystem scoring, temporal analysis, configurable D01-D08 rules, instrumentation discrimination, separate confidence/severity, deterministic JSON events, coherent scenario validation, unit tests, feedback fields, and versioned deployment metadata.

The result remains a **prototype decision-support system**. Production approval still requires approved PCS7 operating limits, higher-frequency historian data with time-based persistence recalibration, operator/maintenance-confirmed event labels, and event-level historical validation. Until that evidence exists, diagnoses are probable and listed causes are suspected checks—not confirmed root causes."""
            )
        ),
    ]

    notebook.cells[next_task_index:next_task_index] = diagnosis_cells
    if next_task_index + len(diagnosis_cells) < len(notebook.cells):
        final_cell = notebook.cells[next_task_index + len(diagnosis_cells)]
        if final_cell.cell_type == "markdown" and final_cell.source.lstrip().startswith(
            "## Next task"
        ):
            final_cell.source = """## Next task

Collect operator- and maintenance-confirmed event outcomes using the versioned feedback schema, replace prototype PCS7 limits with approved values, and rerun event-level chronological validation before any production deployment or supervised fault classifier is considered."""

    nbformat.write(notebook, NOTEBOOK_PATH)
    print(f"Updated {NOTEBOOK_PATH} with {len(diagnosis_cells)} diagnosis cells.")


if __name__ == "__main__":
    main()
