# STORYBOARD

**14 scenes · 10–15 minutes · one continuous world · presenter-controlled**

Fourteen sits inside the stated maximum of fifteen. Each scene carries exactly
one idea, and no two could be merged without losing one. The count is driven by
the argument, not by a template.

---

## The spine

The whole film is built on **one geometry that is continuously reinterpreted**:

```
MAP granule stream          (S02–S04)  material moving through space
        ↓ camera rises, the path straightens
TIME AXIS                   (S05)      the same line, now 12 hours long
        ↓ signals fill the dark interval
PREDICTED MOISTURE TRACE    (S06)      the same line, now a soft-sensor output
        ↓ the trace flattens into evidence
VALIDATION CHART            (S09)      the same line, now 165 held-out points
        ↓ the chart frame acquires a dashboard
POWER BI VISUAL             (S10)      the same line, now the real supervision artifact
        ↓ the camera pushes through the plane
SQL → PYTHON → REPLAY       (S11)      the same line, now the runtime
        ↓ the stream reconnects
THE DRYER                   (S14)      the same line, back where it started
```

Nothing disappears to be replaced. The audience should never feel that a slide
changed — only that they were shown another layer of the same object.

A second, quieter thread: **the dryer is present in every scene**, always
rotating, receding into fog rather than unloading. It is the only object that
survives from frame one to frame last.

---

## SCENE 01 — AWAKENING
**Idea:** this is a real industrial process, and it is already running.

Near black. Dust motes drift in a shaft of weak light. The camera moves slowly
forward at human height between green structural columns — silhouettes only.
A pale mass resolves ahead: the rotary dryer shell, rim-lit, turning. The
process light inside the discharge hood pulses faintly.

The camera settles into a three-quarter view. Title arrives, left third:

> **INTELLIGENT DIGITALIZATION**
> **OF SOLUBLE MAP PRODUCTION**
>
> Predictive quality · Early anomaly detection · Real-time supervision

OCP and ENSAM marks sit at the bottom safe edge at 45 % opacity, 18 px tall.
No title card, no logo animation, no centred layout.

*Duration ≈ 34 s (mostly held silence for the opening line).*

---

## SCENE 02 — WHY THIS MATERIAL
**Idea:** phosphorus feeds plants; soluble MAP is how it gets there.

The camera moves to a **photograph of the real product in storage at the site**,
framed like a print hung in the hall — full bleed, premium crop, the copy column
holding the left third.

Three words arrive on **three presenter-driven beats**, each with a small easing
push toward the print:

> **PHOSPHORUS** → **PLANT NUTRITION** → **SOLUBLE MAP**

Then the truthful product line:

> `MAP · MONOAMMONIUM PHOSPHATE · 12-61-00 · SOLUBLE IN WATER`

*≈ 24 s, 3 steps.*

> **Rebuilt.** This scene was a procedural macro granule: an icosahedron of
> detail 0 scaled 46x, with the camera parked 3.59 units from a solid whose
> circumradius is 3.91 — i.e. *inside* it. The frame contained no granule at all,
> only a featureless grey wall of dryer shell, and the three words auto-advanced
> on a `setInterval` the presenter could not control. The site photograph the
> scene's own note referred to was shipped in the bundle and never referenced.
> It is the subject now.

---

## SCENE 03 — FOLLOW THE MATERIAL
**Idea:** continuous transformation through a coupled chain; the dryer is one
stage of it.

The camera tracks the granule stream along a curving path through the verified
sequence, and STOPS at every stage:

`acid pretreatment · ammonia vaporization · neutralization · buffer /
stabilization · concentration & crystallization · centrifugation · DRYING ·
cooling & conditioning`

Each station carries the silhouette of the KIND of machine the operation needs
— a receiver feeding two horizontal shell-and-tube vaporizers, a train of three
agitated reactors, a row of agitated buffer tanks, a crystalliser with an
external forced-circulation loop and a vapour condenser, two parallel
horizontal centrifuges on a skid. A key and a rim light ride the material down
the chain, so the stage the material is in is the stage that is lit.

Each stage is named ONCE, by a small screen-facing index and label on a leader
line anchored to the equipment. Never all seven at once, never in world-space
type that skews with the camera.

The mother-liquor recycle leaves centrifugation as a painted pipe running low
and behind, parallel to the material line and in the opposite direction, and
rejoins neutralization. It is labelled where it leaves.

One caption holds throughout, monospace, bottom-left:
`H₃PO₄ + NH₃ ⇌ NH₄H₂PO₄`

The last beat looks BACK up the whole chain from the dryer end, because the
idea it carries is about the whole chain rather than about the last object in
it.

*≈ 78 s, 8 steps — the camera travels WITH the material and settles at every
stage. Four stops for seven stations meant the audience was flown past
pretreatment, ammonia vaporization, the buffer tanks and centrifugation. The
audience should feel a journey, not read a diagram — but they should also be
able to name every machine they passed.*

---

## SCENE 04 — ENTER THE DRYER
**Idea:** machine → physics → data.

No cut. The environment recedes as fog density rises and the key light narrows
onto the dryer, which becomes the hero object: inclined shell, two riding rings
on trunnion rollers, girth-gear drive, feed chute high end, discharge hood low
end, exhaust duct rising.

**Beat 1 — MACHINE.** A slow arc around the drum. Real proportions. Dust.
**Beat 2 — PHYSICS.** The shell fades to wireframe. Inside: flights lift the
material bed and cascade it; hot air moves counter-current; moisture leaves as
faint vapour toward the exhaust. Caption: `SCHEMATIC — NOT A CFD RESULT`.
**Beat 3 — DATA.** Seven telemetry chips attach to the points that produce them,
with real values from the held-out replay:

```
dryer air temperature   176.2 °C
steam pressure            8.33 bar
air flow rate           24,351 m³/h
wet product feed rate     26.59 m³/h
residence time            24.47 min
vacuum                    48.60 mmH2O
fan speed                1,344.8 rpm
```

Then the output side, in `--lab` white: `FINAL MOISTURE / % / LABORATORY ONLY`.

*≈ 72 s. The longest scene, because it is the one the whole argument stands on.*

---

## SCENE 05 — THE GAP *(signature)*
**Idea:** the process is continuous; knowledge of quality is not.

Product leaves the discharge hood and moves away on the flow line. The camera
rises above it. As it rises, **the flow line straightens and stretches into a
time axis** — 12 hours of held-out TEST, `2026-07-05 00:00 → 12:00`. The granule
stream keeps flowing along it, dense and unbroken. The dryer is still visible at
the origin, still turning.

Then the quality dimension appears above the line — and it is almost entirely
dark. Six bright vertical markers stand on it, exactly two hours apart, at the
six real laboratory samples:

```
00:00  0.0742 %
02:00  0.0796 %
04:00  0.0804 %
06:00  0.0806 %
08:00  0.0812 %
10:00  0.0800 %
```

The camera drops to axis level and **travels down the dark interval** between
the first two markers. A monospace counter runs `+00:00 … +02:00`. The granules
keep streaming past. Nothing else is known.

> **TWO HOURS.**
> *(hold)*
> **NO MEASUREMENT.**

`LAB Δt ≈ 2 h` sits small beside the markers.

Closing line, quiet: between those two results the product actually moved by
`0.0054 %`, and nothing measured it.

*≈ 76 s. The jury must feel the interval, so the travel through it is played at
real reading pace and not hurried.*

---

## SCENE 06 — THE ENGINEERING RESPONSE
**Idea:** fill the interval with inference, not with more sampling.

Same space, no reset. The camera is still inside the gap.

> **HOW DO WE SEE IN BETWEEN?**

Process signals rise from the dryer at the origin — thin teal lines, one per
variable — and travel down the time axis into the dark. As they arrive, the
**continuous predicted-moisture trace draws itself** across the gap, left to
right, at reading speed: 695 real soft-sensor points, landing close to each
laboratory marker without ever overwriting it.

The camera pulls back to see all 12 hours at once: dense continuous estimate,
six solid measurements.

Two statements, staged:

> **ESTIMATE MOISTURE BETWEEN SAMPLES.**
> **DETECT ABNORMAL BEHAVIOUR EARLIER.**
>
> **TWO QUESTIONS. ONE SUPERVISION SYSTEM.**

Guard rail on screen: `LABORATORY ANALYSIS REMAINS THE REFERENCE`.

*≈ 40 s, 2 steps. The third beat — TWO QUESTIONS. ONE SUPERVISION SYSTEM. —
was cut: scene 08 opens on exactly that idea 80 s later, with the models on
screen, and the beat parked the camera at the farthest pose in the film.*

---

## SCENE 07 — PHYSICAL BECOMES DIGITAL
**Idea:** the architecture is what the signals build when they leave the process.

The camera flies back up the time axis toward the dryer — the reverse of the
Scene 05 move, so the space is re-anchored. Sensor nodes ignite on the equipment
where the real variables are produced. The dryer partially transitions to point
cloud and wireframe, still turning.

Data packets detach from each node and travel. They do not fly into a diagram —
**they stack, and the stack is the architecture.** Each layer forms only when
enough packets have arrived:

```
PROCESS      1,589,760 rows · Δt = 5 s (prototype replay)
SENSE        9 process variables
ALIGN        residence-time alignment · prior laboratory density & temperature
FEATURES     16 moisture · 15 process-only
INTELLIGENCE Ridge soft sensor · One-Class SVM novelty
PERSIST      PostgreSQL · 3 tables · 5 views
SUPERVISE    Power BI · DirectQuery · ~5 s refresh
OPERATOR     advisory decision
```

### Residence-time alignment gets two beats, not one

It is two claims and they are different kinds of claim, so compressing them into
one sentence over a glowing slab meant the jury had to take the most defensible
idea in the project on trust.

**Beat 3 — THE DELAY IS PHYSICAL.** The camera leaves the stack and comes to a
lane in front of it. A marker enters at `MATERIAL ENTERS`, crosses at constant
speed — no easing, because this is a machine with a length, not a UI element —
and arrives at `SAMPLE TAKEN`. The span is labelled `RESIDENCE TIME 24.5 min`,
and under it, `MEASURED PER SAMPLE — 24.15 to 24.89 min`, because residence time
is one of the nine measured variables and not a constant anybody assumed. No data
claim is made in this beat at all.

**Beat 4 — ALIGN THE DATA TO THE PRODUCT.** Two rails appear against a three-hour
clock: process variables above, laboratory quality below. The naive pairing is
drawn **first**, straight down at the same timestamp, dashed, in the film's fault
colour — because an unshown mistake is not a correction. Then the process block
slides back by the residence time and the link turns to the prediction colour,
labelled `SHIFTED BACK 24.5 min`. A dimmer, backward-pointing dashed link then
reaches to the previous laboratory sample two hours earlier, which is where the
density and product-temperature features come from. Finally the `ALIGN` layer of
the stack behind the lane lights, and the marked packet inside it waits: the lane
is an explanation *of* the stack, so the stack acknowledges it.

The lane runs on a **three-hour** clock rather than a tighter one specifically so
the two offsets stay on the same honest scale — a 24.5-minute shift and a
two-hour-old reference. Cropping the window to make the shift look bigger would
have made the geometry lie about the proportion between them.

*≈ 78 s. This is the one scene that got longer in the final pass; every second of
it came out of scenes 04, 05, 12 and 14.*

---

## SCENE 08 — TWO INTELLIGENCE PATHWAYS
**Idea:** two different questions, two different kinds of model, one system.

The packet stream splits into two lanes in space.

**Lane A — QUALITY INTELLIGENCE** (left)
16 aligned features enter a compact solid form; one continuous value leaves it.
`RIDGE · α = 10 · selected on validation RMSE`.
> **WHAT IS THE MOISTURE NOW?**

**Lane B — PROCESS INTELLIGENCE** (right)
The camera moves into an actual 3-D point cloud: **2,400 real TRAIN process
states**, PCA-projected (93.7 % variance). Then **136 brighter points** — the
model's own support vectors — resolve on the cloud's outer shell.
`ONE-CLASS SVM · ν = 0.02 · UNSUPERVISED NOVELTY DETECTION · LEARNS NORMAL ONLY`.

A single moving point enters: the current process state, following the real
recorded trajectory. It orbits inside the cloud calmly — then, over 44 minutes
of replay, **it leaves**. Distance from the learned region grows, the point
turns amber then red, and the contributing variables name themselves.
> **IS THIS PROCESS STATE UNUSUAL?**

The lanes converge into one word: **SUPERVISION**.

Explicit on screen: `NO ANOMALY LABEL IS USED IN TRAINING`.

*≈ 68 s, 3 steps — the trajectory is a sub-reveal inside PROCESS INTELLIGENCE,
not a fourth beat reached by six units of camera. No brains, no neural nets, no
robots — the model is shown as the
geometry it actually is.*

---

## SCENE 09 — PROVE IT
**Idea:** here is the evidence, and here is exactly what it is worth.

**The lights come up.** Fog thins, exposure lifts, the world turns to OCP cream
editorial. The dryer is still there, now pale and distant.

The prediction trace from Scene 06 flattens, rotates to face the camera and
becomes the first evidence panel.

**Panel A — moisture soft sensor.** Actual vs predicted, 165 chronological
held-out laboratory targets, drawn point by point.

> **R² 0.8245** · **MAE 0.00107 %** · **RMSE 0.00140 %**
> `HELD-OUT TEST · n = 165 · 2026-07-03 → 2026-07-16 · CHRONOLOGICAL`

Beside it, small: candidate comparison. Ridge `0.001357`, Elastic Net
`0.001362`, Linear Regression `0.001367`, Gradient Boosting `0.001430`,
Random Forest `0.001467`. *The regularised linear model won.*

**Panel B — anomaly detector.** The four-hour close-up around the labelled
disturbance. Risk trace with warning and critical bands. The `steam_dip` band
shades in behind it.

> Mean risk **inside** the labelled event **0.804** · **outside 0.235**
> **73 of 79** warning-level points fall inside the event · peak **0.976**
> `THE DETECTOR IS UNSUPERVISED AND NEVER SAW THIS LABEL`

**The limits, stated on screen, not glossed:**
`SYNTHETIC PROTOTYPE DATA · DISTURBANCE LABELS ARE GENERATOR GROUND TRUTH,
USED FOR DISPLAY ONLY · CHRONOLOGICAL HOLD-OUT · ADVISORY · NOT PLANT VALIDATION`

*≈ 104 s. The evidence act was the most rushed in the deck and is now the most
generous; each beat also has its own spatial relationship rather than a third
identical vertical drop.*

---

## SCENE 10 — THE MODEL LEAVES THE NOTEBOOK
**Idea:** the same two models, now answering into an operator's screen.

### The signature sequence: artifact → service → inference → screen

The beat that carries the film's biggest headline used to be a two-second
cross-fade. It is now the one transformation in the project that is *true*, and
it is checkable rather than asserted:

```
  0.4 s   TRAINED ARTIFACT resolves and is read
          quality_moisture_pipeline.joblib · anomaly_model.joblib
          sha256 b525c7b8 · notebooks/03_Model1_SoftSensor.ipynb
  3.2 s   the words leave, then the card tips and folds
  3.6 s   realtime_service.py — LOADED ONCE · 9 ms AVERAGE CYCLE,
          pulsing on the project's own five-second tick
  5.4 s   inference travels the corridor toward the plane
  6.4 s   the report resolves BECAUSE the stream arrived
  7.4 s   the corridor dissolves into the page it feeds
```

Three properties make it defensible rather than decorative:

1. **It is verifiable.** `models/model_registry.json` carries the artifact's
   SHA-256 and `runtime_uses_exact_notebook03_artifact: true`;
   `realtime_service.py::load_artifacts()` joblib-loads that exact path once at
   start and never re-fits. The file the notebook wrote **is** the file the
   service loads, and the caption says where to check.
2. **It has a continuity object.** The cube the artifact folds into is the same
   geometry, colour and material as the runtime checkpoints in scene 11, where
   the camera meets it again as `PYTHON INFERENCE`. It is the only object in the
   film that survives a change of environment — which is the point: the model was
   not re-implemented on the way to an operator's screen, it was loaded.
3. **It claims nothing it should not.** No deployment, no control action, no
   closed loop. The stream ends at a screen, the guard line in the script says
   *handover, not deployment*, and the corridor is gone by the time the page is
   legible — nothing shares the frame with the deliverable.

The camera **arrives** rather than cutting: the beat opens nine units further
back and settles onto the scene's own pose, so the report grows into the frame as
it resolves. Because the move ends exactly where the settled pose already was, it
cannot crop the page.

### The report itself

The camera arrives in front of the real report, which is **legible from the first
frame it is on screen**. Five regions are then named in reading order, about 1.3 s
each:

1. predicted final moisture
2. latest laboratory moisture
3. validated moisture error
4. current anomaly risk (warning 0.50 · critical 0.80)
5. process status · anomaly severity
6. rolling 8-hour moisture and risk trend
7. critical process variables
8. diagnosis context and operator guidance

The freshness pill, the refresh cadence and the advisory footer are visible
because they are on the real screen.

*≈ 76 s. Nothing is invented — every highlighted element exists in the shipped
report.*

> **Two things changed here, and both were credibility, not polish.**
>
> The claim was `THE SAME CHART. AN OPERATOR'S SCREEN.` over a crossfade in which
> the scene-09 hold-out scatter stayed legible across the top of the Power BI
> capture. They are different charts of different windows — a 165-point 13-day
> scatter and a smooth 8-hour rolling trend — so the assertion was contradicted
> by the image carrying it. The claim is now `THE MODEL LEAVES THE NOTEBOOK`,
> which is true, and the evidence layer is driven to **zero** on entry so there
> is no ghost.
>
> The capture itself was re-taken. The old one announced `DATA · STALE`, `STALE`
> on every process tile and `ingested 8525 min ago` — under an eyebrow about
> real-time supervision — and it was captured in its null state, so the diagnosis
> scene had nothing to show. The current capture is a live replay state taken
> inside an injected disturbance: `LIVE DATA`, anomaly 0.95, severity HIGH,
> ranked contributors and operator guidance populated. It was also introduced at
> 30 % opacity; it now reaches full legibility as the headline does.

---

## SCENE 11 — BEHIND THE DASHBOARD
**Idea:** end-to-end integration, proved by travelling through it.

Instead of an architecture slide, the camera **passes through the report plane**
and comes to rest ACROSS the runtime — five checkpoints on one rising line,
watched from the side so they separate cleanly, and walked **in data-flow order**:

```
REPLAY               held-out TEST · one row every 5 s · 237,600 rows
   →
PYTHON INFERENCE     realtime_service.py · the exact notebook artifacts, once
                     9 ms average inference cycle, 47 ms maximum
   →
POSTGRESQL           dryer_map · dryer_model_outputs · dryer_abnormal_variables
   →
FIVE SEMANTIC VIEWS  vw_dryer_dashboard_powerbi · vw_dryer_contributors_powerbi
                     vw_dryer_lab_samples · vw_dryer_anomaly_events
                     vw_dryer_overview_trends_powerbi
   →
POWER BI             DirectQuery · reads views only
   →
OPERATOR             advisory decision
```

The camera then comes back out in front of the plane: the report above, the
operator terminal below it, and the route arriving from behind both. The packet
stream **terminates at the operator**.

`POWER BI NEVER LOADS A MODEL AND NEVER RUNS INFERENCE.`
`NOTHING IN THIS SYSTEM WRITES BACK TO THE PROCESS.`

*≈ 66 s.*

> **Rebuilt twice over.**
>
> It was a second stack of translucent labelled slabs — the same metaphor scene
> 07 already owns — ordered so the camera met POWER BI first and REPLAY last,
> i.e. backwards to the narration, with four of five labels occluded by the slab
> in front. It also carried a measured **677.8 ms** frame stall, because the
> layer's materials had never been rendered before that moment.
>
> The path fixed the ordering, and then broke differently: walking it from the
> deep end put the camera on the far side of every +Z-facing label, so REPLAY,
> POSTGRESQL and POWER BI all rendered **mirrored**, and the report showed its
> reversed back face. Labels now turn to the lens; the report is front-faced with
> a real dark back plate; the route is compact and viewed from across.
>
> The loop-close packets used to run **back into the dryer**, which reads as
> closed-loop control two scenes before scene 13 says it does not exist. They end
> at an operator terminal — which was itself invisible at first, drawn
> *underneath* the plant's 400 x 220 ground plane, because that plane writes
> depth even at 5 % opacity.

---

## SCENE 12 — WHAT THIS IS WORTH
**Idea:** the defensible operational value, and nothing beyond it.

Editorial light returns. The whole architecture simplifies into one ring the
camera looks down on, with the material still moving around it:

```
PROCESS → SENSE → PREDICT → DETECT → SUPERVISE → DECIDE → PROCESS
```

Four statements, one at a time:

> More continuous moisture visibility between laboratory results.
> Earlier awareness of unusual multivariable process behaviour.
> Ranked, operator-readable evidence instead of raw alarms.
> A supervision layer that supports production continuity.

And immediately, in the same weight:

> No ROI is claimed. No control action is taken. The laboratory remains the
> reference and the operator remains the decision-maker.

*≈ 30 s. Three claims, not four; six ring nodes matching a six-word headline;
one signal travelling the loop once as the direction cue.*

---

## SCENE 13 — TODAY → NEXT
**Idea:** an honest boundary between what exists and what does not.

The ring resolves into two states. **Solid geometry = implemented today.**
**Outlined geometry = not built.**

**Solid:** canonical dataset · residence-time alignment · 16-feature Ridge soft
sensor · 15-feature One-Class SVM · diagnosis engine · PostgreSQL persistence ·
five semantic views · two-page Power BI report · 5 s replay runtime ·
33 automated tests.

**Outline, in order:**
representative plant historian data → data-quality validation → shadow-mode
operation → operator feedback loop → governed advisory deployment →
*(conditional)* assisted setpoint guidance → *(only after rigorous validation)*
closed-loop regulation.

The last two remain outlined and dimmer than the rest, and the caption says it
plainly:

> `CLOSED-LOOP CONTROL DOES NOT EXIST IN THIS PROJECT.`

*≈ 52 s. The rail is TRAVELLED rather than framed all at once — twelve labelled
stages cannot exceed ~16 px in a single 16:9 framing, which is why the honesty
slide used to render at ~9 px.*

---

## SCENE 14 — RETURN
**Idea:** the physical process never stopped; digitalisation made more of it
visible.

The camera returns to the opening framing — the same columns, the same dryer,
the same rim light. It is recognisably frame one.

But the world now carries a calm digital layer: sensor nodes glow softly,
signal lines move along the flow path, a faint prediction trace runs above the
product line. Nothing flashes. The dryer keeps turning.

> **THE PROCESS NEVER STOPPED.**
> **DIGITALIZATION MADE MORE OF IT VISIBLE.**
>
> *(hold, the world alone)*
>
> **FROM PROCESS MONITORING**
> **TO INTELLIGENT INDUSTRIAL OPERATION.**

The camera drifts. Then, small, bottom-left, in the eyebrow style:

> `QUESTIONS`

No "thank you". No summary slide. No credits.

*≈ 40 s, 2 steps. The two micro-dollies that used to follow the return were cut:
they walked the camera off the opening pose four seconds after landing on it.*

---

## Timing

| Act | Scenes | Target |
|---|---|---|
| I — Purpose | 01–02 | 0 min 51 s |
| II — Industry | 03–04 | 2 min 15 s |
| III — The gap | 05–06 | 1 min 34 s |
| IV — Digitalization | 07–08 | 2 min 26 s |
| V — Evidence & supervision | 09–11 | 3 min 54 s |
| VI — Value & future | 12–14 | 1 min 38 s |
| | | **12 min 38 s** |

*(Act figures are the scene table's own `seconds` fields; the total is exact, not
an estimate. Transition time is inside those figures — the tiers run 101.5 s over
38 transitions.)*

**The final pass took 48 s out and put 16 s back.** Out: the push across the
machine (13 s → 8.4 s), the settle after the time axis forms, 1.3 s off the truck
down the axis, the loop signal in scene 12, and the `QUESTIONS` card, which had
been budgeted as though the Q&A that follows it were part of the film. In: two
beats that were carrying more argument than they had room for — residence-time
alignment and the artifact-to-service handover. Net −26 s, which leaves roughly
fifty seconds of slack inside a 13 min 30 s slot for a jury that interrupts.

**The pacing was inverted before this pass.** Scenes 01, 02, 03 and 12 held about
165 s of near-static frame — 19 % of the runtime — while the densest act, the one
carrying the evidence and the deliverable, was the most rushed. Roughly 110 s were
recovered by tightening 01, 02, 03 and 12 and cutting four redundant beats, and
redistributed into scenes 09 and 10.

The speaker notes provide a marked **12-minute path** and a **10-minute emergency
path**. The presenter controls every advance, so the experience contracts and
expands without any edit to the build.

---

## What the jury should be able to say afterwards

1. OCP produces soluble MAP; this is one dryer inside that chain.
2. Final moisture is the quality that matters at the dryer.
3. The laboratory measures it roughly every two hours; production is continuous.
4. That interval is a real supervision problem.
5. A soft sensor estimates moisture in between, using residence-time-aligned
   process data and the previous laboratory result.
6. A separate unsupervised model asks a different question: is the process
   behaving unusually?
7. Both were evaluated on a chronological hold-out, and the numbers are modest,
   specific and stated.
8. The data is synthetic; this is a prototype, not a validated plant system.
9. Results reach PostgreSQL and then Power BI, which only visualises.
10. The system is advisory. The laboratory and the operator remain in charge.
11. There is a concrete, staged path to industrialisation, and closed-loop
    control is not on today's side of the line.
