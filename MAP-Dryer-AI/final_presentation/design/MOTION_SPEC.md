# MOTION SPEC

Every transition in the film, specified. Each one answers *why is this moving?*
If the answer had been "to look nice", the motion was cut.

> **This document is generated against the source.** The table in §4 comes from
> `web/scripts/spec-dump.mjs`, which reads `state/scenes.js` directly. Regenerate
> it with `node scripts/spec-dump.mjs > ../design/_motion_table.md` after any
> change to a camera pose, a tier or a lens. The previous version of this file
> described a build that no longer exists — a uniform 2.2 s transition, a macro
> granule in scene 02, and beats that have since been cut — which is exactly the
> failure mode this note exists to prevent.

---

## 1. GLOBAL CONSTANTS

* **One GSAP timeline per transition.** Camera, layer presence, material
  crossfades, light changes and in-world reveals are all children of it, so they
  cannot desynchronise. There is no independent `setTimeout` in the application.
* **`gsap.ticker.lagSmoothing(0)`.** A hitch skips frames instead of stretching a
  3.1 s move into 30 s. For a live talk the wall clock is what matters.
* **Camera ease** `power2.inOut` · **reveal** `power3.out` · **exit** `power2.in`.
* **Reverse** runs at `tier x 0.72`; **random access** (the `G` prefix) settles in
  0.9 s and hard-sets every channel first, so a jump can never leave a half-dressed
  world.
* **Light resolves early:** mode changes tween over `min(1.4, dur x 0.55)` from
  position 0, so a lighting flip and a long translation are never both still
  finishing at the end of a move.
* **Idle drift** +/-0.12 u over ~24 s, **disabled in editorial mode** — breathing the
  camera makes static type swim.

### Text is sequenced against the world, not swapped underneath it

The single highest-value motion fix in the deck. `Overlay.jsx` no longer re-keys
on scene+beat.

| Phase | Values |
|---|---|
| old copy leaves | opacity → 0, y → −8 px, blur → 3 px, **0.34 s** |
| world travels | the transition's own tier |
| new copy resolves | opacity 0 → 1, y +14 px → 0, blur 4 → 0, **0.7 s**, 0.06 s stagger |

The swap fires at `max(0.34, tier x 0.46)`. A micro-beat therefore stays snappy and
an act change gets room; the world always arrives before the language does.

---

## 2. TRANSITION TIERS

Duration follows **narrative weight first, spatial distance second**. Before this
existed, a 4.6 u micro-creep and a 100 u act change both took 2.2 s, which is what
made the film read as templated rather than directed.

| Tier | s | Used for | Count |
|---|---|---|---|
| `micro` | **1.5** | a small adjustment inside one idea | 3 |
| `standard` | **1.9** | a normal beat change | 11 |
| `act` | **3.1** | a new place, a new act, or a lighting change | 20 |
| `signature` | **3.5** | the three transformations the film is built on | 3 |
| `return` | **3.6** | the one journey home | 1 |

**Transition budget: 101.5 s over 38 transitions — 13.4 % of the 758 s runtime.**

The three `signature` beats are `05a` (distance becomes time), `10a` (artifact →
service → screen) and `11a` (through the plane). `return` is used once, for
`13b → 14a`.

---

## 2b. THE EASING VOCABULARY

The camera had a grammar and the world did not. Forty-eight channel tweens used
ten different curves, which looks varied in a grep and is not: `power2.out` was
carrying a vessel filling, a chart appearing, a service starting and a label
fading, so the variation was incidental rather than meaningful. Motion that eases
the same way regardless of what is moving is the clearest tell that a film was
assembled from a library.

Seven intents, declared once in `three/transitions.js` as `EASE` and named by
every world tween that carries meaning:

| Intent | Curve | What it is for |
|---|---|---|
| `MECH` | `power3.inOut` | something with mass moves — the path straightening into a time axis, the artifact folding into a service, the loop rising |
| `ARRIVE` | `power4.out` | an object lands and stops. No wind-up; a long settle. Weight coming to rest, not a fade finishing |
| `DATA` | `power2.out` | a value resolving. Crisp and short — a number has no inertia |
| `REVEAL` | `power1.inOut` | something becomes visible without moving. Restrained; anything more assertive turns an appearance into an event |
| `ALARM` | `power2.in` | the anomaly grammar: an accelerating departure. A state leaving its learned region does not ease politely out of it |
| `COUNT` | `none` | linear, and only where the animation is counting real arrivals — the stack assembling from packets, the runtime lighting checkpoints, the marker crossing the dryer. Easing these would be a lie about a rate |
| `SOLID` | `back.out(1.4)` | the one overshoot in the film, reserved for the six laboratory results, because they are the only directly measured points in it |

Thirty-six tweens name an intent. What deliberately does **not**: the neutral
layer cross-fade (`ch()`), the camera (which has its own tier grammar above), the
reduced-motion fallbacks, and a handful of fade-outs — where the curve carries no
meaning and pretending otherwise would be worse than the default.

---

## 3. LENS LANGUAGE

Focal length carries meaning, so it is declared once in `lib/curves.js` and
referenced **by name** from the scene table — never as a literal. A scene changes
lens at most once, and never at the same time as a large translation.

| Role | FOV | Meaning |
|---|---|---|
| `ESTABLISH` | 40° | the hall, the plant, the return |
| `TRAVEL` | 46° | moving along the material or along time |
| `EQUIPMENT` | 34° | a machine understood in the round |
| `INTERIOR` | 38° | inside the shell |
| `SYSTEM` | 44° | architecture, manifold, runtime |
| `EDITORIAL` | 38° | charts and evidence — fixed for the whole act |
| `EDITORIAL_WIDE` | 36° | the roadmap rail only |
| `MATERIAL` | 30° | the product itself |

Scenes 08 and 13 hold **one** lens across all their beats. The evidence act (09)
and the supervision act (10) share `EDITORIAL`, so walking from the last chart to
the operator's screen carries no focal change at all — the only thing that changes
is where you are.

---

## 4. THE TABLE

`Δpos` = camera translation from the previous step · `Δtgt` = look-at translation ·
`r` = camera-to-target radius at rest.

| # | Step | Beat | Mode | Tier | s | Δpos | Δtgt | ΔFOV | r | Lens |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | **01** | Awakening | dark | `standard` | 1.9 | 0 | 0 | +0 | 39 | ESTABLISH 40° |
| 1 | **02a** | PHOSPHORUS | focus | `act` | 3.1 | 26.8 | 49.3 | -10 | 26 | MATERIAL 30° |
| 2 | **02b** | PLANT NUTRITION | focus | `micro` | 1.5 | 3.5 | 0 | +0 | 23 | MATERIAL 30° |
| 3 | **02c** | SOLUBLE MAP | focus | `micro` | 1.5 | 3.5 | 0.1 | +0 | 19 | MATERIAL 30° |
| 4 | **03a** | THE CHAIN | dark | `act` | 3.1 | 76.2 | 54.1 | +16 | 44 | TRAVEL 46° |
| 5 | **03b** | 01 PRETREATMENT | dark | `standard` | 1.9 | 19.2 | 11.3 | +0 | 21 | TRAVEL 46° |
| 6 | **03c** | 02 AMMONIA VAPORIZATION | dark | `standard` | 1.9 | 13.9 | 14.5 | +0 | 24 | TRAVEL 46° |
| 7 | **03d** | 03 NEUTRALIZATION | dark | `act` | 3.1 | 12 | 11.8 | +0 | 23 | TRAVEL 46° |
| 8 | **03e** | 04 BUFFER / STABILIZATION | dark | `standard` | 1.9 | 13.2 | 13.1 | +0 | 26 | TRAVEL 46° |
| 9 | **03f** | 05 CRYSTALLIZATION | dark | `act` | 3.1 | 14.7 | 14.6 | +0 | 28 | TRAVEL 46° |
| 10 | **03g** | 06 CENTRIFUGATION | dark | `standard` | 1.9 | 18.8 | 15.9 | +0 | 22 | TRAVEL 46° |
| 11 | **03h** | INTO THE DRYER | dark | `act` | 3.1 | 30.4 | 15.3 | +0 | 48 | TRAVEL 46° |
| 12 | **04a** | MACHINE | focus | `act` | 3.1 | 28.5 | 42.2 | -12 | 49 | EQUIPMENT 34° |
| 13 | **04b** | PHYSICS | focus | `act` | 3.1 | 35.7 | 2.4 | +4 | 15 | INTERIOR 38° |
| 14 | **04c** | DATA | focus | `act` | 3.1 | 36.4 | 14.3 | -4 | 47 | EQUIPMENT 34° |
| 15 | **05a** | DISTANCE BECOMES TIME | dark | `signature` | 3.5 | 49.4 | 53.1 | +12 | 66 | TRAVEL 46° |
| 16 | **05b** | SIX LABORATORY RESULTS | dark | `act` | 3.1 | 44.9 | 15 | +0 | 93 | TRAVEL 46° |
| 17 | **05c** | THROUGH THE INTERVAL | dark | `act` | 3.1 | 81.6 | 31 | +0 | 31 | TRAVEL 46° |
| 18 | **06a** | THE QUESTION | dark | `act` | 3.1 | 33.2 | 24 | +0 | 50 | TRAVEL 46° |
| 19 | **06b** | ESTIMATE BETWEEN MEASUREMENTS | dark | `standard` | 1.9 | 34.4 | 4.5 | +0 | 81 | TRAVEL 46° |
| 20 | **07a** | SENSORS | dark | `act` | 3.1 | 77.5 | 76.5 | -2 | 34 | SYSTEM 44° |
| 21 | **07b** | THE STACK BUILDS | dark | `standard` | 1.9 | 27.1 | 46.1 | +0 | 53 | SYSTEM 44° |
| 22 | **07c** | RESIDENCE-TIME ALIGNMENT | dark | `standard` | 1.9 | 29.7 | 8.2 | +0 | 42 | SYSTEM 44° |
| 23 | **08a** | THE SPLIT | dark | `act` | 3.1 | 23.8 | 26.7 | +0 | 54 | SYSTEM 44° |
| 24 | **08b** | QUALITY INTELLIGENCE | dark | `act` | 3.1 | 48.9 | 35.4 | +0 | 28 | SYSTEM 44° |
| 25 | **08c** | PROCESS INTELLIGENCE | dark | `act` | 3.1 | 49.5 | 60.5 | +0 | 38 | SYSTEM 44° |
| 26 | **09a** | MOISTURE HOLD-OUT | editorial | `act` | 3.1 | 29.7 | 18.6 | -6 | 44 | EDITORIAL 38° |
| 27 | **09b** | WHY RIDGE | editorial | `standard` | 1.9 | 22.4 | 23.5 | +0 | 44 | EDITORIAL 38° |
| 28 | **09c** | ANOMALY EVIDENCE | editorial | `standard` | 1.9 | 22.4 | 24 | +0 | 44 | EDITORIAL 38° |
| 29 | **09d** | WHAT IT IS WORTH | editorial | `act` | 3.1 | 26.6 | 21.9 | +0 | 49 | EDITORIAL 38° |
| 30 | **10a** | VALIDATION → SUPERVISION | supervision | `signature` | 3.5 | 19.7 | 30.6 | +0 | 39 | EDITORIAL 38° |
| 31 | **10b** | WHAT THE OPERATOR READS | supervision | `micro` | 1.5 | 2.4 | 1 | +0 | 40 | EDITORIAL 38° |
| 32 | **10c** | DIAGNOSTICS PAGE | supervision | `standard` | 1.9 | 4.5 | 2 | +0 | 40 | EDITORIAL 38° |
| 33 | **11a** | THROUGH THE PLANE | supervision | `signature` | 3.5 | 116.2 | 44.1 | +6 | 52 | SYSTEM 44° |
| 34 | **11b** | THE RUNTIME PATH | supervision | `act` | 3.1 | 18.2 | 10.2 | +0 | 51 | SYSTEM 44° |
| 35 | **11c** | IT ENDS WITH A PERSON | supervision | `act` | 3.1 | 106.3 | 35.1 | +2 | 51 | TRAVEL 46° |
| 36 | **12** | What this is worth | editorial | `act` | 3.1 | 65.9 | 60 | -8 | 42 | EDITORIAL 38° |
| 37 | **13a** | IMPLEMENTED TODAY | editorial | `act` | 3.1 | 38.2 | 31.8 | -2 | 43 | EDITORIAL_WIDE 36° |
| 38 | **13b** | WHAT COMES NEXT | editorial | `act` | 3.1 | 40.4 | 28 | +0 | 73 | EDITORIAL_WIDE 36° |
| 39 | **14a** | MORE OF IT VISIBLE | dark | `return` | 3.6 | 67.2 | 20.8 | +4 | 39 | ESTABLISH 40° |
| 40 | **14b** | QUESTIONS | dark | `standard` | 1.9 | 0 | 0 | +0 | 39 | ESTABLISH 40° |

### Reading the outliers

| Step | Δpos | Why it is that big |
|---|---|---|
| `11a` | 116.2 u | The push through the report plane **and** the relocation to the far side of the runtime, as one `signature` move. 32 u/s — travel, not a teleport. |
| `11c` | 106.3 u | Back out in front of the plane for the handover to the operator. 34 u/s. |
| `05c` | 81.6 u | Sets up the 6.5 s constant-velocity gap travel. Protected. |
| `03a` | 76.2 u | Out to the head of the chain for the establishing wide. 25 u/s on an `act` tier — and it is the only big move left in scene 03. The seven that follow it are 12–19 u each, because the camera is now WALKING the chain rather than jumping between four of its seven stations. |
| `07a` | 77.5 u | Process → architecture. Staged so the lighting has already resolved. |
| `14a` | 67.2 u | The return. Lands on scene 01's pose exactly. Protected. |
| `12` | 65.9 u | Rise to altitude **plus** the dark → cream chapter flip. Given the `act` tier explicitly; a scene with no beats would otherwise inherit `standard`. |
| `14b` | **0.0 u** | **Deliberate hold, not a cut.** The closing rhyme is the ending; the world must not move again once it has landed. Only the copy changes, and idle drift keeps the frame alive. |

The three `micro` moves are genuinely small adjustments inside one idea:
`02b` and `02c` (3.5 u each) are word-level beats easing toward a still
photograph, and `10b` (2.4 u) is a lean toward the report's KPI row while the
five callout regions are named. `10c` keeps the `standard` tier despite moving
only 4.5 u, because the *content* event is a full page change — narrative
weight first, distance second.

---

## 5. SIZE, SCALE AND ANNOTATION RULES

### Scale is a motion decision too

Two things are sized to the distance the camera actually uses, not to a single
"correct" value:

* **Granules** (`granuleSize`) — 1 through the process scenes at 15-45 units,
  **0.45** in scene 03, where the camera settles close enough to the pipe that
  the stream otherwise reads as beads threaded on it, **2.2** on the time axis
  at 66-93 units, **1.5** on the 05c travel at 31, and
  **2.8** at the soft-sensor scene at 50-80. A granule at its process size
  subtends about two pixels out on the axis, which turned the film's signature
  reveal into a speckle. The stream represents flow; it is not a claim about
  grain size.
* **Value-loop labels** (scene 12) are billboarded *and* depth-compensated, so
  the near and far side of the ring read at one size instead of a 1.75x spread
  that implied a ranking.

### Annotations face the lens

In-world text that annotates an object — runtime checkpoints, architecture
layers, ring nodes, telemetry chips, physics direction cues, chain stations —
turns to the camera and, where it must never be occluded, draws with depth
testing off. Text that lies in the world's own plane skews, swings out of frame
at the edges, and can be rendered mirrored by a camera on the far side of it.
All three happened before this rule existed — and the chain stations were still
doing the first of them until the second pass, because the rule was written here
and never applied there. Every equipment name in scene 03 was rendering as
skewed italics. It is applied now.

---

## 6. WHAT THE MOTION IS *NOT* DOING

Removed in remediation, and to stay removed:

* the Ridge model's permanent rotation (a spinning crystal is the "AI black box"
  trope the scene exists to refuse);
* the synchronised seven-dot sensor pulse (reads as a blinking UI, not telemetry);
* the value-ring breathing pulse, replaced by **one** signal travelling the loop
  once — which also supplies the direction cue the ring never had;
* the wireframe held on through scene 07, where it only added haze;
* scene 02's `setInterval` word cycle — three presenter-driven beats now;
* the scene-10 highlight boxes leaking into scene 11;
* idle drift in editorial mode.

Sound: **there is none, and none is to be added.** The presenter's voice is the
soundtrack, and the 6.5 s silent travel in `05c` is where the silence does the work.
