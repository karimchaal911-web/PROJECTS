import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';
import { useShow } from '../state/useShow.js';
import { SCENES, STEPS } from '../state/scenes.js';
import { MODES } from '../lib/palette.js';
import { channel, tweenChannels } from './usePresence.js';
import { buildTransition } from './transitions.js';
import { budget, prefersReducedMotion } from '../lib/perf.js';

/**
 * The camera rig and the show's single clock.
 *
 * Every transition is one GSAP timeline. Camera, layer presence, material
 * crossfades, light changes and in-world reveals are all children of it, so
 * they can never desynchronise — there is no independent setTimeout anywhere in
 * the application.
 *
 * The presenter can interrupt at any moment: the active timeline is killed, the
 * world tweens (never cuts) to the settled state of the scene being left, and
 * the next transition starts from there.
 */

const TRANSITION = 2.2;

// GSAP's default lag smoothing clamps large frame deltas, which makes a 2.2 s
// transition take 20 s on a machine that is dropping frames. For a presentation
// the wall clock is what matters: the presenter's pacing must not depend on the
// projector laptop's GPU. Disabling it means a hitch skips frames instead of
// stretching the scene.
gsap.ticker.lagSmoothing(0);

export default function Rig() {
  const { camera } = useThree();
  const step = useShow((s) => s.step);
  const started = useShow((s) => s.started);
  const safeMode = useShow((s) => s.safeMode);
  const setTransitioning = useShow((s) => s.setTransitioning);

  const target = useMemo(() => new THREE.Vector3(-4, 5.4, 2), []);
  const pos = useMemo(() => new THREE.Vector3(-34, 2.4, 26), []);
  const tl = useRef(null);
  const prevStep = useRef(-1);
  const idle = useRef({ t: Math.random() * 100 });
  const drift = useMemo(() => new THREE.Vector3(), []);
  const reduced = useMemo(() => prefersReducedMotion(), []);

  // Camera pose lives in plain objects so GSAP can tween it without React.
  const state = useRef({
    px: -34, py: 2.4, pz: 26,
    tx: -4, ty: 5.4, tz: 2,
    fov: 38,
  });

  useEffect(() => {
    if (!started) return;
    const { scene: sceneIndex, beat } = STEPS[step];
    const scene = SCENES[sceneIndex];
    const back = step < prevStep.current;
    const first = prevStep.current === -1;
    const dur = first ? 0.01 : (back ? TRANSITION * 0.7 : TRANSITION);

    // Interrupt: kill the running timeline and settle before moving on.
    if (tl.current) {
      tl.current.kill();
      tl.current = null;
    }

    setTransitioning(true);
    const timeline = gsap.timeline({
      defaults: { ease: 'power2.inOut' },
      onComplete: () => setTransitioning(false),
    });
    tl.current = timeline;

    // --- camera ------------------------------------------------------------
    // A beat may override the scene pose. Scenes that walk a wall of evidence
    // or travel down the time axis need the camera to move between beats, not
    // only between scenes.
    const cam = scene.beats?.[beat]?.camera ?? scene.camera;
    timeline.to(state.current, {
      px: cam.pos[0], py: cam.pos[1], pz: cam.pos[2],
      tx: cam.target[0], ty: cam.target[1], tz: cam.target[2],
      fov: cam.fov,
      duration: dur,
      ease: reduced ? 'power1.inOut' : 'power2.inOut',
    }, 0);

    // --- lighting mode -----------------------------------------------------
    const mode = MODES[scene.mode] ?? MODES.dark;
    tweenChannels(timeline, {
      lightAmbient: mode.ambient,
      lightKey: mode.key,
      lightRim: mode.rim,
      exposure: mode.exposure,
      fogDensity: mode.fogDensity,
      fogMix: scene.mode === 'editorial' ? 1 : 0,
    }, { duration: reduced ? 0.4 : 1.4, ease: 'power1.inOut', position: 0 });

    // --- layer presence ----------------------------------------------------
    // A beat may raise or lower individual layers on top of the scene's own
    // state — the dryer's PHYSICS beat brings the internals up, the DATA beat
    // brings the telemetry up, without either becoming a separate scene.
    const layers = { ...scene.layers, ...(scene.beats?.[beat]?.layers ?? {}) };
    tweenChannels(timeline, layers, {
      duration: reduced ? 0.4 : dur,
      ease: 'power2.inOut',
      position: 0,
    });

    // --- scene-specific choreography --------------------------------------
    buildTransition(timeline, {
      scene, sceneIndex, beat, back, first,
      duration: dur, reduced, safeMode,
      camState: state.current,
    });

    prevStep.current = step;
    return () => { /* timeline is killed on the next change, not on unmount */ };
  }, [step, started, safeMode, reduced, setTransitioning]);

  useFrame((_, dt) => {
    const s = state.current;
    idle.current.t += dt;

    // The camera is never perfectly still. ±0.12 u over 24 s reads as a held
    // shot rather than a locked-off render.
    const b = budget(safeMode);
    if (b.idleDrift && !reduced) {
      const t = idle.current.t;
      drift.set(
        Math.sin(t * 0.262) * 0.12,
        Math.sin(t * 0.191 + 1.7) * 0.08,
        Math.cos(t * 0.223 + 0.4) * 0.12
      );
    } else {
      drift.set(0, 0, 0);
    }

    pos.set(s.px, s.py, s.pz).add(drift);
    target.set(s.tx, s.ty, s.tz);
    camera.position.copy(pos);
    camera.lookAt(target);
    if (typeof window !== 'undefined') {
      window.__CAM__ = { pos: pos.toArray().map((v) => +v.toFixed(2)), target: target.toArray(), fov: +camera.fov.toFixed(1) };
    }
    if (Math.abs(camera.fov - s.fov) > 0.01) {
      camera.fov = s.fov;
      camera.updateProjectionMatrix();
    }
  });

  return null;
}

/** Exposed so the recovery path can hard-set a pose without a tween. */
export function poseChannel() {
  return channel('__pose');
}
