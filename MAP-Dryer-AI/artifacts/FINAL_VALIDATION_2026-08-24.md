# Final canonical implementation validation — 2026-08-24

## Canonical source

- Supplied source: `data/raw/MAP_Dryer_Canonical_5s_deterministic.csv`
- Active processed path: `data/processed/MAP_Dryer_Canonical_5s.csv`
- Dataset version: `map_canonical_5s_user_deterministic_v1.0`
- Supplied source filename: `MAP_Dryer_Canonical_5s_deterministic.csv`
- SHA-256: `ae9216518e73e9b2a5101205774fa8235ffca0964a799b7980fbae6561fb0124`
- Interval: 2026-04-16 00:00:00 through 2026-07-16 23:59:55 (92 consecutive days)
- Process grid: 1,589,760 unique, monotonic, gap-free timestamps at 5 seconds
- Laboratory schedule: 1,104 rows at 120 minutes
- Supervised handoff: 1,103 rows; first lab timestamp excluded because no strictly previous laboratory input exists

## Chronological moisture evaluation

- TRAIN: 772 rows (69.9909%), 2026-04-16 02:00:00 through 2026-06-19 08:00:00
- VALIDATION: 166 rows (15.0499%), 2026-06-19 10:00:00 through 2026-07-03 04:00:00
- TEST: 165 rows (14.9592%), 2026-07-03 06:00:00 through 2026-07-16 22:00:00
- Time-aware tuning: five-fold `TimeSeriesSplit` on TRAIN only
- Selected by VALIDATION RMSE: Ridge (`alpha=10`)
- Feature count: the original 16 ordered features; direct residence-adjusted process values and strictly previous laboratory density/temperature inputs are used, with no mean/std/last model columns and no quality target as an input
- TEST: MAE 0.0010686339; RMSE 0.0014026195; R² 0.8245295479; bias 0.0000661688; maximum absolute error 0.0056205663
- Artifact: `models/5s/quality_moisture_pipeline.joblib`
- Artifact SHA-256: `b525c7b8598e90fb831db30612b70e7b6ded9de36edd0fc99f9b1753a7b00858`

## Notebook execution

- Notebook 01: original 17-cell structure and IDs preserved; 4 source cells adapted; 7/7 code cells executed; 0 error outputs
- Notebook 02: original 36-cell structure and IDs preserved; 7 source cells adapted; 20/20 code cells executed; 0 error outputs
- Notebook 03: all original 49 cells and IDs preserved; exactly two requested Elastic Net code cells added; 28/28 code cells executed; 0 error outputs
- Notebook 04: original 64-cell structure and IDs preserved; 9 source cells adapted; 32/32 code cells executed; 0 error outputs

## Chronological anomaly evaluation

- Notebook 04 depends on the audited Notebook 03 split and canonical handoff
- Selected runtime detector: One-Class SVM with 15 ordered process-only features
- TRAIN process rows: 1,111,681; deterministic fit sample: 6,000 rows
- VALIDATION check: 20,000 rows; observed novelty flag rate: 5.925%
- Model: `models/5s/anomaly_model.joblib`; SHA-256: `07bce32b6bf72a2adcc7196b72a7960d0fd3f46925eea291d51d1dbb6722bb61`
- Scaler SHA-256: `af28219037fd559500ba53ffcb5f54fdc5f0d9d545874392e0152ef56deb4fe1`
- Reference profile SHA-256: `b83fe03d03cec3086858c7b5497fecafc65c833a1604a267875aef5df48dfd44`

## Runtime and Power BI

- Runtime contract checks: 16 of 16 passed, including exact Notebook 03 moisture and Notebook 04 anomaly artifacts and ordered feature contracts
- Replay: `data/processed/MAP_Dryer_TEST_Replay_5s.csv`, 237,600 rows and 165 laboratory rows, derived from chronological TEST
- Replay SHA-256: `cec99e6a984a11440bfa06230b877f6231299bc9213bd5acb77cfe605553b2c2`
- PostgreSQL smoke replay: 1,500 rows, 2 laboratory rows, 0 anomaly flags, 0 grouped events, 9/47 ms average/maximum cycle latency
- Live PostgreSQL/TMDL verification: five of five view contracts passed
- View populations: dashboard 1,500; contributors 0; labs 2; events 0; overview 1,500

## Tests and report

- `pytest -q`: 33 passed and 8 subtests passed in 2.89 seconds
- LaTeX: two successful `pdflatex` passes; no undefined references or missing figures
- PDF: `final_report/MAP_Dryer_AI_Internship_Report.pdf`, 46 pages
- PDF SHA-256: `e137d7e32491175ec84c0379b5a04f5438053625b4cffb456654a57139af2064`
- Visual QA: affected canonical-data, model, runtime, results, conclusion and bibliography pages rendered and inspected
