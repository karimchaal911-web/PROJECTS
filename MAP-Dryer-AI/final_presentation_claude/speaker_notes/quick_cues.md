# QUICK CUES

One card per step. Print two-up, or press **P** in the presentation to see the
same cues on screen. `→` = one press. **41 steps, 14 scenes.**

**Start:** `.\RUN_PRESENTATION.ps1` — works from the repository root or from
`final_presentation_claude`. Wait for `Server ready`, then press **F** for
fullscreen. A discreet
`NOT FULLSCREEN — press F` reminder appears if you forget.

**Controls:** `→`/`Space` next · `←` back · **`G` then a key** = go to scene ·
`F` fullscreen · `P` notes · `S` safe mode · `H` help · `Home`/`End` first/last.

**Go-to-scene map** (press `G` first, then):
`1`–`9` → scenes 01–09 · `0` → 10 · `Q` → 11 · `W` → 12 · `X` → 13 · `C` → 14.

> **Bare digits no longer jump.** A mistyped key used to throw the show mid-
> sentence, and the old `Shift`+`!@#$` mapping for scenes 11–14 assumed a US
> keyboard — on the AZERTY layout this will likely be presented on, it broke
> entirely. The `G` prefix is layout-independent; `Esc` cancels it.

> **Holding the arrow key does not fast-forward.** Repeats inside 120 ms are
> ignored on purpose, so a stuck key cannot run the show away from you.

> **Clicking the slide does not advance it.** Only the keyboard, or a deliberate
> click on the narrow invisible strip along the very bottom edge.

---

### 01 · AWAKENING
- Rotary dryer, soluble MAP line, Jorf Lasfar.
- **Continuous. Never stops.**
- Industrial digitalization project; AI is the intelligence layer, not the point.

---

### 02a · PHOSPHORUS
- The reason the plant exists.

### 02b · PLANT NUTRITION
- Phosphorus and nitrogen in a form a crop can take up.

### 02c · SOLUBLE MAP
- **This is a photograph of the real product, in storage at the site.**
- Real spec: **12-61-00, soluble in water**.
- ⇒ residual moisture *is* the quality. Move on.

---

> **Eight steps now, one per stage.** The scene used to fly past pretreatment,
> ammonia vaporization, the buffer tanks and centrifugation without stopping.
> Each stage gets its own frame: it arrives, the camera settles, the equipment
> is named on screen, you say what it does, the material moves on.

### 03a · THE CHAIN
- Wide. Seven stages, one continuous flow. H3PO4 + NH3 go in at this end.

### 03b · 01 PHOSPHORIC-ACID PRETREATMENT
- First of the two feeds. Conditioned before it reaches the reaction.

### 03c · 02 AMMONIA VAPORIZATION
- Second feed. Liquid ammonia vaporised in the two horizontal exchangers,
  enters the reaction as a gas.

### 03d · 03 NEUTRALIZATION
- **The reaction that makes the salt.** Three agitated reactors in series.
- Mother liquor returns to this stage from downstream — the low green line.

### 03e · 04 BUFFER / STABILIZATION
- Held and blended before crystallization.
- **This is the stage that mixes and delays every disturbance.** Say it here;
  it is the setup for the whole diagnosis problem later.

### 03f · 05 CONCENTRATION & CRYSTALLIZATION
- Solids form. From here the product is a wet solid, not a liquid.

### 03g · 06 CENTRIFUGATION
- Crystals separate from the mother liquor. Crystals → dryer.
- **Point at the labelled green line** — liquor → back to neutralization.

### 03h · INTO THE DRYER
- Looking back up the whole chain.
- **[GUARD]** The dryer is the last stage, not the only cause. Coupled *and*
  recycled ⇒ final moisture cannot be attributed to any one of them.

---

### 04a · MACHINE
- Inclined shell, two riding rings. Wet in high, dry out low.

### 04b · PHYSICS
- Flights cascade the bed through counter-current hot air.
- The three arrows say it: **SOLIDS →**, **← HOT AIR**, **MOISTURE → EXHAUST**.
- **[GUARD]** "Schematic — not a CFD result."

### 04c · DATA
- Nine process variables, 5-second prototype grid.
- **The one thing that is not continuous is final moisture** — bottom right,
  "LABORATORY ONLY".

---

### 05a · DISTANCE BECOMES TIME
- *Do not talk over the straighten.*
- Axis = 12 h of held-out TEST. Material still flowing.

### 05b · SIX RESULTS
- Every lab sample in the window. **Six, and all six are on screen.**
- 0.0742 → 0.0796 → 0.0804 → 0.0806 → 0.0812 → 0.0800 %.

### 05c · THROUGH THE INTERVAL
- **Silence for ~6 s.** Let them feel it.
- "Two hours. No measurement."
- Real movement in the gap: **0.0054 % moisture**, unmeasured.

---

### 06a · THE QUESTION
- How do we see between measurements?
- Not more sampling — inference from what is already continuous.

### 06b · ESTIMATE BETWEEN MEASUREMENTS
- 695 estimates, same window.
- Process values aligned to the product + previous lab result.
- A second question — is the process behaving unusually — gets its own model.
- **[GUARD]** "Laboratory remains the reference."

---

### 07a · SENSORS
- Nine process variables, on the 5-second prototype grid.

### 07b · THE STACK BUILDS
- PROCESS · SENSE · ALIGN · FEATURES · INTELLIGENCE · PERSIST · SUPERVISE · OPERATOR.
- Nothing drawn in advance — **each layer is named only when its data arrives**.

### 07c · ALIGNMENT
- Product sampled now left the dryer **24.5 min** ago.
- **Watch the marked packet wait.** Read the process *as it was then* + previous lab.
- **[GUARD]** Causal by construction. No future information.

---

### 08a · THE SPLIT
- One stream. 16 features → quality. 15 process-only → behaviour.
- Neither model sees the other's answer.

### 08b · QUALITY INTELLIGENCE
- **Ridge, alpha = 10**, 16 standardised coefficients.
- Beat 4 alternatives on validation RMSE. "I didn't need it complicated."

### 08c · PROCESS INTELLIGENCE
- 2,400 training states from the prototype dataset, PCA(3), ~94 % variance.
- The **136 bright points are the model's own support vectors** — the learned
  boundary. The moving point is a real recorded trajectory leaving the region.
- **[GUARD]** One-Class SVM, `nu = 0.02`, unsupervised, never saw an anomaly label.

---

### 09a · MOISTURE HOLD-OUT
- **n = 165**, chronological hold-out, last two weeks.
- **R2 0.8245 · MAE 0.00107 % · RMSE 0.00140 %**.
- "Modest, specific — I'll defend exactly that."

### 09b · WHY RIDGE
- Val RMSE: Ridge 0.001357 · ElasticNet 0.001362 · Linear 0.001367 ·
  GBM 0.001430 · RF 0.001467.

### 09c · ANOMALY EVIDENCE
- Labelled `steam_dip`, ~44.5 min.
- Risk **0.804 inside** vs **0.235 outside**. **73 of 79** warning points inside.
- **[GUARD]** Detector is unsupervised; the label exists only in the generator.

### 09d · WHAT IT IS WORTH
- **[GUARD]** Read the four world lines out loud — two PROVES, two DOES NOT.
- Synthetic prototype data · chronological hold-out · advisory · not plant validation.
- Say it before they ask.

---

### 10a · THE MODEL LEAVES THE NOTEBOOK
- Same two models, same artifacts — now answering continuously into a screen.
- **This is a live replay state of the shipped report, not a mock-up.**
- If asked: the pill top-right reads **LIVE DATA**, ingested minutes ago.

### 10b · OPERATIONS OVERVIEW
- Walk five regions, ~1.3 s each: predicted moisture → laboratory reference →
  anomaly state → diagnosis → the selected process variables.
- Predicted **0.0798 %** vs laboratory **0.0752 %**, validated error **0.0013 %**.
- Anomaly score **0.95**, severity **HIGH**, subsystem *drying-air and exhaust circuit*.
- **[GUARD]** Point at **PROTOTYPE · REPLAY · ADVISORY**.

### 10c · DIAGNOSTICS AND ROOT CAUSE
- Ranked abnormal contributors · normalised deviation · likely subsystem · checks.
- **[GUARD]** "Evidence, not proven causality."

---

### 11a · BEHIND THE DASHBOARD
- We go through the report plane, not around it.
- Power BI reads five semantic SQL views. **It never loads a model and never
  runs inference.**

### 11b · THE RUNTIME PATH
- Five checkpoints, left to right, **in the direction the data travels**:
  REPLAY → PYTHON INFERENCE → POSTGRESQL → FIVE SEMANTIC VIEWS → POWER BI.
- One Python service, exact notebook artifacts, idempotent writes.
- **9 ms average inference cycle, 47 ms maximum.**

### 11c · IT ENDS WITH A PERSON
- The last step is **not an actuator** — it is an operator reading evidence.
- **Nothing in this system writes back to the process.**
- **[GUARD]** "Prototype replay, 5 s tick. No control action is taken."

---

### 12 · WHAT THIS IS WORTH
- Three claims, and only three: continuous visibility between lab results ·
  earlier awareness of unusual behaviour · ranked evidence instead of raw alarms.
- One signal travels the loop once — that is the direction, not decoration.
- **[GUARD]** No ROI · no control action · **the operator closes the loop**.

---

### 13a · SOLID MEANS BUILT
- Dataset · alignment · both models + diagnosis · PostgreSQL + 5 views ·
  2-page report on a 5 s runtime · 33 tests.

### 13b · OUTLINED MEANS NOT YET
- Plant historian data → data quality → shadow mode → operator feedback →
  governed advisory rollout.
- **Amber = conditional, may never be built.**
- **[GUARD]** "Closed-loop control does not exist in this project."

---

### 14a · MORE OF IT VISIBLE
- Same frame as scene 01 — **pause and let them notice.**
- "The physical process never stopped. Every one of those points is now a signal
  the system reads."

### 14b · QUESTIONS
- Stop. Do not advance. This frame holds for the whole defence.

---

## IF SOMETHING GOES WRONG

| Symptom | Do this |
|---|---|
| Stutter or low frame rate | Press **S** (safe mode). Position is kept. It also arms itself: 90 consecutive frames below 30 fps drop the show into safe mode automatically. |
| Lost your place | Press **`G`**, then the scene key (`1`–`9`, `0`, `Q`, `W`, `X`, `C`). The world hard-sets to that scene's full state. |
| Black screen / WebGL failure | The static fallback keeps the arrow keys and the copy working. If not, open the PDF. |
| Projector cannot drive the browser | Open `FINAL_MAP_Soluble_Digitalization_Soutenance_Claude.pptx`. |
| Browser shows "site can't be reached" | The server did not start. Close the window, re-run the launcher, and read its error line. |
| **"Your dashboard says the data is stale"** | It does not — the capture reads `LIVE DATA` and was taken inside a live replay with an active anomaly. If challenged, offer the static backup in `exports/` and the runtime log. |
| Nothing works | Play `..._Backup.mp4` and narrate over it. |

## THE FIVE SENTENCES

If you had sixty seconds and one slide:

1. Soluble MAP production is continuous; the dryer sets final moisture.
2. The laboratory measures that moisture roughly every two hours, so quality
   visibility is sparse while production is not.
3. A Ridge soft sensor estimates moisture between laboratory results —
   R2 0.82, MAE 0.00107 % on a chronological hold-out.
4. A separate unsupervised One-Class SVM asks a different question — is the
   process behaving unusually — and it fires inside a disturbance it never saw
   labelled.
5. Both reach the operator through PostgreSQL and Power BI as advisory
   evidence, on synthetic prototype data, with the laboratory still the
   reference.
