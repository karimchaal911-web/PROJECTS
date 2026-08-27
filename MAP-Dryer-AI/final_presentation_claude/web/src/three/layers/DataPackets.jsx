import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { ARCH_ORIGIN, ARCH_STEP, ARCH_LAYERS, DRYER } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { useShow } from '../../state/useShow.js';
import { budget } from '../../lib/perf.js';

/**
 * Signals leaving the process.
 *
 * The packets are one instanced mesh whose targets are reassigned rather than
 * re-emitted, which is what lets scene 08 show the stream *bifurcating* — the
 * audience must see one input being split into two questions, not two separate
 * streams appearing.
 *
 * In scene 11 the same instances run the loop closed, from the replay slab back
 * to the dryer they describe.
 */

const _o = new THREE.Object3D();
const _a = new THREE.Vector3();
const _b = new THREE.Vector3();
const _c = new THREE.Vector3();

const SOURCES = [
  [-9.6, 3.4, 0.2], [12.4, 2.4, 2.4], [-8.6, 13.6, 0], [-12.9, 10.8, 0],
  [0, 7.6, 0], [-9.6, 8.0, 0], [24, 12.0, -9.5], [4, 6.2, 0], [-4, 6.2, 0],
];

const ARCH_TOP = ARCH_ORIGIN.y + ARCH_STEP * (ARCH_LAYERS.length - 1);
const LANE_A = new THREE.Vector3(-26, 14, -78);
const LANE_B = new THREE.Vector3(28, 15, -78);
const REPLAY_SLAB = new THREE.Vector3(76, 10, -40);

export default function DataPackets() {
  const mesh = useRef();
  const presence = useChannel('packets');
  const flow = useChannel('packetFlow', 0);
  const split = useChannel('laneSplit', 0);
  const align = useChannel('alignPause', 0);
  const loop = useChannel('loopClose', 0);
  const safeMode = useShow((s) => s.safeMode);
  const count = budget(safeMode).packets;

  const mat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.dataCyan, transparent: true, opacity: 0, depthWrite: false,
    blending: THREE.AdditiveBlending,
  }), []);
  const geo = useMemo(() => new THREE.BoxGeometry(0.13, 0.13, 0.32), []);

  const seeds = useMemo(() => {
    const s = new Float32Array(count * 4);
    for (let i = 0; i < count; i += 1) {
      s[i * 4] = Math.random();                                  // phase
      s[i * 4 + 1] = Math.floor(Math.random() * SOURCES.length); // source
      s[i * 4 + 2] = Math.random();                              // lane bias
      s[i * 4 + 3] = 0.6 + Math.random() * 0.8;                  // speed
    }
    return s;
  }, [count]);

  const phase = useRef(0);

  useFrame((state, dt) => {
    const p = presence.current;
    if (mesh.current) {
      mesh.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    mat.opacity = p * 0.85;
    phase.current += dt * 0.16 * (0.25 + flow.current);

    const sp = split.current;
    const al = align.current;
    const lp = loop.current;

    for (let i = 0; i < count; i += 1) {
      const src = SOURCES[seeds[i * 4 + 1]];
      let u = (seeds[i * 4] + phase.current * seeds[i * 4 + 3]) % 1;

      _a.set(src[0], src[1], src[2]);

      // Stage 1 — up into the architecture stack.
      const archY = ARCH_ORIGIN.y + u * (ARCH_TOP - ARCH_ORIGIN.y);
      _b.set(
        THREE.MathUtils.lerp(src[0], ARCH_ORIGIN.x, Math.min(1, u * 1.6)),
        archY,
        THREE.MathUtils.lerp(src[2], ARCH_ORIGIN.z, Math.min(1, u * 1.6))
      );

      // The waiting packet: residence-time alignment made visible. One packet
      // stops at the ALIGN layer for 24.5 minutes of replay while the rest dim.
      if (al > 0.01 && i % 97 === 0) {
        const hold = ARCH_ORIGIN.y + ARCH_STEP * 2;
        _b.y = THREE.MathUtils.lerp(_b.y, hold, al);
        _b.x = THREE.MathUtils.lerp(_b.x, ARCH_ORIGIN.x + 2.2, al);
      }

      // Stage 2 — the stream bifurcates into two lanes.
      if (sp > 0.01) {
        const toB = seeds[i * 4 + 2] > 0.516; // 15 of 31 go right
        const lane = toB ? LANE_B : LANE_A;
        _c.copy(_b);
        _c.x = THREE.MathUtils.lerp(_c.x, lane.x, u);
        _c.y = THREE.MathUtils.lerp(_c.y, lane.y, u);
        _c.z = THREE.MathUtils.lerp(_c.z, lane.z, u);
        _b.lerp(_c, sp);
      }

      // Stage 3 — the loop closes: replay slab back to the dryer.
      if (lp > 0.01) {
        _c.set(
          THREE.MathUtils.lerp(REPLAY_SLAB.x, DRYER.x, u),
          THREE.MathUtils.lerp(REPLAY_SLAB.y, DRYER.y + 1.5, u),
          THREE.MathUtils.lerp(REPLAY_SLAB.z, DRYER.z, u)
        );
        _b.lerp(_c, lp);
      }

      _o.position.copy(_b);
      _o.lookAt(_b.x, _b.y + 1, _b.z);
      const s = al > 0.01 && i % 97 === 0 ? 1.9 : 1.0;
      _o.scale.setScalar(s);
      _o.updateMatrix();
      mesh.current.setMatrixAt(i, _o.matrix);
    }
    mesh.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={mesh} args={[geo, mat, count]} frustumCulled={false} />
  );
}
