import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { ARCH_LAYERS, ARCH_ORIGIN, ARCH_STEP } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';

/**
 * The architecture, built by arriving packets.
 *
 * This is deliberately not a floating block diagram: each slab scales up only
 * when its share of the packet stream has arrived, so the audience reads the
 * system as a consequence of the data rather than as a picture drawn in
 * advance.
 */

const W = 15;
const H = 1.5;
const D = 7;

export default function Architecture() {
  const group = useRef();
  const labels = useRef();
  const presence = useChannel('arch');
  const build = useChannel('archBuild', 0);
  const align = useChannel('alignPause', 0);
  const refs = useRef([]);

  const mats = useMemo(
    () => ARCH_LAYERS.map((_, i) => new THREE.MeshStandardMaterial({
      color: i === 4 ? C.forest700 : C.steelDark,
      roughness: 0.68,
      metalness: 0.25,
      emissive: new THREE.Color(C.dataTeal),
      emissiveIntensity: 0.05,
      transparent: true,
      opacity: 0,
    })),
    []
  );

  const edgeMat = useMemo(() => new THREE.LineBasicMaterial({
    color: C.dataTeal, transparent: true, opacity: 0,
  }), []);

  const edgeGeo = useMemo(
    () => new THREE.EdgesGeometry(new THREE.BoxGeometry(W, H, D)),
    []
  );

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const b = build.current;
    edgeMat.opacity = p * 0.45;
    // Labels are legible or absent — never a ghost over another scene.
    if (labels.current) labels.current.visible = p > 0.4;

    ARCH_LAYERS.forEach((_, i) => {
      const g = refs.current[i];
      const m = mats[i];
      if (!g) return;
      // A layer forms when its packet count threshold is met.
      const local = THREE.MathUtils.clamp((b * ARCH_LAYERS.length - i) / 0.5, 0, 1);
      g.scale.y = Math.max(0.001, local);
      g.visible = local > 0.005;
      m.opacity = p * local;
      // The ALIGN layer glows while the followed packet waits inside it.
      m.emissiveIntensity = i === 2 ? 0.05 + align.current * 0.4 : 0.05;
    });
  });

  return (
    <group ref={group} position={ARCH_ORIGIN}>
      {ARCH_LAYERS.map((layer, i) => (
        <group key={layer.id} position={[0, i * ARCH_STEP, 0]}>
          <group ref={(el) => { refs.current[i] = el; }}>
            <mesh castShadow receiveShadow material={mats[i]}>
              <boxGeometry args={[W, H, D]} />
            </mesh>
            <lineSegments geometry={edgeGeo} material={edgeMat} />
          </group>
        </group>
      ))}

      <group ref={labels}>
        {ARCH_LAYERS.map((layer, i) => (
          <group key={layer.id} position={[0, i * ARCH_STEP, 0]}>
            <WLabel position={[W / 2 + 1.1, 0.36, 0]} fontSize={0.78} color={C.dustBright} fillOpacity={0.92}>
              {layer.label}
            </WLabel>
            <WMono position={[W / 2 + 1.1, -0.48, 0]} fontSize={0.46} color={C.dataTeal} fillOpacity={0.65}>
              {layer.sub}
            </WMono>
          </group>
        ))}
      </group>
    </group>
  );
}
