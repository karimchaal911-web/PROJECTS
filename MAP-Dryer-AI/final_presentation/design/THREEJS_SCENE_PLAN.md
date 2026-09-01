# THREE.JS SCENE PLAN

One persistent `<Canvas>`. One scene graph. One camera. Fourteen states.

Nothing is unmounted between scenes; visibility, opacity, material state and
camera pose are driven from a single scene index. React Three Fiber owns the
graph, GSAP owns the time.

---

## 1. Runtime architecture

```
web/src/
  main.jsx                    React root, StrictMode off (R3F double-invokes)
  App.jsx                     Canvas, boot gate, keyboard, error boundary
  state/
    scenes.js                 the 14 scenes - single source of truth
    useShow.js                zustand store: step, safeMode, hud, help
  three/
    World.jsx                 the persistent scene graph, mounts every layer
    Rig.jsx                   camera controller and the show's single clock
    transitions.js            per-scene choreography on that timeline
    usePresence.js            animated layer-presence channels (see below)
    Lighting.jsx              key / rim / hemisphere / process warmth / fog
    StudioEnv.jsx             procedural IBL - metals render black without it
    Post.jsx                  GTAO ambient occlusion + ACES output pass
    Prewarm.jsx               one offscreen frame that pays every first-use cost
    PerfGuard.jsx             sustained frame collapse -> safe mode
    WorldText.jsx             SDF text, bundled fonts, offline glyph folding
    layers/
      Plant.jsx               ground, green steel, platforms, ducts, roof, dust
      Dryer.jsx               the hero rotary dryer (procedural)
      DryerInternals.jsx      flights, cascading bed, counter-current air, vapour
      Granules.jsx            instanced MAP stream riding flowPath
      ProcessChain.jsx        6 upstream unit operations, the material line,
                              the mother-liquor recycle, and a key + rim that
                              track the material down the chain
      TimeAxis.jsx            axis + 6 lab markers + the 695-point trace
      SensorNodes.jsx         telemetry board, leader-lined to the equipment
      DataPackets.jsx         instanced packets, bifurcation, the waiting packet
      Architecture.jsx        the stack the packets build
      Residence.jsx           the residence-time lane: the physical delay, then
                              the data shift that follows from it
      Pathways.jsx            Ridge lane + the real PCA manifold and trajectory
      Evidence.jsx            hold-out chart, candidate bars, risk trace, limits
      Dashboard.jsx           the real Power BI pages + highlight sequence
      Handover.jsx            artifact -> service -> inference -> screen
      Runtime.jsx             SQL / Postgres / Python / replay staircase
      ValueLoop.jsx           the operational ring
      Roadmap.jsx             solid vs outlined future geometry
  overlay/
    Overlay.jsx               scene-driven DOM copy, scrim, identity marks
    Chrome.jsx                progress rail, boundary badge, presenter HUD, help
  data/
    load.js                   fetch + memoise the seven JSON payloads
  lib/
    curves.js                 flowPath, the world map, layout constants
    palette.js                design tokens and the four lighting modes
    perf.js                   device probe and safe-mode budgets
    surfaces.js               seven procedural industrial surface families
```

Three groupings differ from the first sketch, for cohesion rather than
convenience. `TimeAxis.jsx` holds the axis, the laboratory markers and the
prediction trace together because all three resolve their coordinates from one
shared mapping, and splitting them would mean exporting that mapping just to
keep them registered. `Pathways.jsx` holds both intelligence lanes because
scene 08 cross-fades between them on a single `laneFocus` channel.
`Chrome.jsx` holds the four pieces of persistent and presenter-only UI, none of
which is more than thirty lines.

**Why zustand and not context:** scene changes must not re-render the React tree
during a GSAP timeline. The store publishes a step index; three-side components
read layer state through `usePresence` channels - plain `{ current: number }`
boxes that GSAP tweens and the render loop samples - so advancing a scene never
re-renders the scene graph. The DOM overlay is the only part that re-renders per
step.

**Beats own their framing.** A beat may carry its own `camera` and a `layers`
patch merged over the scene's state. That is what lets scene 09 walk a wall of
evidence, and scene 04 raise the internals and then the telemetry, without
either becoming a separate scene with a separate world state.

---

## 2. World coordinates

Units are metres. The world is built once, at these fixed positions, and the
camera visits them. This is what makes the space legible: the audience can build
a mental map because the map never changes.

| Region | Extent | Contents |
|---|---|---|
| **Plant hall** | x −40…+40, z −24…+24 | Ground plane, 12 green steel columns, overhead ducts, grating platforms |
| **Dryer** | centred (0, 5.2, 0), axis +X | Drum L 22 m, R 2.0 m, incline −1.4°, feed end x −11 (high), discharge x +11 (low) |
| **Upstream chain** | x −96…−16, z 0…−14 | 7 stations along a curve arriving at the feed chute; the 7th IS the dryer, so 6 are built here |
| **Time axis** | x +16…+142, y 4, z 0 | 12 h of held-out TEST mapped to 126 m → **1 h = 10.5 m**, 1 lab interval = 21 m |
| **Quality plane** | above the time axis, y 4…16 | Lab markers, prediction trace, later the evidence panels |
| **Architecture stack** | (−6, 2…30, −44) | 8 layers built by arriving packets |
| **Quality lane** | (−26, 14, −78) | Ridge solid + single output value |
| **Manifold** | (28, 15, −78), r ≈ 11 | Real PCA point cloud |
| **Dashboard plane** | (76, 10, 26), facing −Z, 26 × 14.6 m | The real Power BI capture |
| **Runtime slabs** | a staircase from (78, 17, 18) to (70, −3, −38) | Power BI, SQL, Postgres, Python, replay |
| **Value ring** | (0, 24, 0), r 11, horizontal | Looked down on from above |
| **Roadmap** | (−19, 19, 0), 11 stages at 4 m | Solid built stages, outlined future stages |

The dryer sits at the origin because every other region is described relative to
it. The camera's mental home is always "where the dryer is".

---

## 3. The one geometry, reinterpreted

`lib/curves.js` owns a single parametric path, `flowPath(t)`, `t ∈ [0,1]`, and a
morph parameter `straighten ∈ [0,1]`.

* `straighten = 0` → the curved material path through the plant (Scenes 02–04).
* `straighten = 1` → a straight line along +X, which *is* the time axis
  (Scenes 05–06).

The granule instances, the prediction trace and the evidence baseline all sample
the same path. Morphing `straighten` from 0 → 1 during the Scene 04 → 05
transition is what turns distance into time, in one continuous motion, with the
granules still riding it.

`TimeAxis` maps `2026-07-05 00:00 → 12:00` onto `x ∈ [16, 142]`. Every temporal
object in the film — lab markers, prediction points, risk values — resolves its
x from that one function, so they are guaranteed to register with each other.

---

## 4. Geometry budget

Procedural Three.js, no imported meshes required. Blender was evaluated and
rejected for this build: every form here is a lathe, cylinder, box, extrusion or
instanced primitive, and keeping it procedural means the whole presentation is a
text repository that runs offline with no binary asset pipeline, no Draco
decoder and no KTX2 transcoder to fail on presentation hardware. That is the
right trade for a soutenance.

| Object | Construction | Tris | Draw calls |
|---|---|---|---|
| Drum shell | `CylinderGeometry(2, 2, 22, 64, 1, true)` + caps | ~8.4 k | 1 |
| Riding rings ×2 | `TorusGeometry(2.12, 0.16, 12, 48)` | ~2.3 k | 1 (merged) |
| Trunnion rollers ×4 | `CylinderGeometry` | ~1.6 k | 1 (merged) |
| Girth gear | `TorusGeometry` + 96 instanced teeth | ~3.1 k | 2 |
| Feed chute / discharge hood | extruded profiles | ~1.2 k | 2 |
| Exhaust duct | `TubeGeometry` along a Catmull-Rom | ~2.4 k | 1 |
| Support structure | merged boxes | ~4.0 k | 1 |
| Columns ×12 + bracing | instanced I-beam profile | ~6.0 k | 1 |
| Platforms + handrails | merged boxes + instanced tubes | ~5.0 k | 2 |
| Internal flights ×12 | instanced boxes | ~1.4 k | 1 |
| Upstream unit operations ×6 | 7 shared unit geometries, scaled per mesh | ~30 k | a few hundred, all small |
| Granules | `InstancedMesh(icosahedron, 1)` × 2,600 | ~5.2 k | 1 |
| Dust motes | `Points` × 1,800 | — | 1 |
| Manifold cloud | `Points` × 2,400 + 136 | — | 2 |
| Data packets | `InstancedMesh(box)` × 900 | ~1.8 k | 1 |
| Charts / traces | `Line2` / `BufferGeometry` | ~4 k | ~10 |
| Architecture / runtime slabs | boxes + `Text` | ~3 k | ~14 |

**Total ≈ 62 k triangles, ~55 draw calls, 3 shadow-casting lights → 1.**
Only the key light casts shadows, and its frustum is fitted to the dryer only.

Text uses `troika-three-text` (SDF, one draw call per block, no DOM reflow) for
in-world labels; the DOM overlay handles hero copy where kerning and wrapping
matter more.

---

## 5. Per-scene state matrix

`L` = layer visible, `·` = hidden, `w` = wireframe/point state, `~` = fading.

| # | Scene | Plant | Dryer | Intern. | Gran. | Chain | Axis | Lab | Trace | Sensors | Packets | Arch | Lanes | Manifold | Evid. | Dash | Runtime | Ring | Road | Mode |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Awakening | L | L | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | dark |
| 02 | Why MAP | ~ | L | · | L | · | · | · | · | · | · | · | · | · | · | · | · | · | · | dark |
| 03 | Follow | L | L | · | L | L | · | · | · | · | · | · | · | · | · | · | · | · | · | dark |
| 04 | Dryer | ~ | L | L`w` | L | ~ | · | · | · | L | · | · | · | · | · | · | · | · | · | dark |
| 05 | Gap | ~ | L | · | L | · | L | L | · | · | · | · | · | · | · | · | · | · | · | dark |
| 06 | Response | ~ | L | · | L | · | L | L | L | L | · | · | · | · | · | · | · | · | · | dark |
| 07 | Digital | ~ | L`w` | L`w` | ~ | · | ~ | · | ~ | L | L | L | · | · | · | · | · | · | · | dark |
| 08 | Pathways | · | ~ | · | · | · | · | · | · | · | L | ~ | L | L | · | · | · | · | · | dark |
| 09 | Prove it | ~ | ~ | · | · | · | L | L | L | · | · | · | · | ~ | L | · | · | · | · | **light** |
| 10 | Supervision | ~ | ~ | · | · | · | ~ | ~ | ~ | · | · | · | · | · | ~ | L | · | · | · | dark+ |
| 11 | Through | ~ | L | · | L | · | · | · | · | L | L | · | · | · | · | L | L | · | · | dark+ |
| 12 | Value | ~ | L | · | L | · | · | · | · | · | ~ | · | · | · | · | · | ~ | L | · | **light** |
| 13 | Roadmap | ~ | L | · | L | · | · | · | · | · | · | · | · | · | · | · | · | ~ | L | **light** |
| 14 | Return | L | L | · | L | · | · | · | ~ | L | ~ | · | · | · | · | · | · | · | · | dark |

Every `~` is a *fade to a low presence*, not an unmount. The plant never
disappears; it recedes into fog. The dryer is visible in **all fourteen**.

---

## 6. Camera poses

Position and target in world units. The rig tweens both, plus `fov`, on one
timeline. All values are the *settled* pose; the camera then idles ±0.12 units.

| # | Position | Target | FOV | Note |
|---|---|---|---|---|
| 01 | (−26.0, 2.4, 19.0) | (−4.0, 5.4, 2.0) | 38 | Human height, walking in between columns |
| 02 | (−13.4, 5.9, 6.2) | (−11.6, 5.7, 4.4) | 26 | Macro on one granule, long lens compression |
| 03 | (−58.0, 16.0, 30.0) | (−48.0, 6.0, −4.0) | 44 | Tracking; animated along the chain |
| 04 | (2.0, 6.6, 15.5) | (0.0, 5.2, 0.0) | 34 | Hero three-quarter; arcs to (−9, 7, 11) |
| 05 | (34.0, 27.0, 34.0) | (74.0, 6.0, 0.0) | 46 | Rises, sees the axis form; then drops to (46, 4.6, 5.2) |
| 06 | (60.0, 12.0, 40.0) | (78.0, 7.5, 0.0) | 44 | Sees all 12 h at once |
| 07 | (−2.0, 12.0, 26.0) | (−5.0, 14.0, −22.0) | 42 | Flies back, then faces the building stack |
| 08 | (0.0, 16.0, −34.0) | (0.0, 15.0, −78.0) | 46 | Between the two lanes; pushes into the manifold |
| 09 | (79.0, 10.5, 44.0) | (79.0, 10.5, 0.0) | 34 | Straight-on, flat, editorial |
| 10 | (76.0, 10.0, 52.0) | (76.0, 10.0, 26.0) | 32 | Dashboard fills the frame |
| 11 | (76.0, 10.0, 30.0) → (76, 10, −36) | ahead | 52 | Pushes **through** the plane |
| 12 | (0.0, 46.0, 22.0) | (0.0, 24.0, 0.0) | 40 | Looking down on the ring |
| 13 | (16.0, 30.0, 34.0) | (0.0, 22.0, 0.0) | 40 | Ring seen obliquely, future extends away |
| 14 | (−26.0, 2.4, 19.0) | (−4.0, 5.4, 2.0) | 38 | **Identical to 01** |

Scene 14 reusing Scene 01's pose exactly is the film's closing rhyme. It only
works because the world was never rebuilt.

---

## 7. Data binding

Six JSON payloads, produced by `data_build/extract_presentation_data.py`,
fetched once at boot behind the loading gate.

| File | Size | Consumed by |
|---|---|---|
| `facts.json` | 4.7 KB | Overlay captions, telemetry, architecture labels, boundary text |
| `gap.json` | 72 KB | `TimeAxis`, `LabMarkers`, `PredictTrace`, Scene 04 telemetry values |
| `holdout.json` | 8.2 KB | `Evidence` panel A (165 real points) |
| `candidates.json` | 0.9 KB | `Evidence` candidate bars |
| `coefficients.json` | 1.1 KB | `Pathways` - the 16 standardised Ridge coefficients |
| `anomaly.json` | 293 KB | `Evidence` panel B, risk trace, the `steam_dip` event |
| `manifold.json` | 107 KB | `ManifoldCloud` — 2,400 + 136 + trajectory |

Seven payloads, **487 KB** of JSON, all local, gzip ≈ 150 KB. No runtime computation of
model output: the app renders numbers, it does not produce them.

---

## 8. Performance and safe mode

Target 60 fps at 1920×1080 on integrated graphics.

**Standard mode:** DPR capped at 1.75, shadows on (2048), granules 2,600, dust
1,800, manifold 2,400, packets 900, antialias on.

**No post-processing pass ships.** Bloom and vignette were specified, then cut:
`@react-three/postprocessing` conflicted on peer versions, and the same read is
achieved by additive emissive materials plus a CSS radial vignette - at zero
shader-compilation risk on unfamiliar presentation hardware. Tone mapping is
ACES Filmic, built into three.

**Safe mode** (`S`, or auto-entered when the boot probe measures < 42 fps over
the first 90 frames, or on `prefers-reduced-motion`):

| Reduction | Standard | Safe |
|---|---|---|
| DPR | 1.75 | 1.0 |
| Shadows | 2048 PCF soft | off (baked contact shadow plane) |
| Granules | 2,600 | 700 |
| Dust motes | 1,800 | 0 |
| Manifold points | 2,400 | 900 |
| Antialias | MSAA | off, `powerPreference: "low-power"` |
| Packets | 900 | 260 |
| Idle drift | on | off |

Safe mode is a **visual downgrade, never a narrative one**: every scene, beat,
number and transition still happens. The presenter can toggle it at any moment,
including mid-scene, without losing position.

**Boot sequence:** probe device → load fonts → fetch the seven JSON files →
build geometry → warm up (render one hidden frame per material to force shader
compilation) → fade from black. Shader compilation is forced up front
specifically so that no scene stutters the first time it is reached.

---

## 9. Failure behaviour

| Failure | Behaviour |
|---|---|
| WebGL context unavailable | Full-screen static fallback: the exported scene stills with the same overlay copy, arrow keys still advance |
| WebGL context lost mid-show | Auto-restore, re-enter the current scene at its settled pose, no position lost |
| A JSON payload fails to load | That layer renders empty and logs once; the show continues; no exception reaches the render loop |
| A texture fails | Material falls back to flat token colour |
| Frame rate collapses | Auto safe mode after 90 consecutive frames below 30 fps, announced only in the presenter HUD |
| Software GL detected | Post-processing unmounts itself; rendering hands straight back to r3f |

There are no uncaught errors in the render loop by construction: every layer
guards its own data, and `App` wraps the canvas in an error boundary that
degrades to the static fallback rather than a blank screen.

### What a restored context actually has to rebuild

`useShow.renderEpoch` is incremented once per restore, and three things take it
as a dependency. `StudioEnv` regenerates the PMREM environment and `Post`
rebuilds the composer — both hold *rendered* targets, which come back allocated
but empty, so without this the film returns with every metal surface black and no
occlusion. The `Rig` re-settles the world into the step the presenter is already
on.

Three things it must **not** do, all of which it used to:

1. **Move the camera.** `state.current` is plain JS and survived the loss intact,
   including however far a scene's own slow drift had travelled. Re-tweening to
   the beat's settled pose snapped the shot back to where that drift *started*.
2. **Replay the choreography.** `buildTransition` returns immediately on a
   restore. Several beats own absolute timings that do not scale with the
   transition duration, so building the beat's timeline on top of an
   already-settled world re-ran it — a context loss during scene 10 replayed the
   whole nine-second artifact-to-service sequence over a dashboard the presenter
   had been talking over for a minute.
3. **Disagree with the ordinary path about where "settled" is.** A restore sets
   channels from `sceneChannelState`; the arrow key animates them with
   `buildTransition`. Those two tables were written at different times and had
   never been compared.

### Proving it

Two harnesses, because a reliability claim that is never exercised is a claim.

`scripts/qa-restore.mjs` reaches a step by random access, records the camera
pose, the focal length, all 68 presence channels and the environment and AO
epochs, kills the context through `WEBGL_lose_context`, restores it, and asserts
that the step did not move, the pose came back, every channel came back, both
GPU-side resources were *rebuilt* rather than merely still present, and the page
is drawing at the rate it drew at a moment earlier.

`scripts/qa-channels.mjs` walks all 42 steps and diffs the live channel values
against what a number-key jump — or a restore — would put there instead,
classifying each disagreement by whether the owning layer is on screen. It found
four that were: the scene-03 chain head (two tables, disagreeing on four of eight
beats, by as much as half the chain), the scene-03 granule size, the scene-07
value chips, and the scene-11 packet flow.


---

## 10. Camera poses - as built

Section 6 recorded the poses from the design gate. They were recomposed during
the visual QA pass, and beats gained their own framing. The authoritative values
now live in `web/src/state/scenes.js`, which is the single source of truth for
camera, mode, layer presence and copy.

Three findings from that pass are worth keeping, because they will recur in any
similar build:

1. **Metalness without an environment map renders black.** Every metal surface
   in the first pass was invisible. A procedural `RoomEnvironment` through
   `PMREMGenerator` fixes it with no asset and no network.
2. **Fog erases subjects, not only backgrounds.** At the first densities
   anything past roughly sixty units - the runtime staircase, the far end of the
   time axis - dissolved entirely into the fog colour. Densities were roughly
   halved and long-range subjects were given `fog: false`.
3. **Coplanar slabs viewed head-on occlude each other.** The runtime layers had
   to become a staircase stepping back, down and across, read from an oblique
   angle, before all five could be seen at once.
