import { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { primeSurfaces } from '../lib/surfaces.js';
import { useShow } from '../state/useShow.js';

/**
 * A procedural studio environment for image-based lighting.
 *
 * Metalness is meaningless without something to reflect: without this, every
 * metal surface in the scene renders black, which is exactly what the first
 * render pass showed. drei's <Environment preset> would fetch an HDRI from a
 * CDN, which the offline requirement forbids, so this uses three's own
 * RoomEnvironment — generated in memory, no asset, no network.
 *
 * The intensity is deliberately low: this is a fill that makes steel read as
 * steel, not a lighting scheme. The key and rim in Lighting.jsx still do the
 * cinematography.
 */
export default function StudioEnv({ intensity = 0.28 }) {
  const { gl, scene } = useThree();
  // A PMREM target holds a RENDERED image. A restored context hands it back
  // empty, which is the difference between steel and black plastic, so the
  // environment is regenerated rather than assumed to have survived.
  const epoch = useShow((s) => s.renderEpoch);

  useEffect(() => {
    // Generate the procedural surface families here rather than lazily on
    // first material use: this effect runs inside the boot window, and doing
    // it later would put ~12 ms of JS on whichever transition first touched a
    // family. It also needs `gl` to match the GPU's anisotropic filtering,
    // without which the floor aliases into moire at grazing angles.
    primeSurfaces(gl);

    const pmrem = new THREE.PMREMGenerator(gl);
    pmrem.compileEquirectangularShader();
    const room = new RoomEnvironment();
    const target = pmrem.fromScene(room, 0.04);
    scene.environment = target.texture;
    scene.environmentIntensity = intensity;

    // Diagnostics. scripts/qa-restore.mjs asserts that this epoch ADVANCED
    // across a context loss: a restored context hands the PMREM target back
    // empty, and an environment that was not regenerated renders every metal
    // surface in the film black.
    if (typeof window !== 'undefined') {
      window.__ENV__ = { ready: true, epoch, intensity };
    }

    return () => {
      scene.environment = null;
      target.dispose();
      pmrem.dispose();
      room.traverse((o) => {
        if (o.geometry) o.geometry.dispose();
        if (o.material) o.material.dispose();
      });
      if (typeof window !== 'undefined' && window.__ENV__) window.__ENV__.ready = false;
    };
  }, [gl, scene, intensity, epoch]);

  return null;
}
