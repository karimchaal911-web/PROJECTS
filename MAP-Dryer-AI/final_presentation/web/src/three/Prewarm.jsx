import { useEffect, useMemo, useRef, useState } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { isDataLoaded } from '../data/load.js';

/**
 * Pay every first-use cost while the audience is still looking at a black
 * panel.
 *
 * WHAT THE COST ACTUALLY IS. Three separate things are deferred until the
 * frame that first draws an object, and only one of them is shader compilation:
 *
 *   1. program link — `gl.compile` covers this, and it covers it for INVISIBLE
 *      objects too, because it walks `scene.traverse`, not `traverseVisible`.
 *   2. buffer upload — every BufferGeometry is uploaded on its first DRAW.
 *      `compile` never draws, so it never uploads one.
 *   3. texture upload + mipmap generation — same rule. The seven procedural
 *      surface families are ~2 MB of DataTexture and none of them reaches the
 *      GPU until something wearing them is rasterised.
 *
 * Measured, with only `gl.compile` in place: a single **1310.8 ms** frame the
 * instant scene 03 revealed the process chain — the largest freeze in the film,
 * landing exactly on an act change. The programs were already linked; what cost
 * a second and a third of a second was uploading the chain's geometry and the
 * five surface families nothing before it had worn.
 *
 * THE FIX. One offscreen frame with the whole world visible. Everything is
 * drawn once, at 64 x 64, through a camera positioned to contain the entire
 * world so nothing is frustum-culled out of the upload. Programs link,
 * buffers upload, textures upload, and the AO pass's own material variants are
 * built — all of it behind the boot gate, none of it in front of the jury.
 *
 * The visibility flags are forced and restored inside one synchronous block, so
 * no layer can observe the change: every layer re-asserts its own visibility
 * from its presence channel on the next `useFrame` regardless.
 */
export default function Prewarm() {
  const { gl, scene, camera } = useThree();
  const [done, setDone] = useState(false);
  const frames = useRef(0);

  // 64 x 64 is enough. Vertex work, buffer upload, texture upload and program
  // link are all resolution-independent; only fragment shading is not, and
  // fragment shading is the one cost that is NOT deferred to first use.
  const target = useMemo(
    () => new THREE.WebGLRenderTarget(64, 64, { depthBuffer: true }),
    []
  );

  /**
   * A camera that contains the world.
   *
   * The show's own camera is at the scene-01 pose during boot, which puts the
   * process chain 100 units behind it and the roadmap rail 30 units above it.
   * Anything outside the frustum is culled before it is drawn, and culled means
   * not uploaded — so prewarming through the show camera warms the opening
   * frame and nothing else. The world spans roughly x ∈ [-120, 150],
   * y ∈ [-10, 50], z ∈ [-85, 85]; this contains it with margin.
   */
  const wide = useMemo(() => {
    const c = new THREE.PerspectiveCamera(90, 1, 1, 1400);
    c.position.set(20, 330, 210);
    c.lookAt(15, 8, 0);
    c.updateMatrixWorld();
    return c;
  }, []);

  useEffect(() => {
    if (done) return undefined;
    let raf = 0;

    const warm = () => {
      const hidden = [];
      scene.traverse((o) => {
        if (o.visible === false) { hidden.push(o); o.visible = true; }
      });
      try {
        // Programs first: cheap, and it means the draw below is only paying
        // for uploads.
        gl.compile(scene, wide);
        const prev = gl.getRenderTarget();
        gl.setRenderTarget(target);
        gl.render(scene, wide);
        gl.setRenderTarget(prev);
      } catch {
        // Best-effort. A failure here must never block boot — the worst case
        // is the hitch this component exists to remove, not a black show.
      } finally {
        for (const o of hidden) o.visible = false;
      }
    };

    const tick = () => {
      // Nothing is warmed until the seven payloads land. Every data-driven
      // layer builds its buffers from `getData()`, so warming before the
      // fetches resolve uploads the EMPTY sentinel and the hitch survives.
      if (!isDataLoaded()) { raf = requestAnimationFrame(tick); return; }
      frames.current += 1;
      // Twice. The first pass, two frames after the data lands, covers every
      // geometry React has built. The second covers troika's text meshes,
      // which are generated on a worker and are simply not in the scene graph
      // yet when the first pass runs.
      if (frames.current === 2 || frames.current === 10) warm();
      if (frames.current > 12) { setDone(true); return; }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [gl, scene, camera, wide, target, done]);

  useEffect(() => () => target.dispose(), [target]);

  return null;
}
