# RESOURCE AUDIT

**Audited:** 2026-08-27 · **Repository:** `MAP-Dryer-AI` · **Branch:** `experiment/ollama-dashboard-upgrade`

This audit establishes what is *true* about the project before any design
decision is made. Every claim the soutenance makes on screen must trace back to
a row in this document.

---

## 1. Technical source of truth

| Question | Verified answer | Evidence |
|---|---|---|
| What is the dataset? | Deterministic **synthetic** 92-day canonical CSV | `artifacts/notebook01_canonical_audit.json` |
| Dataset version | `map_canonical_5s_user_deterministic_v1.0` | `models/model_registry.json` |
| SHA-256 | `ae92165…fb0124` | registry + validation record |
| Process rows | **1,589,760** at a **5-second** grid, gap-free | audit `checks.gap_free_5_second_grid: true` |
| Interval | 2026-04-16 00:00:00 → 2026-07-16 23:59:55 | audit |
| Laboratory samples | **1,104** rows at **120 minutes** | audit |
| Supervised handoff | **1,103** rows (first lab timestamp excluded — no strictly prior lab input) | `notebook02_feature_handoff.json` |
| Disturbances implemented | **7** | audit `disturbance_count` |

**Cadence language is constrained.** The audit itself records the interval
interpretation as *"prototype temporal resolution and replay cadence; not a
proven PCS7 historian acquisition interval."* On-screen the presentation must
therefore say **`PROTOTYPE REPLAY - 5 s TICK`**, never "the plant samples every
five seconds". Three distinct five-second things must not be conflated: the
replay writes one row every 5 s, the report page auto-refreshes on a 60 s cycle
(`AUTO 60 SEC` on the screen), and **no physical instrument sampled at 5 s** —
that is the prototype historian grid.

---

## 2. Models — what they actually are

### Moisture soft sensor
* Family: **Ridge**, `alpha = 10.0`, inside a `StandardScaler → Ridge` pipeline.
* Inputs: the original **16 ordered features** — 9 residence-time-aligned
  process values, 2 strictly-previous laboratory values (`product_density`,
  `final_product_temp`), and 5 engineered terms (`temperature_drop`,
  `air_product_delta`, `air_per_feed`, `steam_temp_interaction`,
  `heating_index`).
* **No rolling means/std, no "last" columns, and the quality target is never an
  input.**
* Selection: five-fold `TimeSeriesSplit` on TRAIN only; chosen by VALIDATION RMSE.
* Split: chronological TRAIN 772 / VALIDATION 166 / TEST 165.

**Held-out TEST (re-derived and asserted in `data_build/extract_presentation_data.py`):**

| Metric | Value |
|---|---|
| MAE | `0.0010686339` % moisture |
| RMSE | `0.0014026195` % moisture |
| R² | `0.8245295479` |
| bias | `+0.0000661688` |
| max abs error | `0.0056205663` |
| n | 165 |

Candidate validation RMSE (real, from `notebook03_model_evaluation.json`):
Ridge `0.001357` · Elastic Net `0.001362` · Linear Regression `0.001367` ·
Gradient Boosting `0.001430` · Random Forest `0.001467`.
→ The honest story is *the simple regulariser won*, not *we used AI*.

**Scale trap.** Final moisture is on a **percentage-point** scale:
`0.075` means `0.075 %` moisture, not `7.5 %`. All on-screen figures use 3–4
decimals and name the quantity beside the `%`, matching the shipped Power BI
report — see the engineering typography policy in `DESIGN_SYSTEM.md`.

### Anomaly detector
* Family: **One-Class SVM**, `nu = 0.02`, `gamma = "scale"` (fitted γ ≈ 0.06654).
* **Unsupervised novelty detection.** It learns *normal operation only*. It
  never received a disturbance label at any point.
* Inputs: **15 process-only** features (9 process variables + 6 instant
  engineered terms: `air_product_delta`, `cooler_delta`, `air_per_feed`,
  `steam_per_feed`, `thermal_load`, `thermal_exposure`).
* TRAIN process rows 1,111,681; deterministic fit sample 6,000; the fitted model
  retains **136 support vectors** — these are the points that define the learned
  boundary and are rendered literally in Scene 08.
* Risk display: `risk = 1 / (1 + exp(score / 2.7968971))`. Boundary → 0.50.
  Warning 0.50, critical 0.80. **Not a probability of failure.**
* VALIDATION novelty flag rate: 5.925 %.

### Diagnosis
Robust reference quantiles + ranked direct contributors + process rules mapped
to five subsystems (`thermal_system`, `drying_air_exhaust`, `feed_loading`,
`cooling_system`, `instrumentation`). Contract wording: *"evidence localization,
not proven causality."*

---

## 3. New evidence derived for this presentation

Computed in `final_presentation_claude/data_build/extract_presentation_data.py`
from the exact artifacts. Reproducible, not fabricated.

### 3.1 The visibility gap has a real shape
Held-out window **2026-07-05 00:00 → 12:00**: 8,640 process rows,
**6 laboratory samples**. Real lab moisture: `0.0742, 0.0796, 0.0804, 0.0806,
0.0812, 0.0800 %`. The continuous soft-sensor trace over the same window
(695 points, runtime residence-time alignment reproduced exactly) ranges
`0.0754 → 0.0806`.

> Between the 00:00 and 02:00 laboratory results the true product moved by
> `0.0054 %` moisture — and nothing measured it. That is the gap, drawn from data.

### 3.2 The unsupervised detector lands on a labelled disturbance
Peak-risk 24-hour held-out window: **2026-07-07 06:00 → 2026-07-08 06:00**.
It contains one labelled synthetic disturbance, `steam_dip`, spanning
**2026-07-08 05:00:00 → 05:44:30 (44.5 min)**.

| Measure | Value |
|---|---|
| Mean display risk **inside** the labelled event | **0.804** |
| Mean display risk **outside** it | **0.235** |
| Points above the 0.50 warning line | 79 |
| …of which fall **inside** the labelled event | **73** |
| Peak risk | **0.976** |

**Framing rule.** The label comes from the synthetic generator and is used for
*validation display only*. The detector is unsupervised and never saw it. The
data is synthetic; this is prototype evidence, not plant validation. Every
on-screen use of this result carries that qualifier.

### 3.3 The learned region is renderable
PCA(3) on the standardised TRAIN process rows explains **93.7 %** of variance
(0.642 / 0.160 / 0.135). In that projection the disturbance trajectory sits at
mean distance **4.36** from the normal centroid versus **2.13** outside the
event — visibly leaving the cloud. Support vectors project onto the cloud's
outer shell, exactly as they should.

---

## 4. Runtime and supervision layer

```
canonical CSV → realtime_service.py (5 s replay + inference)
              → PostgreSQL  dryer_map · dryer_model_outputs · dryer_abnormal_variables
              → five views  vw_dryer_dashboard_powerbi · vw_dryer_contributors_powerbi
                            vw_dryer_lab_samples · vw_dryer_anomaly_events
                            vw_dryer_overview_trends_powerbi
              → Power BI Desktop (PBIP, DirectQuery, ~5 s page refresh)
```

Power BI **reads views only**. It never loads a joblib and never runs inference.
Smoke replay latency: 9 ms average, 47 ms maximum. `pytest -q`: 33 passed,
8 subtests, 2.89 s. Runtime contract checks: 16/16. View contracts: 5/5.

**The real dashboard has two pages**, and the presentation uses the actual
captures:
1. *Operations Overview* — predicted moisture, latest lab moisture, validated
   moisture error, current anomaly risk, process status, anomaly severity,
   rolling 8-hour moisture & risk trend, critical process variables, diagnosis
   context, operator guidance.
2. *Diagnostics & Root Cause* — anomaly risk timeline with warning/critical
   bands, selected event card, top abnormal contributors with normalised
   deviation, cause analysis and recommended verification, recent events table.

Both pages carry a visible `PROTOTYPE · REPLAY` pill and an advisory footer.
Nothing beyond these capabilities may be shown or implied.

---

## 5. Industrial process — verified sequence

From `final_report/chapters/chapter2.tex`, itself built on the supplied process
report, field notes, on-site photographs and MAP SOLUBLE PCS7 screens:

```
phosphoric-acid pretreatment → ammonia vaporization → neutralization
→ buffer / stabilization → concentration & crystallization → centrifugation
→ DRYING → cooling / conditioning
                       ↑
      mother-liquor recycle returns to neutralization
```

Drying-stage variable map (report Fig. `dryzoom`):
* **In:** wet crystals feed rate; steam pressure + dryer-air temperature;
  air flow + fan speed + vacuum.
* **In the dryer:** heat and mass transfer, residence time.
* **Out:** cooler air temperature → final product temperature + moisture.

Reaction shown in the report: `H₃PO₄ + NH₃ ⇌ NH₄H₂PO₄`.

**Constraint carried into the 3D model:** the report explicitly refuses to map
photographed equipment to PCS7 tags. The presentation therefore models the
dryer as a *credible simplified rotary dryer*, labels only repository variables,
and never asserts equipment identity or tag numbers.

---

## 6. Visual reference material

### 6.1 Real process photographs — the most valuable art direction input
`assets/process/`

| File | What it proves |
|---|---|
| `rotary_dryer_shell.jpeg` | Large horizontal drum, riding ring/tyre band, support structure, grating platforms, handrails, overhead ductwork, pale MAP dust coating everything |
| `drying_section_structure.jpeg` | **The plant's structural steel is painted green**, with yellow handrails, grey insulated columns, blue pump motors, dusty concrete |
| `downstream_solids_transfer.jpeg` | Downstream conveying context |
| `soluble_map_storage.jpeg` | Real product identity: **"MAP Monoammonium Phosphate 12-61-00 · Soluble in water"** |

> **Key art-direction finding.** OCP green is not only a logo colour — the
> plant steel is literally green. The brand palette and the industrial reality
> are the same palette. The 3D world can be OCP-grounded *and* photoreal at the
> same time, with no styling lie. This decision drives the whole design system.

### 6.2 PCS7 screens
`assets/process/pcs7_*.jpeg` — 8 real supervised screens (neutralization,
buffer, crystallization 300/400, centrifugation, drying, ammonia vaporization,
acid scrubber). Used as **evidence of the supervised context** in Scene 03/07,
never as an interface to imitate and never with tag-level claims.

### 6.3 Model result figures
`assets/model_results/` — 20 notebook figures. **These are rebuilt, not
embedded**: the underlying values are re-derived from artifacts so the on-screen
charts are native, animatable and projector-legible, while the numbers are
byte-identical to the notebooks.

### 6.4 Inspiration references
`resources/presentation_resources/screenshots/` (project root) — the single
canonical copy of the reference captures.

| Reference | Extracted principle | Rejected |
|---|---|---|
| **OCP** (`ocp_reference_01/02/03`) | Cream/ivory editorial ground, deep-forest headline green, thin numbered progress rails (`01 —— 05`), outline pill buttons, full-bleed earth photography, one idea per band | Corporate copy, carousels, marketing tone |
| **SiteAssist** (`siteassist_reference_01/02/03`) | Wide uppercase display type, small square accent marker, aerial industrial plates, restrained technical metadata, generous whitespace | Purple brand accent, SaaS nav chrome |
| **Otsuka /zeroz** | Continuous camera choreography, spatial rather than page-based progression, seamless state change | Scroll-driven pacing (this is presenter-driven) |
| **KMZ Industries** | Believable heavy-equipment scale and proportion | Catalogue-style equipment hero shots |

### 6.5 Derived palette (sampled from the actual assets)

| Token | Hex | Sampled from |
|---|---|---|
| OCP green | `#007830` | `assets/original/ocp.png` dominant |
| OCP lime | `#84B40C` | `assets/original/ocp.png` secondary |
| Deep forest | `#003C30` | Power BI sidebar, dominant |
| Warm ivory | `#FCF0D8` | Power BI card ground |
| Plant steel green | `#2E4A34` | `drying_section_structure.jpeg` |
| Dust / olive grey | `#48483C` | `drying_section_structure.jpeg` dominant |

---

## 7. Explicit no-go list produced by this audit

1. No claim that the plant historian samples every 5 s.
2. No supervised framing of the One-Class SVM; no "trained on anomalies".
3. No moisture figure written as a percent-of-100 (`7.5 %`).
4. No closed-loop control, no automatic write to PCS7, no replacement of the lab.
5. No PCS7 tag ↔ photograph ↔ dataset mapping.
6. No invented dashboard capability, ROI figure, or plant-validation claim.
7. No metric that is not re-derivable by
   `data_build/extract_presentation_data.py`, which asserts against
   `artifacts/notebook03_model_evaluation.json` and fails loudly on drift.

---

## 8. Prior presentation attempts

`final_presentation/` contains an earlier non-React Three.js + GSAP attempt.
It was deliberately **not** read for storyboard, layout, scene composition,
motion or visual direction, and nothing in it is inherited. It is left
untouched. This audit and everything under `final_presentation_claude/` derive
directly from the repository, the report and `resources/`.
