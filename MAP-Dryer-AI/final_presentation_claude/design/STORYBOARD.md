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

*Duration ≈ 50 s (mostly held silence for the opening line).*

---

## SCENE 02 — WHY THIS MATERIAL
**Idea:** phosphorus feeds plants; soluble MAP is how it gets there.

The camera pushes past the dryer and finds a single MAP granule, macro, held in
a shaft of light — a real object, studio-lit, slowly rotating. The industrial
world stays visible, defocused, behind it.

Three words arrive and leave, one at a time, in the same position:

> **PHOSPHORUS** → **PLANT NUTRITION** → **SOLUBLE MAP**

Then the truthful product line, from the storage photograph:

> `MAP · MONOAMMONIUM PHOSPHATE · 12-61-00 · SOLUBLE IN WATER`

The single granule multiplies — 1, then a handful, then a stream — and begins
to move. **The stream is the object that carries the next ten minutes.**

*≈ 35 s. Deliberately the shortest scene: context, then straight back to
engineering.*

---

## SCENE 03 — FOLLOW THE MATERIAL
**Idea:** continuous transformation through a coupled chain; the dryer is one
stage of it.

The camera tracks the granule stream along a curving path through seven
volumetric stations, each a simplified credible vessel form, dim until the
stream is inside it, then lit:

`acid pretreatment · ammonia vaporization · neutralization · buffer /
stabilization · concentration & crystallization · centrifugation · DRYING ·
cooling & conditioning`

The mother-liquor recycle leaves centrifugation as a thin returning line and
rejoins neutralization behind the camera — visible for two seconds, enough to
establish that the chain is coupled.

One caption holds throughout, monospace, bottom-left:
`H₃PO₄ + NH₃ ⇌ NH₄H₂PO₄`

At the drying station the camera slows. Everything upstream falls into fog.

*≈ 60 s. No PFD. No labels on every vessel. The audience should feel a journey,
not read a diagram.*

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
vacuum                    48.60 mmH₂O
fan speed                1,344.8 rpm
```

Then the output side, in `--lab` white: `FINAL MOISTURE — % H₂O`.

*≈ 75 s. The longest scene, because it is the one the whole argument stands on.*

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
00:00  0.0742 % H₂O
02:00  0.0796 % H₂O
04:00  0.0804 % H₂O
06:00  0.0806 % H₂O
08:00  0.0812 % H₂O
10:00  0.0800 % H₂O
```

The camera drops to axis level and **travels down the dark interval** between
the first two markers. A monospace counter runs `+00:00 … +02:00`. The granules
keep streaming past. Nothing else is known.

> **THE PROCESS NEVER STOPS.**
> *(hold)*
> **LAB VISIBILITY DOES.**

`LAB Δt ≈ 2 h` sits small beside the markers.

Closing line, quiet: between those two results the product actually moved by
`0.0054 % H₂O`, and nothing measured it.

*≈ 80 s. The jury must feel the interval, so the travel through it is played at
real reading pace and not hurried.*

---

## SCENE 06 — THE ENGINEERING RESPONSE
**Idea:** fill the interval with inference, not with more sampling.

Same space, no reset. The camera is still inside the gap.

> **HOW DO WE SEE BETWEEN MEASUREMENTS?**

Process signals rise from the dryer at the origin — thin teal lines, one per
variable — and travel down the time axis into the dark. As they arrive, the
**continuous predicted-moisture trace draws itself** across the gap, left to
right, at reading speed: 695 real soft-sensor points, landing close to each
laboratory marker without ever overwriting it.

The camera pulls back to see all 12 hours at once: dense continuous estimate,
six solid measurements.

Two statements, staged:

> **PREDICT QUALITY BETWEEN MEASUREMENTS.**
> **DETECT ABNORMAL BEHAVIOUR EARLIER.**
>
> **TWO QUESTIONS. ONE SUPERVISION SYSTEM.**

Guard rail on screen: `LABORATORY ANALYSIS REMAINS THE REFERENCE`.

*≈ 60 s.*

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

One packet is followed individually through the ALIGN layer: it **waits**
`24.5 min` before joining, and the caption explains why — the product being
measured now left the dryer then. This is the one piece of the method that
cannot be shown any other way.

*≈ 70 s.*

---

## SCENE 08 — TWO INTELLIGENCE PATHWAYS
**Idea:** two different questions, two different kinds of model, one system.

The packet stream splits into two lanes in space.

**Lane A — QUALITY INTELLIGENCE** (left)
16 aligned features enter a compact solid form; one continuous value leaves it.
`RIDGE · α = 10 · selected on validation RMSE`.
> **WHAT IS THE LIKELY FINAL MOISTURE NOW?**

**Lane B — PROCESS INTELLIGENCE** (right)
The camera moves into an actual 3-D point cloud: **2,400 real TRAIN process
states**, PCA-projected (93.7 % variance). Then **136 brighter points** — the
model's own support vectors — resolve on the cloud's outer shell.
`ONE-CLASS SVM · ν = 0.02 · UNSUPERVISED NOVELTY DETECTION · LEARNS NORMAL ONLY`.

A single moving point enters: the current process state, following the real
recorded trajectory. It orbits inside the cloud calmly — then, over 44 minutes
of replay, **it leaves**. Distance from the learned region grows, the point
turns amber then red, and the contributing variables name themselves.
> **IS THE PROCESS BEHAVING UNUSUALLY?**

The lanes converge into one word: **SUPERVISION**.

Explicit on screen: `NO ANOMALY LABEL IS USED IN TRAINING`.

*≈ 80 s. No brains, no neural nets, no robots — the model is shown as the
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

> **R² 0.8245** · **MAE 0.00107 % H₂O** · **RMSE 0.00140 % H₂O**
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

*≈ 90 s.*

---

## SCENE 10 — VALIDATION BECOMES SUPERVISION
**Idea:** the evidence is not a report; it is already an operator's screen.

The camera pulls back from Panel A. Its frame thickens, gains a title bar, a
legend, a card edge — **it has become a Power BI visual.** The real dashboard
assembles around it, card by card, in reading order, from the actual capture:

1. predicted final moisture
2. latest laboratory moisture
3. validated moisture error
4. current anomaly risk (warning 0.50 · critical 0.80)
5. process status · anomaly severity
6. rolling 8-hour moisture and risk trend
7. critical process variables
8. diagnosis context and operator guidance

The `PROTOTYPE · REPLAY` pill and the advisory footer are visible because they
are on the real screen. The lighting warms: dashboard light spilling into a
dark control room.

*≈ 65 s. Nothing is invented — every highlighted element exists in the shipped
report.*

---

## SCENE 11 — THROUGH THE DASHBOARD
**Idea:** end-to-end integration, proved by travelling through it.

Instead of an architecture slide, the camera **pushes through the dashboard
plane**. Behind it, in depth:

```
POWER BI     DirectQuery · ~5 s automatic page refresh · reads views only
   ↓
SQL          5 semantic views
             vw_dryer_dashboard_powerbi · vw_dryer_contributors_powerbi
             vw_dryer_lab_samples · vw_dryer_anomaly_events
             vw_dryer_overview_trends_powerbi
   ↓
POSTGRESQL   dryer_map · dryer_model_outputs · dryer_abnormal_variables
   ↓
PYTHON       realtime_service.py · loads the exact notebook artifacts once
             9 ms average inference cycle, 47 ms maximum
   ↓
REPLAY       held-out TEST · 237,600 rows · Δt = 5 s
```

The replay stream leaves the last slab — and **runs back to the dryer**, which
is still turning in the distance. The loop closes in one continuous camera move
and the whole system is visible in a single frame.

`POWER BI NEVER LOADS A MODEL AND NEVER RUNS INFERENCE.`

*≈ 65 s.*

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

*≈ 50 s.*

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

*≈ 55 s.*

---

## SCENE 14 — RETURN
**Idea:** the physical process never stopped; digitalisation made more of it
visible.

The camera returns to the opening framing — the same columns, the same dryer,
the same rim light. It is recognisably frame one.

But the world now carries a calm digital layer: sensor nodes glow softly,
signal lines move along the flow path, a faint prediction trace runs above the
product line. Nothing flashes. The dryer keeps turning.

> **THE PHYSICAL PROCESS NEVER STOPPED.**
> **DIGITALIZATION MADE MORE OF IT VISIBLE.**
>
> *(hold, the world alone)*
>
> **FROM PROCESS MONITORING**
> **TO INTELLIGENT INDUSTRIAL OPERATION.**

The camera drifts. Then, small, bottom-left, in the eyebrow style:

> `QUESTIONS`

No "thank you". No summary slide. No credits.

*≈ 45 s.*

---

## Timing

| Act | Scenes | Target |
|---|---|---|
| I — Purpose | 01–02 | 1 min 25 s |
| II — Industry | 03–04 | 2 min 15 s |
| III — The gap | 05–06 | 2 min 20 s |
| IV — Digitalization | 07–08 | 2 min 30 s |
| V — Evidence & supervision | 09–11 | 3 min 40 s |
| VI — Value & future | 12–14 | 2 min 30 s |
| | | **≈ 14 min 40 s** |

That is the upper bound with full pauses. The speaker notes provide a marked
**12-minute path** (compressing 02, 12 and holding fewer beats in 04 and 09) and
a **10-minute emergency path**. The presenter controls every advance, so the
experience contracts and expands without any edit to the build.

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
