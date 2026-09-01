import { create } from 'zustand';
import { SCENES, STEPS } from './scenes.js';

/**
 * Show state. Deliberately small: the three-side world reads `step` through
 * refs and drives itself imperatively, so advancing a scene does not re-render
 * the scene graph. Only the DOM overlay subscribes to the copy fields.
 */
export const useShow = create((set, get) => ({
  step: 0,
  safeMode: false,
  hud: false,
  help: false,
  started: false,
  startedAt: null,

  /**
   * Incremented once every time the WebGL context is restored.
   *
   * A lost context takes every GPU-side resource with it, but NOT the show:
   * `step`, the presence channels and the camera pose all live in plain JS and
   * survive untouched. What does not survive is anything whose CONTENT was
   * produced by rendering into a target — the PMREM studio environment and the
   * post-processing buffers — because re-uploading a render target re-allocates
   * it empty. Without a rebuild the film comes back with every metal surface
   * black and no ambient occlusion.
   *
   * Layers that own such a resource take this as an effect dependency and
   * rebuild. The Rig takes it too, and re-settles the CURRENT step rather than
   * restarting the show. Nothing here is a second state system: the pose and
   * the channel values come from the same scene table the presenter's arrow
   * key uses.
   */
  renderEpoch: 0,
  contextRestored: () => set((s) => ({ renderEpoch: s.renderEpoch + 1 })),

  get scene() {
    return SCENES[STEPS[get().step].scene];
  },

  begin: () => set({ started: true, startedAt: Date.now() }),

  next: () => set((s) => ({ step: Math.min(s.step + 1, STEPS.length - 1) })),
  prev: () => set((s) => ({ step: Math.max(s.step - 1, 0) })),
  goScene: (i) => {
    const clamped = Math.max(0, Math.min(i, SCENES.length - 1));
    const idx = STEPS.findIndex((s) => s.scene === clamped);
    set({ step: idx < 0 ? 0 : idx });
  },

  toggleSafe: () => set((s) => ({ safeMode: !s.safeMode })),
  setSafe: (v) => set({ safeMode: v }),
  toggleHud: () => set((s) => ({ hud: !s.hud })),
  toggleHelp: () => set((s) => ({ help: !s.help })),
}));

/** Derived selectors — cheap, used by the overlay. */
export const selScene = (s) => SCENES[STEPS[s.step].scene];
export const selBeat = (s) => {
  const scene = SCENES[STEPS[s.step].scene];
  const bi = STEPS[s.step].beat;
  return scene.beats && scene.beats.length ? scene.beats[bi] : null;
};
export const selSceneIndex = (s) => STEPS[s.step].scene;
export const selBeatIndex = (s) => STEPS[s.step].beat;
