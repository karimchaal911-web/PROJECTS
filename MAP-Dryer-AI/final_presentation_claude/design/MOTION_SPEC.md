# MOTION SPEC

Every transition in the film, specified. Each one answers *why is this moving?*
If the answer had been "to look nice", the motion was cut.

**Global constants** — transition 2.2 s · camera `power2.inOut` · reveal
`power3.out` · exit `power2.in` · text in 0.7 s with 0.06 s stagger · 0.4 s
settle tail · idle drift ±0.12 u over 24 s.

Each transition is **one GSAP timeline**. Camera, object morphs, material
crossfades, light changes and overlay copy are all children of it, so they can
never desynchronise and there is no independent `setTimeout` anywhere.

---

## T00 → 01 · BOOT → AWAKENING

* **Anchor:** darkness itself.
* **Camera:** (−34, 2.4, 26) → (−26.0, 2.4, 19.0), target (−4, 5.4, 2). FOV 38.
* **Transform:** none — the world is already there.
* **Material:** dryer shell emissive 0 → 0.02; dust motes opacity 0 → 0.5.
* **Light:** ambient 0 → 0.35 over 3.0 s; rim 0 → 0.9 delayed 1.2 s; process
  warmth 0 → 1.0 delayed 2.0 s and then begins its ±8 % sine.
* **Duration:** 4.0 s. **Ease:** `power1.inOut` for light, `power2.out` camera.
* **Why:** the plant is not switched on — it is *found*. The rim light arriving
  last is what makes the drum read as a solid object rather than a shape.

## T01 → 02 · AWAKENING → WHY THIS MATERIAL

* **Anchor:** a single granule already resting in the discharge stream.
* **Camera:** dolly in and lens up: (−26, 2.4, 19) → (−13.4, 5.9, 6.2),
  FOV 38 → 26. Target snaps to the granule over the first 0.6 s.
* **Transform:** one granule instance scales 1 → 46× while the camera closes,
  so it appears to be a macro shot, not a growing object.
* **Material:** background DOF-substitute — plant fog density 0.014 → 0.030,
  which defocuses the hall without a post-processing pass.
* **Duration:** 2.6 s. **Ease:** `power2.inOut`.
* **Why:** long-lens compression is how a product is introduced. The fog trick
  buys the depth-of-field read for zero GPU cost.

## T02 → 03 · WHY THIS MATERIAL → FOLLOW THE MATERIAL

* **Anchor:** the granule → the stream.
* **Camera:** pulls back and up to (−58, 16, 30), FOV 26 → 44, then **tracks**
  along the chain for the scene's duration (a separate looping timeline the
  presenter's next press interrupts cleanly).
* **Transform:** the single granule shrinks back to 1× as 2,600 instances fade
  in along `flowPath`; flow velocity 0 → 1.
* **Material:** the 7 stations' emissive lifts from 0 to 0.06 as the stream
  enters each — driven by the stream head position, not by time.
* **Duration:** 2.4 s to settle, then continuous tracking.
* **Why:** causality. The stations light *because* the material arrives, so the
  audience reads a process, not a slideshow of vessels.

## T03 → 04 · FOLLOW → ENTER THE DRYER

* **Anchor:** the dryer, already the destination of the stream.
* **Camera:** (−58, 16, 30) → (2.0, 6.6, 15.5), target → (0, 5.2, 0), FOV 44 → 34.
  Then a slow 22° arc to (−9, 7, 11) over the scene.
* **Transform:** none on the dryer — **the world recedes instead.** Upstream
  stations opacity → 0.12, fog density 0.014 → 0.026, key light cone narrows.
* **Light:** key intensity 2.4 → 3.1, shadow frustum refits to the drum.
* **Duration:** 2.6 s. **Ease:** `power2.inOut`.
* **Why:** this is the film's thesis about focus — we do not cut to the dryer,
  we let everything else fall away. It costs nothing and reads as cinema.

### T04a · MACHINE → PHYSICS *(within Scene 04)*
* Shell material crossfades to wireframe over 1.1 s (`opacity 1 → 0.18`,
  wireframe overlay `0 → 0.5`); flights, material bed and counter-current air
  fade in with 0.08 s stagger; vapour particles start.
* **Why:** the audience must see *inside* to accept that moisture removal is a
  transfer problem, not a black box.

### T04b · PHYSICS → DATA *(within Scene 04)*
* Seven telemetry chips arrive with 0.09 s stagger, each on a 0.5 s
  `power3.out`, each with a 1 px leader line drawn to its origin point on the
  equipment.
* **Why:** every number is anchored to the physical thing that produces it.
  This is the moment the project stops being about a machine.

---

## T04 → 05 · DRYER → THE GAP *(the film's most important move)*

* **Anchor:** the material flow line.
* **Camera:** (−9, 7, 11) → (34, 27, 34), target (0, 5.2, 0) → (74, 6, 0),
  FOV 34 → 46. Then, after the axis has formed, drop to (46, 4.6, 5.2),
  target (78, 5, 0), FOV → 40.
* **Transform:** `straighten` 0 → 1 over **3.2 s**. The flow path unbends into
  a straight line along +X. **The granules keep riding it throughout** — they
  are never hidden and never re-emitted. Simultaneously the axis extends from
  x 16 to x 142 by animating `drawRange`.
* **Material:** the quality plane above the axis fades in at 0.04 opacity —
  visible as an emptiness, not as a surface.
* **Light:** rim holds; key dims to 1.8 so the lab markers can be the brightest
  thing in the frame.
* **Duration:** 4.6 s total (the longest transition in the film).
* **Ease:** `power2.inOut` on camera, `power3.inOut` on `straighten`.
* **Why:** **distance becomes time.** This is the single transformation the
  whole argument depends on, so it is given the most screen time, the slowest
  ease and no competing motion. Nothing else animates during it.

### T05a · THE MARKERS *(within Scene 05)*
* Six lab markers rise from the axis with 0.14 s stagger, 0.6 s `back.out(1.4)`
  — the only overshoot in the entire film, reserved for the one thing that is
  actually measured.
* **Why:** overshoot reads as *solidity*. It says these are facts.

### T05b · THE TRAVEL *(within Scene 05)*
* Camera translates x 46 → 67 at **constant velocity** over 5.5 s (`none`
  easing — the only linear move in the film), holding y and target offset.
  A monospace counter runs `+00:00 → +02:00`. Granules stream past at speed.
* **Why:** linear motion with no easing is uncomfortable, and it should be.
  The jury is meant to feel the duration, not admire the camera.

## T05 → 06 · THE GAP → THE ENGINEERING RESPONSE

* **Anchor:** the empty interval; the camera does not leave it.
* **Camera:** (67, 4.6, 5.2) → (60, 12, 40), target → (78, 7.5, 0), FOV 40 → 44.
  This pull-back only begins **after** the trace is 60 % drawn.
* **Transform:** signal lines emit from the dryer's sensor points and travel
  +X along the axis (0.9 s each, 0.05 s stagger). As each arrives, the
  prediction trace's `drawRange` advances — **the trace is drawn by the arriving
  signals, not by a timer.**
* **Material:** trace `--predict`, additive, 2 px; lab markers hold full
  brightness and are never overdrawn.
* **Duration:** 5.2 s for the draw, 2.2 s for the pull-back, overlapped.
* **Why:** causality again, and the discipline of never letting the estimate
  visually outrank the measurement.

## T06 → 07 · RESPONSE → PHYSICAL BECOMES DIGITAL

* **Anchor:** the time axis, travelled in reverse.
* **Camera:** flies back down the axis, (60, 12, 40) → (−2, 12, 26), then
  rotates to face the stack at target (−5, 14, −22). FOV 44 → 42.
* **Transform:** the axis and trace fade to 0.15 as the camera passes them —
  they recede rather than vanish. Sensor nodes ignite on arrival (0.3 s each).
  The dryer crossfades to a point-cloud/wireframe hybrid over 1.4 s **while
  still rotating**.
* **Duration:** 3.4 s. **Ease:** `power2.inOut`.
* **Why:** reversing the Scene 05 move re-anchors the space. The audience knows
  exactly where they are because they have flown this line before.

### T07a · THE STACK BUILDS *(within Scene 07)*
* 900 instanced packets stream from sensors to (−6, y, −44). Each architecture
  layer's slab scales y 0 → 1 (0.5 s, `power3.out`) **only when its packet
  count threshold is met**. Eight layers, ≈ 7 s total.
* **Why:** the architecture is a consequence, not an illustration.

### T07b · THE WAITING PACKET *(within Scene 07)*
* One packet is isolated (others dim to 0.25), stops at the ALIGN layer, and a
  monospace counter counts `24.5 min` while it waits. Then it joins.
* **Duration:** 3.5 s of near-stillness.
* **Why:** residence-time alignment is the one methodological idea that cannot
  be explained by a static picture. It is worth three seconds of the film.

## T07 → 08 · DIGITAL → TWO PATHWAYS

* **Anchor:** the packet stream.
* **Camera:** (−2, 12, 26) → (0, 16, −34), target (0, 15, −78), FOV 42 → 46.
* **Transform:** the single stream **bifurcates** — instance targets are
  reassigned over 1.6 s so packets visibly choose a lane. 16 go left, 15 go
  right, and the counts are shown.
* **Duration:** 2.8 s.
* **Why:** one input, two questions. The split must be seen to happen to the
  same data.

### T08a · INTO THE MANIFOLD *(within Scene 08)*
* Camera pushes from (0, 16, −34) to (26, 15, −64) — **inside** the point cloud.
  2,400 points fade in over 1.2 s; 136 support vectors brighten 0.8 s later.
* The current-state point follows the real recorded trajectory. Over 6 s of
  playback it leaves the cloud; its colour ramps normal → `--warn` at risk 0.50
  → `--critical` at 0.80, sampled from the real risk series.
* A thin tether line to the cloud centroid lengthens as distance grows.
* **Why:** "novelty detection" is an abstraction until you watch a point leave a
  region. The tether is the only added metaphor, and it is honest: it is the
  distance the model is actually measuring.

## T08 → 09 · PATHWAYS → PROVE IT

* **Anchor:** the prediction trace, recalled from Scene 06.
* **Camera:** (26, 15, −64) → (79, 10.5, 44), target (79, 10.5, 0), FOV 46 → 34.
  A long move; it is covered by the mode change.
* **Transform:** the trace flattens (its z-variance → 0) and rotates to face
  camera, becoming the axis of the holdout scatter. 165 real points arrive with
  a 0.008 s stagger — 1.3 s of accumulating evidence.
* **Light / mode:** **dark → OCP editorial** over 1.4 s: fog `--ink-deep` →
  `--cream` and density 0.026 → 0.004; ambient 0.35 → 0.9; tone-mapping exposure
  1.0 → 1.35; overlay palette crossfades on the same timeline.
* **Duration:** 3.0 s.
* **Ease:** `power2.inOut` camera, `power1.inOut` exposure (linear-ish, so the
  lights feel like they come *up* rather than snap).
* **Why:** evidence is presented in the light. The mode change is dramatic
  precisely because it happens once.

## T09 → 10 · PROVE IT → SUPERVISION

* **Anchor:** panel A's frame.
* **Camera:** (79, 10.5, 44) → (76, 10, 52), target → (76, 10, 26), FOV 34 → 32.
* **Transform:** the chart's bounding frame **thickens into a card**: border
  0 → 1 px, corner radius 0 → 6 px, a title bar grows above it, a legend row
  below. The frame's world position and scale are tweened so that at the end of
  the move the chart sits **exactly registered** over the trend-chart rectangle
  of the real Power BI capture, which fades up beneath it at 0.62 s.
* **Then:** eight dashboard regions highlight in reading order, 0.55 s apart —
  a 1 px `--ocp-green` outline plus a 4 % brightness lift, no zoom, no pop.
* **Light:** exposure 1.35 → 1.1; a soft area light warms from the dashboard
  plane, spilling green-white onto the dark world behind the camera.
* **Duration:** 2.6 s + 4.4 s of highlights.
* **Why:** this is the promised transformation — *the graph becomes the real
  Power BI visual.* The registration must be pixel-honest or the trick fails,
  so the target rectangle is measured from the actual capture, not eyeballed.

## T10 → 11 · SUPERVISION → THROUGH THE DASHBOARD

* **Anchor:** the dashboard plane.
* **Camera:** (76, 10, 52) → (76, 10, 30) → **through** z = 26 → (76, 10, −36).
  FOV 32 → 52 (the widening is what makes it feel like passing through).
* **Transform:** as the near plane crosses the dashboard, its material switches
  to `side: DoubleSide` and opacity drops to 0.25 — we see it from behind,
  which is the point. Four runtime slabs are revealed in depth, each with a
  0.4 s `power3.out` scale-in as the camera reaches it.
* **Final beat:** the replay stream leaves the last slab as a line of packets
  and travels back to the dryer at the origin. The camera yaws 34° so that the
  dashboard, the slabs, the stream and the still-turning dryer are **all in one
  frame**.
* **Duration:** 5.0 s.
* **Why:** end-to-end integration is a spatial claim. Proving it spatially is
  more convincing than any block diagram, and the closing frame is the proof.

## T11 → 12 · THROUGH → WHAT THIS IS WORTH

* **Anchor:** the returning replay stream.
* **Camera:** (76, 10, −36) → (0, 46, 22), target (0, 24, 0), FOV 52 → 40.
  Rises and looks down.
* **Transform:** the runtime slabs and architecture collapse inward and resolve
  into seven ring nodes (1.8 s, `power3.inOut`). The material stream continues
  around the ring.
* **Light / mode:** dark → editorial again, 1.2 s.
* **Duration:** 3.2 s.
* **Why:** altitude is the visual grammar for synthesis. We rise because we are
  summarising.

## T12 → 13 · VALUE → TODAY → NEXT

* **Anchor:** the ring.
* **Camera:** (0, 46, 22) → (16, 30, 34), target (0, 22, 0). FOV holds at 40.
* **Transform:** implemented nodes stay solid; the roadmap extends away from
  the ring as **outlined** geometry, one stage at a time (0.45 s each, 0.25 s
  apart). The last two stages arrive dimmer and with a dashed edge.
* **Material:** solid `--ocp-green` / outline `--outline`, 0.4 opacity, dashed.
* **Duration:** 2.4 s + 3.2 s of staging.
* **Why:** the distinction between built and not-built is the most important
  honesty signal in the presentation, so it is carried by material, opacity,
  line style and position — four redundant channels.

## T13 → 14 · ROADMAP → RETURN

* **Anchor:** the dryer, which has been turning for fourteen minutes.
* **Camera:** (16, 30, 34) → **(−26.0, 2.4, 19.0)**, target (−4, 5.4, 2),
  FOV 40 → 38. The exact opening pose.
* **Transform:** roadmap and ring fade to 0 over 1.4 s. The plant fades back in.
  Sensor nodes remain lit at 0.4. A faint prediction trace runs above the
  product line at 0.25 opacity. Signal lines move slowly.
* **Light / mode:** editorial → dark over 1.8 s. Process warmth returns.
* **Duration:** 4.2 s. **Ease:** `power2.inOut`.
* **Why:** the closing rhyme. Same frame, same light, same machine — but the
  audience can now read the data layer, and that difference *is* the conclusion.
  It only lands because the world was persistent.

---

## Motion that was considered and cut

| Idea | Why it was cut |
|---|---|
| Orbiting the dryer continuously | Gaming camera. It hides the machine's axis and makes scale unreadable. |
| Camera shake on the anomaly event | Drama the data does not support. Risk 0.976 is a number, not an explosion. |
| Particles bursting on each metric reveal | Decorative. Answers none of the four motion questions. |
| Flying the architecture diagram in as a unit | It would have been a slide. Building it from arriving packets is the whole point. |
| A "neural network" visual for the Ridge model | It is a 16-coefficient linear model. Drawing a network would be a lie. |
| Parallax on the DOM overlay | Competes with real 3D depth and reads as a website. |
| Cross-dissolve between scenes | The film has no dissolves at all. Every change is a move through space. |

---

## Interruption behaviour

The presenter can advance at any moment, including mid-transition.

* The active timeline is **killed, not reversed**.
* The world snaps to the *settled* state of the scene being left (0.25 s
  `power2.out`), then the next transition starts from there.
* Camera position is never discontinuous — the snap tweens, it does not cut.
* Rapid presses (< 0.4 s apart) queue at most one scene ahead, so hammering the
  arrow key cannot desynchronise the show.
* `Left Arrow` reverses through the same poses at 0.7× duration, because
  backward navigation is recovery, not narrative, and should be quick.

---

## As built — three amendments

The spec above was written before implementation. Three things changed, and each
is worth recording because the reasoning generalises.

### 1. Lag smoothing is disabled

GSAP clamps large frame deltas by default, so on a machine dropping frames a
2.2-second transition stretched to roughly **twenty seconds**. It was invisible
on a fast machine and only surfaced when the automated capture kept
photographing scenes mid-move.

`gsap.ticker.lagSmoothing(0)` in `Rig.jsx` makes a hitch **skip frames instead
of stretching the scene**. For a live presentation that is the right trade: the
presenter's pacing must not depend on the projector laptop's GPU.

### 2. Beats own their framing, and choreography is relative

Camera poses live in `state/scenes.js` — per scene, and per beat where a scene
needs to move between beats. Anything in `transitions.js` that also moves the
camera is expressed **relatively** (`px: '+=34'`), so it continues from the
settled pose rather than restating an absolute one.

This was learned the hard way. Absolute overrides left in `transitions.js` after
the poses were recomposed silently won the argument, and scene 11 spent a full
QA cycle looking at the inside of its own geometry.

### 3. The scene 04 arc became a drift

The specified 22° orbit was replaced with a slow lateral drift
(`px: '-=9', pz: '-=6'` over 26 s). An orbit around a 22-metre horizontal drum
swings the camera through the support structure and past the axis, which loses
the machine's length — the one property the shot exists to establish. A drift
holds the length and still reveals depth.

### Unchanged

Everything else shipped as specified: the 2.2 s transition, the single timeline
per step, the `straighten` morph as the film's longest and slowest move, the
`back.out` overshoot reserved solely for the laboratory markers, the linear
no-easing travel through the gap, and the total absence of cross-dissolves.
