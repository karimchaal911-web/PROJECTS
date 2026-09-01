# Final internship report

Main source: `main.tex`

Final deliverable: `MAP_Dryer_AI_Internship_Report.pdf`

The final report contains 47 physical pages. It is A4 portrait except for two dedicated landscape pages that keep the final Power BI dashboard captures readable. The report uses the supplied deterministic 92-day canonical source for model evidence and keeps the separate two-day injected dashboard replay explicitly limited to jury demonstration.

The evidence path now includes:

- chronological Ridge selection and untouched TEST metrics;
- comparison with the previous-laboratory-moisture persistence baseline;
- residual and persistence-baseline diagnostics;
- held-out One-Class SVM response by synthetic disturbance episode and ranked-contributor workflow;
- full accelerated analytical replay;
- current six-view PostgreSQL/Power BI contract validation;
- concise claim-to-artifact traceability and reproducibility commands.

Regenerate the independent report evidence from the project root:

```powershell
$env:PYTHONPATH="src"
python tools/generate_report_enhancement_evidence.py
```

Compile from `final_report` with MiKTeX:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
Copy-Item build/main.pdf MAP_Dryer_AI_Internship_Report.pdf
```

Current verification commands:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q
python tools/validate_report_fields.py
python realtime_pipeline/src/verify_powerbi_views.py
```

See `REPORT_ENHANCEMENT_CHANGELOG.md` for the evidence and writing changes and `FINAL_SELF_EVALUATION.md` for the remaining limitations.
