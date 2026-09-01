import { useMemo } from 'react';

/**
 * Animated "presence" channels shared between the show state and the scene
 * graph.
 *
 * A channel is just a `{ current: number }` box. Layers read it every frame
 * through a ref, so changing a scene never re-renders the React tree — GSAP
 * tweens the numbers and the render loop picks them up. This is what keeps the
 * world persistent: nothing is ever unmounted, presence simply goes to a low
 * value and the layer recedes into fog.
 */

const channels = new Map();

export function channel(key, initial = 0) {
  let ref = channels.get(key);
  if (!ref) {
    ref = { current: initial };
    channels.set(key, ref);
  }
  return ref;
}

export function useChannel(key, initial = 0) {
  return useMemo(() => channel(key, initial), [key, initial]);
}

export function getChannel(key) {
  return channel(key).current;
}

/**
 * Tween a set of channels onto one timeline.
 * @param {gsap.core.Timeline} tl
 * @param {Record<string, number>} values
 */
export function tweenChannels(tl, values, { duration = 2.2, ease = 'power2.inOut', position = 0 } = {}) {
  for (const [key, value] of Object.entries(values)) {
    const ref = channel(key);
    tl.to(ref, { current: value, duration, ease }, position);
  }
}

/** Immediately set channels without animation (used on hard recovery). */
export function setChannels(values) {
  for (const [key, value] of Object.entries(values)) {
    channel(key).current = value;
  }
}

/**
 * Every channel and its current value.
 *
 * Diagnostics only, and it exists for exactly one job: proving that a WebGL
 * context restore puts the world back into the state the presenter was already
 * in. The claim "the show resumes where it was" is otherwise untestable from
 * outside the page — the camera pose is observable through `window.__CAM__`,
 * but the thirty-odd presence channels that decide what is actually ON SCREEN
 * are not. See scripts/qa-restore.mjs.
 */
export function channelSnapshot() {
  const out = {};
  for (const [key, ref] of channels) out[key] = +ref.current.toFixed(4);
  return out;
}

if (typeof window !== 'undefined') window.__CHANNELS__ = channelSnapshot;
