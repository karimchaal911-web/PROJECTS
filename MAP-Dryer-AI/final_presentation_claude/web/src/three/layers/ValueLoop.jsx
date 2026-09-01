import { useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { LOOP_NODES, RING_CENTRE, RING_RADIUS } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel } from '../WorldText.jsx';

/**
 * The operational loop the whole system serves.
 *
 * PROCESS → SENSE → PREDICT → DETECT → SUPERVISE → DECIDE → PROCESS.
 * It is a ring because the last step returns to the first: the operator acts on
 * the process, and the process is what is being sensed. Rendering it flat as an
 * arrow chain would lose exactly the property that matters.
 */

const CENTRE = new THREE.Vector3(...RING_CENTRE);
const R = RING_RADIUS;

export default function ValueLoop() {
  const { camera } = useThree();
  const group = useRef();
  const presence = useChannel('ring');
  const reveal = useChannel('ringReveal', 0);
  const refs = useRef([]);
  const travel = useChannel('ringTravel', 0);
  const runner = useRef();
  const labelRefs = useRef([]);
  const _w = useMemo(() => new THREE.Vector3(), []);

  const nodes = useMemo(
    () => LOOP_NODES.map((label, i) => {
      const a = (i / LOOP_NODES.length) * Math.PI * 2 - Math.PI / 2;
      return { label, a, x: Math.cos(a) * R, z: Math.sin(a) * R };
    }),
    []
  );

  const ringPts = useMemo(() => {
    const pts = [];
    for (let i = 0; i <= 96; i += 1) {
      const a = (i / 96) * Math.PI * 2;
      pts.push([Math.cos(a) * R, 0, Math.sin(a) * R]);
    }
    return pts;
  }, []);

  const nodeMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.ocpGreen, roughness: 0.45, metalness: 0.2,
    emissive: new THREE.Color(C.ocpGreen), emissiveIntensity: 0.16,
    transparent: true, opacity: 0,
  }), []);

  const ringRef = useRef();

  useFrame((state, dt) => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const r = reveal.current;
    nodeMat.opacity = p * r;
    if (ringRef.current) ringRef.current.material.opacity = p * r * 0.5;

    // ONE signal travels the ring ONCE. The previous ambient breathing pulse
    // was the only direction cue in the scene, and in a still frame — or on a
    // projector — it was not readable at all, so the loop had no direction.
    const t = THREE.MathUtils.clamp(travel.current, 0, 1);
    refs.current.forEach((g, i) => {
      if (!g) return;
      const local = THREE.MathUtils.clamp(r * nodes.length - i, 0, 1);
      g.visible = local > 0.01;
      const d = Math.abs(((i / nodes.length) - t + 1) % 1);
      const near = Math.max(0, 1 - d * nodes.length * 0.9);
      g.scale.setScalar(local * (1 + near * 0.22));
    });
    // Names face the lens and hold one apparent size.
    //
    // Upright text still SKEWS when the camera looks down on the ring at 34
    // degrees, and perspective made the near nodes read almost twice the size
    // of the far ones — a hierarchy that does not exist. Billboarding removes
    // the skew; compensating the scale by depth removes the false ranking.
    for (let i = 0; i < labelRefs.current.length; i += 1) {
      const b = labelRefs.current[i];
      if (!b) continue;
      b.quaternion.copy(camera.quaternion);
      b.getWorldPosition(_w);
      const d = camera.position.distanceTo(_w);
      b.scale.setScalar(THREE.MathUtils.clamp(d / 44, 0.7, 1.5));
    }

    if (runner.current) {
      const a = t * Math.PI * 2 - Math.PI / 2;
      runner.current.position.set(Math.cos(a) * R, 0.5, Math.sin(a) * R);
      runner.current.visible = t > 0.001 && t < 0.999;
      runner.current.material.opacity = p * r;
    }
  });

  return (
    <group ref={group} position={CENTRE}>
      <Line ref={ringRef} points={ringPts} color={C.ocpGreen} lineWidth={1.6}
        transparent opacity={0} />

      {/* the travelling signal */}
      <mesh ref={runner}>
        <sphereGeometry args={[0.62, 16, 12]} />
        <meshBasicMaterial color={C.ocpLime} transparent opacity={0} depthWrite={false} />
      </mesh>

      {/* arrowheads: the ring reads as directed even in a still frame */}
      {nodes.map((n, i) => {
        const a = n.a + Math.PI / nodes.length;
        return (
          <mesh
            key={`arrow-${n.label}`}
            position={[Math.cos(a) * R, 0.1, Math.sin(a) * R]}
            rotation={[Math.PI / 2, 0, -a - Math.PI / 2]}
            material={nodeMat}
          >
            <coneGeometry args={[0.42, 1.1, 12]} />
          </mesh>
        );
      })}

      {nodes.map((n, i) => (
        <group key={n.label} position={[n.x, 0, n.z]}>
          <group ref={(el) => { refs.current[i] = el; }}>
            <mesh material={nodeMat} castShadow>
              <cylinderGeometry args={[1.15, 1.15, 0.5, 24]} />
            </mesh>
          </group>
          <group ref={(el) => { labelRefs.current[i] = el; }} position={[0, 3.4, 0]}>
            <WLabel overlay fontSize={1.15} color={C.inkEditorial}
              anchorX="center" fillOpacity={0.98}>
              {n.label}
            </WLabel>
          </group>
        </group>
      ))}
    </group>
  );
}
