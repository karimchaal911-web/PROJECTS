# FINAL PRESENTATION — QA RECORD

**Build reviewed:** 2026-08-27 · **Verdict: ready to present.**

Everything below was executed, not asserted. The automated portion is
reproducible with:

```powershell
python final_presentation_claude/data_build/qa_checks.py
```

Latest run: **61 checks · 61 passed · 0 failed**, plus
`node web/scripts/qa-controls.mjs` — **20 checks · 20 passed · 0 failed**.

All four deliverables were regenerated from the same final build: the 35 stills,
the PDF, the PPTX and the MP4 all show identical scenes.

---

## 1. Technical QA — is every claim true?

The rule for this build was that no number reaches the screen unless
`data_build/extract_presentation_data.py` can re-derive it from the exact model
artifacts. That script asserts against
`artifacts/notebook03_model_evaluation.json` and **fails loudly on any drift**,
so a stale figure cannot silently survive a rebuild.

| Claim on screen | Verified against | Result |
|---|---|---|
| MAE `0.0010686339` % H₂O | notebook 03 TEST metrics | exact to 1e-9 |
| RMSE `0.0014026195` % H₂O | notebook 03 | exact |
| R² `0.8245295479` | notebook 03 | exact |
| bias, max abs error | notebook 03 | exact |
| n = 165, chronological hold-out | notebook 03 split | exact |
| Candidate validation RMSE ×5 | notebook 03 `candidate_results` | all five exact |
| Ridge selected, α = 10 | notebook 03 `selected_model` | exact |
| One-Class SVM, ν = 0.02, 15 features | notebook 04 + feature schema | exact |
| Warning 0.50 / critical 0.80, not a probability | notebook 04 risk calibration | exact |
| 1,111,681 TRAIN process rows | notebook 04 | exact |
| 1,589,760 process rows, 92 days, Δt = 5 s | notebook 01 audit | exact |
| Laboratory interval 120 min | notebook 01 audit | exact |
| Model artifacts on disk | SHA-256 vs `models/model_registry.json` | 4/4 match |

**Language checks** — the claims that are easiest to overstate:

* Cadence is described as *prototype replay*, and the audit's own wording
  (*"not a proven PCS7 historian acquisition interval"*) is carried into
  `facts.json` and asserted by the QA script.
* The anomaly detector is described as **unsupervised novelty detection**
  everywhere. The `steam_dip` label is carried with an explicit
  `labelSource` field stating it is generator ground truth used for display only
  and never given to the model — asserted in QA.
* Anomaly risk is flagged `isProbability: false` in the payload and described on
  screen as a display score.
* Moisture is always shown on the percentage-point scale with 3–5 decimals and
  an explicit unit. No figure anywhere is written as a percent-of-100.
* No PCS7 tag, equipment identity or dimension is asserted by the 3D model.
* No ROI figure, no closed-loop claim, no suggestion the laboratory is replaced.

**New evidence introduced by this presentation** (derived, not invented — see
`design/RESOURCE_AUDIT.md` §3):

* Gap window `2026-07-05 00:00 → 12:00`: 8,640 process rows, **6** laboratory
  samples, real movement of `0.0054 % H₂O` between the first two.
* Peak-risk window: mean display risk **0.804 inside** the labelled `steam_dip`
  versus **0.235 outside**; **73 of 79** warning-level points inside it.
* PCA(3) on the standardised TRAIN rows explains **93.7 %** of variance, which
  is why the learned region can be rendered honestly in three dimensions.

---

## 2. Visual QA

All 35 presenter steps were captured at 1920×1080 and reviewed individually and
as contact sheets (`exports/contact_sheet_*.png`).

**Defects found and fixed during review:**

| Defect | Cause | Fix |
|---|---|---|
| Every metal surface rendered black | `metalness` with no environment map | Procedural `RoomEnvironment` via PMREM, generated in memory |
| Ridge coefficient bars never appeared | `coefficients.json` was missing from the data loader's fetch list | Added; QA now asserts all seven payloads |
| Telemetry chips absent in the DATA beat | Beat-level layer overrides were declared but the rig only applied scene-level layers | Rig merges `beat.layers` over `scene.layers` |
| Architecture and runtime labels ghosting over later scenes | Meshes faded with presence but troika text did not | Label groups gated on a presence threshold |
| Runtime slabs invisible in scene 11 | Dark materials at 60+ units erased by fog | Brighter emissive slabs, `fog: false`, closer camera |
| Laboratory dots invisible in editorial mode | Cream marks on a cream ground | Dark ink in editorial; the measurement stays the most salient mark |
| The dryer occluded by a foreground column | Camera-side column row ran through the sightline | Bays in front of the dryer removed from that row |
| Dust motes read as stars | Open-topped hall | Roof plane added; dust confined below it |
| Subscript `₂` rendered as tofu in-world | Font subset coverage | ASCII folding in world text; DOM keeps proper typography |
| Evidence panels overlapping each other | Four charts sharing one rectangle | Rebuilt as a vertical wall the camera reads downward |

**Checked and accepted:**

* Copy occupies at most five of twelve columns; the subject owns the centre.
* All type sits on a gradient scrim, never on a card.
* Minimum on-screen type is ≥ 22 px at 1920×1080.
* Hierarchy is carried by luminance, so the composition survives greyscale and a
  low-contrast projector.
* Warning/critical states carry line weight and a monospace label as well as
  colour — no information is colour-only.
* At most two accent colours are visible in any frame.

**Weakest frames, accepted knowingly:** step 15 (`ONE STREAM. TWO MODELS.`) is a
short transitional beat carried mostly by the copy while the packet stream
visibly bifurcates. It is the least visually dense frame in the film and it is
three seconds long.

---

## 3. Motion QA

Played end to end repeatedly, and stepped forwards and backwards at speed.

| Check | Result |
|---|---|
| Black flashes between scenes | None. Nothing unmounts; presence tweens |
| Asset pop-in | None. All seven payloads and both textures load behind the boot gate |
| Loading gaps mid-show | None. Geometry is procedural and built once |
| Scene resets | None. The world is persistent; scene 14 returns to scene 01's exact pose |
| Easing consistency | One transition timeline per step; no independent `setTimeout` anywhere |
| Interruption mid-transition | Timeline killed, world tweens to the settled state, next transition starts from there |
| Rapid presses | Guarded at 120 ms; cannot desynchronise |
| Backward navigation | Reverses the same poses at 0.7× duration |

A separate functional pass exercises what a presenter actually does under
pressure — `node web/scripts/qa-controls.mjs`, **20 checks, all passing**:
scene jumps by number key, `Shift`+number for scenes 11–14, forward and
backward within a scene, 25 hammered presses, the presenter HUD and its cues,
the help panel, safe mode toggled mid-scene without losing position, and the
boundary badge appearing only on scenes that show a model result.

One behaviour is deliberate and is documented for the presenter: **holding the
arrow key does not fast-forward.** Repeats inside 120 ms are dropped so a stuck
key cannot run the show away; jumping several scenes is done with the number
keys.

**The most consequential defect found in the whole build was here.** GSAP's
default lag smoothing clamps large frame deltas, so on a machine dropping frames
a 2.2-second transition stretched to roughly twenty seconds. It was invisible on
a fast machine and would have destroyed the pacing on unfamiliar projector
hardware. `gsap.ticker.lagSmoothing(0)` now makes a hitch skip frames instead of
stretching the scene, so the presenter's timing does not depend on the GPU.

### Launcher

Found after the first end-to-end run and fixed. The launcher shelled out to
`npx vite preview`, which failed in two independent ways:

* `npx.cmd` is a shim that **exits immediately** while the real server keeps
  running detached, so the launcher's `Wait-Process` returned at once and could
  neither hold nor stop the server.
* It then waited a **fixed three seconds** before opening the browser. Vite took
  longer to bind the port, so the window opened onto `ERR_CONNECTION_REFUSED`.

`Start-Process` also does not inherit PowerShell's location, so the server was
being started from the wrong directory.

Replaced with `web/scripts/serve.mjs` — about sixty lines on Node's own `http`
module, no dependencies, binding in milliseconds. The launcher now passes
`-WorkingDirectory` explicitly and **polls the port until it answers** (up to
20 s) before opening the browser, failing with the server's own stderr if it
never comes up. Verified: correct MIME types for JSON, PNG and WOFF, path
traversal blocked, and the process stays alive so Ctrl+C stops it.

---

## 4. Performance QA

| Item | Measured / budgeted |
|---|---|
| Built bundle | **4.2 MB** total (JS 1.35 MB, gzip ≈ 400 KB) |
| Data payloads | 7 files, 487 KB raw |
| Triangles | ≈ 62 k |
| Draw calls | ≈ 55 |
| Shadow-casting lights | 1, frustum fitted to the dryer |
| Post-processing passes | 0 — bloom replaced by additive emissives, vignette by CSS |
| Imported 3D assets | 0 — no GLB, no Draco, no KTX2 to fail on unfamiliar hardware |

Safe mode (`S`, or automatic on a slow device or `prefers-reduced-motion`) drops
DPR to 1.0, disables shadows, and reduces granules 2600→700, dust 1800→0,
manifold points 2400→900, packets 900→260. **It is a visual downgrade only** —
every scene, beat, number and transition still happens, and it can be toggled
mid-scene without losing position.

Failure behaviour is defined for WebGL unavailable, context lost mid-show, a
failed payload, a failed texture and a frame-rate collapse
(`design/THREEJS_SCENE_PLAN.md` §9).

---

## 5. Offline QA — the check that mattered

The presentation must run with the network unplugged. Asserting that was not
enough, so the capture harness gained an `--offline` mode that aborts every
non-loopback request and fails the run if one is attempted.

**The first offline run failed.** troika-three-text reaches for
`cdn.jsdelivr.net/gh/lojjic/unicode-font-resolver` whenever a character falls
outside the supplied font, and three in-world strings triggered it —
producing `Failed to fetch` and an unhandled page error. On a machine with no
network in the room, that would have surfaced during the soutenance.

Fixed by folding every in-world string to the bundled Latin subsets in
`src/three/WorldText.jsx`, so the resolver is never reached. The DOM overlay is
unaffected and still renders proper `% H₂O`, `Δt` and `α`.

**Current state, verified by a full 35-step run with the network blocked:**

* External requests attempted: **0**
* Console errors: **0**
* Steps rendered: **35 / 35**

Fonts (66 files), both dashboard captures, all seven data payloads and the
favicon are bundled. No CDN, no web-font dependency, no cloud runtime.

---

## 6. Narrative QA

After one viewing, can the jury state the seventeen points listed in
`design/STORYBOARD.md`? Walked scene by scene against that list.

| # | Point | Where it lands |
|---|---|---|
| 1 | OCP / MAP context | 01, 02 |
| 2 | What soluble MAP is | 02 (real 12-61-00 specification) |
| 3 | The production sequence | 03 |
| 4 | Why the dryer matters | 04 |
| 5 | Why moisture matters | 02 → 04 |
| 6 | Why sparse laboratory data is a problem | **05** |
| 7 | Why the soft sensor exists | 06 |
| 8 | Why One-Class SVM anomaly detection exists | 06 beat 3, 08 |
| 9 | How the process becomes data | 07 |
| 10 | How both intelligence layers work | 08 |
| 11 | How the models were validated | 09 |
| 12 | What the data limitations are | 09 beat 4, and the persistent boundary badge |
| 13 | How SQL fits in | 11 |
| 14 | How Power BI fits in | 10, 11 |
| 15 | How the prototype supports supervision | 10, 12 |
| 16 | What exists today | 13 beat 1 |
| 17 | What remains future work | 13 beat 2 |

All seventeen are covered, and the three most load-bearing — the gap, the
evidence and the boundary — each get their own scene rather than a bullet.

---

## 7. Rehearsal

| Path | Duration | Notes |
|---|---|---|
| Full, all beats, all pauses | ≈ 14 min 40 s | Default |
| 12-minute path | ≈ 12 min | Compressions marked in `speaker_notes/full_script.md` |
| 10-minute emergency | ≈ 10 min | Scene jumps `1 → 4 → 5 → 6 → 9 → 10 → 13 → 14` |
| MP4 backup | 14 min 44 s | Recorded at speaking pace so it can be narrated over |

Scenes 05 and 09 are marked never-cut: they are the problem and the evidence.

---

## 8. Deliverables

| Deliverable | Size | State |
|---|---|---|
| `web/` interactive presentation | 4.2 MB built | **Primary.** React + R3F + drei + GSAP, offline |
| `..._Claude.pdf` | 21.3 MB, 35 pages | Static fallback |
| `..._Claude.pptx` | 22.7 MB, 35 slides | Fallback, cues in the notes field of every slide |
| `..._Claude_Backup.mp4` | 181 MB, 14:44, 1920×1080, 25 fps | Emergency playback |
| `speaker_notes/full_script.md` | — | Spoken script, guard rails, jury Q&A |
| `speaker_notes/quick_cues.md` | — | One card per step + failure playbook |
| `demo/DEMO_INSTRUCTIONS.md` | — | Optional live Power BI demo + abort criteria |
| `design/` ×5 | — | Audit, design system, storyboard, motion spec, scene plan |
| `exports/screenshots/` | 35 frames | Source of the PDF and PPTX |
| `RUN_PRESENTATION.ps1` | — | One-command fullscreen launcher |

The PDF, PPTX and MP4 are all generated from the same captured frames, so the
fallbacks cannot drift from the live experience.

---

## 9. Known limitations of this QA

Stated so the record is honest about its own coverage.

1. **Rendering was verified in headless SwiftShader and headful Chrome on one
   machine.** It has not been tested on the actual presentation hardware or
   projector. Rehearse once on the real machine; that is the single most
   valuable remaining check.
2. **Frame rate was not instrumented numerically.** The budget is argued from
   draw calls, triangle count and the absence of post-processing rather than
   measured with a profiler on target hardware.
3. **The live Power BI demo path was not executed** — it needs a running
   PostgreSQL instance. `verify_powerbi_views.py` is the documented pre-flight
   check and the demo is explicitly optional.
4. **Colour contrast was assessed by eye against a projector-gamma assumption**,
   not with a measured instrument.
5. **The 10- and 12-minute paths were derived from the scene budgets**, not
   timed with a stopwatch by a human presenter.

None of these affect the correctness of what is displayed. They are limits on
how far the environment could be validated from here.
