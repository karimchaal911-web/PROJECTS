# FINAL SOUTENANCE — INTELLIGENT DIGITALIZATION OF SOLUBLE MAP PRODUCTION

A presenter-controlled cinematic 3D keynote for the OCP soluble MAP dryer
digitalization project. **14 scenes · 42 steps · 12–13 minutes · runs offline.**

The primary deliverable is an interactive React + Three.js experience, not a
slide deck. PDF, PPTX and MP4 exist only as fallbacks, and all three are
generated from the same captured frames so they cannot drift from it.

---

## Run it

```powershell
.\RUN_PRESENTATION.ps1
```

`RUN_PRESENTATION.ps1` is the single supported launcher name. It works from the
repository root and from this directory.

Opens the presentation fullscreen in Chrome or Edge with no browser chrome.
Press **F** for fullscreen, then drive it with the arrow keys.

Add `-Safe` for reduced-performance mode:

```powershell
.\RUN_PRESENTATION.ps1 -Safe
```

Nothing is fetched from the network at any point. This is verified, not assumed
— see `qa/FINAL_PRESENTATION_QA.md` §5.

### Controls

| Key | Action |
|---|---|
| `→` `Space` `PgDn` | next beat |
| `←` `PgUp` | previous beat |
| `G` then `1`–`9` `0` | jump to scenes 1–10 |
| `G` then `Q` `W` `X` `C` | jump to scenes 11–14 |
| `Esc` | cancel an armed `G` |
| `Home` / `End` | first / last scene |
| `F` | fullscreen |
| `P` | presenter notes (audience never sees this) |
| `S` | safe mode — visual downgrade only, position kept |
| `H` `?` | help |

---

## What to read first

| If you want to… | Read |
|---|---|
| Present it tomorrow | `speaker_notes/quick_cues.md` |
| Rehearse properly | `speaker_notes/full_script.md` — includes jury Q&A |
| Know what is true and what is not | `design/RESOURCE_AUDIT.md` |
| Understand the argument | `design/STORYBOARD.md` |
| Change something visual | `design/DESIGN_SYSTEM.md` |
| Change something that moves | `design/MOTION_SPEC.md` |
| Change the code | `design/THREEJS_SCENE_PLAN.md` |
| Trust the numbers | `qa/FINAL_PRESENTATION_QA.md` |
| Run the live dashboard demo | `demo/DEMO_INSTRUCTIONS.md` |

---

## The idea

The whole film is built on **one geometry, continuously reinterpreted**:

```
MAP granule stream  →  time axis  →  predicted moisture trace
     →  validation chart  →  Power BI visual  →  SQL and runtime  →  the dryer
```

Nothing disappears to be replaced. The audience should never feel that a slide
changed — only that they were shown another layer of the same object. The dryer
is present in all fourteen scenes, always turning, and scene 14 returns to scene
01's exact camera pose so the closing rhyme lands.

The argument in one line: **the process is continuous, laboratory visibility is
not, and that gap is worth closing with inference rather than with more
sampling.**

---

## Every number is real

No figure reaches the screen unless
`data_build/extract_presentation_data.py` can re-derive it from the exact model
artifacts in `models/5s/`. That script asserts its results against
`artifacts/notebook03_model_evaluation.json` and **fails loudly on drift**.

```powershell
python data_build/extract_presentation_data.py   # rebuild the data payloads
python data_build/qa_checks.py                   # 61 checks, currently all green
```

Headline evidence, all verified:

* **Moisture soft sensor** — Ridge, α = 10, 16 causally aligned features.
  R² `0.8245`, MAE `0.00107 % H₂O`, RMSE `0.00140 % H₂O` on a chronological
  hold-out of 165 laboratory targets.
* **Anomaly detector** — One-Class SVM, ν = 0.02, 15 process-only features,
  **unsupervised**. In the peak-risk held-out window the mean display risk is
  `0.804` inside a labelled `steam_dip` and `0.235` outside it; **73 of 79**
  warning-level points fall inside an event the model never saw labelled.
* **The gap** — a real 12-hour held-out window contains 8,640 process rows and
  **6** laboratory samples. Between the first two the product moved
  `0.0054 % H₂O`, unmeasured.

And what it is not: synthetic prototype data, generator-produced disturbance
labels, a calibrated display score rather than a probability, evidence
localisation rather than proven root cause, advisory only — with the laboratory
still the reference. The presentation says all of this on screen, in scene 09
and in a persistent badge, rather than leaving it to be extracted under
questioning.

---

## Layout

```
final_presentation_claude/
├── RUN_PRESENTATION.ps1              one-command launcher
├── FINAL_..._Claude.pdf              static fallback   (35 pages)
├── FINAL_..._Claude.pptx             deck fallback     (35 slides + notes)
├── FINAL_..._Claude_Backup.mp4       emergency playback (14:45, 1080p)
│
├── web/                              THE PRESENTATION
│   ├── src/
│   │   ├── state/scenes.js           the 14 scenes — single source of truth
│   │   ├── three/                    persistent world, rig, 15 layers
│   │   ├── overlay/                  DOM copy, rail, presenter HUD
│   │   └── lib/curves.js             the one geometry, and the world map
│   ├── public/data/                  7 verified JSON payloads
│   └── scripts/                      capture · record · offline proof
│
├── design/                           the design gate (5 documents)
├── speaker_notes/                    full script · quick cues
├── demo/                             live Power BI demo procedure
├── qa/                               executed QA record
├── data_build/                       extraction · fallbacks · QA · contact sheets
├── assets/                           source photography, dashboard captures
├── higgsfield/                       why generative assets were not used
└── exports/                          35 stills · contact sheets · offline proof
```

---

## Rebuilding

```powershell
cd web
npm install
npx vite build                        # → web/dist, ~4.2 MB, fully self-contained

node scripts/capture-scenes.mjs       # 41 stills + console-error report
node scripts/capture-scenes.mjs --offline   # proves it needs no network
node scripts/record-tour.mjs          # re-record the MP4 backup (~15 min)

cd ..
python data_build/build_fallbacks.py  # PDF + PPTX from the captured frames
python data_build/qa_checks.py        # 61 checks
```

---

## Notes on the build

* **Procedural geometry only.** No GLB, no Draco, no KTX2 — nothing binary to
  fail to load on unfamiliar presentation hardware. See `higgsfield/README.md`
  for why Blender and generative assets were evaluated and not used.
* **One persistent world.** Layers are never unmounted; scenes change presence.
  This is what makes the closing rhyme possible.
* **One GSAP timeline per transition.** Camera, lights, materials and layer
  presence are all children of it, so they cannot desynchronise. There is no
  independent `setTimeout` in the application.
* **Lag smoothing is disabled** so a dropped frame skips rather than stretching
  the scene — the presenter's pacing must not depend on the projector laptop.
* **The Power BI pages are the real exported report**, unmodified. The scene 09
  → 10 chart-becomes-visual transformation registers against a rectangle
  measured from the actual 1600×900 export.

---

## Relationship to the rest of the repository

This directory reads from the repository and writes nothing back to it. The
source of truth stays where it belongs:

| Input | Used for |
|---|---|
| `models/5s/` | The exact model artifacts, verified by SHA-256 |
| `artifacts/notebook0*.json` | Every metric, asserted against |
| `data/processed/` | Hold-out replay, gap window, manifold projection |
| `final_report/` | Process narrative, on-site photographs, PCS7 evidence |
| `POWERBI DASHBOARD/preview/` | The real dashboard pages |
| `resources/presentation_resources/` | OCP and SiteAssist art direction |

An earlier non-React attempt lived at `final_presentation/`. It was
deliberately not used as a foundation, reference or storyboard, and was
removed in the final repository audit; it remains in Git history.
**This directory is the canonical final version.**
