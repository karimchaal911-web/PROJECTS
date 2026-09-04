# Dashboard demonstration replay

`MAP_Dryer_Dashboard_Demo_5s.csv` is a dedicated, deterministic Power BI
demonstration stream. It contains the two final complete calendar days from
the authoritative 92-day canonical dataset (July 15–16, 2026) and eight
additional, temporally coherent episodes derived from measured residual
profiles of anomaly families already present in that dataset.

The file is not training, validation, or test evidence. It does not contain
manufactured model scores or predictions. The unchanged runtime preprocessing,
trained models, diagnosis logic, PostgreSQL schema, and Power BI report process
the process measurements during replay.

`MAP_Dryer_Dashboard_Demo_Scenarios.csv` is the traceability sidecar.
`MAP_Dryer_Dashboard_Demo_Audit.json` records integrity checks, protected-file
hashes, and unchanged-model inference behavior.

`MAP_Dryer_Dashboard_Warmup_5s.csv` contains the three canonical hours directly
before the visible replay. The service loads it only into the in-memory
residence-time/laboratory buffer, so the soft sensor has a prediction on the
first visible row. These rows are never replayed, inserted into PostgreSQL, or
shown in Power BI.

Regenerate and validate the fork explicitly with:

```powershell
python tools/build_dashboard_demo.py
```

The generator reads but never writes canonical datasets, notebooks, or model
artifacts. Sparse laboratory reference values are copied unchanged.
