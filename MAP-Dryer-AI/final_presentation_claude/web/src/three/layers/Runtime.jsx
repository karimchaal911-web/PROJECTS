import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { RUNTIME_SLABS } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';

/**
 * What is behind the dashboard.
 *
 * Rather than showing an architecture slide, the camera pushes through the
 * Power BI plane and finds the runtime laid out in depth. End-to-end
 * integration is a spatial claim, so it is proved spatially — and the closing
 * frame, with the dashboard, the slabs, the returning stream and the still
 * turning dryer all visible at once, is the proof.
 */

const ORIGIN = new THREE.Vector3(76, 10, 0);
const W = 24;
const H = 8.4;

export default function Runtime() {
  const group = useRef();
  const labels = useRef();
  const presence = useChannel('runtime');
  const reveal = useChannel('runtimeReveal', 0);
  const refs = useRef([]);

  const mats = useMemo(
    () => RUNTIME_SLABS.map((s, i) => new THREE.MeshStandardMaterial({
      color: i === 0 ? C.forest900 : '#123028',
      roughness: 0.55,
      metalness: 0.15,
      emissive: new THREE.Color(C.dataTeal),
      emissiveIntensity: 0.22,
      fog: false,
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
    })),
    []
  );

  const edgeMat = useMemo(() => new THREE.LineBasicMaterial({
    color: C.dataTeal, transparent: true, opacity: 0, fog: false,
  }), []);
  const edgeGeo = useMemo(
    () => new THREE.EdgesGeometry(new THREE.PlaneGeometry(W, H)),
    []
  );

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const r = reveal.current;
    edgeMat.opacity = p * r * 0.8;
    if (labels.current) labels.current.visible = p > 0.35;
    RUNTIME_SLABS.forEach((_, i) => {
      const g = refs.current[i];
      if (!g) return;
      // Each slab scales in as the camera reaches its depth.
      const local = THREE.MathUtils.clamp(r * RUNTIME_SLABS.length - i, 0, 1);
      g.visible = local > 0.01;
      g.scale.set(0.8 + local * 0.2, local, 1);
      mats[i].opacity = p * local * 0.9;
    });
  });

  return (
    <group ref={group} position={ORIGIN}>
      {RUNTIME_SLABS.map((slab, i) => (
        <group key={slab.id} position={[slab.x ?? 0, slab.y ?? 0, slab.z]}>
          <group ref={(el) => { refs.current[i] = el; }}>
            <mesh material={mats[i]}>
              <planeGeometry args={[W, H]} />
            </mesh>
            <lineSegments geometry={edgeGeo} material={edgeMat} />
          </group>
        </group>
      ))}

      <group ref={labels}>
        {RUNTIME_SLABS.map((slab) => (
          <group key={slab.id} position={[slab.x ?? 0, slab.y ?? 0, slab.z]}>
            <WLabel position={[-W / 2 + 0.9, H / 2 - 1.4, 0.2]} fontSize={0.92}
              color={C.dustBright} fillOpacity={0.95}>
              {slab.label}
            </WLabel>
            <WMono position={[-W / 2 + 0.9, H / 2 - 2.6, 0.2]} fontSize={0.44}
              color={C.dataTeal} fillOpacity={0.75} maxWidth={W - 2}>
              {slab.sub}
            </WMono>
          </group>
        ))}
      </group>

      {/* Sits under the foot of the staircase, clear of the first slab's own
          title, so the two never read as one line. */}
      <WMono position={[-W / 2 + 0.9, -18.5, -38]} fontSize={0.72}
        color={C.dataCyan} fillOpacity={0.85}>
        POWER BI NEVER LOADS A MODEL AND NEVER RUNS INFERENCE
      </WMono>
    </group>
  );
}
