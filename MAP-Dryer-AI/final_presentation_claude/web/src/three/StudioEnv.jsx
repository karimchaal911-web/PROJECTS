import { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

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

  useEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    pmrem.compileEquirectangularShader();
    const room = new RoomEnvironment();
    const target = pmrem.fromScene(room, 0.04);
    scene.environment = target.texture;
    scene.environmentIntensity = intensity;

    return () => {
      scene.environment = null;
      target.dispose();
      pmrem.dispose();
      room.traverse((o) => {
        if (o.geometry) o.geometry.dispose();
        if (o.material) o.material.dispose();
      });
    };
  }, [gl, scene, intensity]);

  return null;
}
