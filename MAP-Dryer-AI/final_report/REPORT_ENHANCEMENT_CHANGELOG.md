# Report enhancement change log

## Diagnosis of the previous version

The earlier report had a sound technical sequence, but it relied too heavily on descriptive text and repeated prototype caveats. Several claims had also drifted behind the current project state: the dashboard source was described as canonical TEST rather than the dedicated demo fork, the vacuum sign description conflicted with the positive canonical values, the manifest's seven-entry disturbance catalog was treated as complete, and the appendix file was not included in the compiled report.

Model reporting was incomplete. Ridge metrics were presented without an operational baseline, residual analysis or uncertainty study. The One-Class SVM was described mainly through its validation flag rate, without testing the frozen detector against the labelled episodes in the held-out canonical interval. The dashboard figures were older, lower-precision captures.

## Evidence added

- Added a reproducible, read-only report audit in `tools/generate_report_enhancement_evidence.py`.
- Compared Ridge with the strictly previous laboratory moisture baseline on identical TEST rows.
- Added residual distribution, autocorrelation, bias and fitted-level checks.
- Added a separate TRAIN-fit / VALIDATION-calibration / TEST-audit split-conformal pilot.
- Evaluated the frozen One-Class SVM on all 237,600 canonical TEST rows and reported row and episode response, normal-period flags, persistence and event grouping.
- Added a controlled `nu` sensitivity study showing the detection/flag-burden trade-off and the persistent feed-surge miss.
- Added a full accelerated analytical replay benchmark with explicit exclusions.
- Audited the CSV labels directly: 22 embedded episodes versus seven entries in the stale manifest catalog.
- Added a feature/formula/unit audit and corrected the vacuum convention at report level.
- Synchronized the final high-precision dashboard captures and documented the two-day demo fork separately from model evaluation.

## Writing and structure changes

- Rewrote the abstract, introduction, project objectives, data, model, runtime, Power BI, validation and conclusion chapters in a more direct engineering-student voice.
- Made the student's contribution explicit without inventing personal experience.
- Reduced generic AI-style transitions, repeated warnings and promotional claims.
- Added measurable prototype criteria and a clear existing-context versus student-contribution table.
- Added wet/dry-basis conversion and an honest rotary-dryer heat-balance framework, including the measurements missing for closure.
- Added peer-reviewed sources on soft sensors, chronological validation, One-Class SVM, conformal prediction, fault diagnosis and rotary-dryer modelling, plus IEC alarm-management guidance.
- Included the appendices in `main.tex`, expanded the table of contents to section level and added complete traceability/reproduction material.
- Gave each dashboard capture a dedicated landscape page for legibility.

## Final verification

- Compiled PDF: 49 physical pages.
- Python: 77 tests and 8 subtests passed.
- Power BI structure: 86 visuals and 114 field references resolve against 303 fields in six tables.
- Live PostgreSQL/TMDL check: all six views match.
- LaTeX: no undefined references, no overfull boxes and no rerun warning.
- Text extraction: no mojibake markers and no unresolved `??` references.

## Remaining project limitations

The canonical data are synthetic; the original generator code, seed and complete configuration are unavailable. There is no live PCS7/historian connection, no representative OCP fault-label set, no closed heat balance, no approved plant alarm limits and no autonomous control. The anomaly detector misses the held-out feed-surge episode. These limitations are now visible in the main results rather than confined to a final disclaimer.
