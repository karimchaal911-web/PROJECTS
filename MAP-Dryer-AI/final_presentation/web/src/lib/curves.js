import * as THREE from 'three';

/**
 * The one geometry, reinterpreted.
 *
 * `flowPath(t, straighten)` returns a point on the material path.
 *   straighten = 0 → the curved route through the plant (scenes 02–04)
 *   straighten = 1 → a straight line along +X, which IS the time axis (05–06)
 *
 * Granules, the prediction trace and the evidence baseline all sample this
 * same function, which is why distance can become time in one continuous move
 * without anything being re-created.
 *
 * See design/THREEJS_SCENE_PLAN.md §3.
 */

// World anchors
export const DRYER = { x: 0, y: 5.2, z: 0, length: 22, radius: 2.0, incline: -1.4 };
export const FEED_END = -DRYER.length / 2;      // x = -11, high end
export const DISCHARGE_END = DRYER.length / 2;  // x = +11, low end

// Time axis: 12 hours of held-out TEST mapped to x ∈ [16, 142]
export const AXIS = { x0: 16, x1: 142, y: 4, hours: 12 };
export const AXIS_LEN = AXIS.x1 - AXIS.x0;
export const METRES_PER_HOUR = AXIS_LEN / AXIS.hours; // 10.5 m

/** Upstream process chain control points (curved route into the feed chute). */
export const CHAIN_POINTS = [
  new THREE.Vector3(-96, 3.0, -12),
  new THREE.Vector3(-84, 3.4, -13.5),
  new THREE.Vector3(-72, 4.0, -12),
  new THREE.Vector3(-60, 4.6, -8),
  new THREE.Vector3(-48, 5.2, -3),
  new THREE.Vector3(-36, 6.0, 0.5),
  new THREE.Vector3(-24, 7.2, 1.5),
  new THREE.Vector3(-16, 8.0, 0.8),
];

export const chainCurve = new THREE.CatmullRomCurve3(CHAIN_POINTS, false, 'catmullrom', 0.4);

/** The seven upstream stations, in verified process order. */
/**
 * Verified sequence (design/RESOURCE_AUDIT.md section 5, from
 * final_report/chapters/chapter2.tex):
 *
 *   phosphoric-acid pretreatment -> ammonia vaporization -> neutralization
 *   -> buffer / stabilization -> concentration & crystallization
 *   -> centrifugation -> DRYING -> cooling / conditioning
 *          ^ mother liquor returns from centrifugation to neutralization
 *
 * `form` differentiates the silhouettes. Seven variations on "beige cylinder
 * with a cap" told a chemical engineering jury that seven different unit
 * operations are the same equipment, so each form is now built from the KIND
 * of machine the operation needs:
 *
 *   vessel       vertical vessel, dished head, skirt, ladder      (pretreatment)
 *   vaporizer    receiver + two horizontal shell-and-tube
 *                exchangers on saddles                            (ammonia vaporization)
 *   reactors     three agitated reactors in series                (neutralization)
 *   tankfarm     a row of flat-roofed agitated tanks              (buffer / stabilization)
 *   crystalliser body + cone + external forced-circulation loop
 *                and a vapour condenser                           (crystallization)
 *   centrifuges  two parallel horizontal machines on a skid       (centrifugation)
 *
 * The generic unit-operation FORMS come from the site's own PCS7 mimics in
 * `assets/process/` — pcs7_ammonia_vaporization (a receiver feeding two
 * horizontal shell-and-tube vaporizers), pcs7_neutralization (three agitated
 * reactors in series), pcs7_buffer_tanks ("Reservoirs tampons", a row of
 * agitated tanks), pcs7_crystallization_300_second_effect (a body over a cone
 * with an external circulation loop and a vapour condenser),
 * pcs7_centrifugation ("Essorage", two parallel horizontal machines).
 *
 * What is NOT claimed: no tag number, dimension, count or equipment identity.
 * The report explicitly refuses to map photographed equipment to PCS7 tags, so
 * these remain generic forms of the right kind of machine — never the plant's
 * actual machines. Structural steel is green and handrails are yellow because
 * that is what assets/process/drying_section_structure.jpeg shows.
 *
 * `anchor` is where the label's leader line attaches, in local units relative
 * to the station's own footprint: [x * r, y, z * r].
 */
export const STATIONS = [
  { id: 'acid', n: '01', label: 'PHOSPHORIC-ACID PRETREATMENT', t: 0.02, r: 2.9, h: 9.5, form: 'vessel', anchor: [0.9, 9.6, 0] },
  { id: 'vapor', n: '02', label: 'AMMONIA VAPORIZATION', t: 0.16, r: 2.3, h: 9.0, form: 'vaporizer', anchor: [0.7, 9.4, 0] },
  { id: 'neutral', n: '03', label: 'NEUTRALIZATION', t: 0.33, r: 2.5, h: 7.6, form: 'reactors', anchor: [0.25, 10.4, 0] },
  { id: 'buffer', n: '04', label: 'BUFFER / STABILIZATION', t: 0.48, r: 2.2, h: 6.8, form: 'tankfarm', anchor: [0.2, 9.2, 0] },
  { id: 'crystal', n: '05', label: 'CONCENTRATION & CRYSTALLIZATION', t: 0.64, r: 3.2, h: 13, form: 'crystalliser', anchor: [0.5, 14.6, 0] },
  { id: 'centri', n: '06', label: 'CENTRIFUGATION', t: 0.8, r: 2.4, h: 6.4, form: 'centrifuges', anchor: [0.2, 6.9, 0] },
  { id: 'dry', n: '07', label: 'DRYING', t: 0.96, r: 0, h: 0, form: 'none', anchor: [0, 0, 0] },
];

/** Where the mother-liquor recycle leaves and where it returns. */
export const RECYCLE = { from: 'centri', to: 'neutral' };

const _v = new THREE.Vector3();
const _a = new THREE.Vector3();
const _b = new THREE.Vector3();

/**
 * Sample the material path.
 * @param {number} t 0..1 along the whole route (chain → dryer → downstream)
 * @param {number} straighten 0..1 morph into the time axis
 * @param {THREE.Vector3} out
 */
export function flowPath(t, straighten = 0, out = _v) {
  const tc = THREE.MathUtils.clamp(t, 0, 1);

  // --- curved route -------------------------------------------------------
  // 0.00–0.55 upstream chain, 0.55–0.75 through the dryer, 0.75–1.0 downstream
  if (tc < 0.55) {
    chainCurve.getPoint(tc / 0.55, _a);
  } else if (tc < 0.75) {
    const u = (tc - 0.55) / 0.20;
    _a.set(
      THREE.MathUtils.lerp(FEED_END - 3, DISCHARGE_END + 2, u),
      DRYER.y + THREE.MathUtils.lerp(1.1, -0.9, u),
      THREE.MathUtils.lerp(0.6, 0, u)
    );
  } else {
    const u = (tc - 0.75) / 0.25;
    _a.set(
      THREE.MathUtils.lerp(DISCHARGE_END + 2, AXIS.x1, u),
      THREE.MathUtils.lerp(DRYER.y - 0.9, AXIS.y, Math.min(1, u * 2.6)),
      THREE.MathUtils.lerp(0, 0, u)
    );
  }

  if (straighten <= 0.001) return out.copy(_a);

  // --- straightened route: a pure time axis --------------------------------
  // The whole path collapses onto y = AXIS.y, z = 0, x spanning the axis, so
  // upstream history compresses to the left of x0 and stays off-screen.
  const xs = THREE.MathUtils.lerp(AXIS.x0 - 120, AXIS.x1, tc);
  _b.set(xs, AXIS.y, 0);

  return out.lerpVectors(_a, _b, THREE.MathUtils.clamp(straighten, 0, 1));
}

/** Map a fraction of the 12-hour window to a world x on the time axis. */
export function timeToX(frac) {
  return AXIS.x0 + THREE.MathUtils.clamp(frac, 0, 1) * AXIS_LEN;
}

/** Map an ISO timestamp inside the gap window to world x. */
export function makeTimeMapper(startIso, endIso) {
  const t0 = Date.parse(startIso.replace(' ', 'T'));
  const t1 = Date.parse(endIso.replace(' ', 'T'));
  const span = t1 - t0 || 1;
  return (iso) => timeToX((Date.parse(iso.replace(' ', 'T')) - t0) / span);
}

/**
 * Map a moisture value to world y above the axis.
 * The window is deliberately tight so 0.005 % moisture of movement is visible —
 * the domain comes from the data, not from a round number.
 */
export function makeMoistureMapper(lo, hi, height = 9) {
  const span = hi - lo || 1;
  return (m) => AXIS.y + 1.4 + ((m - lo) / span) * height;
}

/** Architecture stack layers, built by arriving packets (scene 07). */
export const ARCH_LAYERS = [
  { id: 'process', label: 'PROCESS', sub: '1,589,760 rows · 5 s replay' },
  { id: 'sense', label: 'SENSE', sub: '9 process variables' },
  { id: 'align', label: 'ALIGN', sub: 'residence time · previous lab' },
  { id: 'features', label: 'FEATURES', sub: '16 quality · 15 process' },
  { id: 'intel', label: 'INTELLIGENCE', sub: 'Ridge · One-Class SVM' },
  { id: 'persist', label: 'PERSIST', sub: 'PostgreSQL · 3 tables · 5 views' },
  { id: 'supervise', label: 'SUPERVISE', sub: 'Power BI · DirectQuery' },
  { id: 'operator', label: 'OPERATOR', sub: 'advisory decision' },
];

export const ARCH_ORIGIN = new THREE.Vector3(-6, 2, -44);
export const ARCH_STEP = 3.5;

/**
 * The residence-time lane (scene 07, beats ALIGN 1 and 2).
 *
 * A three-hour window laid out along +X, in front of the architecture stack it
 * explains. Three hours rather than a tighter window because the second beat
 * has to show TWO temporal relationships at once and both must be on the same
 * honest scale: the 24.5-minute process shift, and the two-hour-old previous
 * laboratory sample that also enters the feature vector. Drawing the shift
 * bigger by cropping the window would have made the geometry lie about the
 * proportion between them, which is the one thing this beat exists to get
 * right.
 *
 *   hours          the lane's own clock, so every offset below is a ratio
 *   sampleAt       where the laboratory sample lands — 2 h 35 into the window
 *   shiftFraction  24.5 min of residence time as a fraction of the lane
 *   priorAt        the previous laboratory sample, two hours before the current
 *                  one, which supplies the density and product-temperature
 *                  features and is what makes the vector causal
 *
 * Residence time is a MEASURED variable, not a constant: 24.54 min mean over
 * the canonical 1,589,760 rows, 24.15 to 24.89 min range, 24.44 min mean over
 * the twelve-hour window this film replays. The runtime shifts by the value at
 * each timestamp. 24.5 is the number said out loud; the spread is on screen
 * underneath it so the claim is not rounder than the data.
 */
export const RESIDENCE = {
  // BEHIND the dryer and ABOVE the ground, at the architecture stack's own
  // depth. The first placement put the lane at z = -22 with the camera at
  // z = +9, which meant the beat was shot straight through the dryer shell:
  // a translucent 22-unit cylinder lay across the middle of the frame and the
  // right-hand end of the lane was cropped by the frame edge. The lane now
  // sits in clear air in front of the stack it explains, with the camera on
  // the far side of the machine so nothing is between the lens and the idea.
  origin: new THREE.Vector3(-6, 16, -30),
  length: 15,
  hours: 3,
  railGap: 3.4,
  sampleAt: 155 / 180,
  shiftFraction: 24.5 / 180,
  priorAt: (155 - 120) / 180,
};

/**
 * The runtime, as a path the camera travels rather than a stack it looks at.
 *
 * Scene 07 already owns the stacked-layer metaphor for the *architecture*.
 * Repeating it here made the two scenes read as the same idea, so the runtime
 * is now five spatial checkpoints laid out in DATA-FLOW ORDER — replay first,
 * dashboard last — climbing toward the operator. The camera enters at the deep
 * end and travels forward with the data, so the direction the viewer moves is
 * the direction the data moves.
 */
export const RUNTIME_NODES = [
  { id: 'replay', label: 'REPLAY', sub: 'held-out TEST - 5 s tick', pos: [74, -6, -18] },
  { id: 'py', label: 'PYTHON INFERENCE', sub: 'realtime_service.py - 9 ms average', pos: [74, -3, -10] },
  { id: 'pg', label: 'POSTGRESQL', sub: 'three tables, written idempotently', pos: [74, 0, -2] },
  { id: 'sql', label: 'FIVE SEMANTIC VIEWS', sub: 'five views - one contract', pos: [74, 3, 6] },
  { id: 'powerbi', label: 'POWER BI', sub: 'DirectQuery - reads views only', pos: [74, 6, 14] },
];

/**
 * Why these coordinates.
 *
 * The route is a straight 34-unit run climbing toward the report, and the
 * camera watches it from ACROSS rather than from along. Riding the centre
 * line put every checkpoint on the same screen position, so the five boxes
 * stacked into one silhouette and four of the five labels were hidden behind
 * the box in front. Viewed from the side at ~40 units, the checkpoints land
 * at roughly 36 / 49 / 61 / 72 / 81 % of frame width — evenly spaced, clear of
 * the copy column, reading left to right in the direction the data travels.
 *
 * The run was also 54 units long, which could not fit beside the copy column
 * at any legible focal length. Thirty-four fits with margin at ~30 px labels.
 */

/**
 * Where the runtime hands off to the person. Nothing continues past this.
 *
 * Placed BELOW and in front of the dashboard plane (which spans y 2.7 - 17.3
 * at z = 26), not on it. At its old position the terminal and its label were
 * drawn straight across the dashboard's own trend chart — the same "written
 * on it rather than behind it" failure the runtime reveal was rebuilt to fix.
 * Below the screen it also reads correctly: the report above, the person who
 * acts on it underneath.
 */
export const OPERATOR_NODE = { pos: [76, -6, 32], label: 'OPERATOR', sub: 'advisory decision' };

/**
 * The handover (scene 10, beat BECOME) — artifact, service, screen.
 *
 * Laid out in the scene's OWN camera frame rather than beside it. Scene 10's
 * pose is (66, 10, 65) looking at (66, 10, 26) on a 38 mm-equivalent lens, and
 * the report plane already occupies screen x 44 % to 98 % while the copy column
 * owns 0 % to 41 %. There is no empty frame left to put a third thing in.
 *
 * So the handover is placed IN FRONT of the report, in the corridor between the
 * lens and the plane, and it is SEQUENCED rather than composed around: while the
 * artifact and the service are lit the report is still at zero, and by the time
 * the report is legible the handover has receded to a trail. Nothing is ever
 * asked to share the frame with the deliverable.
 *
 *   card  z = 47, 18 units from the lens — the artifact, read at ~78 px type
 *   node  z = 38, 27 units out — the service, on the way to the screen
 *   sink  the report plane's own surface, where inference lands
 *
 * The x values put both objects at roughly 60 % and 68 % of frame width: clear
 * of the copy column, inside the region the report will later claim.
 */
export const HANDOVER = {
  card: { pos: [72, 9.4, 42], w: 8.0, h: 4.8 },
  node: { pos: [73.5, 9.1, 34] },
  sink: [72.5, 8.4, 26.4],
};

/**
 * Why those depths and not nearer ones.
 *
 * The beat ARRIVES: it opens nine units further back and settles onto the
 * scene's own pose, so everything in the corridor grows through the shot. An
 * object placed for the frame it starts in is a different size by the time the
 * shot lands. Checked at four points along the move with
 * scripts/_probe_handover.mjs: at z = 42 the artifact holds between 44 % and
 * 93 % of frame width for the whole of its visible life — clear of the copy
 * column at 41 % and clear of the frame edge — where the first placement, ten
 * units nearer, was already past both by the time it folded.
 */


/** The operational loop (scene 12). Sits over the middle of the system. */
export const RING_CENTRE = [24, 28, 0];
export const RING_RADIUS = 11;
export const LOOP_NODES = [
  'PROCESS', 'SENSE', 'PREDICT', 'DETECT', 'SUPERVISE', 'DECIDE',
];

/**
 * Roadmap stages (scene 13). `built` drives solid vs outlined.
 *
 * `label` is deliberately SHORT. At 11 stages on one rail, a label long enough
 * to wrap to four or five lines collides with its neighbours, with the band
 * headers and with the DOM copy — which is what happened when the type was
 * finally raised to a projector-legible size. The full inventory is in the
 * scene's own note, where it has a scrim and the complete font; the world
 * carries the name only.
 *
 * ROADMAP_STEP is 6.0 so that a two-line label at 0.95 world units has a
 * gutter on both sides. Eleven stages therefore span 60 units, which is why
 * scene 13 travels along the rail rather than trying to frame all of it at
 * once — at one framing this content cannot exceed ~16 px on a 1080 line.
 */
export const ROADMAP_ORIGIN = [-18, 21, 0];
export const ROADMAP_STEP = 6.0;
export const ROADMAP = [
  { label: 'Canonical dataset', built: true },
  { label: 'Causal alignment', built: true },
  { label: 'Both models & diagnosis', built: true },
  { label: 'PostgreSQL & views', built: true },
  { label: 'Power BI & 5 s runtime', built: true },
  { label: 'Plant historian data', built: false },
  { label: 'Data-quality validation', built: false },
  { label: 'Shadow-mode operation', built: false },
  { label: 'Operator feedback', built: false },
  { label: 'Governed advisory rollout', built: false },
  { label: 'Assisted setpoint guidance', built: false, conditional: true },
  { label: 'Closed-loop regulation', built: false, conditional: true },
];

/**
 * The evidence gallery.
 *
 * Four editorial panels are no longer stacked on one vertical wall — that made
 * scene 09 a scroll. They now form a corridor that begins beside the model
 * region and ends in front of the operator's screen, so walking the evidence
 * is literally walking from the model to the dashboard.
 */
export const EVIDENCE_PANELS = [
  { id: 'moisture', pos: [30, 14, -62], yaw: 0.30 },
  { id: 'candidates', pos: [46, 12, -44], yaw: 0.24 },
  { id: 'anomaly', pos: [60, 8, -24], yaw: 0.16 },
  { id: 'limits', pos: [70, 4, -4], yaw: 0.08 },
];

/**
 * Power BI overview capture: the trend-chart plot rectangle, in UV.
 * Measured from the real 1600×900 export, not estimated — this is what makes
 * the scene 09 → 10 chart-becomes-visual registration honest.
 */
export const PBI_PLANE = { w: 26, h: 14.625 };
export const PBI_TREND_UV = { u0: 0.0794, u1: 0.6288, v0: 0.400, v1: 0.610 };


/**
 * The regions the scene-10 walkthrough points at, in UV of the 1600x900
 * report canvas.
 *
 * These are read straight off the report layout's own absolute coordinates
 * (tools/render_dashboard_preview.py) rather than eyeballed, so a box can
 * never drift off the thing it is naming. Only five regions are called out:
 * the walkthrough exists to name what the operator reads first, not to
 * inventory everything the page contains.
 */
const PBI_PX = (x, y, w, h) => ({
  u: [x / 1600, (x + w) / 1600],
  v: [y / 900, (y + h) / 900],
});

export const PBI_HIGHLIGHTS = [
  { id: 'predicted', label: 'PREDICTED FINAL MOISTURE', ...PBI_PX(110, 86, 234, 118) },
  { id: 'lab', label: 'LATEST LABORATORY RESULT - THE REFERENCE', ...PBI_PX(358, 86, 234, 118) },
  { id: 'state', label: 'ANOMALY SCORE - STATUS - SEVERITY', ...PBI_PX(854, 86, 730, 118) },
  { id: 'trend', label: 'MOISTURE AND RISK TREND - ROLLING 8 h', ...PBI_PX(110, 218, 940, 254) },
  { id: 'diagnosis', label: 'DIAGNOSIS AND OPERATOR GUIDANCE - ADVISORY', ...PBI_PX(1064, 218, 520, 666) },
];

/**
 * Lens language.
 *
 * Focal length carries meaning here, so it is declared once and referenced by
 * name from the scene table. A scene changes lens at most once, and never at
 * the same time as a large translation — the two together read as a zoom
 * rather than as a move.
 *
 *   ESTABLISH  the hall, the plant, the return    — wide but disciplined
 *   TRAVEL     moving along the material or time  — slightly wider, stable
 *   EQUIPMENT  a machine understood in the round
 *   INTERIOR   inside the shell
 *   SYSTEM     architecture, manifold, runtime
 *   EDITORIAL  charts, roadmap — fixed, never changes inside the act
 *   MATERIAL   the product itself
 */
export const LENS = {
  ESTABLISH: 40,
  TRAVEL: 46,
  EQUIPMENT: 34,
  INTERIOR: 38,
  SYSTEM: 44,
  EDITORIAL: 38,
  // The roadmap only: a placement shot that has to hold a 72-unit rail. It is
  // the one wide editorial lens, and scene 13 uses it for BOTH beats so the
  // travel along the rail is a pure truck with no focal change riding on it.
  EDITORIAL_WIDE: 36,
  MATERIAL: 30,
};

export function pbiRectToLocal() {
  const { w, h } = PBI_PLANE;
  const { u0, u1, v0, v1 } = PBI_TREND_UV;
  return {
    x0: -w / 2 + u0 * w,
    x1: -w / 2 + u1 * w,
    y0: h / 2 - v1 * h,
    y1: h / 2 - v0 * h,
  };
}
