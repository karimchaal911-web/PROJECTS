# Design System — Industrial Spatial Intelligence

## Visual philosophy

The presentation behaves like one continuous industrial place. The jury does not jump between decorated slides; the camera moves through an abstract soluble-MAP line whose physical objects become signals, records, models, and supervision surfaces. Spatial continuity is the argument: digital intelligence is not a separate universe added to the plant, but another readable layer of the same operation.

Material honesty governs the world. Steel is matte and slightly cool, ducts are silver-grey, process vessels are disciplined geometric forms, and OCP green marks structure, flow, and verified state. There is no cyberpunk neon, fictional control-room gloss, or ornamental circuitry. Digital elements inherit the plant’s geometry as wireframes, pulses, precise lines, and measured typographic labels.

The rhythm alternates darkness and light. Dark chapters hold process scale, movement, and atmospheric depth. Cream chapters slow the camera and present evidence with editorial calm. This creates an Apple-like sense of deliberate reveal without imitating consumer-product advertising or abandoning the industrial context.

Typography is a precise instrument. Large statements are rare, short, and aligned to the world’s geometry. Small labels use a monospaced voice for measurements, chapters, and qualifiers. Copy never competes with the visual transformation. Data values use tabular numerals and generous breathing room.

Motion explains causality. Product granules travel through equipment; sensor pulses align with physical variables; a wireframe emerges from the dryer; data packets split into two intelligence paths; and the resulting evidence resolves into Power BI supervision. Every major transition has a semantic origin and destination.

The result should feel constructed rather than themed: a restrained spatial essay about an industrial operation becoming more observable.

## Tokens

### Color

| Token | Value | Use |
| --- | --- | --- |
| `--ocp-green` | `#017B30` | Brand mark, verified state, core flow |
| `--ocp-leaf` | `#73B72B` | Sparse highlight, particle success state |
| `--forest` | `#063D34` | Dark green surfaces, light-scene text |
| `--night` | `#07110E` | Primary dark background |
| `--steel` | `#8D9893` | Machinery and neutral structure |
| `--fog` | `#C9CFCA` | Secondary text on dark |
| `--cream` | `#F3F1E5` | Evidence and decision chapters |
| `--ink` | `#101713` | Primary text on light |
| `--amber` | `#F2A33A` | Warning threshold only |
| `--red` | `#D64C42` | Critical display threshold only |

Opacity is preferred over additional hues. Green glow is local and low-radius. White is never pure full-screen glare; cream carries light scenes.

### Typography

- Display: `Arial`, `Helvetica Neue`, system sans-serif; weight 300–500; optical tracking `-0.035em` for hero statements.
- Interface labels: `Cascadia Mono`, `Consolas`, monospace; uppercase; 0.08–0.14em tracking.
- Numeric evidence: tabular numerals, weight 500.
- 1920×1080 scale: hero 96–126 px; chapter title 64–84 px; evidence metric 64 px; body 26–32 px; technical label 14–18 px.
- Visible text stays under roughly 32 words per scene except the final boundary/roadmap scene.

### Layout

- Safe frame: 96 px horizontal, 72 px vertical.
- Primary grid: 12 columns; 24 px gutters.
- Statements occupy 4–7 columns; visuals own the remainder.
- Technical index at top-left; prototype qualifier at top-right when data is moving.
- Navigation and progress remain quiet at the bottom edge.
- No bento grids, pills, UI-card walls, or ornamental dashboard chrome.

### Materials and depth

- Machinery: roughness 0.55–0.78, metalness 0.18–0.48.
- Digital twin: emissive OCP green wireframe at 20–55% opacity.
- Data particles: compact points with restrained additive blending.
- Panels: off-white/near-black planes with 1 px hairline; shadows only for spatial separation.
- Photography: cover crop, controlled vignette, never placed in a generic rounded card.

## Composition families

1. **World reveal** — nearly full spatial canvas, minimal type.
2. **Scale lock** — one machinery object dominates; tiny annotations explain it.
3. **Transformation** — the same object changes material/state as the camera moves.
4. **Evidence table** — light cream stage, one authentic plot, three large metrics.
5. **Supervision surface** — Power BI fills a physical plane inside the world.
6. **Decision horizon** — world recedes while a precise current→next path remains.

## Accessibility and presentation ergonomics

- One WebGL renderer for the entire runtime.
- Canvas has `role="img"` and a useful `aria-label`.
- Autoplay is the default. `Space` pauses/resumes; ArrowRight/ArrowLeft are Q&A navigation; `R` restarts; Home/End jump; `S` safe mode; `P` presenter view; `F` fullscreen.
- Focus is visible on all controls.
- `prefers-reduced-motion` is observed live; transitions resolve immediately and particles stop when enabled.
- Safe mode caps pixel ratio, removes shadows, cuts particle count, and disables continuous ornament.
- All core claims exist in accessible HTML outside the canvas.

## Prohibited patterns

- Purple/blue “AI” gradients, glowing circuit brains, robotic imagery.
- Fake Power BI pages or invented operational data.
- Repetitive card grids and icon rows.
- Scroll-jacking, uncontrolled parallax, or uninterruptible long transitions.
- Decorative motion with no narrative role.
- Small print used to hide scope limits.
