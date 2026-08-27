# Final QA - Cinematic Soutenance

Date: 2026-08-27

Target: 1920x1080, 16:9

Canonical scene count: 15

## Live 3D experience

- Production build: PASS (`vite build`).
- Persistent world: PASS; about 303 objects and 115 tracked materials.
- Standard captures: PASS; 15/15 PNGs at 1920x1080.
- Safe capture: PASS at 1366x768.
- Autoplay: PASS; scene 1 advanced without click in browser QA.
- Pause/resume: PASS; scene/progress remained stable while paused and resumed correctly.
- Reduced motion: PASS; media emulation resolved scene 4 immediately and set the reduced-motion state.
- Browser console/page errors: PASS; none in scene capture or browser QA.
- Fallback panel: PASS; hidden during normal/safe operation.
- Camera continuity: PASS; curved retargetable paths, FOV/roll changes, drift, focus, fog, light, and visibility channels.
- Interaction fallback: PASS; arrows/Home/End/Q&A navigation, Space pause, R restart, P cues, S safe, F fullscreen.

## Visual review

- Scene montage: `qa/cinematic-montage.png`.
- PowerPoint-render montage: `qa/pptx-montage.png`.
- Dryer hero/cutaway: PASS; rotation, lifters, particle cascade, heat field, vapor, sensor pulses.
- Time-axis scene: PASS; sparse laboratory anchors and dense replay pulses are spatial, not chart-only.
- Preprocessing/architecture: PASS; signals structure into gates and a five-layer 3D pipeline.
- Intelligence split: PASS; Ridge and One-Class SVM have different geometries and colors.
- Validation: PASS; authentic chronological hold-out plot and visible metrics/qualifiers.
- Control room: PASS; authentic overview/diagnostics previews integrated into a curved environment.
- Closing: PASS; dryer remains in motion while the visibility ribbon continues past lab anchors.

## Claim accuracy

- Ridge TEST metrics: PASS against `models/model_registry.json` and `models/5s/training_report.json`.
  - R2 0.8245295479, displayed 0.8245.
  - MAE 0.0010686339, displayed 0.001069.
  - RMSE 0.0014026195, displayed 0.001403.
- Ridge alpha 10 and 16 features: PASS.
- One-Class SVM 15 process-only features: PASS.
- Validation novelty-flag rate 0.05925 / 5.925 percent: PASS against `artifacts/notebook04_anomaly_evaluation.json`.
- Dataset counts: PASS against `data/processed/MAP_Dryer_Canonical_5s.manifest.json` and training report.
  - 1,589,760 replay rows.
  - 1,104 laboratory observations.
  - 1,103 supervised rows.
- Synthetic/reproducibility limitation: explicit in scenes, notes, README, and roadmap.
- Five-second qualifier: explicit as prototype replay/visualization, not plant historian frequency.
- Laboratory-reference qualifier: explicit in Ridge and closing scenes.
- Power BI role: explicit as visualization only; Python runs models.
- Advisory/no-write-back/no-live-PCS7/no-closed-loop boundary: explicit.
- Risk-not-probability and evidence-not-causality boundaries: explicit.

## PowerPoint, PDF, and film

- PowerPoint: PASS; 15 slides, 960x540-point 16:9 page, native PowerPoint open/render succeeded.
- Embedded media: PASS; `ppt/media/media1.mp4` present, 53,235,795 bytes.
- Slide 1 autoplay: PASS; media shape found and `PlayOnEntry = -1`.
- Notes: PASS; 15 notes-slide XML parts and 15 notes with text.
- PowerPoint slide rendering: PASS; 15/15 1920x1080 PNG exports.
- PDF: PASS; 15 pages, 960x540 points, rendered through Poppler.
- Film: PASS; 83 seconds, 1920x1080, H.264, yuv420p, 30 fps, no audio.
- Artifact sizes:
  - PPTX: 70,690,989 bytes.
  - PDF: 2,226,608 bytes.
  - MP4: 53,235,795 bytes.

## Repository regression

- `pytest -q`: PASS; 33 tests and 8 subtests.
- Production dependencies (`npm audit --omit=dev`): PASS; 0 vulnerabilities.

## Delivery note

The web version is the highest-fidelity live 3D experience. The PowerPoint embeds the complete film on slide 1 and retains chapter frames for Q&A. The PDF is intentionally static. Media playback should be tested once on the final presentation machine because Office security/media policies are machine-specific.
