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
export const STATIONS = [
  { id: 'acid', label: 'PHOSPHORIC-ACID\nPRETREATMENT', t: 0.02, r: 3.0, h: 9 },
  { id: 'vapor', label: 'AMMONIA\nVAPORIZATION', t: 0.16, r: 2.4, h: 11 },
  { id: 'neutral', label: 'NEUTRALIZATION', t: 0.33, r: 3.4, h: 10 },
  { id: 'buffer', label: 'BUFFER /\nSTABILIZATION', t: 0.48, r: 3.0, h: 8 },
  { id: 'crystal', label: 'CONCENTRATION &\nCRYSTALLIZATION', t: 0.64, r: 3.6, h: 13 },
  { id: 'centri', label: 'CENTRIFUGATION', t: 0.80, r: 2.6, h: 7 },
  { id: 'dry', label: 'DRYING', t: 0.96, r: 0, h: 0 },
];

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
 * The window is deliberately tight so 0.005 % H₂O of movement is visible —
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
 * Runtime slabs behind the dashboard (scene 11).
 *
 * A staircase, not a stack of parallel planes: each layer steps back, down and
 * across so an oblique camera can see all five at once. Five coplanar slabs
 * viewed head-on would simply occlude each other.
 */
export const RUNTIME_SLABS = [
  { id: 'powerbi', label: 'POWER BI', sub: 'DirectQuery · reads views only', z: 18, y: 7, x: 2 },
  { id: 'sql', label: 'SQL — FIVE SEMANTIC VIEWS', sub: 'dashboard · contributors · labs · events · trends', z: 4, y: 2, x: 0 },
  { id: 'pg', label: 'POSTGRESQL', sub: 'dryer_map · dryer_model_outputs · dryer_abnormal_variables', z: -10, y: -3, x: -2 },
  { id: 'py', label: 'PYTHON INFERENCE', sub: 'realtime_service.py · 9 ms average · 47 ms maximum', z: -24, y: -8, x: -4 },
  { id: 'replay', label: 'REPLAY', sub: 'held-out TEST · 237,600 rows · Δt = 5 s', z: -38, y: -13, x: -6 },
];

/** The operational loop (scene 12). */
export const LOOP_NODES = [
  'PROCESS', 'SENSE', 'PREDICT', 'DETECT', 'SUPERVISE', 'DECIDE',
];

/** Roadmap stages (scene 13). `built` drives solid vs outlined. */
export const ROADMAP = [
  { label: 'Canonical dataset & causal alignment', built: true },
  { label: 'Moisture soft sensor · anomaly detector · diagnosis', built: true },
  { label: 'PostgreSQL persistence & semantic views', built: true },
  { label: 'Power BI operations dashboard · 5 s replay runtime', built: true },
  { label: 'Representative plant historian data', built: false },
  { label: 'Data-quality validation', built: false },
  { label: 'Shadow-mode operation', built: false },
  { label: 'Operator feedback loop', built: false },
  { label: 'Governed advisory deployment', built: false },
  { label: 'Assisted setpoint guidance', built: false, conditional: true },
  { label: 'Closed-loop regulation', built: false, conditional: true },
];

/**
 * Power BI overview capture: the trend-chart plot rectangle, in UV.
 * Measured from the real 1600×900 export, not estimated — this is what makes
 * the scene 09 → 10 chart-becomes-visual registration honest.
 */
export const PBI_PLANE = { w: 26, h: 14.625 };
export const PBI_TREND_UV = { u0: 0.0794, u1: 0.6288, v0: 0.400, v1: 0.610 };

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
