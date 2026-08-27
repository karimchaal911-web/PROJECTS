import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { LOOP_NODES } from '../../lib/curves.js';
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

const CENTRE = new THREE.Vector3(0, 24, 0);
const R = 11;

export default function ValueLoop() {
  const group = useRef();
  const presence = useChannel('ring');
  const reveal = useChannel('ringReveal', 0);
  const refs = useRef([]);
  const pulse = useRef(0);

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

    pulse.current = (pulse.current + dt * 0.16) % 1;
    refs.current.forEach((g, i) => {
      if (!g) return;
      const local = THREE.MathUtils.clamp(r * nodes.length - i, 0, 1);
      g.visible = local > 0.01;
      // A slow travelling emphasis: the loop is running, not posed.
      const d = Math.abs(((i / nodes.length) - pulse.current + 1) % 1);
      const near = Math.max(0, 1 - d * nodes.length * 0.9);
      g.scale.setScalar(local * (1 + near * 0.16));
    });
  });

  return (
    <group ref={group} position={CENTRE}>
      <Line ref={ringRef} points={ringPts} color={C.ocpGreen} lineWidth={1.6}
        transparent opacity={0} />

      {nodes.map((n, i) => (
        <group key={n.label} position={[n.x, 0, n.z]}>
          <group ref={(el) => { refs.current[i] = el; }}>
            <mesh material={nodeMat} castShadow>
              <cylinderGeometry args={[1.15, 1.15, 0.5, 24]} />
            </mesh>
          </group>
          <WLabel position={[0, 1.6, 0]} rotation={[-Math.PI / 2, 0, 0]}
            fontSize={1.02} color={C.inkEditorial} anchorX="center" fillOpacity={0.95}>
            {n.label}
          </WLabel>
        </group>
      ))}
    </group>
  );
}
