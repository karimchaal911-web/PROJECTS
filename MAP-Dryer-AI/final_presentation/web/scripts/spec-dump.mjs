/**
 * Emits the motion table straight from the scene table, so MOTION_SPEC.md is
 * derived from the source of truth rather than transcribed from it.
 *
 *   node scripts/spec-dump.mjs > ../design/_motion_table.md
 */
import { SCENES, STEPS, TIERS, tierFor, TOTAL_SECONDS } from '../src/state/scenes.js';
import { LENS } from '../src/lib/curves.js';

// Several roles deliberately share a focal length (EDITORIAL and INTERIOR are
// both 38 deg). Report the role the SCENE asked for, not the first match.
const ROLE = {
  awakening: 'ESTABLISH', material: 'MATERIAL', chain: 'TRAVEL', dryer: 'EQUIPMENT',
  gap: 'TRAVEL', response: 'TRAVEL', digital: 'SYSTEM', pathways: 'SYSTEM',
  evidence: 'EDITORIAL', supervision: 'EDITORIAL', through: 'SYSTEM',
  value: 'EDITORIAL', roadmap: 'EDITORIAL_WIDE', return: 'ESTABLISH',
};
const lensName = (fov, sceneId, beatId) => {
  if (sceneId === 'dryer' && beatId === 'physics') return 'INTERIOR';
  if (sceneId === 'through' && beatId === 'loop') return 'TRAVEL';
  const named = ROLE[sceneId];
  if (named && LENS[named] === fov) return named;
  return Object.entries(LENS).find(([, v]) => v === fov)?.[0] ?? `${fov}`;
};

const poseOf = (s, b) => {
  const sc = SCENES[s];
  return sc.beats?.[b]?.camera ?? sc.camera;
};
const d3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

let prev = null;
const rows = [];
for (let i = 0; i < STEPS.length; i += 1) {
  const { scene, beat } = STEPS[i];
  const sc = SCENES[scene];
  const bt = sc.beats?.[beat];
  const cam = poseOf(scene, beat);
  const tierKey = bt?.tier ?? sc.tier ?? 'standard';
  const dur = tierFor(scene, beat);
  const dp = prev ? d3(cam.pos, prev.pos) : 0;
  const dt = prev ? d3(cam.target, prev.target) : 0;
  const dfov = prev ? cam.fov - prev.fov : 0;
  const r = d3(cam.pos, cam.target);
  rows.push({
    i,
    id: `${sc.n}${bt ? String.fromCharCode(97 + beat) : ''}`,
    label: bt?.label ?? sc.title,
    mode: sc.mode,
    tier: tierKey,
    dur,
    dp: +dp.toFixed(1),
    dt: +dt.toFixed(1),
    dfov: +dfov.toFixed(0),
    r: +r.toFixed(0),
    lens: lensName(cam.fov, sc.id, bt?.id),
    fov: cam.fov,
  });
  prev = cam;
}

console.log('| # | Step | Beat | Mode | Tier | s | Δpos | Δtgt | ΔFOV | r | Lens |');
console.log('|---|---|---|---|---|---|---|---|---|---|---|');
for (const r of rows) {
  console.log(`| ${r.i} | **${r.id}** | ${r.label} | ${r.mode} | \`${r.tier}\` | ${r.dur} | ${r.dp} | ${r.dt} | ${r.dfov >= 0 ? '+' : ''}${r.dfov} | ${r.r} | ${r.lens} ${r.fov}° |`);
}
console.error(`steps=${rows.length} scenes=${SCENES.length} declared=${TOTAL_SECONDS}s tiers=${JSON.stringify(TIERS)}`);
const budget = rows.slice(1).reduce((a, b) => a + b.dur, 0);
console.error(`transition budget = ${budget.toFixed(1)} s over ${rows.length - 1} transitions (${((budget / TOTAL_SECONDS) * 100).toFixed(1)} % of runtime)`);
const byTier = {};
for (const r of rows.slice(1)) byTier[r.tier] = (byTier[r.tier] ?? 0) + 1;
console.error('tier use:', JSON.stringify(byTier));
const jumps = rows.slice(1).filter((r) => r.dp > 60).map((r) => `${r.id}:${r.dp}`);
console.error('moves > 60 u:', jumps.join(', ') || 'none');
const micro = rows.slice(1).filter((r) => r.dp < 6).map((r) => `${r.id}:${r.dp}`);
console.error('moves < 6 u:', micro.join(', ') || 'none');
