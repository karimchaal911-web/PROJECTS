/**
 * Device probe and safe-mode budgets.
 * Safe mode is a visual downgrade, never a narrative one: every scene, beat,
 * number and transition still happens. See THREEJS_SCENE_PLAN.md §8.
 */

export const BUDGET = {
  standard: {
    dpr: 1.75,
    shadows: true,
    shadowMap: 2048,
    granules: 2600,
    dust: 700,
    manifold: 2400,
    packets: 900,
    antialias: true,
    idleDrift: true,
    glow: true,
  },
  safe: {
    dpr: 1.0,
    shadows: false,
    shadowMap: 512,
    granules: 700,
    dust: 0,
    manifold: 900,
    packets: 260,
    antialias: false,
    idleDrift: false,
    glow: false,
  },
};

export function budget(safeMode) {
  return safeMode ? BUDGET.safe : BUDGET.standard;
}

export function prefersReducedMotion() {
  if (typeof window === 'undefined' || !window.matchMedia) return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Watches frame time and reports a sustained collapse so the app can auto-enter
 * safe mode. Only fires once.
 *
 * Wired into the render loop by <PerfGuard> in World.jsx. It was written,
 * exported and documented but never called, which meant the only degrade path
 * in the whole application was a boot-time heuristic requiring BOTH <= 4 cores
 * AND <= 4 GB memory. A typical 8-core laptop with weak integrated graphics,
 * or any machine that throttles ten minutes into a defence, would never
 * degrade no matter how badly it was running.
 */
export function makeFpsWatch(onSlow, { threshold = 30, frames = 90 } = {}) {
  let bad = 0;
  let fired = false;
  let last = performance.now();
  return () => {
    if (fired) return;
    const now = performance.now();
    const dt = now - last;
    last = now;
    if (dt > 1000 / threshold) {
      bad += 1;
      if (bad >= frames) {
        fired = true;
        onSlow();
      }
    } else {
      bad = Math.max(0, bad - 1);
    }
  };
}

/** Cheap capability read used at boot to pick a starting budget. */
export function probeDevice() {
  const reduced = prefersReducedMotion();
  const cores = navigator.hardwareConcurrency ?? 4;
  const mem = navigator.deviceMemory ?? 4;
  const smallGpu = cores <= 4 && mem <= 4;
  return { reduced, cores, mem, suggestSafe: reduced || smallGpu };
}
