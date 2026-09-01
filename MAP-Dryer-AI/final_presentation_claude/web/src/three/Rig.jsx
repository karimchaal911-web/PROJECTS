import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';
import { useShow } from '../state/useShow.js';
import { SCENES, STEPS, tierFor, easeFor } from '../state/scenes.js';
import { MODES } from '../lib/palette.js';
import { channel, tweenChannels, setChannels } from './usePresence.js';
import { buildTransition, BASELINE, sceneChannelState } from './transitions.js';
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

// Duration now comes from the scene table's transition tier, not from one
// constant. A beat that refines an idea and a beat that changes act cannot
// take the same time without the film reading as templated.

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
  const epoch = useShow((s) => s.renderEpoch);

  const target = useMemo(() => new THREE.Vector3(-4, 5.4, 2), []);
  const pos = useMemo(() => new THREE.Vector3(-34, 2.4, 26), []);
  const tl = useRef(null);
  const prevStep = useRef(-1);
  const prevEpoch = useRef(0);
  const idle = useRef({ t: Math.random() * 100 });
  const editorial = useRef(false);
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
    // A jump of more than one step is random access (number keys), not a
    // narrative move: settle the world into the destination's full state
    // rather than tweening a half-dressed one into place.
    const jumped = !first && Math.abs(step - prevStep.current) > 1;
    // A restored WebGL context is not a narrative move. The show has not
    // advanced, so nothing may animate: the world is put back into the settled
    // state of the step the presenter is ALREADY on, in one frame, and the
    // sentence being spoken over it is not interrupted.
    const restored = epoch !== prevEpoch.current;
    prevEpoch.current = epoch;
    const tier = tierFor(sceneIndex, beat);
    const dur = (first || restored) ? 0.01 : (jumped ? 0.9 : (back ? tier * 0.72 : tier));

    if (first || jumped || restored) {
      // Every channel the show uses, restored to this step's value. Without
      // this, jumping straight to scene 11 left sensors unrevealed, packets
      // frozen and the flow path unstraightened.
      setChannels({ ...BASELINE, ...sceneChannelState(sceneIndex, beat) });
    }

    // Interrupt: kill the running timeline and settle before moving on.
    if (tl.current) {
      tl.current.kill();
      tl.current = null;
    }

    // No `transitioning` flag is published. The overlay does not need to be
    // told when the world settles: it derives its own copy timing from the
    // step's transition tier, which is deterministic and survives a dropped
    // frame. A store field written every transition and read by nobody is
    // just a re-render nobody asked for.
    const timeline = gsap.timeline({ defaults: { ease: 'power2.inOut' } });
    tl.current = timeline;

    // --- camera ------------------------------------------------------------
    // A beat may override the scene pose. Scenes that walk a wall of evidence
    // or travel down the time axis need the camera to move between beats, not
    // only between scenes.
    const cam = scene.beats?.[beat]?.camera ?? scene.camera;
    // The curve comes from the tier, not from one constant — see TIER_EASE.
    // Stepping BACK is a correction, not a move the audience is being shown,
    // so it always takes the crisp curve regardless of what it is undoing.
    const camEase = reduced ? 'power1.inOut' : (back ? 'power2.out' : easeFor(sceneIndex, beat));
    // A restored context must not MOVE the camera. `state.current` is plain JS
    // and survived the loss intact, including however far a scene's own slow
    // drift had travelled — scene 04's eight-second push across the machine,
    // scene 05's truck down the time axis. Re-tweening to the beat's settled
    // pose here snapped the shot back to where the drift STARTED, which is the
    // one visible restart the recovery path was supposed to avoid. The pose is
    // already correct; the only thing that has to come back is the GPU.
    if (!restored) {
      timeline.to(state.current, {
        px: cam.pos[0], py: cam.pos[1], pz: cam.pos[2],
        tx: cam.target[0], ty: cam.target[1], tz: cam.target[2],
        fov: cam.fov,
        duration: dur,
        ease: camEase,
      }, 0);
    }

    // --- lighting mode -----------------------------------------------------
    const mode = MODES[scene.mode] ?? MODES.dark;
    editorial.current = scene.mode === 'editorial';
    tweenChannels(timeline, {
      lightAmbient: mode.ambient,
      lightKey: mode.key,
      lightRim: mode.rim,
      exposure: mode.exposure,
      fogDensity: mode.fogDensity,
      fogMix: scene.mode === 'editorial' ? 1 : 0,
      // Light resolves in the first part of the move so a mode change and a
      // large translation are never both still happening at the end of it.
    }, { duration: reduced ? 0.4 : Math.min(1.4, dur * 0.55), ease: 'power1.inOut', position: 0 });

    // --- layer presence ----------------------------------------------------
    // A beat may raise or lower individual layers on top of the scene's own
    // state — the dryer's PHYSICS beat brings the internals up, the DATA beat
    // brings the telemetry up, without either becoming a separate scene.
    const layers = { ...scene.layers, ...(scene.beats?.[beat]?.layers ?? {}) };

    // On an ACT-scale move the outgoing world LEAVES BEFORE the incoming world
    // ARRIVES. Cross-fading both over the full duration put two unrelated
    // scenes on screen at once at the midpoint — captured mid-transition on
    // 08c -> 09a, the manifold cloud, its support vectors and its provenance
    // captions were all still legible across the incoming evidence panel. They
    // are 90 units apart in the world; superimposing them reads as a
    // double-exposure, not as a dissolve.
    //
    // Beat-scale moves keep the simple simultaneous tween: there the camera
    // barely travels, both states belong to the same place, and a dip would
    // read as a flicker.
    if (reduced || dur < 3.0) {
      tweenChannels(timeline, layers, {
        duration: reduced ? 0.4 : dur,
        ease: 'power2.inOut',
        position: 0,
      });
    } else {
      const falling = {};
      const rising = {};
      for (const [key, value] of Object.entries(layers)) {
        if (value < channel(key).current - 0.02) falling[key] = value;
        else rising[key] = value;
      }
      tweenChannels(timeline, falling,
        { duration: dur * 0.46, ease: 'power2.in', position: 0 });
      tweenChannels(timeline, rising,
        { duration: dur * 0.58, ease: 'power2.out', position: dur * 0.42 });
    }

    // --- scene-specific choreography --------------------------------------
    buildTransition(timeline, {
      scene, sceneIndex, beat, back, first, restored,
      duration: dur, reduced, safeMode,
      camState: state.current,
      // The pose this step is travelling TO. A scene that wants to arrive at
      // its own frame rather than cut to it has to state the from-values in
      // terms of the destination, not in terms of `camState` — which, at the
      // moment the timeline is built, still holds the PREVIOUS step's pose.
      // Reading it there silently anchored two of the film's arrivals to the
      // scene before them: the opening settle finished four units off the
      // pose scene 14 rhymes with, and the scene-10 arrival finished nineteen
      // units short of the report.
      camPose: cam,
    });

    prevStep.current = step;
    return () => { /* timeline is killed on the next change, not on unmount */ };
  }, [step, started, safeMode, reduced, epoch]);

  useFrame((_, dt) => {
    const s = state.current;
    idle.current.t += dt;

    // The camera is never perfectly still. ±0.12 u over 24 s reads as a held
    // shot rather than a locked-off render.
    const b = budget(safeMode);
    // Editorial scenes are typography and charts. Breathing the camera there
    // makes static text swim; it belongs to the industrial world only.
    if (b.idleDrift && !reduced && !editorial.current) {
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
