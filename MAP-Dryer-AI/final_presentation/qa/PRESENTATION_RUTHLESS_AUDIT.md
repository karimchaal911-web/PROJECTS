# RUTHLESS FINAL AUDIT — SOLUBLE MAP SOUTENANCE (Three.js / R3F build)

**Audited:** 2026-08-27 · **Subject:** `final_presentation/web` (React Three Fiber, 14 scenes / 39 steps)
**Nothing in the presentation was modified.** This is a diagnostic pass only.

> **Path note.** The brief specified `final_presentation/qa/`. That directory belongs to the
> earlier Codex attempt; the audited build lives in `final_presentation/`. This report is
> written to the requested path and mirrored alongside the work it audits. It supersedes the
> earlier `PRESENTATION_RUTHLESS_AUDIT.md` in `final_presentation/qa/`, several of whose
> claims I could not reproduce and have corrected below.

## Method — what was actually inspected, not recalled

| Pass | Evidence |
|---|---|
| A — full run | All 35 captured stills at 1920×1080 (`exports/screenshots/`, captured 2026-08-27T17:27Z) reviewed frame by frame |
| B — motion | All 39 camera poses extracted programmatically from `state/scenes.js`; 34 inter-step deltas computed (position distance, target distance, ΔFOV, direction vector, radial distance) |
| C — content | `state/scenes.js` copy tree, `overlay/Chrome.jsx` cue deck, `lib/curves.js` data constants |
| D — Apple discipline | Composition, negative space, type scale and layer count per still |
| E — engineering jury | Every on-screen claim traced to its data source; unit rendering, symbol rendering, honesty badges |
| F — technical | **New GPU measurement run for this audit**: `node scripts/qa-perf.mjs --hold 2000`, headful Chrome, 1920×1080, standard mode, all 35 steps. Plus full read of all 33 source files, bundle inventory, dead-code trace |

Where this report gives a number (pixel heights, frame times, camera distances), it was measured or
computed, not estimated.

---

# 1. EXECUTIVE VERDICT

**The argument is excellent. The film is not.**

The intellectual spine of this presentation is genuinely strong and in places better than the
target: a real causal-alignment story, a chronological hold-out, an unsupervised detector defended
honestly, an on-screen honesty contract that never leaves the frame, and a roadmap that says
"closed-loop control does not exist in this project" out loud. An engineering jury will respect the
content. The narrative order — material → chain → machine → gap → response → digitalization →
two models → evidence → supervision → runtime → value → boundary → return — is correct and does not
need restructuring.

**What separates it from an Apple-level, scene-based, 3D OCP keynote is not polish. It is six
structural defects, all invisible in a storyboard and all obvious the moment you look at a rendered
frame:**

1. **The DOM overlay and the 3D world are never in sync.** `Overlay.jsx` re-keys on `${scene}:${beat}`,
   so the copy is destroyed and rebuilt instantly with a 0.7 s CSS entrance, while the world tweens
   over 2.2 s. There is **no exit animation at all** — the previous scene's headline vanishes on the
   frame the key changes. For ~1.5 s on **all 34 transitions**, the next scene's headline is fully
   legible over the previous scene's world. The `transitioning` flag exists in `useShow.js` and is
   set by the Rig — and is read by nothing. The wiring for the fix was built and never connected.

2. **The signature transformation is a crossfade, not a transformation.** Step `09d→10a` promises
   "THE SAME CHART. AN OPERATOR'S SCREEN." In the capture, the scene-09 hold-out chart (its title,
   its `n = 165` subtitle, its y-ticks, its R²/MAE/RMSE row) is **still legible, ghosted, across the
   top half of the Power BI capture**, and the two charts visibly do not correspond — one is a
   165-point 13-day scatter, the other an 8-hour smooth rolling trend with step changes. The
   `PBI_TREND_UV` registration rectangle was measured honestly from the export and then not used:
   nothing lands on it. The film's central conceit is asserted in the documentation and contradicted
   on screen.

3. **The project's actual deliverable is shown at its worst.** The Power BI capture announces
   `DATA · STALE` in red at top-right, `STALE` on all five process-variable tiles, and
   `ingested 8525 min ago` (≈ 6 days) — while the eyebrow above it reads `~5 S PAGE REFRESH` and the
   copy talks about real-time supervision. It is also captured in its **null state** (NORMAL / "No
   active anomaly" / "No anomaly-related cause list is generated"), so the diagnosis story has
   nothing to show. And at beat `10a` it is rendered at **30 % opacity** (`base = clamp((0.45-0.3)/0.5)`),
   i.e. unreadable, for the entire introduction of the dashboard.

4. **Scene 09 is a web page, not a scene.** The four evidence beats move the camera
   `[0,−15,−2]`, `[0,−19,+2]`, `[0,−15,−4]` — three consecutive, near-identical, pure-vertical drops
   at constant radius (r = 36–40) and zero FOV change. That is scrolling. And `10b→10c` moves the
   camera **0.0 units with 0.0 target change and 0° FOV change** — a literal static cut between two
   full screens of content, in a presentation whose thesis is "one continuous world."

5. **Type below legibility carries the most important content.** The roadmap stage labels — the
   built-vs-not-built honesty signal — are set at `fontSize 0.36` world units viewed from 52.6 units
   at 46° FOV. That renders at **≈ 8.7 px tall on a 1080-line output**, cap height ≈ 6 px. On a
   projector they are gone. The same class of problem hits the scene-03 station labels (dark grey on
   dark green, three of seven occluded by geometry), scene 08's world captions (dark, skewed,
   near-black-on-black) and scene 14's telemetry chips.

6. **A measured 677.8 ms frame stall lands inside the signature push-through.** Standard mode on a
   fast GPU averages 230.8 fps with no scene under 50 fps — but step `11a` produced a single
   **677.8 ms** frame. The `Runtime` layer's five `MeshStandardMaterial`s and `EdgesGeometry` are
   never rendered before scene 11 (`group.visible = presence > 0.01`), so their shaders compile at
   first reveal. `BootGate`'s two-frame warm-up cannot cover them. On a mid-range projector laptop
   this becomes a 1.5–3 s freeze on the deck's most important camera move.

**Is it a coherent cinematic journey, or impressive scenes stitched together?** Honestly: it is a
*coherent argument* delivered as *scenes stitched together*. The persistent-world architecture is
real and is the right idea — nothing is unmounted, presence recedes rather than cuts, the flow path
genuinely becomes the time axis. But three things break the illusion of one world: the text/world
desync on every transition, the ghosting of receded layers into scenes where they mean nothing, and
the fact that every one of the 34 transitions uses the **identical 2.2 s duration and identical
`power2.inOut` ease**. A micro-beat and a 100-unit act change take exactly the same time. That
uniformity is what makes the deck read as templated rather than directed.

---

# 2. HONEST OVERALL SCORE

# **6.3 / 10**

**Why 6.3 and not an average.** The straight mean of the eighteen category scores below is ≈ 6.0.
I have not simply averaged, because two things pull in opposite directions and both are real:

- **Upward:** the engineering honesty, the data integrity (every number traced to a verified
  artifact), the narrative order, and the OCP palette derivation are genuinely at or near the
  target. Scene 09 beat 1 is a legitimately good editorial data frame.
- **Downward, and this is what caps it:** the presentation's own deliverable — the Power BI
  dashboard — is presented in its worst possible state (P: 4.5), and the two frames a jury will
  remember most (`11a` and `09d`) are respectively an unreadable six-layer overlap and a frame that
  prints its own headline twice.

Against normal academic decks this is a 9. Against **Apple-level cinematic discipline × elite
Three.js motion design × industrial credibility × OCP showcase quality**, which is the standard the
brief demands, it is a **6.3** — a strong, honest, well-argued presentation with shipping defects
that a keynote director would refuse to ship, and every one of them fixable in a focused pass.

---

# 3. CATEGORY SCORECARD

| # | Category | Score | One-line justification |
|---|---|---|---|
| A | Overall Presentation Quality | **6.5** | Strong argument, unreliable delivery |
| B | Apple-Style Discipline | **5.5** | No exit animations; double-exposure on every transition; 6 layers stacked in 11a |
| C | Cinematic Quality | **6.0** | Real lighting intent, but 34 identical 2.2 s transitions and one zero-motion cut |
| D | 3D Scene Quality | **6.0** | Untextured primitives; 7 process stations are 7 identical capsules; detail-0 icosahedron granules read as low-poly confetti |
| E | Scene-to-Scene Continuity | **5.5** | Persistent world is right; text/world desync + layer ghosting break it |
| F | Motion Design Quality | **6.0** | Zero duration or easing variation across 14 minutes |
| G | Animation Purposefulness | **6.5** | Mostly justified; four permanent sine pulses + a spinning Ridge model + labels arriving before their slabs |
| H | Visual Hierarchy | **5.0** | Headlines land on the subject; three competing columns in 07b; labels occluded in 03 and 11b |
| I | Typography | **5.0** | ~9 px roadmap labels; five sentences of body copy set in mono; `% H20`; `N = 0.02`; duplicated headline in 09d |
| J | OCP Visual Integration | **7.0** | Green structural steel derived from the real plant is the deck's best design decision; logos illegible at 0.5 opacity |
| K | Industrial Credibility | **6.0** | Honesty badges and real metrics are strong; generic vessels, unreadable physics, zero real photographs, STALE dashboard |
| L | Technical Clarity | **6.0** | Support vectors indistinguishable; runtime flow reads backwards; α/ν rendered two ways in one frame |
| M | Narrative Clarity | **7.0** | The strongest dimension — the argument is correct and well-ordered |
| N | Presentation Pacing | **5.5** | ~19 % dead time; first model result at 8:30 of 14:40; scene 03 holds 60 s on one frame |
| O | Data Visualization Quality | **6.5** | Panel A is good; no x-axis anywhere; mint-on-cream trace is the least legible line in the evidence act |
| P | Power BI Integration | **4.5** | STALE data, 30 % opacity intro, crossfade not transformation, cropped both edges, null diagnostic state |
| Q | Performance / Smoothness | **7.0** | Measured 230.8 fps mean / none < 50 fps — but a 677.8 ms stall and a dead auto-degrade path |
| R | Reliability for Live Soutenance | **6.0** | Offline, error boundary, safe mode, good keyboard — undercut by the stall, `makeFpsWatch` never wired, and half-dressed random access |

---

# 4. SCENE-BY-SCENE AUDIT

```text
SCENE 01 — AWAKENING (50 s, 1 step, dark)

Purpose:
Find the plant already running; establish scale, identity and the three promises.

What currently works:
- The rim-light-arriving-last idea genuinely reads; the drum is a solid object, not a shape.
- The 4.0 s power2.out settle-in is the correct opening gesture — found, not switched on.
- OCP green structural steel derived from the real plant photograph is the single best design
  decision in the deck.

Issues:
- The 4-line headline collides with the machine. Lines 3 and 4 ("OF SOLUBLE MAP / PRODUCTION")
  sit directly on the dryer's feed head; the left scrim has faded to zero by 60% width.
- The upper third is unresolved geometry: four large white cylinders with no purpose crossing
  frame, one running out of the top-right corner like an error.
- The yellow handrail (--handrail #B8952E) is the highest-contrast line in frame after the
  headline, and it crosses the hero object horizontally at its midpoint.
- The 1800 suspended dust points read as white fireflies / sensor noise against pure black,
  not as atmosphere. Clustered visibly in the upper right.
- Ground plane is flat #2B2A24 with hard-edged shadow rectangles — reads as a viewport floor.
- Identity lockup at opacity 0.5: the ENSAM/UMI mark is an unreadable grey smudge, its Arabic
  line is mush. On a projector it is worse.
- ~46 s of the 50 s hold has no motion but idle drift.

Motion issues:
- BootGate is unmounted, not faded: `{!started && <BootGate/>}`. The `.boot { transition:
  opacity 0.9s }` rule and the `is-ready` class are dead — no CSS rule matches `.is-ready`
  anywhere in styles.css. The show therefore HARD CUTS from the boot screen into scene 01.

Visual issues: see above.
Narrative ambiguity: none — this scene is honest.
Redundancy: the same frame returns in 14a (intended, and correct).
Technical ambiguity: none.

Recommended action: REFINE
Severity: MEDIUM
```

```text
SCENE 02 — WHY THIS MATERIAL (35 s, 1 step, focus)

Purpose:
Phosphorus → plant nutrition → soluble MAP. A macro moment on the product.

What currently works:
- The idea (the hero granule is a real instance of the same stream, not a prop) is correct.

Issues:
- THE MACRO SHOT DOES NOT HAPPEN. heroGranule tweens to 46 on an IcosahedronGeometry(0.085, 0)
  → circumradius 3.91, inradius 3.10, parked at (-11.6, 5.7, 4.4). The camera sits at
  (-13.0, 5.86, 7.7) — distance 3.59. The camera is BETWEEN the inradius and the circumradius,
  i.e. inside or grazing the solid, with near = 0.5. The capture confirms it: there is no hero
  granule in frame at all. What fills the frame is the dryer shell.
- The granules that ARE visible are detail-0 icosahedra at close range: obvious, faceted
  polygons. They read as generic 3D confetti, not MAP crystals.
- ~80 % of the frame is a featureless mid-grey wall (the shell). No focal point, no depth,
  no composition.
- A hard vertical edge (a structural column, arbitrarily cropped) sits directly behind the
  headline at the left.
- This is the only scene with no eyebrow — inconsistent with all thirteen others.
- The note says "Observed on product stored at the site." The site photograph
  (public/img/soluble_map_storage.jpg, 1280×960) is shipped in the bundle and NEVER REFERENCED.
  The claim is made with procedural geometry while the real evidence sits unused.

Motion issues:
- StepWord runs on setInterval(1900 ms) — three words auto-advance on a timer the presenter
  cannot control, in a presentation whose entire premise is presenter control. If the speaker is
  slow the words are gone; if fast, they are stuck. This is the only timed content in the deck.

Narrative ambiguity: "SOLUBLE MAP" appears with no visual referent.
Redundancy: none.
Technical ambiguity: none.

Recommended action: REBUILD
Severity: CRITICAL (this is the weakest scene in the presentation)
```

```text
SCENE 03 — FOLLOW THE MATERIAL (60 s, 1 step, dark)

Purpose:
Seven coupled stations with mother-liquor recycle; a deviation at the end is not one
component's fault.

What currently works:
- The chainHead fill (16 s, ease none) — stations light because material arrives — is a
  genuinely good causal idea.
- The equation and the coupling note are the right content.

Issues:
- ALL SEVEN STATIONS ARE THE SAME OBJECT: a cylinder with a hemisphere dome, varying only in
  scale. A neutralizer, a crystallizer and a centrifuge look nothing alike. A chemical
  engineering jury reads this as decoration, not process.
- LABEL COLLAPSE. "PHOSPHORIC-ACID PRETREATMENT" is cut by the left frame edge.
  "NEUTRALIZATION" is bisected by a vessel dome. "CONCENTRATION & CRYSTALLIZATION" is
  overlapped by its own vessel. "CENTRIFUGATION" is overlapped by green structure. Labels are
  dark grey on dark green. Three of seven are unreadable.
- The headline overlaps the first two stations; the eyebrow runs into "AMMONIA VAPORIZATION".
- The mother-liquor recycle — explicitly named in the copy — is a bare hairline curve with no
  arrowhead, no direction, no label, and no visible endpoint. The audience cannot see the recycle.
- Right third is an undifferentiated tangle of beams and cylinders with no hierarchy.
- Large dead zone across the bottom-centre-left.

Motion issues:
- 60 s hold with 16 s of fill = ~44 s of dead time. The largest single dead moment in the deck.

Narrative ambiguity: the recycle claim is unsupported visually.
Redundancy: none.
Technical ambiguity: seven identical vessels imply seven identical unit operations.

Recommended action: REBUILD (station geometry + labels) / SIMPLIFY (cut to ~40 s)
Severity: HIGH
```

```text
SCENE 04 — ENTER THE DRYER (75 s, 3 beats, focus)

Purpose:
MACHINE → PHYSICS → DATA. The stage that sets final moisture.

What currently works:
- The three-beat structure is exactly right and is the best-designed scene in the film.
- The dryer geometry is the strongest 3D asset: riding rings, girth gear with 96 instanced
  teeth, trunnions, feed chute, discharge hood, exhaust duct. Proportions are credible.
- The 26 s slow drift in 04a (relative tween, continues from the settled pose) is correct.
- "SCHEMATIC — NOT A CFD RESULT" is exemplary honesty. Protect it.

Issues (04b PHYSICS — the important one):
- THE PHYSICS IS IMPLEMENTED BUT NOT LEGIBLE. DryerInternals renders 12 instanced flights,
  900 bed particles, 420 counter-current air points and 260 vapour points — all correct. But
  at the beat camera (distance ≈ 33, FOV 40) a size-0.11 bed point subtends ≈ 2.5 px and the
  size-0.085 air points ≈ 2 px. On the capture they are indistinguishable mush.
- The three claims in the copy — flights lift and cascade, counter-current hot air, moisture
  leaves with the exhaust — have ZERO readable visual support. No flight blade is visible in
  section, no bed, no air direction, no exhaust plume.
- Turning on the wireframe drops shell opacity to 18 % (`1 - 0.82`), which also ghosts the
  surrounding plant. The upper-left third becomes an unreadable stack of translucent
  rectangles with no depth ordering.
- The wireframe twin is a 28×8 cylinder — the result reads as longitudinal cyan stripes, not
  as a machine section.
- Overall luminance in 04b sits around 8–15 %. In a lit soutenance room this frame is black.

Motion issues:
- 04a→04b is a 15.3 u dolly-in with a +6 FOV widen — the FOV change fights the dolly and
  partly cancels the sense of approach.

Narrative ambiguity: the audience is told physics and shown a glowing tube.
Redundancy: the wireframe idea returns in scene 07 (see redundancy map).
Technical ambiguity: the transparent shell reads as a glass dryer.

Recommended action: REFINE (get the camera inside; enlarge bed/air; raise exposure)
Severity: HIGH
```

```text
SCENE 05 — THE VISIBILITY GAP (80 s, 3 beats, dark)

Purpose:
Distance becomes time. Six lab results, two hours apart. The process never stops.

What currently works:
- flowPath(t, straighten) is the deck's best engineering idea: granules are never hidden and
  never re-emitted while distance becomes time. Architecturally correct.
- The 6.5 s constant-velocity travel in 05c (the only linear move in the film) is the right
  instinct — make the jury FEEL the interval.
- The back.out(1.4) overshoot reserved for the one measured thing is a genuinely good
  motion-design decision.
- Lab marker Y does encode moisture (via makeMoistureMapper). Honest.

Issues:
- "SIX RESULTS." IS SAID WHILE FOUR ARE ON SCREEN. Geometry confirms it: the axis spans
  x ∈ [16, 142]; the 05b camera (pos [44,20,58], target [58,4,0], FOV 44) has a half-width of
  ≈ 43 u, so visible x ≈ 15–101. The 10:00 and 12:00 markers (x ≈ 121, 142) are off-frame, and
  00:00 is clipped at the left edge. The jury will count.
- The axis title "HELD-OUT TEST · 2026-07-05 · 12 HOURS · PROTOTYPE REPLAY" is C.outline at
  0.55 fillOpacity on near-black, skewed in perspective, and cut by the left frame edge.
  Effectively invisible — and it is the line that establishes the replay boundary.
- Leftover plant geometry (plant 0.3) renders as translucent green beams and a white pipe in
  the upper-left. Pure noise in what should be the cleanest data scene in the deck.
- The material stream is a thin white speckled line. At projector scale it reads as dust.
- The "quality plane" (126 × 10.8, teal, 4.5 % opacity) is an unexplained faint rectangle with
  a hard edge. It has no label. It reads as a rendering artifact.
- ~60 % of the frame is empty black with the subject stranded as a thin band in the upper middle.

Motion issues:
- 05a→05b moves 4.9 u — a micro-adjustment that reads as drift, not intent.

Narrative ambiguity: the count mismatch is the worst in the deck.
Redundancy: none.
Technical ambiguity: 0.0054 % H₂O of movement is stated but not visually locatable.

Recommended action: REFINE (widen 05b to contain all six; kill the plant ghost; label or cut
the quality plane)
Severity: HIGH
```

```text
SCENE 06 — THE ENGINEERING RESPONSE (60 s, 3 beats, dark)

Purpose:
Not more sampling — inference. Two questions, one supervision system.

What currently works:
- "Not by sampling more often. By inferring from what is already measured continuously." is the
  single best sentence in the deck.
- The 5.2 s trace draw at position 0.6, driven by the arriving signals, is well motivated.
- "LABORATORY ANALYSIS REMAINS THE REFERENCE" caption is correct and necessary.

Issues:
- THREE CONSECUTIVE PULL-BACKS. Radius goes 31 → 50 → 80 → 102 across 05c→06a→06b→06c. Four
  retreats in a row, each larger than the last, all the same gesture. By 06c the camera is
  102 u out and the subject is a hairline.
- The scene ends at the farthest camera position in the deck and is immediately followed by a
  98.5 u jump (06c→07a, r 102→34). That pair is the most disorienting moment in the film.
- Boundary badge is present (good) but the scene otherwise has the least visual substance of
  any three-beat scene.

Motion issues: as above.
Visual issues: at r = 102 the axis, trace and markers are all sub-pixel-thin.
Narrative ambiguity: "TWO QUESTIONS. ONE SUPERVISION SYSTEM." is then restated as scene 08's
entire thesis ("ONE STREAM. TWO MODELS.").
Redundancy: HIGH — see content redundancy list, item 1.
Technical ambiguity: none.

Recommended action: SIMPLIFY (fold 06c into 08a; keep 06a and 06b)
Severity: MEDIUM
```

```text
SCENE 07 — PHYSICAL BECOMES DIGITAL (70 s, 3 beats, dark)

Purpose:
Sensors → the stack builds from arriving packets → residence-time alignment.

What currently works:
- "Nothing here is drawn in advance. Each layer forms when its data arrives." is the right
  claim, and archBuild genuinely implements it (7 s, ease none).
- The alignPause beat — one packet waiting 24.5 min inside the ALIGN layer while the rest dim —
  is the most sophisticated single idea in the whole film. Protect it.
- "CAUSAL BY CONSTRUCTION — NO FUTURE INFORMATION" is exactly the right caption.

Issues:
- LABELS ARRIVE BEFORE THEIR SLABS. Architecture.jsx gates labels all-or-nothing
  (`labels.current.visible = p > 0.4`) while slabs build progressively over 7 s. For the whole
  build, up to 8 labels float in empty black with no slab beside them. The capture shows
  OPERATOR, SUPERVISE and PERSIST hanging in the void above the top slab, which destroys the
  label→slab mapping the scene depends on. The code comment claims "Labels are legible or
  absent — never a ghost over another scene"; the implementation does the opposite.
- Three competing columns: headline left, stack centre-right, label column far right. No
  reading path.
- Receded plant/dryer (0.2/0.55) washes a large milky quadrilateral across the lower-left,
  occluding the PROCESS and SENSE sub-labels.
- The OPERATOR node is a thin white line disappearing off the top of frame into nothing. The
  human in the loop — the deck's stated position — is rendered as an absence.
- Slabs scale from centre (`g.scale.y = local`) rather than from their base, so they inflate
  rather than stack.
- The translucent-slab-stack metaphor is used again, differently, in scene 11.

Motion issues: the align glow (emissiveIntensity 0.05 → 0.45) is too subtle to read at this
camera distance. Also `i % 97 === 0` holds TEN packets, not the "one packet" the comment claims.
Narrative ambiguity: which slab is which.
Redundancy: shares its metaphor with scene 11.
Technical ambiguity: MEDIUM.

Recommended action: REFINE (gate labels per-slab; cut the plant ghost; anchor OPERATOR)
Severity: HIGH
```

```text
SCENE 08 — TWO INTELLIGENCE PATHWAYS (80 s, 4 beats, dark)

Purpose:
One stream, two models. Ridge for quality; One-Class SVM for behaviour.

What currently works:
- Reassigning packet targets rather than re-emitting them, so the audience sees ONE stream
  bifurcate, is architecturally correct and narratively important.
- Rendering the manifold from real geometry — 2,400 real TRAIN states, PCA(3), the model's own
  136 support vectors, the real recorded trajectory — is the most intellectually honest 3D
  decision in the deck.
- "NO ANOMALY LABEL IS USED IN TRAINING" is essential and correctly placed.

Issues:
- THE SUPPORT VECTORS ARE NOT DISTINGUISHABLE. normalMat is size 0.34 with AdditiveBlending
  over 2,400 points; supportMat is size 0.62 with AdditiveBlending over 136. In dense regions
  the accumulated brightness of the normal cloud exceeds the support points. The copy stakes
  its most technical claim ("the 136 brighter points ... define the learned boundary") on a
  distinction the render does not deliver. Verified against the capture: the bright region reads
  as a denser part of the cloud, nothing more.
- THE SAME PARAMETER IS PRINTED TWO WAYS IN ONE FRAME. The world label reads `v = 0.02`
  (troika font-fold of ν). The DOM caption reads `N = 0.02`, because `.caption` has
  `text-transform: uppercase` and CSS uppercases Greek ν → Ν, which is visually identical to
  Latin N. A jury reads "N = 0.02" as a sample size, which is nonsense. Same defect class hits
  the Ridge lane: world says `alpha = 10`, DOM says `α = 10`.
- The Ridge model is drawn as a CONTINUOUSLY ROTATING icosahedron
  (`solid.rotation.y = elapsedTime * 0.14`). A spinning crystal is the exact "AI black box"
  trope the design brief says it avoided, and it contradicts the code's own stated intent
  ("compact, solid, unmysterious"). It never stops.
- Packets have NO DIRECTIONAL READ: `_o.lookAt(_b.x, _b.y + 1, _b.z)` orients every instance
  straight up regardless of travel direction. They render as vertical tick-marks, which is why
  the capture shows grey/teal rectangles scattered in empty black on the left.
- World captions at the bottom ("2,400 TRAIN STATES · PCA(3) · 93.7 % OF VARIANCE" / "136
  SUPPORT VECTORS — THE LEARNED BOUNDARY") are C.outline at 0.7, skewed, near-black-on-black.
  Invisible on a projector.
- The 08b QUALITY beat is badly framed by construction: the lane content spans world x ≈ −33.5
  to −16.5 while the camera targets x = −34, putting the entire subject hard right of centre.

Motion issues: 08c→08d moves 6.0 u — effectively a static cut carrying a 6 s trajectory.
Narrative ambiguity: whether the trajectory is real or illustrative (it IS real; nothing says so
in-frame beyond the note).
Redundancy: restates 06c.
Technical ambiguity: HIGH (ν/N, support vectors).

Recommended action: REFINE
Severity: HIGH
```

```text
SCENE 09 — PROVE IT (90 s, 4 beats, editorial)

Purpose:
The evidence: hold-out, model selection, anomaly detection, and the limits.

What currently works:
- The cream editorial mode is a real chapter break and lands.
- Beat 09a is the single best frame in the presentation: legible chart, clear actual-vs-predicted,
  three metrics and only three, correct hierarchy. Projector-safe.
- Metrics are byte-identical to the notebook artifacts. This is real.
- Beat 09d exists at all. Stating the limits before the jury does is the right instinct.

Issues:
- THIS SCENE IS A SCROLLING WEB PAGE. Camera deltas: [0,−15,−2], [0,−19,+2], [0,−15,−4]. Three
  consecutive pure-vertical drops, constant radius (36–40), zero FOV change. There is no other
  reading of this than scrolling.
- BEAT 09d PRINTS ITS OWN HEADLINE TWICE. "WHAT THIS EVIDENCE IS WORTH." appears in the DOM
  overlay (left, huge) AND as world text (centre, large) simultaneously. Its sub-copy is also
  duplicated: the DOM note ("Synthetic prototype data. Chronological hold-out. Advisory. This is
  not plant validation.") restates three of the five world bullets verbatim. This is the most
  obviously embarrassing frame in the deck.
- PANELS NEVER TURN OFF. useFade(presence, beat, from, to=99) means PanelA (from 1) and PanelB
  (from 3) stay visible for all subsequent beats. At 09d the capture shows PanelB's red caption,
  its three metrics and a clipped event band still occupying the top of frame above the limits
  text. Only Candidates (2,2) and Limits (4,4) are correctly gated.
- Candidates HARD-POPS off at the midpoint of the 09b→09c tween — `g.visible` flips while
  opacity is still full. A visible pop, not a fade.
- NO X-AXIS ANYWHERE. Panel A plots 165 chronological points with no time ticks, no axis line
  and no labels. The reader cannot locate any point in time.
- `% H20` appears three times in Panel A. The font-fold turns the subscript into a character
  that reads as a zero. In a chemistry-adjacent presentation this is sloppy.
- The predicted trace is C.predict (#3DD6B0) on cream (#F5F2E4) — contrast ≈ 1.6:1. It is the
  most important line in the evidence act and the least legible element on screen. It will wash
  out on a projector.
- Y-ticks are computed at 15 / 50 / 85 % of range, producing 0.0801 / 0.0734 / 0.0666. Non-round,
  unreadable numbers where round ticks belong.
- THE PROGRESS RAIL IS INVISIBLE IN EDITORIAL MODE. `.rail` uses `color: var(--dust)` (#C9C4B6)
  on cream (#F5F2E4). Same for the amber boundary badge. Applies to scenes 09, 12, 13.
- Five sentences of body copy set in JetBrains Mono. Monospace is ~30 % wider and materially
  less legible for continuous reading.
- ~45 % dead space at the bottom of 09d while content clips off the top.

Motion issues: as above.
Redundancy: CRITICAL at 09d.
Technical ambiguity: none — the content is honest.

Recommended action: REBUILD the camera path (09) / REBUILD 09d layout
Severity: CRITICAL
```

```text
SCENE 10 — VALIDATION BECOMES SUPERVISION (65 s, 3 beats, supervision)

Purpose:
The hold-out chart becomes the operator's screen. Overview, then diagnostics.

What currently works:
- The intent is exactly right and is the correct climax for the argument.
- Measuring PBI_TREND_UV from the real 1600×900 export rather than eyeballing it was the right
  engineering instinct.
- Beat 10b, once the capture is at full opacity, is legible and credible.
- "PROTOTYPE · REPLAY · ADVISORY" caption is correct.

Issues:
- THE TRANSFORMATION IS A CROSSFADE. At 10a the scene-09 chart is still fully legible, ghosted,
  across the top half of the dashboard: its title, its `n = 165` subtitle, its y-ticks and its
  R²/MAE/RMSE row. Two entirely different charts occupy the same screen space. Nothing lands on
  the measured rectangle. `ch({ evidence: 0.3 })` keeps Evidence at 30 % presence for the whole
  scene, so the ghost persists into 10b as well.
- THE TWO CHARTS DO NOT CORRESPOND. Hold-out: 165 points, 2026-07-03 → 07-16, dense wiggle.
  Power BI: smooth 8-hour rolling curve with step discontinuities. "THE SAME CHART" is visibly
  false. This is the deck's largest visual overclaim, on its most important transition.
- THE DASHBOARD IS INTRODUCED AT 30 % OPACITY. base = presence × clamp((0.45 − 0.3)/0.5) = 0.3.
  For the entire 10a beat the project's actual deliverable is a murky grey rectangle.
- `DATA · STALE` (red pill, top right). `STALE` on all five process-variable tiles.
  `ingested 8525 min ago` ≈ 6 days. Directly under an eyebrow that says `~5 S PAGE REFRESH`.
  This is the single most damaging credibility contradiction in the presentation.
- THE NULL STATE WAS CAPTURED. PROCESS STATUS NORMAL, ANOMALY SEVERITY NORMAL, "No active
  anomaly", "No anomaly-related cause list is generated." The diagnosis story — an entire scene —
  has literally nothing to show.
- THREE DATE UNIVERSES ON SCREEN AT ONCE: hold-out 2026-07-03→07-16, last event 2026-08-06,
  ingested 2026-08-14. Unexplained.
- The capture is cropped off the right edge at 10a (DATA · STAL[E], Current diagnosis co[ntext],
  Operator guidance clipped) and off the bottom.
- The dashboard is a flat plane floating at x = 76 in an empty void. No bezel, no screen, no
  control room, no operator. "AN OPERATOR'S SCREEN" with neither operator nor screen.
- 10b→10c IS A ZERO-MOTION CUT: position delta 0.0, target delta 0.0, ΔFOV 0. Two full screens
  of content swap with no camera movement at all.
- The dashboard's own body text renders at ~6–7 px in frame. The "walk the KPI row" speaker cue
  asks the presenter to point at text the jury cannot read.

Motion issues: 10a→10b moves 11.2 u; 10b→10c moves 0.
Redundancy: the ghost chart.
Technical ambiguity: CRITICAL (STALE vs 5 s refresh; replay vs live).

Recommended action: REBUILD
Severity: CRITICAL
```

```text
SCENE 11 — THROUGH THE DASHBOARD (65 s, 3 beats, supervision)

Purpose:
Push through the Power BI plane; find the runtime in depth; close the loop.

What currently works:
- Proving end-to-end integration spatially rather than with a block diagram is the right idea.
- "POWER BI NEVER LOADS A MODEL AND NEVER RUNS INFERENCE" is precisely the claim a jury needs.
- The 11c closing frame concept — dashboard, slabs, returning stream and the still-turning dryer
  in one shot — is the best composition idea in the deck.

Issues:
- BEAT 11a IS THE WORST FRAME IN THE PRESENTATION. Six layers stacked simultaneously: the Power
  BI capture (opaque, cropped BOTH edges), five semi-transparent teal runtime slabs, five runtime
  labels written directly over the dashboard's own text, a LEFTOVER green highlight box from
  scene 10 ("DIAGNOSIS CONTEXT · OPERA…"), the granule stream, and the DOM copy. Nothing is
  legible. The intended claim "the runtime is BEHIND the dashboard" renders as "the runtime is
  written ON the dashboard."
- SCENE 10's HIGHLIGHT CHROME LEAKS IN. Scene 11 sets `dashHighlight: 1` and `dashPage: 0`;
  Dashboard.jsx only hides highlight boxes when `pg >= 0.5`. All eight boxes therefore remain.
- THE REVEAL IS MISTIMED AGAINST THE CAMERA. runtimeReveal starts at position D (2.2 s); the
  camera push starts at D + 0.6 (2.8 s) and runs 3.2 s. The runtime appears 0.6 s before the
  camera begins moving, and the two are co-located for the entire push.
- MEASURED 677.8 ms FRAME STALL at this step (see §13). Almost certainly first-use shader
  compilation for the five Runtime MeshStandardMaterials + EdgesGeometry, which are never
  rendered before this moment.
- 11b: FOUR OF FIVE SLAB LABELS ARE OCCLUDED. POWER BI covers "SEMANTIC VIEW[S]"; SQL covers
  POSTGRESQL; POSTGRESQL covers "INFERENCE"; PYTHON covers "REPLA[Y]". The staircase offsets in
  RUNTIME_SLABS were chosen specifically so "an oblique camera can see all five at once." They
  do not.
- THE FLOW READS BACKWARDS. Front-to-back the stack is POWER BI → SQL → POSTGRESQL → PYTHON →
  REPLAY, while the narration and the data both run REPLAY → … → POWER BI. There is no
  directional cue anywhere.
- SAME METAPHOR AS SCENE 07. Two different scenes use stacked translucent labelled slabs for two
  related concepts. A jury will not distinguish the architecture stack from the runtime stack.
- Sub-labels are light grey mono on saturated teal at an angle — barely readable.
- 11c is the slowest measured beat (83.6 fps mean, p95 16.7 ms) — 4.3× the cost of the evidence
  act on the same machine.
- Loop-close packets lerp in a straight diagonal across ~85 units of empty space with no path.

Motion issues / visual issues / redundancy / technical ambiguity: as above.

Recommended action: REBUILD 11a; REFINE 11b (label placement + flow direction)
Severity: CRITICAL
```

```text
SCENE 12 — WHAT THIS IS WORTH (50 s, 1 step, editorial)

Purpose:
Four defensible operational statements. No ROI, no control action.

What currently works:
- The four claims are correctly scoped and defensible.
- "NO ROI IS CLAIMED · NO CONTROL ACTION IS TAKEN · THE LABORATORY REMAINS THE REFERENCE" is
  the right caption in the right place.
- Rising to altitude as the grammar for synthesis is a sound instinct.

Issues:
- THE LOOP HAS NO DIRECTION. Six nodes on an ellipse joined by a hairline. No arrowheads, no
  flow, no travelling packet. In a still you cannot tell which way it goes. The only direction
  cue is a 0.16/s node-scale pulse, which reads as breathing, not flow.
- THE HEADLINE AND THE RING DISAGREE. "SENSE. PREDICT. DETECT. SUPERVISE." — four. The ring
  shows six: PROCESS, SENSE, PREDICT, DETECT, SUPERVISE, DECIDE. The jury will look for four.
- NODE LABELS ARE ROTATED FLAT (`rotation={[-π/2, 0, 0]}`) and viewed from a 34° elevation, so
  they are heavily foreshortened and their apparent sizes vary by ~3× with depth. PREDICT and
  DETECT are huge; PROCESS and SENSE are small. The size difference implies a hierarchy that
  does not exist.
- The nodes are flat cylinders. They read as poker chips.
- THE GHOSTED PLANT IS OVERWHELMING. In cream mode the receded plant/dryer/granules render as
  large pale shapes filling the lower right — a giant ghost dryer that is the single largest
  object in frame and collides with the DETECT node. It reads as a printing double-exposure.
- A hard horizontal seam appears across the upper third where the editorial fog wash changes
  value. It looks like a bug.
- The caption wraps to two lines with an orphaned "REFERENCE".
- 50 s on ONE step with a 1.8 s reveal ≈ 48 s of dead time. Combined with a bullet list, this is
  the most "static slide pasted into a cinematic presentation" moment in the deck, and it arrives
  immediately after the three densest scenes.
- Progress rail and boundary badge invisible on cream.

Recommended action: SIMPLIFY / REBUILD the ring
Severity: HIGH
```

```text
SCENE 13 — TODAY → NEXT (55 s, 2 beats, editorial)

Purpose:
Solid means built. Outlined means not yet. Closed-loop control does not exist here.

What currently works:
- This scene should not exist in most student decks and its existence is a credit.
- "CLOSED-LOOP CONTROL DOES NOT EXIST IN THIS PROJECT" is exactly right.
- The eleven stages are correctly and honestly classified.

Issues:
- THE LABELS RENDER AT ≈ 8.7 px TALL ON A 1080-LINE OUTPUT. fontSize 0.36 world units; camera
  distance 52.6; FOV 46 → screen height 44.7 world units → 0.36/44.7 × 1080 ≈ 8.7 px, cap height
  ≈ 6 px. Set in light grey on cream. On a projector this content does not exist. This is the
  most important honesty slide in the presentation and it is unreadable.
- LABELS ZIGZAG above/below the rail by index parity with no semantic rule, which makes scanning
  hard and multiplies collisions with the ghosted plant.
- The headline collides with the timeline — "MEANS NOT YET." runs into the first green block.
- THE DESIGN DOC'S CLAIM IS OVERSTATED. Roadmap.jsx's comment says built-vs-not-built is carried
  by "four redundant channels ... material, opacity, line style, and position." Line style is not
  implemented — the outlines are solid EdgesGeometry, not dashed. Three channels, not four.
- The two CONDITIONAL stages (assisted setpoint guidance, closed-loop regulation) are
  differentiated only by opacity (0.34 vs 0.75 line, 0.6 vs 0.85 fill). At 34 % on cream they
  effectively vanish rather than reading as "conditional".
- No time axis, no dates, no direction arrow on the rail.
- TODAY / NEXT headers are pale green and grey on cream — low contrast; NEXT is barely visible.
- The ghosted plant fills the bottom two-thirds. Same problem as scene 12.
- Entire upper third is dead space.

Recommended action: REFINE (type size is the whole fix) — highest value-per-effort in the deck
Severity: CRITICAL
```

```text
SCENE 14 — RETURN (45 s, 3 beats, dark)

Purpose:
Same frame as scene 01. The process never stopped; digitalization made more of it visible.
Then: QUESTIONS.

What currently works:
- The closing rhyme is the strongest structural idea in the film, and beat 14a executes it
  exactly (identical camera pose to scene 01).
- "THE PHYSICAL PROCESS NEVER STOPPED. / Digitalization made more of it visible." is the right
  closing line.
- The dryer has turned continuously for fourteen minutes. That commitment is real and it pays off.

Issues:
- THE RHYME IS THROWN AWAY BY ITS OWN LAST TWO BEATS. 14a matches scene 01 exactly. 14b and 14c
  then creep the camera in — [+4.0, +1.6, −3.0] and [+4.0, +1.2, −2.0], the SAME micro-dolly
  twice — ending at pos [-22, 7.4, 22] / FOV 42 against the opening's [-30, 4.6, 27] / FOV 40.
  By the final frame the composition is a different shot. The deck's best idea is diluted over
  two beats that add nothing.
- "QUESTIONS" IS THE SMALLEST TYPE IN THE DECK. It renders through `.mono` at ~0.88 rem ≈ 14 px,
  teal, floating mid-left with no anchor. This is the last word of the presentation and the frame
  that stays on screen for the entire Q&A. Completely unearned.
- THE CLOSING FRAME SHOWS A FROZEN ANIMATION. sensorReveal is set to 0.4, and SensorNodes stages
  each chip by `clamp((r − i×0.07)/0.5, 0, 1)`. At r = 0.4 that gives chips 0–4 at partial scale
  and opacity and chips 5–6 invisible. The final image of the presentation is a stagger stopped
  40 % of the way through.
- The telemetry chips are unreadable: dark teal on black, skewed, overlapping structure, several
  clipped by the frame edge, with mangled unit strings.
- Granules exiting the discharge hood read as a grey smoke blob; a second stream floats
  unattached in mid-air at handrail height.
- Composition is bottom-heavy and cluttered — five pipes across the top, beams everywhere, drum,
  deck, two handrails. Nothing is quiet. The opposite of a closing frame.
- Identity lockup still at 0.5 opacity and illegible.
- A visible repeating rectangular shadow grid on the floor reads as a checkerboard artifact.

Recommended action: SIMPLIFY (cut 14b or 14c; hold the rhyme) + REBUILD the QUESTIONS card
Severity: HIGH
```

---

# 5. TRANSITION-BY-TRANSITION AUDIT

All 34 transitions share one duration (**2.2 s forward / 1.54 s back**) and one ease
(**`power2.inOut`**). That uniformity is itself the headline finding and is not repeated in every
entry below. `Δpos` = camera position distance, `Δtgt` = look-at distance, `r` = camera-to-target
radius before → after.

### The three signature transitions, in full

```text
04c → 05a   DISTANCE BECOMES TIME
Current: 2.2 s scene tween + straighten & axisDraw 0→1 over 3.2 s, power3.inOut, from +0.2 s.
Δpos 46.4 · Δtgt 55.1 · ΔFOV +8 · r 44→66
Purpose: the material path IS the time axis. The film's central metaphor.
Logically connects the scenes?      YES — architecturally this is the deck's best idea.
Anchor object survives?             YES — granules are never hidden or re-emitted. Correct.
Camera movement makes spatial sense? PARTIALLY — a 46 u lateral leap with a simultaneous FOV
                                     widen and a 22 u radius increase; three changes at once.
Too long?  NO      Too short?  NO
Repeats a previous animation idea?  NO — this is the one genuinely unique move.
Decorative instead of narrative?    NO.
Causes visual confusion?            YES — the flow line is a hairline and the granule stream is a
                                     thin white speckle, so at r = 66 the straightening is barely
                                     perceptible. The idea is right; the render is too faint to
                                     read it. Leftover plant geometry compounds it.
Feels Apple-like?                   PARTIALLY.
Recommended change: hold the camera still for the straighten; thicken the flow line and raise
granule contrast; move the FOV change to a separate beat. Current ~3.2 s → recommend ~2.6 s with
a static camera.
```

```text
09d → 10a   THE CHART BECOMES THE VISUAL
Current: 2.2 s scene tween; evidence → 0.3 (NOT 0); dashAssemble 0 → 0.45 over 1.8 s.
Δpos 44.2 · Δtgt 50.3 · ΔFOV +2 · r 36→20
Purpose: the hold-out figure IS the operator's screen.
Logically connects the scenes?      YES conceptually.
Anchor object survives?             NO. Nothing migrates. The chart fades to 30 % and stays there
                                     as a ghost; the dashboard fades up underneath at 30 %.
Camera movement makes spatial sense? NO — a 43 u vertical translation (+43 in Y) with a
                                     simultaneous mode change from cream editorial to dark
                                     supervision. Two disorienting changes at once.
Too long?  NO      Too short?  YES — 1.8 s is not enough for the audience to relate two charts.
Repeats a previous animation idea?  YES — it is another crossfade.
Decorative instead of narrative?    It is neither; it is an omission.
Causes visual confusion?            YES, severely. Two unrelated charts are simultaneously legible.
Feels Apple-like?                   NO. This is the least Apple-like moment in the film.
Recommended change: REBUILD. Either genuinely morph the chart geometry onto the measured
PBI_TREND_UV rectangle, or abandon the claim and cut cleanly. Do not ship the crossfade with the
"THE SAME CHART" headline over it. Current ~1.8 s → recommend ~3.5 s if morphing.
```

```text
10c → 11a   THROUGH THE PLANE
Current: 2.2 s scene tween; runtimeReveal 0 → 0.45 from +2.2 s over 2.4 s; camera pz/tz −26 with
FOV → 54 from +2.8 s over 3.2 s.
Δpos 9.4 · Δtgt 6.8 · ΔFOV +4 · r 31→28
Purpose: end-to-end integration proved spatially.
Logically connects the scenes?      YES — the best structural idea in the second half.
Anchor object survives?             YES (the dashboard plane).
Camera movement makes spatial sense? PARTIALLY — the beat pose barely moves (9.4 u); the real
                                     move is the relative leg, which fires 0.6 s AFTER the reveal
                                     has already begun.
Too long?  NO      Too short?  NO
Repeats a previous animation idea?  YES — the runtime stack is scene 07's architecture stack again.
Decorative instead of narrative?    NO.
Causes visual confusion?            YES, severely. See scene 11a. Six layers, leftover scene-10
                                     highlight chrome, labels written over dashboard text, and a
                                     measured 677.8 ms stall.
Feels Apple-like?                   NO.
Recommended change: fade the dashboard capture to 0 BEFORE the runtime labels appear; kill
dashHighlight on scene entry; pre-warm the Runtime materials at boot. Reorder so the camera leads
the reveal by ~0.4 s instead of trailing it by 0.6 s.
```

### All 34, compressed

Legend: **Logic** = does it connect the scenes · **Spatial** = does the camera make sense ·
**Repeat** = repeats a prior motion idea · **Apple** = feels like disciplined keynote motion.

| # | Transition | Δpos | Δtgt | ΔFOV | r | Logic | Spatial | Repeat | Decorative | Confusing | Apple | Verdict / recommended change |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 01→02 | 25.8 | 11.1 | −18 | 39→3 | YES | **NO** | NO | NO | **YES** | **NO** | Camera ends *inside* the hero granule; a −18 FOV crush plus a 36 u radius collapse. **Rebuild.** 2.6 s → 2.0 s once the target is a real macro subject. |
| 2 | 02→03 | 60.1 | 41.2 | +28 | 3→55 | YES | **NO** | NO | NO | YES | **NO** | The largest FOV swing in the deck (22→50) in 2.2 s, escaping from inside an object. Reads as a teleport. |
| 3 | 03→04a | 63.2 | 48.2 | −16 | 55→49 | YES | PARTIALLY | NO | NO | NO | PARTIALLY | 62 u of pure +X travel at 28 u/s. Justified (we follow the material) but too fast to read. **2.2 → 3.0 s.** |
| 4 | 04a→04b | 15.3 | 1.1 | +6 | 49→33 | YES | PARTIALLY | NO | NO | NO | PARTIALLY | Dolly-in fights a FOV widen; they partly cancel. Drop the FOV change. |
| 5 | 04b→04c | 13.1 | 13.2 | 0 | 33→44 | YES | YES | NO | NO | NO | YES | Good. Keep. |
| 6 | 04c→05a | 46.4 | 55.1 | +8 | 44→66 | YES | PARTIALLY | NO | NO | YES | PARTIALLY | See signature audit above. |
| 7 | 05a→05b | 4.9 | 6.1 | −4 | 66→62 | YES | PARTIALLY | NO | **YES** | NO | NO | Micro-move that reads as drift. Should instead widen to contain all six markers. |
| 8 | 05b→05c | 35.3 | 10.0 | −2 | 62→31 | YES | YES | NO | NO | NO | **YES** | Sets up the 6.5 s linear travel. Best-motivated approach in the deck. Keep. |
| 9 | 05c→06a | 33.2 | 24.0 | +2 | 31→50 | YES | PARTIALLY | **YES** | NO | NO | PARTIALLY | Pull-back #1 of four. |
| 10 | 06a→06b | 34.4 | 2.2 | +2 | 50→80 | PARTIALLY | PARTIALLY | **YES** | NO | NO | NO | Pull-back #2. Merge with #11. |
| 11 | 06b→06c | 24.2 | 4.1 | 0 | 80→102 | PARTIALLY | **NO** | **YES** | **YES** | NO | NO | Pull-back #3, ending at the deck's farthest pose with the subject sub-pixel. **Cut this beat.** |
| 12 | 06c→07a | 98.5 | 80.2 | −2 | 102→34 | YES | **NO** | NO | NO | **YES** | **NO** | 98.5 u at 45 u/s. A teleport dressed as a move, immediately after three retreats. **2.2 → 3.2 s**, or stage it through an intermediate pose. |
| 13 | 07a→07b | 27.1 | 46.1 | −4 | 34→53 | YES | YES | NO | NO | NO | YES | Good. Keep. |
| 14 | 07b→07c | 28.7 | 10.3 | +2 | 53→41 | YES | YES | NO | NO | NO | YES | Good — the align beat earns its move. Keep. |
| 15 | 07c→08a | 23.2 | 27.1 | +14 | 41→54 | YES | PARTIALLY | NO | NO | NO | PARTIALLY | +14 FOV to 56 is the widest lens in the deck; edge distortion is visible. Cap at 50. |
| 16 | 08a→08b | 44.6 | 35.0 | −12 | 54→34 | YES | PARTIALLY | NO | NO | YES | PARTIALLY | Lands with the subject hard right of centre by construction. Re-aim the target to x ≈ −26. |
| 17 | 08b→08c | 47.2 | 60.2 | −2 | 34→42 | YES | PARTIALLY | NO | NO | NO | PARTIALLY | A 46 u lateral hop between two lanes with nothing between them. Add a connective pass. |
| 18 | 08c→08d | 6.0 | 2.2 | +2 | 42→42 | PARTIALLY | **NO** | NO | **YES** | NO | NO | Effectively a static cut carrying a 6 s trajectory. Merge into 08c as a sub-reveal. |
| 19 | 08d→09a | **100.9** | 89.0 | −4 | 42→40 | YES | **NO** | NO | NO | **YES** | **NO** | The deck's longest jump, simultaneous with the dark→cream mode flip. Two shocks at once. **Hold black for ~0.4 s, or stage the mode change first.** 2.2 → 3.0 s. |
| 20 | 09a→09b | 15.1 | 15.0 | 0 | 40→38 | YES | PARTIALLY | **YES** | NO | NO | **NO** | Vertical scroll #1. |
| 21 | 09b→09c | 19.1 | 19.0 | 0 | 38→40 | YES | PARTIALLY | **YES** | NO | NO | **NO** | Vertical scroll #2 — identical gesture. Also where Candidates hard-pops off. |
| 22 | 09c→09d | 15.5 | 15.0 | −2 | 40→36 | YES | PARTIALLY | **YES** | NO | **YES** | **NO** | Vertical scroll #3, arriving at the duplicated-headline frame. **Rebuild the whole path.** |
| 23 | 09d→10a | 44.2 | 50.3 | +2 | 36→20 | YES | **NO** | **YES** | NO | **YES** | **NO** | See signature audit. |
| 24 | 10a→10b | 11.2 | 2.0 | 0 | 20→31 | YES | YES | NO | NO | NO | PARTIALLY | Acceptable. The dashboard finally reaches full opacity here — that should have happened at 10a. |
| 25 | 10b→10c | **0.0** | **0.0** | **0** | 31→31 | PARTIALLY | **NO** | — | — | **YES** | **NO** | **A literal static cut.** Two full screens swap with zero camera motion. Give it a lateral slide or a page-turn; anything but nothing. |
| 26 | 10c→11a | 9.4 | 6.8 | +4 | 31→28 | YES | PARTIALLY | **YES** | NO | **YES** | **NO** | See signature audit. Measured 677.8 ms stall. |
| 27 | 11a→11b | 26.4 | 36.7 | +2 | 28→58 | YES | YES | NO | NO | YES | PARTIALLY | Move is fine; destination has four occluded labels. |
| 28 | 11b→11c | 23.7 | 32.6 | +6 | 58→67 | YES | YES | NO | NO | NO | YES | Good — the loop-close frame is earned. Keep. |
| 29 | 11c→12 | 56.3 | 55.0 | −8 | 67→39 | YES | PARTIALLY | NO | NO | YES | PARTIALLY | 56 u plus a mode flip to cream. Same double-shock as #19. |
| 30 | 12→13a | 21.8 | 5.4 | −2 | 39→40 | YES | YES | NO | NO | NO | YES | Good. Keep. |
| 31 | 13a→13b | 17.2 | 9.0 | +4 | 40→53 | YES | YES | NO | NO | NO | YES | Good — pulling back to reveal "NEXT" is correct. Keep. |
| 32 | 13b→14a | 43.7 | 12.4 | −6 | 53→39 | **YES** | YES | NO | NO | NO | **YES** | The return. Best narrative transition in the deck. Protect it. |
| 33 | 14a→14b | 5.2 | 1.1 | 0 | 39→35 | PARTIALLY | PARTIALLY | **YES** | **YES** | NO | NO | Micro-creep that breaks the rhyme it just established. **Cut.** |
| 34 | 14b→14c | 4.6 | 1.1 | +2 | 35→31 | PARTIALLY | PARTIALLY | **YES** | **YES** | NO | NO | The identical micro-creep again. **Cut; hold 14a and title QUESTIONS properly.** |

---

# 6. ANIMATION REDUNDANCY MAP

| Repeated pattern | Where | Count | Consistency or predictability? | Classification |
|---|---|---|---|---|
| **2.2 s / `power2.inOut` on every transition** | All 34 | 34 | Predictability. A keynote varies duration by narrative weight; here a 4.6 u micro-creep and a 100.9 u act change take exactly the same time. | **CRITICAL REPETITION** |
| **DOM `.anim` rise (14 px, blur 4→0, 0.7 s, 0.06 s stagger)** | Every text element in every scene | ~150 instances | Genuine consistency — this is the deck's typographic signature and it works. | **GOOD REPETITION** |
| **Vertical camera drop, constant radius, zero ΔFOV** | 09a→09b, 09b→09c, 09c→09d | 3 | Predictability. Reads as page scrolling. | **CRITICAL REPETITION** |
| **Camera pull-back (increasing radius)** | 05c→06a, 06a→06b, 06b→06c | 3 consecutive | Predictability. Four retreats before a 98 u jump. | **DISTRACTING** |
| **Translucent labelled slab stack** | Scene 07 (Architecture, 8 slabs) and scene 11 (Runtime, 5 slabs) | 2 | Predictability. Two related concepts get the same metaphor; the jury cannot separate them. | **DISTRACTING** |
| **Staggered `clamp(drive × n − i)` reveal** | Architecture, Runtime, ValueLoop, Roadmap, SensorNodes, Dashboard highlights | 6 layers | Consistency of *implementation*, but it also means six scenes reveal their content with the identical sweep gesture. | **REDUNDANT** |
| **Continuous sine pulse** | Warm hood light (±8 %), sensor dots (±14 %), anomaly marker (×4 Hz), ValueLoop travelling emphasis | 4 independent | The hood light is justified (the plant breathes). The other three are ambient decoration that never stops and never means anything. | **REDUNDANT** |
| **Wireframe / X-ray reveal** | Scene 04b (`dryerWire` 0→1), scene 07 (`dryerWire` held at 1) | 2 | The second use has no narrative reason — the dryer is receded to 0.55 and the wireframe adds only haze. | **REDUNDANT** |
| **Instanced particle stream along a path** | Granules (2,600), DataPackets (900), DryerInternals bed/air/vapour (1,580), Plant dust (1,800) | 4 systems | Four visually similar particle fields with different meanings and no consistent visual grammar to tell them apart. | **REDUNDANT** |
| **Chart-line draw-on (`instanceCount` progressive)** | Evidence PanelA (1.3 s), TimeAxis PredictTrace (5.2 s) | 2 | Acceptable — same idea, different scenes, both motivated. | **ACCEPTABLE REPETITION** |
| **Crossfade instead of transformation** | 09d→10a (chart→dashboard), 10c→11a (dashboard→runtime) | 2 | Both are the moments that most needed a real transformation. | **CRITICAL REPETITION** |
| **Mode flip simultaneous with a >40 u camera jump** | 08d→09a, 09d→10a, 11c→12 | 3 | Two disorienting changes fired together, three times. | **DISTRACTING** |
| **Identical micro-dolly** | 14a→14b [+4.0,+1.6,−3.0], 14b→14c [+4.0,+1.2,−2.0] | 2 | The same tiny move twice, in the closing beats. | **REDUNDANT** |
| **Continuous drum rotation** | Dryer, all 14 scenes, 14+ minutes | 1 | The deck's best sustained decision. Never stop it. | **GOOD REPETITION** |

---

# 7. ANIMATIONS THAT SHOULD PROBABLY BE REMOVED

```text
Animation:  Ridge model icosahedron rotating at 0.14 rad/s, permanently (Pathways.jsx:79)
Purpose currently served:  None. The code comment says "compact, solid, unmysterious"; a
                           perpetually rotating crystal is the standard "AI black box" trope.
Is it necessary?  NO
Recommendation:  REMOVE

Animation:  Sensor-dot synchronised pulse, dotMat.opacity = p·r·(0.72 + sin(t·1.6)·0.14)
Purpose currently served:  Ambient "aliveness". All seven pulse in unison, which reads as a
                           blinking UI, not as telemetry.
Is it necessary?  NO
Recommendation:  REMOVE (or desynchronise per node and tie the rate to the variable's own value)

Animation:  ValueLoop travelling node-scale pulse (pulse += dt·0.16; ×1.16 emphasis)
Purpose currently served:  It is trying to imply loop direction and fails — in a still it is
                           invisible, and in motion it reads as breathing.
Is it necessary?  NO — but the intent is necessary.
Recommendation:  REPLACE with an actual directional element (a travelling packet, or arrowheads)

Animation:  Anomaly-marker pulse, 1 + sin(t·4)·0.12 (Pathways.jsx)
Purpose currently served:  Marginal — risk is already encoded by colour AND by marker scale
                           (0.9 + risk·0.7). The pulse is a third redundant channel.
Is it necessary?  MAYBE
Recommendation:  REDUCE (keep only while risk > 0.5, which the code already gates at 0.2×)

Animation:  Camera idle drift, ±0.12 u over ~24 s, in every scene including editorial ones
Purpose currently served:  Correct in the industrial scenes — it reads as a held shot.
                           Wrong in 09, 12, 13, where the subject is flat editorial content and
                           the drift makes static type swim.
Is it necessary?  MAYBE
Recommendation:  REDUCE — disable in `editorial` mode

Animation:  Scene 02 StepWord setInterval(1900 ms) auto-advance
Purpose currently served:  It advances three words on a wall clock the presenter does not control.
Is it necessary?  NO
Recommendation:  REPLACE with three presenter-driven beats

Animation:  Wireframe held at dryerWire = 1 through all of scene 07
Purpose currently served:  None — the dryer is at 0.55 presence and the wireframe only adds haze
                           behind the architecture stack.
Is it necessary?  NO
Recommendation:  REMOVE (set dryerWire → 0 on scene 07 entry)

Animation:  Dashboard highlight boxes persisting into scene 11 (dashHighlight held at 1)
Purpose currently served:  None. It is leftover chrome from the previous scene sitting on top of
                           the runtime reveal.
Is it necessary?  NO
Recommendation:  REMOVE (drive dashHighlight → 0 on scene 11 entry)

Animation:  Evidence PanelA instanced-dot matrix rebuild, 165 setMatrixAt + a full
            instanceMatrix upload EVERY FRAME, forever, including scenes 10–14 where the layer
            is invisible
Purpose currently served:  The progressive dot reveal — which completes in 1.3 s and then never
                           changes again.
Is it necessary?  NO (after the draw completes)
Recommendation:  REDUCE — early-return once draw ≥ 1

Animation:  Plant suspended dust, 1,800 points, always on
Purpose currently served:  Intended as atmosphere; renders as white fireflies against pure black.
Is it necessary?  MAYBE
Recommendation:  REDUCE — cut count, lower opacity, and confine to the lower half of the volume
```

---

# 8. OVER-ANIMATED SCENES

**Scene 11 beat a — the worst case.** Simultaneously in motion or newly revealed: the camera
(a 26 u dolly *plus* a FOV widen from 44 to 54), five runtime slabs scaling in, five runtime label
pairs fading in, eight leftover dashboard highlight boxes, the dashboard capture cross-fading, the
granule stream flowing, packets flowing at 0.8 presence, and the DOM copy entering. Nine
simultaneous channels.

*What should remain static:* the dashboard capture (fade it fully to 0 **before** anything else
starts), all eight highlight boxes (kill on entry), the granule stream (0 presence — it has no
business in this scene), and the FOV (do the widen or the dolly, not both).

**Scene 07 beat b.** Camera moving, 8 slabs building over 7 s, 8 label pairs already fully
visible, 900 packets flowing, receded plant and dryer ghosting across the lower left, DOM copy
entering.

*What should remain static:* the plant and dryer (0 presence, not 0.2/0.55), and the labels —
which should arrive **with** their slab, not 7 s early.

**Scene 04 beat b.** Wireframe fading in, shell fading to 18 %, 900 bed particles + 420 air +
260 vapour animating, 12 flights rotating with the drum, the drum rotating, granules flowing, and
the surrounding plant ghosting through the now-transparent shell.

*What should remain static:* the surrounding plant (drop to 0.15 and let fog take it), and the
shell should not go below ~40 % — at 18 % the machine stops reading as steel.

**Scene 08 beat c.** Manifold revealing, support vectors revealing 1.0 s later, trajectory
marker pulsing, tether updating, trail drawing, packets flowing, Ridge model spinning in the
adjacent lane, camera moving 47 u.

*What should remain static:* the Ridge lane (drop `laneFocus` fully; it is currently only reduced
to 0.35), and the Ridge model's rotation.

---

# 9. UNDER-ANIMATED SCENES

**Scene 03 — 60 s, one step.** The only motion is a 16 s station fill. **~44 s of held frame.**
Momentum built by the 63 u approach in transition #3 evaporates completely.
*Meaningful motion that would help (not decoration):* let the camera travel **with** the material
along `chainCurve` at the same constant velocity used in 05c, so the audience physically traverses
the seven stations instead of watching them light up from a fixed vantage. That is the same
motion idea as the gap travel, used earlier and for the same reason — and it would let each
station be framed large enough for its label to be readable.

**Scene 12 — 50 s, one step, 1.8 s reveal.** ~48 s of a static ring plus a bullet list, arriving
immediately after the three densest scenes in the deck. This is where a jury's attention breaks.
*Meaningful motion:* a single packet travelling the loop once, at constant velocity, taking about
8 s — which would simultaneously fix the missing direction cue. Nothing else.

**Scene 01 — 50 s, one step, 4.0 s settle.** ~46 s held. Defensible for an opening (the speaker
is talking) but it is the longest single held frame in the deck after scene 03.
*Meaningful motion:* none needed; instead **shorten to ~35 s**.

**Scene 02 — 35 s.** After the 5.7 s of word cycling, ~27 s of a static grey wall.
*Meaningful motion:* none — this scene needs a subject, not movement.

**Beats 10c and 14b/14c** are under-animated in the strict sense (0.0 u and 4.6–5.2 u of camera
travel) but the fix is structural, not additive: give 10c a real move, and cut 14b/14c entirely.

---

# 10. CAMERA CHOREOGRAPHY ISSUES

Ranked by severity. All figures computed from the 39 declared poses.

| Rank | Issue | Evidence | Severity |
|---|---|---|---|
| 1 | **A zero-motion cut inside a "continuous world"** | 10b→10c: Δpos 0.0, Δtgt 0.0, ΔFOV 0 | **CRITICAL** |
| 2 | **Scene 09 is three identical vertical scrolls** | [0,−15,−2], [0,−19,+2], [0,−15,−4]; r constant 36–40; ΔFOV 0 | **CRITICAL** |
| 3 | **Measured 677.8 ms stall during the signature push** | qa-perf, step 11a, standard mode, fast GPU | **CRITICAL** |
| 4 | **Two ~100 u teleports at ~45 u/s** | 06c→07a (98.5 u), 08d→09a (100.9 u), both in 2.2 s | **HIGH** |
| 5 | **Mode flip fired simultaneously with a large jump, three times** | 08d→09a (dark→cream, 100.9 u), 09d→10a (cream→dark, 44.2 u), 11c→12 (dark→cream, 56.3 u) | **HIGH** |
| 6 | **Four consecutive pull-backs** | r 31→50→80→102 across 05c→06a→06b→06c | **HIGH** |
| 7 | **Camera passes into geometry** | 01→02 ends at distance 3.59 from a hero granule whose circumradius is 3.91 and inradius 3.10 — inside or grazing the solid, with near = 0.5 | **HIGH** |
| 8 | **No lens language; FOV oscillates without motivation** | 22 FOV changes across the run, range 22–56, including a 28° swing (40→22→50) in the first 4.4 s. There is no rule mapping focal length to subject type. | **MEDIUM** |
| 9 | **The closing rhyme is destroyed by two identical micro-creeps** | 14a matches scene 01 exactly; 14b and 14c apply [+4.0,+1.6,−3.0] then [+4.0,+1.2,−2.0] | **MEDIUM** |
| 10 | **Micro-moves that read as drift, not intent** | 05a→05b (4.9 u), 08c→08d (6.0 u), 10c→11a beat pose (9.4 u), 14a→14b (5.2 u), 14b→14c (4.6 u) | **MEDIUM** |
| 11 | **Camera and content animate simultaneously in 6 of 14 scenes** | 04a (26 s drift), 05c (6.5 s travel), 11a (3.2 s push) all run *on top of* content reveals | **MEDIUM** |
| 12 | **Idle drift active during editorial scenes** | ±0.12 u sine applied in modes 09/12/13, making static type swim | **LOW** |
| 13 | **08b lands the subject hard right of centre by construction** | Lane content spans x −33.5…−16.5; camera targets x = −34 | **LOW** |

**Orientation.** The world spans roughly x ∈ [−96, +142] — about 240 units, traversed 34 times.
There is no establishing shot, no map, and no persistent spatial cue. The audience is asked to
believe in one continuous world while being teleported 100 units twice with no connective tissue.
The progress rail is the only orientation aid, and it reports scene number, not location.

---

# 11. SPATIAL LOGIC

**Does the viewer understand where they are?** Partially, and only in Acts I–III. The chain
(x ≈ −96 → −16), the dryer (x = 0), and the time axis (x = 16 → 142) form one legible left-to-right
line, and the straighten move is a genuinely beautiful piece of spatial reasoning.

**Does the digital layer emerge from the physical process logically?** Yes. This is the strongest
spatial claim in the deck: `ARCH_ORIGIN` at (−6, 2, −44) sits *behind and above* the machine, and
packets genuinely travel from real sensor positions on the equipment up into it.

**Does movement through the process correspond to the real story?** Yes for material flow. **No
for the runtime**: the RUNTIME_SLABS staircase is ordered so the camera meets Power BI first and
Replay last, which is the reverse of the data flow the narration describes.

### SPATIAL DISCONTINUITIES

1. **The Pathways region (z ≈ −78) is spatially orphaned.** Lanes sit 78 units behind the world
   origin with no visible connection to the architecture stack at z = −44 other than packets that
   are only visible during the split. Arriving there and leaving there are both teleports.
2. **The evidence wall (x = 72, y +22 → −32) exists nowhere.** It is a 54-unit-tall vertical
   plane of editorial content floating in cream fog, entered by a 100.9 u jump and exited by a
   43 u vertical climb. It has no relationship to the plant, the axis or the dashboard.
3. **The dashboard at (76, 10, 26) is not in a room.** No bezel, no wall, no desk, no operator.
   The scene is titled "AN OPERATOR'S SCREEN" and contains neither.
4. **The runtime staircase runs z = +18 → −38 while the dashboard sits at z = +26**, so the first
   slab (POWER BI, z = 18) is only 8 units behind the dashboard plane. The "push through" therefore
   traverses almost nothing before hitting the first slab — which is why the labels land on top of
   the dashboard rather than behind it.
5. **The value ring floats at (0, 24, 0)** — 24 units directly above the dryer, unconnected. The
   ghosted plant below it reads as a double-exposure, not as "the process continues underneath."
6. **The return in 14a is genuinely earned** — same pose, same light, same machine. This is the
   one spatial payoff that works completely, and beats 14b/14c then discard it.

---

# 12. TRANSITION LENGTHS — RECOMMENDED TIMING

Every transition is currently **2.2 s** (1.54 s reversed). Recommendations:

| Where | Current | Recommend | Why |
|---|---|---|---|
| All micro-beats (05a→05b, 08c→08d, 10a→10b, 14a→14b) | 2.2 s | **1.4–1.6 s** | A 5 u move should not take as long as a 100 u move |
| Standard beat changes within a scene | 2.2 s | **1.8–2.0 s** | Slightly tighter; currently the copy has finished entering 1.5 s before the world settles |
| Act changes (04c→05a, 06c→07a, 08d→09a, 11c→12, 13b→14a) | 2.2 s | **3.0–3.2 s** | 45 u/s is a teleport; ~32 u/s reads as travel |
| 09 vertical drops | 2.2 s | **rebuild, not retime** | Retiming a scroll leaves it a scroll |
| 10b→10c | 2.2 s (0 u) | **1.8 s with real motion** | Anything is better than a static cut |
| 10c→11a push | 3.2 s (from +2.8 s) | **2.6 s, starting at +0.4 s** | Camera should lead the reveal, not trail it by 0.6 s |
| 09d→10a chart→dashboard | 1.8 s | **3.5 s** if morphing, **2.0 s** if cutting cleanly | The audience needs time to relate two charts; 1.8 s is not enough |
| straighten (05a) | 3.2 s | **2.6 s with a static camera** | The camera currently moves 46 u during the deck's most important reveal |
| chainHead fill (03) | 16 s | **10 s** | 16 s of watching lights come on is too long for a 60 s scene |
| archBuild (07b) | 7 s | **5.5 s** | Acceptable but slightly indulgent |
| dashHighlight sweep (10b) | 4.4 s over 8 regions | **6.0 s** | 0.55 s per region is faster than the presenter can name them |
| trajectory (08d) | 6 s | **4.5 s** | |
| gap travel (05c) | 6.5 s | **keep 6.5 s** | This one is meant to be felt. Do not shorten it. |
| DOM `.anim` entrance | 0.7 s + stagger | **keep**, but **add a 0.35 s exit** | The missing exit is the single highest-value motion fix in the deck |

---

# 13. PACING

**Declared runtime: 880 s = 14 min 40 s** across 14 scenes / 39 steps.
**Transition budget: 34 × 2.2 s = 74.8 s (8.5 % of runtime).**

| Act | Scenes | Seconds | % | Classification |
|---|---|---|---|---|
| I — PURPOSE | 01–02 | 85 | 9.7 % | **TOO SLOW** — two single-step scenes, ~73 s of held frame |
| II — INDUSTRY | 03–04 | 135 | 15.3 % | **SLOW** — scene 03 alone holds 60 s on one frame |
| III — THE GAP | 05–06 | 140 | 15.9 % | **BALANCED** — the best-paced act |
| IV — DIGITALIZATION | 07–08 | 150 | 17.0 % | **BALANCED**, trending dense |
| V — EVIDENCE | 09–11 | 220 | 25.0 % | **TOO FAST** for its content density — 11 beats, three of them information-saturated |
| VI — VALUE | 12–14 | 150 | 17.0 % | **TOO SLOW** — scene 12 holds 50 s on a bullet list right after Act V |

### Per-step pacing

| Step | Scene | Held s | Motion within | Classification |
|---|---|---|---|---|
| 01 | Awakening | 50 | 4.0 s settle | **TOO SLOW** — 46 s dead |
| 02 | Material | 35 | 2.6 s + 5.7 s word cycle | **SLOW** — 27 s dead |
| 03 | Chain | 60 | 16 s fill | **TOO SLOW** — 44 s dead, the deck's largest |
| 04a–c | Dryer | 25 each | 26 s drift / 1.1 s / 1.4 s | BALANCED |
| 05a–c | Gap | ~27 each | 3.2 s / 1.8 s / 6.5 s | **BALANCED** — best-paced scene |
| 06a–c | Response | 20 each | 0 / 5.2 s / 0 | FAST (thin) |
| 07a–c | Digital | ~23 each | 1.4 s / 7 s / 3.5 s | BALANCED |
| 08a–d | Pathways | 20 each | 1.6 s / 0 / 1.2 s / 6 s | **TOO FAST** — 20 s per beat for this density |
| 09a–d | Evidence | ~22 each | 1.3 s / 0 / 0 / 0 | **TOO FAST** — 22 s to read a chart, a candidate table, an anomaly panel |
| 10a–c | Supervision | ~21 each | 1.8 s / 4.4 s / 1.0 s | **TOO FAST** — 21 s for a nine-visual dashboard |
| 11a–c | Through | ~21 each | 2.4 s / 2.8 s / 3.2 s | BALANCED |
| 12 | Value | 50 | 1.8 s | **TOO SLOW** — 48 s dead |
| 13a–b | Roadmap | ~27 each | 1.6 s / 3.2 s | BALANCED |
| 14a–c | Return | 15 each | 1.8 s / 0 / 0 | FAST, and the ending needs the opposite |

### Structural pacing problems

1. **A slow opening followed by a slow process act.** Scenes 01–03 total 145 s with ~117 s of held
   frame. The first three minutes of a 14-minute presentation have almost no momentum.
2. **The first model result arrives at t ≈ 510 s (8:30 of 14:40).** Fifty-eight percent of the
   presentation elapses before the jury sees a single metric. For a soutenance, that is late.
3. **Total dead time ≈ 165 s ≈ 19 % of runtime** (scenes 01, 02, 03, 12 held frames).
4. **The density curve is inverted.** The thinnest scenes get the most time (03: 60 s, 12: 50 s,
   01: 50 s) and the densest get the least (09a: 22 s for a 165-point chart; 10b: 21 s for a
   nine-visual dashboard).
5. **Act V is where a jury's attention peaks, and it is the most rushed.**
6. **The final act loses energy at exactly the wrong moment** — a 50 s bullet-list hold in scene 12,
   then three 15 s micro-beats to close.

**Realistic delivered runtime.** The declared 880 s assumes the presenter matches the budget
exactly. With Q&A-style pauses and the 74.8 s of transitions, expect **15–17 minutes** in practice.
Trimming scenes 01, 02, 03 and 12 and cutting beats 06c, 08d, 14b, 14c recovers ~110 s, which
should be redistributed into Act V.

---

# 14. CONTENT REDUNDANCY LIST

| # | Redundancy | Where it appears | Why it is redundant | Strongest version | Action |
|---|---|---|---|---|---|
| 1 | **"Two questions / two models"** | 06c ("TWO QUESTIONS. ONE SUPERVISION SYSTEM."), 08a ("ONE STREAM. TWO MODELS.") | Identical idea, 80 s apart, both as a headline beat | **08a** — it is followed by the actual models | **Cut 06c**; fold its note into 06b |
| 2 | **The system architecture** | Scene 07 (8-slab stack: PROCESS/SENSE/ALIGN/FEATURES/INTELLIGENCE/PERSIST/SUPERVISE/OPERATOR), scene 11b (5-slab stack: POWER BI/SQL/POSTGRESQL/PYTHON/REPLAY) | Both are stacked labelled layers describing the same pipeline at different granularity, 5 scenes apart, with the same visual metaphor | **07** — it is causally motivated (built by packets) | Keep both but **differentiate the metaphor**: 11 should be a *path* the camera travels, not a second stack |
| 3 | **"What this evidence is worth"** | 09d DOM headline **and** 09d world headline — verbatim, same frame | The literal same sentence twice, simultaneously | Either, not both | **Delete the world headline**; keep the five world bullets |
| 4 | **Evidence limits** | 09d DOM note, 09d world bullets 1/2/5, the persistent boundary badge, scene 12 caption, scene 13 caption | The honesty message is stated five distinct ways | The **persistent badge** — it is always on and costs nothing | Shorten the 09d DOM note to one clause; keep the bullets |
| 5 | **"Laboratory remains the reference"** | Boundary badge (5 scenes), 06b caption, 12 caption | Three phrasings of one point | The badge | Cut the 12 caption clause |
| 6 | **"Prototype / replay / 5 s"** | 05 axis label, 10 eyebrow, 10c caption, 11c caption, 13 note, boundary badge | Six statements of the same boundary | The badge + 11c caption | Cut from 10c |
| 7 | **Ridge model selection** | 08b note ("selected on validation RMSE against four alternatives"), 09b entire beat ("THE SIMPLE MODEL WON", five candidates with bars) | 08b announces the result that 09b then proves | **09b** — it has the evidence | Reduce 08b's note to the model spec only |
| 8 | **Anomaly detector is unsupervised** | 08c caption, 08d caption, 09c note, 09c world text (in red, full width), 09d bullet | Five statements | 09c world text | Cut from 08d and 09d |
| 9 | **"Power BI never runs inference"** | 11a DOM note, 11b world text at the foot of the staircase | Same sentence twice in one scene | The DOM note (legible) | Delete the world text |
| 10 | **Residence-time alignment** | 07c beat (with the 24.5 min figure), 06b note ("aligned to the product they describe") | 06b pre-announces 07c's payload | **07c** | Simplify 06b's note |
| 11 | **Production continuity** | 12 list item 4, 14b headline ("FROM PROCESS MONITORING TO INTELLIGENT INDUSTRIAL OPERATION") | Overlapping closing sentiment | 14b | Cut item 4 from scene 12's list (three items is stronger than four) |
| 12 | **OCP identity** | Scene 01 lockup, scene 14 lockup, green steel throughout | This is correct and deliberate | — | **Keep — no change** |

---

# 15. VISUAL REDUNDANCY

Separating the two, because the deck confuses them in places:

### VISUAL CONSISTENCY (working as intended — protect)

- **Copy anchored left, at most five of twelve columns, never in a card, contrast from a gradient
  scrim.** Applied in all 14 scenes. This is the deck's typographic identity and it works.
- **The eyebrow → hero → note → caption hierarchy.** Consistent, well-scaled, correct.
- **The amber boundary badge in a fixed position across all model-result scenes.** Excellent.
- **OCP green (#003C30 / #007830) as structural steel, teal (#2FB6A0) as data, cream (#F5F2E4) as
  editorial.** A clean three-way semantic split, derived from real plant photography.
- **Continuous drum rotation** as the world's heartbeat.
- **The `.anim` rise entrance** as the single text-motion vocabulary.

### VISUAL REPETITION (harming — fix)

| Repetition | Instances | Problem |
|---|---|---|
| **Translucent teal labelled slab** | Architecture (8), Runtime (5) | Two systems, one look. The jury cannot tell them apart. |
| **Green outlined rectangle as an annotation** | Dashboard highlights (8), Roadmap outlines (7), Runtime edge lines (5) | Three unrelated meanings share one visual form: "look here", "not yet built", and "a layer boundary". |
| **Thin white speckled particle line** | Granule stream in 03, 05, 11, 14 | At every camera distance used it reads as dust or noise, never as material. Same failure four times. |
| **Rotated / skewed in-world mono caption in a dark colour** | 05 axis label, 08 top and bottom captions, 11b sub-labels, 14 telemetry chips | Five scenes with the same illegibility failure: mono type, low fill opacity, dark-on-dark, in perspective. |
| **Capsule vessel (cylinder + hemisphere)** | 7 stations in scene 03 | One primitive standing for seven distinct unit operations. |
| **Ghosted receded geometry washing across the frame** | 05a (plant 0.3), 07b (plant 0.2 / dryer 0.55), 12 (plant 0.12 / dryer 0.3), 13 (plant 0.1 / dryer 0.22) | "Receded, not removed" is the right principle, but at these values in cream mode it renders as double-exposure. The presence floor is set too high in four scenes. |
| **Frame-edge cropping of key content** | 03 (station label), 05 (axis label, 2 markers), 10a (dashboard right + bottom), 11a (dashboard both edges), 14 (telemetry) | Five scenes where the composition does not fit the 16:9 safe area. |
| **Constant-radius, zero-FOV camera framing** | 09a–09d (r 36–40 throughout) | Four consecutive shots with identical framing. |

---

# 16. AMBIGUITIES / POTENTIAL JURY CONFUSION

| Topic | Is it obvious? | Where the ambiguity lives | Severity |
|---|---|---|---|
| **Real vs synthetic data** | **Mostly yes — this is handled well.** The boundary badge says SYNTHETIC DATA on five scenes and 09d states it explicitly. | But scenes 01–07 carry no such marker, and 08c's note says "**2,400 real training states**" and "the model's **own** support vectors". "Real" here means "real model artifacts from synthetic data" — a jury will hear "real plant data". | **HIGH** |
| **Training vs prototype replay** | Partially | 05's axis label ("PROTOTYPE REPLAY") is rendered at 0.55 fill opacity in #6E8A80 on near-black, skewed, and clipped by the frame edge — i.e. invisible. The disclaimer exists and cannot be read. | **HIGH** |
| **5-second replay ≠ physical sampling** | **No.** | The eyebrow "~5 S PAGE REFRESH", the caption "PROTOTYPE REPLAY Δt = 5 s", and the phrase "recorded on the prototype 5-second grid" all use "5 s" for three different things: the dashboard refresh, the replay tick, and the historian grid. Nothing states that no physical instrument sampled at 5 s. | **HIGH** |
| **Soft sensor vs physical sensor** | Partially | Scene 07's SensorNodes render seven glowing dots **attached to points on the physical equipment**, which correctly implies real instruments. But the moisture output chip is rendered in the same visual language, labelled `%H2O — LABORATORY ONLY`. A jury scanning the frame sees eight identical telemetry chips, one of which is not measured at all. The distinction is carried only by a text label. | **HIGH** |
| **Anomaly detection ≠ automatic correction** | **Yes — well handled.** | "NO CONTROL ACTION IS TAKEN", "ADVISORY", "Operator remains the decision-maker", "Evidence, not proven causality". Best-defended boundary in the deck. | LOW |
| **Power BI is genuine project output** | **Yes** — the real PBIP export is used, unmodified. | Undermined by presenting it at 30 % opacity, cropped, and in its null state. The jury may conclude it is a mock-up precisely *because* it looks degraded. | **MEDIUM** |
| **AI as decision support vs autonomous operation** | **Yes.** | Consistently and correctly framed. | LOW |
| **Future vs implemented** | **Yes in principle, no in practice.** | Scene 13 is exactly the right scene and its labels render at ~9 px. The distinction is made in content the audience cannot read. | **CRITICAL** |
| **Lab moisture ~2 h interval** | Partially | "LAB Δt ≈ 2 H" and "Two hours apart" are clear. But "SIX RESULTS." is said over a frame containing four. And the 0.0054 % H₂O movement claim cannot be located in the visual. | **HIGH** |
| **ν = 0.02** | **No.** | World text renders one way; the DOM caption renders `N = 0.02` because `text-transform: uppercase` maps Greek ν to Ν. A jury reads it as a sample size. Same for Ridge: world `alpha = 10`, DOM `α = 10`. | **HIGH** |
| **`% H20`** | **No.** | The font-fold replaces the subscript with a glyph that reads as zero. Appears in Evidence Panel A (×3), SensorNodes, and Pathways. | **MEDIUM** |
| **Units without symbols** | No | `m3/h`, `C` (for °C), `mmH2O`. Temperature without a degree sign in an engineering presentation. | **MEDIUM** |
| **Support vectors** | **No.** | The claim that 136 brighter points define the learned boundary is not visually verifiable — additive blending over 2,400 points defeats it. | **HIGH** |
| **Three date universes** | No | Hold-out 2026-07-03→07-16; dashboard "Last event 2026-08-06"; "ingested 2026-08-14". Unreconciled on screen. | **MEDIUM** |
| **Mother-liquor recycle** | **No.** | Stated in copy, drawn as an undirected hairline with no arrow, no label, no visible endpoint. | **MEDIUM** |
| **The "quality plane"** | **No.** | A 126 × 10.8 teal plane at 4.5 % opacity with a hard edge and no label. Reads as a render artifact. | **LOW** |
| **Runtime flow direction** | **No.** | Camera meets POWER BI first, REPLAY last; the narration runs the other way; no arrows. | **MEDIUM** |
| **Loop direction (scene 12)** | **No.** | Six nodes, a hairline ring, no arrowheads. | **MEDIUM** |

---

# 17. VISUAL OVERCLAIM RISKS

Places where the *animation* claims more than the *evidence* supports, independent of the text:

| # | Overclaim | Mechanism | Risk |
|---|---|---|---|
| 1 | **"THE SAME CHART"** | The hold-out chart and the Power BI trend are visibly different charts crossfading. The headline asserts an identity the image contradicts. A jury that notices will question every other equivalence claim in the deck. | **CRITICAL** |
| 2 | **The dashboard implies live operation** | It is a static PNG of a report whose own pills read `DATA · STALE` and `ingested 8525 min ago`, presented under a `~5 S PAGE REFRESH` eyebrow with a "5 s" heading. The animation (highlight sweep, page turn) implies interaction with a running system. | **CRITICAL** |
| 3 | **"2,400 real training states"** | "Real" modifies the *model artifacts*, not the data provenance. Rendering them as a physical-looking point cloud reinforces the wrong reading. | **HIGH** |
| 4 | **Sensor chips imply instrumentation that may not exist** | Seven glowing nodes are attached to specific points on the equipment with leader lines, asserting measurement locations. The report explicitly refuses PCS7 tag and equipment-identity mapping — but the visual asserts a mapping anyway. | **HIGH** |
| 5 | **The physics animation implies validated transfer modelling** | Flights, a cascading bed, counter-current air and vapour transport are all animated. The "SCHEMATIC — NOT A CFD RESULT" caption is present and correct — but the caption is one line of amber text against a full-screen simulation. | **MEDIUM** |
| 6 | **The loop closing implies feedback to the process** | Scene 11c animates packets travelling from the replay slab **back into the dryer**. Combined with the ring in scene 12 (PROCESS → … → DECIDE → PROCESS), the visual grammar is a closed loop. Scene 13 then says closed-loop control does not exist. **The animation contradicts the disclaimer two scenes later.** The `loopClose` packets should visibly terminate at the *operator*, not at the machine. | **HIGH** |
| 7 | **The architecture stack implies deployment** | Eight labelled layers from PROCESS to OPERATOR, built, solid, glowing. Nothing in the visual distinguishes "runs on a laptop against replay data" from "deployed". | **MEDIUM** |
| 8 | **`0.80 %` vs `0.0801`** | The dashboard reports moisture as `0.80 %` while scene 09's chart axis reads `0.0801`. Same quantity, two scales, adjacent scenes, unexplained. A jury may read a 100× discrepancy. | **HIGH** |
| 9 | **Panel A has no x-axis** | A chart with no time axis invites the reading that the points are ordered arbitrarily rather than chronologically — which would invalidate the hold-out claim the scene is making. | **MEDIUM** |
| 10 | **The roadmap's unreadable labels** | If the jury cannot read which stages are outlined, the presentation is *visually* asserting a complete pipeline. The honesty is in text at 9 px. | **CRITICAL** |

---

# 18. PERFORMANCE

**Measured for this audit** — `node scripts/qa-perf.mjs --hold 2000`, headful Chrome, real GPU,
1920×1080, standard mode, all 35 steps, sampled on the settled state of each.

```
MODE            STANDARD
mean across all 230.8 fps
slowest scene   11.3 at 83.6 fps
worst frame     677.8 ms in scene 11.1
scenes < 50 fps none
scenes < 30 fps none
```

| Metric | Value |
|---|---|
| Mean FPS across all 35 steps | **230.8** |
| Worst sustained scene | **11c — 83.6 fps** (p95 16.7 ms) |
| Second worst | **14c — 94.7 fps** (p95 16.8 ms, worst 30.7 ms) |
| Third worst | **12 — 113.5 fps** (p95 11.5 ms) |
| Best | 09a–09d, 10a–10b — **~360 fps** (measurement ceiling) |
| **Worst single frame** | **677.8 ms, step 11a** |
| Second worst single frame | 30.7 ms, step 14c |
| Third worst single frame | 19.3 ms, step 14b |

### Interpretation

- **On this machine there is no frame-rate problem.** Nothing drops below 50 fps and the mean is
  ~4× a 60 Hz target. Headroom is enormous.
- **The 677.8 ms stall is the real finding.** It is a 0.68 s hard freeze on the deck's signature
  camera move, and it is a *first-use* cost, not a steady-state cost — the Runtime layer's five
  `MeshStandardMaterial`s (emissive + double-sided) and its `EdgesGeometry` `LineBasicMaterial`
  are never rendered before scene 11, because `group.visible = presence > 0.01` keeps them out of
  the render list. `BootGate` waits two `requestAnimationFrame`s before revealing the show, which
  compiles only what scene 01 draws. On a projector laptop with an integrated GPU, expect
  **1.5–3 s**.
- **The relative cost profile is the useful signal.** Scene 11c is **4.3× the cost** of the
  evidence act on identical hardware. Scenes 11a–c, 12, 14a–c form a heavy cluster (83–142 fps).
  Scaled to a machine ~6× slower, those land at **14–24 fps**.
- **The CPU is the bottleneck, not the GPU.** Per frame, the app rebuilds: 2,600 granule matrices
  (each calling `flowPath`, which evaluates a `CatmullRomCurve3`), 900 packet matrices (each with
  a `lookAt`), 1,580 dryer-internal point positions, and — permanently, even when invisible — 165
  Evidence dot matrices with a full `instanceMatrix` upload. That is ~5,200 CPU-side instance
  updates per frame, sustained for 14 minutes.

### Assets and loading

| Item | Size | Note |
|---|---|---|
| `dist/` total | 4.3 MB | Comfortable |
| `three-*.js` | 704 KB | |
| `r3f-*.js` | 492 KB | |
| `index-*.js` | 160 KB | |
| `dist/img/` | 1.3 MB | **787 KB of it is four plant photographs referenced nowhere in the source** |
| `dist/data/` | 508 KB | Seven verified JSON payloads |
| `dist/fonts/` | 156 KB | Locally bundled; no CDN. Correct. |
| Power BI captures | 1600 × 900 each | Their body text renders at ~6–7 px on a 1080-line output |

### Console / correctness observations

- No console errors or WebGL warnings surfaced during the 35-step run.
- Offline safety is genuinely well engineered: `WorldText.jsx` closes both drei-Roboto and
  troika/`unicode-font-resolver` CDN paths, and every string is folded to the bundled Latin
  subsets. Verified by the existence of `exports/offline_check/`.
- `gsap.ticker.lagSmoothing(0)` is the correct call for a presentation — a hitch skips frames
  instead of stretching a 2.2 s transition to 20 s. Good.

### Dead code confirmed by grep (all exported, none referenced)

`makeFpsWatch`, `killChannels`, `setChannels`, `allChannelKeys`, `poseChannel`, `sceneTitle`,
`stepIndexOf`, `fmtMoisture`, `fmtNum`, `fmtClock`, `useShow.ready` / `setReady`,
`useShow.transitioning` (set by the Rig, read by nobody), the `.boot.is-ready` CSS hook,
and `Frame`'s unused `y1` parameter in `Evidence.jsx`.

---

# 19. LIVE SOUTENANCE RISKS

Imagining an unfamiliar projector, a laptop under load, fullscreen, and nervous manual navigation.

### CRITICAL

1. **The auto-degrade path does not exist.** `makeFpsWatch` is written, exported, documented — and
   never called. The only protection is `probeDevice()`, which requires **cores ≤ 4 AND memory ≤ 4 GB**
   at boot. A typical 8-core / 16 GB laptop with a weak integrated GPU, or a thermally throttled
   machine, will never enter safe mode no matter how badly it performs. The presenter must notice
   and press `S` mid-presentation.
2. **The 677.8 ms stall at step 11a**, in the middle of the signature move, with no recovery path.
   On weaker hardware this becomes a multi-second freeze that will read to the room as a crash.

### HIGH

3. **Number-key jumps produce a half-dressed world.** `goScene(i)` sets `step` and lets the Rig
   apply that scene's `layers` (complete, via the `L()` spread) — but the *animation channels* are
   only partially reset per scene. Jumping to scene 11 from scene 01 gives `dashboard: 0.35` and
   `dashAssemble: 1` (fine) alongside `sensorReveal: 0`, `packetFlow: 0`, `straighten: 0` — i.e.
   sensor nodes present but unrevealed, packets frozen, granules on the curved path in a scene
   that assumes the straightened one. **Number keys are the panic-recovery path, and they are the
   least tested.**
4. **Scene 02's `setInterval` word cycle cannot be paused, reversed or re-triggered.** Stepping
   back into scene 02 restarts it from word 1 on a fresh 1.9 s clock, unrelated to the speaker.
5. **Click-anywhere advances the show.** `window.addEventListener('click', …)` fires on any click
   outside `.hud`, `.help`, `.boot` — including an accidental trackpad tap, a click to focus the
   window, or a click to dismiss a notification. There is no confirmation and no undo other than
   `←`. In a nervous live setting this will cost a beat at least once.
6. **Projector legibility.** Scene 13's roadmap at ~9 px, scene 04b at 8–15 % luminance, the
   mint-on-cream trace at ~1.6:1 contrast, and every dark in-world caption. None of this was
   validated against a projector's gamma and ambient-light penalty.
7. **The dashboard says STALE.** The most likely jury question in the entire defence, arriving at
   the presentation's climax, with no prepared on-screen answer.

### MEDIUM

8. **No fullscreen enforcement.** `F` toggles it, and the boot hint mentions it, but nothing
   detects that the show is running windowed. `--safe: 6vmin` and all `clamp()` type scale to the
   viewport, so a windowed run silently shrinks everything.
9. **Browser focus.** All navigation is `window` `keydown`. Clicking outside the page (a second
   monitor, presenter notes in another app) drops focus and the arrow keys stop working, with no
   on-screen indication of why.
10. **Recovery messaging is thin.** The `webglcontextlost` handler shows "Graphics context lost.
    Restoring…" — but nothing re-applies the current step's pose or channels after restore.
    `poseChannel()` was written for exactly this and is never called.
11. **The presenter HUD is a toggle with no default.** If `P` is not pressed the presenter has no
    clock, no beat counter and no cues. If it *is* pressed and a mirrored display is in use, the
    audience sees the cue deck.
12. **No transition interrupt guard.** The 120 ms `advance` throttle prevents desync, but a
    presenter who presses `→` mid-transition kills the timeline and starts the next from wherever
    the tween happened to be. Kills are handled correctly, but the resulting pose is arbitrary.

### LOW

13. `Shift+1–4` for scenes 11–14 depends on a US-layout `!@#$` mapping. On an AZERTY keyboard —
    plausible in Morocco — those characters are unshifted and the mapping breaks entirely.
14. 787 KB of unused plant photographs in the bundle.
15. The `.rail` and `.boundary` are invisible in editorial mode (scenes 09, 12, 13).

---

# 20. TOP 10 ISSUES TO FIX BEFORE THE SOUTENANCE

### #1 — The Power BI act presents the project's deliverable at its worst
**Severity:** Critical
**Why it matters:** This is the climax of the argument and the one artifact the jury can evaluate
directly. It is currently introduced at 30 % opacity, cropped on the right and bottom, captured in
its null state (NORMAL / no anomaly / no cause list), and it announces `DATA · STALE` and
`ingested 8525 min ago` directly beneath a `~5 S PAGE REFRESH` eyebrow. The `0.80 %` on the
dashboard also sits 100× away from the `0.0801` on the previous scene's axis, unexplained.
**Where:** Scene 10 all beats, scene 11a; `Dashboard.jsx` opacity ramp; `public/img/powerbi_*.png`
**Recommended fix:** Re-capture both pages from a **running** replay with an active anomaly and
fresh timestamps. Bring the capture to full opacity at 10a, not 30 %. Reframe both scenes so
nothing is cropped. Add one line reconciling `0.80 %` with `0.0801`.

### #2 — "THE SAME CHART" is a crossfade, and the two charts visibly differ
**Severity:** Critical
**Why it matters:** The film's central conceit is asserted over an image that contradicts it, while
the previous scene's chart remains legible on top. If the jury notices, every other equivalence
claim becomes suspect.
**Where:** Transition 09d→10a; `transitions.js` case `supervision`; `evidence: 0.3` should be 0
**Recommended fix:** Either genuinely morph the hold-out geometry onto the measured
`PBI_TREND_UV` rectangle over ~3.5 s, or cut the claim and cut cleanly. Drive `evidence` to 0
either way.

### #3 — Scene 13's honesty labels render at ~9 px
**Severity:** Critical
**Why it matters:** The single most important slide for academic integrity is unreadable on a
projector. If the jury cannot read which stages are outlined, the deck is visually claiming a
complete pipeline.
**Where:** `Roadmap.jsx` `fontSize={0.36}`; scene 13 camera at 52.6 u / FOV 46
**Recommended fix:** Raise to ≥ 0.9 world units (≈ 22 px) and pull the camera in, or split the
eleven stages across the two beats so each half can be framed larger. Highest value-per-effort
change in the entire deck.

### #4 — The DOM overlay and the world are desynchronised on all 34 transitions
**Severity:** Critical
**Why it matters:** There is no exit animation. New copy is fully legible over the old world for
~1.5 s, every single time. This is what most separates the deck from Apple-level discipline, and
it happens 34 times.
**Where:** `Overlay.jsx` `key={sceneIndex:beat.id}`; `styles.css` `.anim` (entrance only);
`useShow.transitioning` is set and never read
**Recommended fix:** Add a 0.35 s exit (`opacity → 0`, `y → −8 px`, `blur → 3 px`), delay the new
copy's entrance to `transitionDuration × 0.45`, and connect the existing `transitioning` flag.

### #5 — Scene 11a is unreadable, and it stalls for 677 ms
**Severity:** Critical
**Why it matters:** Six layers stacked at once — the cropped dashboard, five translucent slabs,
five labels over the dashboard's own text, eight leftover scene-10 highlight boxes, the granule
stream and the DOM copy — plus a measured hard freeze on a fast machine.
**Where:** Scene 11 `push` beat; `transitions.js` case `through`; `Dashboard.jsx` highlight gating
**Recommended fix:** Drive `dashHighlight → 0` and `dashboard → 0` on scene-11 entry; delay
`runtimeReveal` until the camera push is 40 % complete; pre-warm the Runtime materials during
`BootGate` by rendering them once off-screen.

### #6 — Scene 09 is a vertical scroll
**Severity:** High
**Why it matters:** Three identical downward camera drops at constant radius and zero FOV change,
in the act where credibility is established. It is the clearest "this is a website, not a keynote"
moment in the deck. Compounded by 09d printing its own headline twice and by PanelA/PanelB never
turning off.
**Where:** Scene 09 beat cameras; `Evidence.jsx` `useFade(..., to = 99)`
**Recommended fix:** Give each evidence beat a distinct spatial relationship (approach for the
chart, lateral for the candidates, orbit for the anomaly panel, pull back for the limits). Gate
PanelA and PanelB to their own beats. Delete the duplicated world headline in 09d.

### #7 — There is no auto-degrade, and the heavy scenes are the closing ones
**Severity:** High
**Why it matters:** `makeFpsWatch` is written and never called. The only degrade trigger requires
≤ 4 cores **and** ≤ 4 GB at boot. Scenes 11c / 14c / 12 are 3–4× the cost of the evidence act and
would land at 14–24 fps on a machine ~6× slower than the test rig.
**Where:** `perf.js`; `App.jsx` boot
**Recommended fix:** Wire `makeFpsWatch` into the render loop with `setSafe(true)` as its callback.
Test the whole deck once in safe mode on the actual presentation laptop.

### #8 — Scene 02 has no subject, and its words run on a timer
**Severity:** High
**Why it matters:** The hero granule never appears (the camera ends inside its geometry); the frame
is a featureless grey wall; the granules that are visible read as low-poly confetti; and three
words auto-advance on a 1.9 s `setInterval` the presenter cannot control. Meanwhile the real site
photograph the note refers to is shipped in the bundle and unused.
**Where:** Scene 02; `Granules.jsx` hero branch; `Overlay.jsx` `StepWord`
**Recommended fix:** Either place the camera at a real macro distance from a properly subdivided
granule with the plant defocused behind it, or replace the scene with the actual
`soluble_map_storage.jpg`. Convert the three words into three presenter-driven beats.

### #9 — Symbols and units are rendered wrongly, in two different ways per frame
**Severity:** High
**Why it matters:** `.caption { text-transform: uppercase }` maps Greek ν → Ν, so the DOM reads
`N = 0.02` while the world label reads it differently in the same frame. Ridge shows `alpha = 10`
in-world and `α = 10` in DOM. `% H20` appears five times. Temperature is written `C`, flow `m3/h`.
An engineering jury notices all of it.
**Where:** `styles.css` `.caption`; `WorldText.jsx` `FOLD`; `SensorNodes.jsx` `NODES` units
**Recommended fix:** Remove `text-transform` from `.caption` and uppercase the strings at source.
Extend the bundled font subset to cover ν, α, ², ³, ° or spell them out consistently in **both**
DOM and world.

### #10 — The pacing is inverted: 19 % dead time up front, the densest act rushed
**Severity:** High
**Why it matters:** Scenes 01, 02, 03 and 12 hold ~165 s of near-static frame. The first model
result arrives at 8:30 of 14:40. Meanwhile 09a gets 22 s for a 165-point chart and 10b gets 21 s
for a nine-visual dashboard.
**Where:** `scenes.js` `seconds` fields; scene 03's 60 s; scene 12's 50 s
**Recommended fix:** Cut scene 03 to ~40 s (and travel with the material), scene 12 to ~30 s,
scene 01 to ~35 s. Delete beats 06c, 08d, 14b, 14c. Redistribute the recovered ~110 s into
scenes 09 and 10.

---

# 21. TOP REDUNDANT ELEMENTS / ANIMATIONS

1. **The uniform 2.2 s / `power2.inOut` transition** — 34 identical instances. **Consolidate into
   three tiers:** micro-beat 1.5 s, beat 1.9 s, act change 3.0 s.
2. **The translucent labelled slab stack** — scene 07 and scene 11b. **Consolidate:** keep the
   stack in 07; make 11 a path the camera travels through, not a second stack.
3. **The vertical camera drop** — three identical instances in scene 09. **Consolidate into one
   varied path.**
4. **The camera pull-back** — four consecutive (05c→06a→06b→06c). **Consolidate:** cut 06c, merge
   06a and 06b.
5. **"Two questions / two models"** — scenes 06c and 08a. **Consolidate into 08a.**
6. **The evidence-limits statement** — five separate expressions (09d DOM note, 09d world bullets,
   the persistent badge, scene 12 caption, scene 13 caption). **Consolidate: the badge plus the
   09d bullets. Cut the rest.**
7. **The four continuous sine pulses** — hood light, sensor dots, anomaly marker, ring travelling
   emphasis. **Consolidate to one** (the hood light, which is motivated).
8. **The four particle systems** — granules, packets, dryer internals, plant dust. **Consolidate
   the visual grammar** so material, signal and atmosphere are distinguishable at a glance.
9. **The green outlined rectangle** — dashboard highlights, roadmap outlines, runtime edges. Three
   unrelated meanings, one form. **Give each its own treatment.**
10. **The rotated, dark, in-world mono caption** — five scenes, same illegibility failure.
    **Consolidate: move all of them to the DOM overlay**, which already has the full font subset,
    proper contrast and a scrim.
11. **"Prototype / replay / 5 s"** — six statements. **Keep the badge and the 11c caption.**
12. **The identical closing micro-dolly** — 14a→14b and 14b→14c. **Cut both.**

---

# 22. WHAT SHOULD BE REMOVED OR SIMPLIFIED

**Remove outright**

- Beat **06c** ("TWO QUESTIONS. ONE SUPERVISION SYSTEM.") — restated 80 s later by 08a, and it
  parks the camera at the deck's farthest pose.
- Beats **14b** and **14c** — two identical micro-creeps that destroy the scene-01 rhyme
  established 4 s earlier. Hold 14a and title QUESTIONS properly there.
- Beat **08d** ("LEAVING THE REGION") — 6.0 u of camera. Fold the trajectory into 08c.
- The **duplicated world headline** in 09d.
- The **world text** "POWER BI NEVER LOADS A MODEL AND NEVER RUNS INFERENCE" in 11b — the same
  sentence is already the DOM note in 11a.
- The **Ridge model's permanent rotation**.
- The **synchronised sensor-dot pulse**.
- The **wireframe** in scene 07 (`dryerWire` should go to 0, not stay at 1).
- The **dashboard highlight boxes** in scene 11 (leftover chrome).
- The **"quality plane"** in scene 05, or give it a label.
- 787 KB of **unused plant photographs** — or better, actually use `soluble_map_storage.jpg` in
  scene 02, where the copy already refers to it.
- All **dead exports**: `makeFpsWatch` should be *wired*, not deleted; the rest
  (`killChannels`, `setChannels`, `allChannelKeys`, `poseChannel`, `sceneTitle`, `stepIndexOf`,
  `fmtMoisture`, `fmtNum`, `fmtClock`, `ready`/`setReady`, `.boot.is-ready`) should go.

**Simplify**

- **Scene 03**: 60 s → ~40 s. Seven identical capsules → three differentiated silhouettes plus
  four receded. Travel with the material instead of holding.
- **Scene 12**: 50 s → ~30 s; four list items → three; six ring nodes → four matching the headline,
  with a real direction cue.
- **Scene 01**: 50 s → ~35 s. Remove two of the four overhead pipes. Cut dust count by half.
- **Scene 09d**: remove ~30 % of the visible elements — the duplicated headline, the duplicated
  note, and PanelB's residue.
- **Scene 07b**: labels should arrive with their slabs, not 7 s early; drop plant/dryer presence
  to ≤ 0.1.
- **Scene 11b**: five slabs whose labels do not occlude each other, and a visible flow direction.
- **The ghosted plant in cream mode** (scenes 12, 13): presence 0.12/0.3 → ~0.04, or cut entirely.
- **Panel A's y-ticks**: round numbers instead of 15/50/85 % of range.

**The 30 % test, scene by scene** — where removing ~30 % of visible elements improves the frame:
scene 01 (overhead pipes, dust), scene 03 (four of seven vessels, the right-hand tangle),
scene 07b (plant ghost, premature labels), scene 09d (duplicated headline and note, PanelB residue),
scene 11a (dashboard, highlight boxes, granules — remove all three), scene 12 (ghost plant, two ring
nodes, one list item), scene 13 (ghost plant), scene 14c (two overhead pipes, the frozen sensor
chips, the floating granule stream).

---

# 23. WHAT IS ALREADY EXCELLENT — DO NOT OVERWORK

**Strongest scene: 04 — ENTER THE DRYER.** The MACHINE → PHYSICS → DATA structure is the
best-designed sequence in the film. Fix the legibility of 04b; do not restructure it.

**Strongest transition: 13b → 14a — THE RETURN.** A 43.7 u move that lands on the exact opening
pose, same light, same machine, with the data layer now readable. This is the deck's best
storytelling moment and it needs nothing except for beats 14b/14c to stop undermining it.

**Strongest 3D asset: the rotary dryer.** Riding rings, 96 instanced girth-gear teeth, trunnion
rollers with bearing housings, plinths, feed chute, discharge hood, exhaust duct, counter-current
supply. Proportions traced to the real photograph. It is credible and it carries the whole film.

**Strongest motion sequence: the 05c travel.** 6.5 s of constant velocity, no easing, the only
linear move in the film, reserved for the one thing the audience is meant to *feel* rather than
admire. The speaker cue even says "Let the travel play. Do not talk over it." That is correct
direction. Do not shorten it.

**Runner-up motion: the 07c alignPause.** One packet holding inside the ALIGN layer for 24.5
minutes of replay while the others dim — making causality visible rather than asserted. The most
sophisticated single idea in the deck. It needs to be *more* visible, not different.

**Strongest chart: Evidence Panel A (scene 09a).** Legible, correctly hierarchised, three metrics
and only three, editorial mode used properly. Add an x-axis and darken the prediction line; change
nothing else.

**Strongest narrative moment: scene 06a.** "How do we see between measurements? — Not by sampling
more often. By inferring from what is already measured continuously." That is the whole thesis in
two sentences and it is perfectly placed.

**Also protect:**
- The **persistent boundary badge** and the entire honesty contract. Non-negotiable.
- **`flowPath(t, straighten)`** as a single shared function. Architecturally correct.
- The **persistent world** — nothing unmounted, presence not membership.
- **One GSAP timeline, no stray `setTimeout`** anywhere in the app.
- **`gsap.ticker.lagSmoothing(0)`** — exactly right for a live presentation.
- The **offline hardening** in `WorldText.jsx` (both CDN escape hatches closed, verified by a
  blocked-network capture).
- The **OCP green structural steel** derived from real plant photography.
- The **cream editorial mode** as a chapter break.
- The **error boundary** and the WebGL context-loss handler.
- The **speaker cue deck** in `Chrome.jsx` — three to five cues per scene, including "Say
  'schematic, not CFD'" and "State the limits yourself before the jury does."

---

# 24. PRIORITIZED FIX PLAN

## MUST FIX BEFORE PRESENTATION

| # | Fix | Why | Effort |
|---|---|---|---|
| 1 | **Re-capture the Power BI pages** from a running replay with an active anomaly and fresh timestamps; remove the `STALE` state | The `DATA · STALE` / `~5 S PAGE REFRESH` contradiction is the most likely and most damaging jury question | M |
| 2 | **Raise scene 13's roadmap labels to ≥ 0.9 world units** | The honesty slide is currently unreadable on a projector | S |
| 3 | **Add a DOM copy exit animation** and delay the entrance to 45 % of the transition | Removes the double-exposure from all 34 transitions in one change | S |
| 4 | **Bring the dashboard to full opacity at 10a**, and drive `evidence → 0` on scene-10 entry | The deliverable is currently introduced at 30 % under a ghost chart | S |
| 5 | **Kill `dashHighlight` and `dashboard` on scene-11 entry**; delay `runtimeReveal` behind the camera push | Makes 11a legible | S |
| 6 | **Pre-warm the Runtime materials at boot** | Eliminates the measured 677.8 ms stall on the signature move | S |
| 7 | **Wire `makeFpsWatch` to `setSafe(true)`** and rehearse the whole deck once in safe mode on the actual laptop | The documented degrade path does not exist | S |
| 8 | **Reframe 05b so all six lab markers are in shot** | "SIX RESULTS." currently shows four | S |
| 9 | **Fix the ν → N and α/alpha divergence**; remove `text-transform` from `.caption`; fix `% H20`, `C`, `m3/h` | Engineering-credibility papercuts a jury will catch | S |
| 10 | **Delete the duplicated headline and note in 09d**; gate PanelA/PanelB to their own beats | The most obviously embarrassing frame | S |
| 11 | **Delete beats 06c, 08d, 14b, 14c** | Removes four redundant transitions and restores the closing rhyme | S |
| 12 | **Give beat 10c a real camera move** | Removes the deck's only literal static cut | S |
| 13 | **Raise scene 04b's exposure and enlarge the bed/air particles** | The physics claim currently has no readable visual support, and the frame is near-black | M |
| 14 | **Set QUESTIONS in the hero type scale** with the identity lockup at full opacity | This frame is on screen for the entire Q&A | S |
| 15 | **Make `loopClose` packets terminate at the operator, not at the dryer** | The animation currently contradicts scene 13's closed-loop disclaimer | S |

## SHOULD FIX

| # | Fix | Why |
|---|---|---|
| 16 | Three transition duration tiers (1.5 / 1.9 / 3.0 s) instead of a uniform 2.2 s | The single largest contributor to the "templated" feeling |
| 17 | Rebuild scene 09's camera path with four distinct spatial relationships | Removes the scroll |
| 18 | Rebuild scene 02 around a real subject (macro granule or the site photograph); convert the word cycle to presenter beats | Weakest scene; also removes the only uncontrollable timer |
| 19 | Gate scene 07's slab labels per-slab | Restores the label→slab mapping |
| 20 | Reposition scene 11b's slabs so no label is occluded; add a flow-direction cue | Four of five labels are currently hidden |
| 21 | Raise support-vector contrast (disable additive blending on the normal cloud, or dim it under `supportReveal`) | Makes the deck's most technical claim verifiable |
| 22 | Add an x-axis to Evidence Panel A; darken the prediction line for cream | Data-viz completeness and projector legibility |
| 23 | Differentiate three of the seven chain vessels; fix the label collisions; give the recycle an arrow | Chemical-engineering credibility |
| 24 | Add a direction cue to the value ring; reconcile six nodes with the four-word headline | Removes an avoidable jury question |
| 25 | Cut scene 03 to ~40 s (travelling with the material), scene 12 to ~30 s, scene 01 to ~35 s | Recovers ~55 s for Act V |
| 26 | Drop the receded plant to ≤ 0.05 in cream scenes | Removes the double-exposure look in 12 and 13 |
| 27 | Move the five dark in-world captions to the DOM overlay | One fix for five illegibility failures |
| 28 | Add one line reconciling `0.80 %` with `0.0801` | Prevents a 100×-discrepancy misreading |
| 29 | Disable idle drift in editorial mode | Static type currently swims |
| 30 | Guard or remove click-to-advance | Removes an accidental-skip risk |

## OPTIONAL POLISH

| # | Fix |
|---|---|
| 31 | Fade the boot gate out over 0.9 s instead of unmounting it (the CSS transition is already written) |
| 32 | Reduce plant dust count and opacity so it reads as atmosphere, not fireflies |
| 33 | Round Panel A's y-tick values |
| 34 | Make the progress rail and boundary badge legible in editorial mode |
| 35 | Early-return the Evidence dot loop once the draw completes |
| 36 | Subdivide the granule icosahedron (detail 1) for close shots |
| 37 | Establish a lens language (e.g. 35 mm for machines, 24 mm for space, 50 mm for detail) and stop oscillating FOV |
| 38 | Add an AZERTY-safe alternative to `Shift+1–4` |
| 39 | Re-apply the current pose after WebGL context restore (`poseChannel` already exists for this) |
| 40 | Remove the 787 KB of unused photographs, or use them |
| 41 | Remove the remaining dead exports |

---

# 25. SOUND

**There is no audio in this build** — no `<audio>` element, no Web Audio, no media assets. Verified.

**This is the correct decision and it should not change.** In a live soutenance the presenter's
voice is the soundtrack; a music bed would compete with it, and cinematic stingers on transitions
would make a controlled keynote feel like a product trailer. The `full_script.md` and the on-screen
cue deck already carry the timing.

**Do not add sound.** The one place a case could be made — the 6.5 s silent travel in 05c, where
the cue explicitly says "Let the travel play. Do not talk over it." — is precisely where silence is
doing the work.

---

# 26. WHAT SEPARATES THIS FROM THE TARGET — IN ONE PARAGRAPH

The engineering is there. The argument is there. The honesty is there and is better than the
target requires. What is missing is **direction**: someone deciding that a micro-beat and an act
change should not take the same 2.2 seconds; that a headline should not be legible over the
previous scene's world; that the most important slide's type cannot be nine pixels tall; that the
project's own dashboard should not announce `STALE` at the climax; that a scene should not scroll;
that a closing frame should be quiet. Every one of those is a decision, not a rebuild. The
architecture underneath — one timeline, one persistent world, one shared path function, one honesty
contract — is sound enough to carry all of them. That is why the score is 6.3 and not lower, and
why a focused pass on the fifteen MUST-FIX items would plausibly reach **8.0–8.5**.

---

*End of audit. No presentation file was modified.*
