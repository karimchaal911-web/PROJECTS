import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { flowPath } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { useShow } from '../../state/useShow.js';
import { budget } from '../../lib/perf.js';

/**
 * The MAP material stream — the object that carries the whole film.
 *
 * These instances ride `flowPath`, and `flowPath` is the same function that
 * later becomes the time axis. When the `straighten` channel goes 0 → 1 the
 * granules are never hidden and never re-emitted: they simply keep flowing
 * while distance turns into time. That continuity is the entire reason the
 * transition works.
 */

const _o = new THREE.Object3D();
const _p = new THREE.Vector3();

export default function Granules() {
  const mesh = useRef();
  const presence = useChannel('granules');
  const straighten = useChannel('straighten');
  const speed = useChannel('flowSpeed', 1);
  const heroScale = useChannel('heroGranule', 1);
  const safeMode = useShow((s) => s.safeMode);
  const count = budget(safeMode).granules;

  const mat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.granule,
    roughness: 0.55,
    metalness: 0.0,
    emissive: new THREE.Color(C.granule),
    emissiveIntensity: 0.04,
    transparent: true,
    opacity: 0,
  }), []);

  const geo = useMemo(() => new THREE.IcosahedronGeometry(0.085, 0), []);

  const seeds = useMemo(() => {
    const s = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      s[i * 3] = Math.random();               // position along the path
      s[i * 3 + 1] = (Math.random() - 0.5);   // lateral jitter
      s[i * 3 + 2] = 0.6 + Math.random() * 0.9; // size variation
    }
    return s;
  }, [count]);

  const offset = useRef(0);

  useFrame((state, dt) => {
    const p = presence.current;
    if (mesh.current) {
      mesh.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    mat.opacity = p;
    offset.current = (offset.current + dt * 0.020 * speed.current) % 1;

    const st = straighten.current;
    const hero = heroScale.current;
    const t = state.clock.elapsedTime;

    for (let i = 0; i < count; i += 1) {
      const u = (seeds[i * 3] + offset.current) % 1;
      flowPath(u, st, _p);

      // Lateral spread narrows as the stream straightens into an axis: the
      // material becomes a signal.
      const jitter = seeds[i * 3 + 1];
      const spread = THREE.MathUtils.lerp(0.9, 0.28, st);
      _o.position.set(
        _p.x + jitter * spread * 0.4,
        _p.y + Math.sin(t * 0.7 + i) * 0.03 + jitter * spread * 0.5,
        _p.z + jitter * spread
      );

      const s = seeds[i * 3 + 2];
      if (i === 0 && hero > 1.05) {
        // The hero granule of scene 02 parks in front of the lens and grows.
        // It is a real instance from the same stream, not a separate prop.
        _o.position.set(-11.6, 5.7, 4.4);
        _o.scale.setScalar(hero);
      } else {
        _o.scale.setScalar(s);
      }
      _o.rotation.set(t * 0.4 + i, t * 0.3 + i * 0.7, 0);
      _o.updateMatrix();
      mesh.current.setMatrixAt(i, _o.matrix);
    }
    mesh.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh
      ref={mesh}
      args={[geo, mat, count]}
      castShadow={false}
      receiveShadow={false}
      frustumCulled={false}
    />
  );
}
