# DESIGN SYSTEM

The soutenance is one continuous 3D world. This document defines the constants
that keep it coherent across fourteen scenes: colour, light, type, layout,
material and the rules for when the world is dark and when it is bright.

---

## 1. The governing idea

> **Green steel, white dust, dark air, one bright signal.**

The audit found that the real plant's structural steel is painted green — the
same family as the OCP identity. So the design does not *apply* a brand to an
industrial scene; it photographs an industrial scene that happens to be OCP
green. Everything else is desaturated: dust-grey concrete, olive shadow, pale
MAP powder. Against that near-monochrome ground, **one saturated colour at a
time carries meaning**: cream for product truth, teal for data, amber for
warning, red for critical.

Restraint rule: **at most two accent colours are visible in any single frame.**

---

## 2. Colour tokens

### 2.1 Core ground

| Token | Hex | Role |
|---|---|---|
| `--ink-void` | `#05100D` | Cinematic near-black; scene ground in dark mode |
| `--ink-deep` | `#081914` | Atmospheric fog colour, depth falloff |
| `--forest-900` | `#003C30` | Deep forest — dashboard sidebar, dark UI surfaces |
| `--forest-700` | `#0C5A48` | Raised dark surface |

### 2.2 OCP identity

| Token | Hex | Role |
|---|---|---|
| `--ocp-green` | `#007830` | Primary identity. Used sparingly: marks, active state, the value loop |
| `--ocp-lime` | `#84B40C` | Secondary accent, growth/plant-nutrition beat only |
| `--ocp-leaf` | `#4E9A3C` | Mid-tone bridge between green and lime |

### 2.3 Editorial light mode

| Token | Hex | Role |
|---|---|---|
| `--cream` | `#F5F2E4` | OCP editorial page ground |
| `--ivory` | `#FCF0D8` | Warm card ground (matches the real dashboard) |
| `--ink-editorial` | `#12261E` | Headline text on cream |
| `--rule` | `#D6D2BE` | Hairline rules, 1 px |

### 2.4 Industrial materials

| Token | Hex | Role |
|---|---|---|
| `--steel-green` | `#2E4A34` | Painted structural steel |
| `--steel-dark` | `#1A2A20` | Steel in shadow |
| `--dust` | `#C9C4B6` | MAP dust coating, concrete |
| `--dust-bright` | `#E8E4D8` | Lit dust, product powder |
| `--granule` | `#EFEADA` | MAP crystal |
| `--handrail` | `#B8952E` | Yellow handrails — tiny quantities, realism anchor |

### 2.5 Data and state

| Token | Hex | Role |
|---|---|---|
| `--data-teal` | `#2FB6A0` | The digital layer. Signals, packets, telemetry |
| `--data-cyan` | `#7FE3D4` | Data highlight / active packet |
| `--predict` | `#3DD6B0` | Predicted moisture trace |
| `--lab` | `#F5F2E4` | Laboratory measurement — deliberately the brightest, most solid mark in the world |
| `--warn` | `#E8A33D` | Anomaly warning ≥ 0.50 |
| `--critical` | `#D1493F` | Anomaly critical ≥ 0.80 |
| `--outline` | `#6E8A80` | Future / not-implemented geometry |

**Semantic locks.** `--lab` is always the brightest mark on screen: the
laboratory remains the reference, and the design says so before the speaker
does. `--predict` never touches `--lab`'s brightness. `--warn`/`--critical`
appear in exactly two scenes (09 anomaly panel, 10 dashboard highlight) so they
never become decoration.

---

## 3. Dark / light rhythm

The world has two lighting states and moves between them **once**, deliberately,
as a dramatic beat — not as alternating slide backgrounds.

| Scenes | Mode | Why |
|---|---|---|
| 01 – 08 | **Dark cinematic** | Industrial night, discovery, the gap, the data layer |
| 09 | **OCP light editorial** | Evidence. The lights come up. Nothing is hidden |
| 10 – 11 | Dark, warming | Supervision — dashboard light spills into the dark world |
| 12 – 13 | **OCP light editorial** | Value and roadmap read as a document, not a film |
| 14 | Dark cinematic | Return to the plant |

Transitions between modes are **exposure changes on the same world**, never
cuts: fog colour, ambient intensity, tone-mapping exposure and the DOM overlay
palette cross-fade over 1.4 s on the same GSAP timeline as the camera move.

---

## 4. Typography

Bundled locally — no CDN, no runtime web-font dependency.

| Role | Family | Weight | Treatment |
|---|---|---|---|
| Hero statement | **Inter Tight** | 600 | `clamp(3.2rem, 6.4vw, 6.2rem)`, tracking `-0.03em`, line-height 0.98 |
| Scene title | Inter Tight | 600 | `clamp(1.9rem, 3.2vw, 3.1rem)`, tracking `-0.02em` |
| Body / caption | **Inter** | 400 | `clamp(0.95rem, 1.15vw, 1.15rem)`, line-height 1.5, max 46ch |
| Eyebrow / label | Inter | 500 | `0.72rem`, tracking `0.18em`, uppercase |
| Telemetry, metrics, timestamps | **JetBrains Mono** | 400/500 | tabular figures, tracking `0.02em` |

Rules:
* **Never more than 22 words of body copy on screen at once.**
* Hero statements are 3–7 words and land on their own, with the world visible.
* Numbers are always monospace with an explicit unit; moisture always shows
  3–4 decimals and `%`, with the quantity NAMED beside it — the same convention
  the shipped Power BI report uses.

**Engineering typography policy — one convention across DOM and world.**
The in-world SDF font ships the bundled Latin subsets only, so a symbol either
renders in *both* surfaces or is spelled out in both. Nothing is written one way
in the overlay and another way in the scene.

| Quantity | Written | Why |
|---|---|---|
| temperature | `°C` | U+00B0 is in the bundled subset; verified in a blocked-network capture |
| volumetric flow | `m³/h` | U+00B3 likewise |
| water content | named quantity + `%` | the subscript in `H₂O` has no glyph in the world subset, and `H2O` in a monospace face whose zero carries no slash is an O/0 coin toss at projector distance |
| vacuum | `mmH2O` | kept, because the shipped report prints it that way |
| Greek | `alpha = 10`, `nu = 0.02` | no Greek in the subset, and CSS `text-transform: uppercase` maps ν to a glyph identical to Latin N — which turned `nu = 0.02` into what reads as a sample size |
| delta | not used | spell the interval out: `5 s tick` |

`.caption` therefore carries **no** `text-transform`; caption strings are written
already-uppercased at source.
* No italics. No text shadow — legibility comes from a scrim, not a glow.

Fallback stack: `"Inter Tight", "Inter", system-ui, "Segoe UI", sans-serif`.

---

## 5. Layout

A 12-column grid on a 16:9 safe frame.

* **Safe area:** 6 % inset on all sides. Projectors crop; nothing meaningful
  lives outside it.
* **Text zones:** copy occupies at most 5 of 12 columns and is anchored left
  (columns 1–5) or right (8–12) — never centred over the subject.
* **The subject owns the centre.** DOM overlay never covers the geometry it is
  describing.
* **Scrim:** any text over the 3D world sits on a linear gradient scrim
  (`--ink-void` at 78 % → transparent) so contrast is guaranteed regardless of
  what the camera is looking at. The scrim is part of the type, not the scene.
* **Progress rail** (borrowed from OCP's own `01 —— 05` pattern): a 1 px rail
  along the bottom safe edge with the scene number in monospace. It is the only
  persistent chrome. Opacity 0.35, rising to 0.7 for 1.2 s after a scene change,
  then settling.

Minimum type size at 1920×1080 is 22 px. Minimum contrast 4.5:1 for body,
3:1 for large display type — checked in the visual QA pass at projector gamma.

---

## 6. Lighting

Premium industrial-product cinematography, not sci-fi.

* **Key:** one directional light, warm-neutral `#FFF4E2`, intensity 2.4, from
  camera-left and above, casting real shadows (PCF soft, 2048 map, tight
  frustum around the hero object only).
* **Rim:** one directional, cool `#9FC7BC`, intensity 0.9, from behind-right —
  this separates the dryer shell from the dark air and is the single most
  important light in the film.
* **Ambient/hemisphere:** sky `#1A2E28`, ground `#0A1512`, intensity 0.35.
  Keeps shadows readable without flattening.
* **Process warmth:** one point light inside the dryer discharge, `#FFAE5C`,
  intensity varying ±8 % on a slow sine — the only "alive" light. It reads as
  heat and it makes the machine feel like it is running.
* **Fog:** exponential, `--ink-deep`, density 0.014 in dark mode, 0.004 in
  editorial mode. Fog is the primary depth cue and the primary tool for making
  the environment *recede* rather than *disappear*.

Forbidden: bloom above 0.35 strength, neon emissive materials, purple or
electric-blue light, chrome/mirror finishes, lens flares, god rays as decoration.

Post-processing is limited to: ACES-Filmic tone mapping, a restrained bloom
(threshold 0.85, strength 0.28) that only the emissive data layer and the
process warmth can reach, and a subtle vignette (0.22). Nothing else.

---

## 7. Material language

| Surface | Base | Roughness | Metalness | Note |
|---|---|---|---|---|
| Dryer shell | `#8E8A7E` | 0.62 | 0.55 | Dust-loaded steel; slight variation by vertex |
| Riding ring / tyre | `#6E6A60` | 0.45 | 0.8 | Polished by contact — the only near-metal highlight |
| Structural steel | `--steel-green` | 0.72 | 0.35 | Painted, chalked by dust |
| Handrail | `--handrail` | 0.8 | 0.2 | Tiny areas only |
| Grating platform | `#54544A` | 0.85 | 0.4 | Alpha-mapped, seen edge-on mostly |
| Ductwork | `#A8A296` | 0.7 | 0.5 | Insulated, pale |
| Concrete | `--dust` | 0.95 | 0.0 | Ground plane |
| MAP granule | `--granule` | 0.55 | 0.0 | Slight subsurface feel via emissive 0.04 |
| Wireframe state | `--data-teal` | — | — | `LineBasicMaterial`, opacity ≤ 0.5 |
| Point cloud | `--data-cyan` | — | — | Additive, size-attenuated, opacity ≤ 0.7 |
| Future/outline | `--outline` | — | — | Dashed lines, opacity 0.4 |

Wear is expressed by **dust accumulation**, not rust or damage: a subtle
vertical gradient lightening downward surfaces, matching the photographs.

---

## 8. Data visualisation inside 3D

Charts are geometry, not textures.

* **Axes:** 1 px lines at `--outline`, opacity 0.35. No grid boxes. At most 4
  ticks per axis, monospace labels.
* **Continuous prediction:** a tube/line in `--predict`, width 2, drawn by
  animating `drawRange` — the line is *written*, left to right, at reading speed.
* **Laboratory samples:** solid spheres in `--lab`, radius 1.8× the line width,
  with a thin vertical drop line to the axis. Always the brightest object.
* **Scatter (actual vs predicted):** points in `--predict` at 0.75 opacity;
  the 1:1 identity line in `--outline`; residual whiskers only on hover-free
  static reveal.
* **Risk trace:** a line whose colour is sampled per-vertex from
  normal → `--warn` at 0.50 → `--critical` at 0.80. Threshold bands are flat
  translucent planes behind it (amber 0.06, red 0.06 opacity).
* **Point cloud (learned region):** 2,400 real projected TRAIN points,
  additive, small; 136 support vectors as slightly larger, brighter points;
  the disturbance trajectory as an animated polyline that visibly exits.

Every chart carries a one-line provenance caption in the eyebrow style, e.g.
`HELD-OUT TEST · n = 165 · CHRONOLOGICAL`.

---

## 9. Motion constants

| Constant | Value | Applies to |
|---|---|---|
| Scene transition | **2.2 s** | Camera + world state, one GSAP timeline |
| Camera easing | `power2.inOut` | All camera position/target tweens |
| Reveal easing | `power3.out` | Elements arriving |
| Exit easing | `power2.in` | Elements leaving |
| Text in | 0.7 s, `power3.out`, y `+14px`, blur `4px → 0` | Hero and title |
| Text stagger | 0.06 s | Multi-line copy |
| Settle | 0.4 s tail on every camera move | Camera never stops abruptly |
| Idle drift | ±0.12 units, 24 s period | Camera is never perfectly still |

**The motion test.** Before any animation ships it must answer *why is this
moving?* with one of: narrative (the story advances), causal (A produced B),
spatial (we changed viewpoint), hierarchical (attention moved). Decorative
motion is deleted. Nothing loops for its own sake except the dryer rotation and
the process light — both of which mean *the plant is running*.

Reduced motion (`prefers-reduced-motion`) collapses transitions to 0.4 s
cross-dissolves and disables idle drift, particles and bloom.

---

## 10. Interface layer

The only persistent UI is the progress rail. Everything else is transient.

* **Telemetry chips** — monospace, `--data-teal` at 0.8, a 1 px left border, no
  box. They appear anchored to the object they describe, hold, and leave.
* **Provenance line** — bottom-left of any evidence frame, 0.72 rem uppercase,
  opacity 0.55.
* **Boundary badge** — `PROTOTYPE · SYNTHETIC DATA · ADVISORY` in the bottom
  safe edge whenever a model result is on screen. Non-negotiable; it is the
  design system's honesty contract.
* **Presenter HUD** (optional, `P`) — a separate overlay: current scene, next
  scene, elapsed time, 3–5 cue bullets. Never visible to the audience by default.

No cards, no glassmorphism, no rounded panels floating in space, no drop
shadows on DOM. Text sits on the world.

---

## 11. Accessibility and projector safety

* Contrast checked against a projector gamma assumption of 2.4 (dimmer than a
  laptop). Body copy targets 7:1 on the laptop so it survives at 4.5:1 projected.
* No information is carried by colour alone: warning/critical states also change
  line weight and carry a monospace label.
* Everything must remain readable if the projector loses saturation: the design
  is legible in greyscale because the hierarchy is built on luminance.
* No pure `#000000` (crushes on projectors) and no pure `#FFFFFF` on cream.
