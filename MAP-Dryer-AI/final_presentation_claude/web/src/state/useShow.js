import { create } from 'zustand';
import { SCENES, STEPS } from './scenes.js';

/**
 * Show state. Deliberately small: the three-side world reads `step` through
 * refs and drives itself imperatively, so advancing a scene does not re-render
 * the scene graph. Only the DOM overlay subscribes to the copy fields.
 */
export const useShow = create((set, get) => ({
  step: 0,
  ready: false,
  safeMode: false,
  hud: false,
  help: false,
  started: false,
  startedAt: null,
  // set by the Rig so the overlay can wait for a transition to finish
  transitioning: false,

  get scene() {
    return SCENES[STEPS[get().step].scene];
  },

  begin: () => set({ started: true, startedAt: Date.now() }),
  setReady: (v) => set({ ready: v }),
  setTransitioning: (v) => set({ transitioning: v }),

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
