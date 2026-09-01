import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { ARCH_ORIGIN, ARCH_STEP, ARCH_LAYERS, RUNTIME_NODES, OPERATOR_NODE } from '../../lib/curves.js';
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
 * In scene 11 the same instances travel the runtime path and TERMINATE AT THE
 * OPERATOR. They used to run from the replay slab back into the dryer, which is
 * the visual grammar of closed-loop control — a thing this project does not
 * implement and explicitly disclaims two scenes later. Nothing in this system
 * writes back to the process, so nothing in this animation may appear to.
 */

const _o = new THREE.Object3D();
const _b = new THREE.Vector3();
const _c = new THREE.Vector3();
const _d = new THREE.Vector3();

const SOURCES = [
  [-9.6, 3.4, 0.2], [12.4, 2.4, 2.4], [-8.6, 13.6, 0], [-12.9, 10.8, 0],
  [0, 7.6, 0], [-9.6, 8.0, 0], [24, 12.0, -9.5], [4, 6.2, 0], [-4, 6.2, 0],
];

const ARCH_TOP = ARCH_ORIGIN.y + ARCH_STEP * (ARCH_LAYERS.length - 1);
const LANE_A = new THREE.Vector3(-26, 14, -78);
const LANE_B = new THREE.Vector3(28, 15, -78);

/**
 * The runtime hand-off, as a polyline in data-flow order:
 * replay → inference → PostgreSQL → semantic views → Power BI → operator.
 * The packets walk the same checkpoints the camera walks, in the same
 * direction, and the last vertex is a person.
 */
const RUNTIME_LINE = [...RUNTIME_NODES.map((n) => new THREE.Vector3(...n.pos)),
  new THREE.Vector3(...OPERATOR_NODE.pos)];
const RUNTIME_SEGS = RUNTIME_LINE.length - 1;

function runtimeAt(u, out) {
  const t = THREE.MathUtils.clamp(u, 0, 1) * RUNTIME_SEGS;
  const i = Math.min(RUNTIME_SEGS - 1, Math.floor(t));
  return out.copy(RUNTIME_LINE[i]).lerp(RUNTIME_LINE[i + 1], t - i);
}

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
  const geo = useMemo(() => new THREE.BoxGeometry(0.13, 0.13, 0.34), []);

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

  useFrame((_state, dt) => {
    const p = presence.current;
    if (!mesh.current) return;
    mesh.current.visible = p > 0.01;
    if (p <= 0.01) return;

    mat.opacity = p * 0.85;
    phase.current += dt * 0.16 * (0.25 + flow.current);

    const sp = split.current;
    const al = align.current;
    const lp = loop.current;

    /**
     * One packet's position at a given progress along its own route.
     * Sampling it twice — now, and a little ahead — is what lets each instance
     * point in the direction it is actually travelling. Every packet used to
     * be oriented straight up regardless of where it was going, so the stream
     * rendered as scattered vertical tick-marks with no directional read.
     */
    const placeAt = (i, u, out) => {
      const src = SOURCES[seeds[i * 4 + 1]];

      // Stage 1 — up into the architecture stack.
      out.set(
        THREE.MathUtils.lerp(src[0], ARCH_ORIGIN.x, Math.min(1, u * 1.6)),
        ARCH_ORIGIN.y + u * (ARCH_TOP - ARCH_ORIGIN.y),
        THREE.MathUtils.lerp(src[2], ARCH_ORIGIN.z, Math.min(1, u * 1.6))
      );

      // The waiting packet: residence-time alignment made visible. A marked
      // packet stops at the ALIGN layer for 24.5 minutes of replay while the
      // rest keep moving, so the wait is something the presenter can point at.
      if (al > 0.01 && i % 97 === 0) {
        const hold = ARCH_ORIGIN.y + ARCH_STEP * 2;
        out.y = THREE.MathUtils.lerp(out.y, hold, al);
        out.x = THREE.MathUtils.lerp(out.x, ARCH_ORIGIN.x + 2.2, al);
      }

      // Stage 2 — the stream bifurcates into two lanes.
      if (sp > 0.01) {
        const lane = seeds[i * 4 + 2] > 0.516 ? LANE_B : LANE_A; // 15 of 31 go right
        _c.copy(out);
        _c.x = THREE.MathUtils.lerp(_c.x, lane.x, u);
        _c.y = THREE.MathUtils.lerp(_c.y, lane.y, u);
        _c.z = THREE.MathUtils.lerp(_c.z, lane.z, u);
        out.lerp(_c, sp);
      }

      // Stage 3 — the runtime path, ending at the operator.
      if (lp > 0.01) {
        runtimeAt(u, _c);
        out.lerp(_c, lp);
      }
      return out;
    };

    for (let i = 0; i < count; i += 1) {
      const u = (seeds[i * 4] + phase.current * seeds[i * 4 + 3]) % 1;
      placeAt(i, u, _b);
      placeAt(i, Math.min(1, u + 0.008), _d);
      if (_d.distanceToSquared(_b) < 1e-8) _d.set(_b.x, _b.y + 1, _b.z);

      _o.position.copy(_b);
      _o.lookAt(_d);
      _o.scale.setScalar(al > 0.01 && i % 97 === 0 ? 1.9 : 1.0);
      _o.updateMatrix();
      mesh.current.setMatrixAt(i, _o.matrix);
    }
    mesh.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={mesh} args={[geo, mat, count]} frustumCulled={false} />
  );
}
