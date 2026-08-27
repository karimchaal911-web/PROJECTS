# QUICK CUES

One card per step. Print two-up, or press **P** in the presentation to see the
same cues on screen. `→` = one press.

**Start:** `.\RUN_PRESENTATION.ps1` — works from the repository root or from
`final_presentation_claude`, and `RUN_SOUTENANCE.ps1` is the same thing. Wait
for `Server ready`, then press **F** for fullscreen.

**Controls:** `→`/`Space` next · `←` back · `1`–`9`,`0` scenes 1–10 ·
`Shift`+`1`–`4` scenes 11–14 · `F` fullscreen · `P` notes · `S` safe mode ·
`H` help.

> **Holding the arrow key does not fast-forward.** Repeats inside 120 ms are
> ignored on purpose, so a stuck key cannot run the show away from you. To move
> several scenes, press the scene number.

---

### 01 · AWAKENING
- Rotary dryer, soluble MAP line, Jorf Lasfar.
- **Continuous. Never stops.**
- Industrial digitalization project; AI is the intelligence layer, not the point.

### 02 · WHY THIS MATERIAL
- Phosphorus → plant nutrition → soluble MAP.
- Real spec: **12-61-00, soluble in water**.
- ⇒ residual moisture *is* the quality. Move on fast.

### 03 · FOLLOW THE MATERIAL
- Acid → ammonia → neutralization → buffer → crystallization → centrifuge → **DRY** → cool.
- Continuous *and* coupled; mother liquor recycles.
- **[GUARD]** A moisture drift is not automatically the dryer's fault.

---

### 04a · MACHINE
- Inclined shell, two riding rings. Wet in high, dry out low.

### 04b · PHYSICS
- Flights cascade the bed through counter-current hot air.
- **[GUARD]** "Schematic — not a CFD result."
- Outcome depends on several things at once.

### 04c · DATA
- Nine process variables, 5-second prototype grid.
- **The one thing that is not continuous is final moisture.**

---

### 05a · DISTANCE BECOMES TIME
- *Do not talk over the straighten.*
- Axis = 12 h of held-out TEST. Material still flowing.

### 05b · SIX RESULTS
- Every lab sample in the window. **Six.** Two hours apart.
- 0.0742 → 0.0796 → 0.0804 → 0.0806 → 0.0812 → 0.0800 % H₂O.

### 05c · THROUGH THE INTERVAL
- **Silence for ~6 s.** Let them feel it.
- "The process never stops. Lab visibility does."
- Real movement in the gap: **0.0054 % H₂O**, unmeasured.

---

### 06a · THE QUESTION
- How do we see between measurements?
- Not more sampling — inference from what is already continuous.

### 06b · ESTIMATE BETWEEN MEASUREMENTS
- 695 estimates, same window.
- Process values aligned to the product + previous lab result.
- **[GUARD]** "Laboratory remains the reference."

### 06c · TWO QUESTIONS
- What is the moisture now? *vs* Is behaviour unusual?
- Different questions → different models.

---

### 07a · SENSORS
- The process becomes data.

### 07b · THE STACK BUILDS
- 1,589,760 rows · 9 variables · align · features · models · SQL · Power BI · operator.
- Nothing drawn in advance.

### 07c · ALIGNMENT
- Product sampled now left the dryer **24.5 min** ago.
- Read the process *as it was then* + previous lab.
- **[GUARD]** Causal by construction. No future information.

---

### 08a · THE SPLIT
- One stream. 16 features → quality. 15 process-only → behaviour.

### 08b · QUALITY INTELLIGENCE
- **Ridge, α = 10**, 16 standardised coefficients.
- Beat 4 alternatives on validation RMSE. "I didn't need it complicated."

### 08c · PROCESS INTELLIGENCE
- 2,400 real training states, PCA(3), ~94 % variance.
- 136 brighter points = **the model's own support vectors**.
- **[GUARD]** One-Class SVM, unsupervised, never saw an anomaly label.

### 08d · LEAVING THE REGION
- Anomaly = **distance from the learned region**.
- Real recorded trajectory departing.

---

### 09a · MOISTURE HOLD-OUT
- **n = 165**, chronological hold-out, last 2 weeks.
- **R² 0.8245 · MAE 0.00107 · RMSE 0.00140 % H₂O**.
- "Modest, specific — I'll defend exactly that."

### 09b · WHY RIDGE
- Val RMSE: Ridge 0.001357 · ElasticNet 0.001362 · Linear 0.001367 ·
  GBM 0.001430 · RF 0.001467.

### 09c · ANOMALY EVIDENCE
- Labelled `steam_dip`, ~44.5 min.
- Risk **0.804 inside** vs **0.235 outside**. **73 of 79** warning points inside.
- **[GUARD]** Detector is unsupervised; label used for display only.

### 09d · WHAT IT IS WORTH
- **[GUARD]** Synthetic data · generator labels · chronological hold-out ·
  risk is a display score · diagnosis localises, doesn't prove · **not plant validation**.
- Say it before they ask.

---

### 10a · THE CHART BECOMES THE VISUAL
- Not a report figure — already the operator's screen.

### 10b · OPERATIONS OVERVIEW
- Predicted · latest lab · validated error · risk (0.50/0.80) · status ·
  8 h trend · critical variables · diagnosis.
- **[GUARD]** Point at the **PROTOTYPE · REPLAY** pill.

### 10c · DIAGNOSTICS AND ROOT CAUSE
- Risk timeline · selected event · ranked contributors · subsystem · checks.
- **[GUARD]** "Diagnostic evidence, not confirmed root cause."

---

### 11a · BEHIND THE PLANE
- Walk through it instead of drawing it.

### 11b · THE RUNTIME
- Power BI → 5 views → 3 tables → 1 Python service → replay.
- **Never loads a model. Never runs inference.**
- 9 ms avg / 47 ms max. 237,600 rows at Δt = 5 s.

### 11c · THE LOOP CLOSES
- Replay leads back to the process. Whole system in one frame, one command.

---

### 12 · WHAT THIS IS WORTH
- Continuous visibility · earlier awareness · ranked evidence · continuity.
- **[GUARD]** No ROI · no control action · no reduction in lab work.

---

### 13a · SOLID MEANS BUILT
- Dataset · alignment · both models · diagnosis · PostgreSQL · 5 views ·
  2-page report · 5 s runtime · 33 tests.

### 13b · OUTLINED MEANS NOT YET
- Plant data → data quality → shadow mode → feedback → governed advisory.
- **[GUARD]** "Closed-loop control does not exist in this project."

---

### 14a · MORE OF IT VISIBLE
- Same frame as scene 01 — let them notice.
- "The physical process never stopped. Digitalization made more of it visible."

### 14b · FROM MONITORING TO OPERATION
- Person in the loop at every step.

### 14c · QUESTIONS
- Stop. Do not advance.

---

## IF SOMETHING GOES WRONG

| Symptom | Do this |
|---|---|
| Stutter or low frame rate | Press **S** (safe mode). Position is kept. |
| Lost your place | Press the scene number: `1`–`9`, `0`, or `Shift`+`1`–`4`. |
| Black screen / WebGL failure | The static fallback keeps the arrow keys working. If not, open the PDF. |
| Projector cannot drive the browser | Open `FINAL_MAP_Soluble_Digitalization_Soutenance_Claude.pptx`. |
| Browser shows "site can't be reached" | The server did not start. Close the window, re-run the launcher, and read its error line. |
| Nothing works | Play `..._Backup.mp4` and narrate over it. |

## THE FIVE SENTENCES

If you had sixty seconds and one slide:

1. Soluble MAP production is continuous; the dryer sets final moisture.
2. The laboratory measures that moisture roughly every two hours, so quality
   visibility is sparse while production is not.
3. A Ridge soft sensor estimates moisture between laboratory results —
   R² 0.82, MAE 0.00107 % H₂O on a chronological hold-out.
4. A separate unsupervised One-Class SVM asks a different question — is the
   process behaving unusually — and it fires inside a disturbance it never saw
   labelled.
5. Both reach the operator through PostgreSQL and Power BI as advisory
   evidence, on synthetic prototype data, with the laboratory still the
   reference.
