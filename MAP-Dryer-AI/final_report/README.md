# Final internship report

Main source: `main.tex`

Final compiled output: `MAP_Dryer_AI_Internship_Report.pdf`

The complete report, including the institutional cover and all report-authored captions and labels, is written in English. It uses numbered citations and one canonical 92-day evidence chain: executed Notebooks 01--04, the exact Notebook 03 moisture and Notebook 04 anomaly artifacts loaded at runtime, a held-out TEST replay, live PostgreSQL/Power BI contract checks, and updated model and data figures. It also retains two validated final SQL-backed Power BI renders, eight distinct project-specific MAP SOLUBLE PCS7 screens, four selected on-site photographs, organization-report context photographs and process-reference material from the supplied Souilmi report. The final screenshots use the active `PROTOTYPE · REPLAY` and `Replay / Refresh: 5 s` wording.

The compiled deliverable contains 48 physical pages and remains within the requested 50-page hard limit.

Compile from this directory with MiKTeX:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
Copy-Item build/main.pdf MAP_Dryer_AI_Internship_Report.pdf
```
