import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { useChannel } from '../usePresence.js';
import { useShow } from '../../state/useShow.js';
import { budget } from '../../lib/perf.js';

/**
 * The plant hall: ground, green structural steel, platforms, handrails,
 * overhead ductwork and suspended dust.
 *
 * The colour decision here is the whole design system in one line — the real
 * plant's structural steel is painted green (see
 * assets/process/drying_section_structure.jpeg), so the OCP identity and the
 * industrial reality are the same palette. Nothing is styled; it is observed.
 */

export default function Plant() {
  const group = useRef();
  const dust = useRef();
  const presence = useChannel('plant');
  const safeMode = useShow((s) => s.safeMode);
  const b = budget(safeMode);

  const mats = useMemo(() => ({
    steel: new THREE.MeshStandardMaterial({ color: C.steelGreen, roughness: 0.7, metalness: 0.12, envMapIntensity: 0.6, transparent: true }),
    dark: new THREE.MeshStandardMaterial({ color: C.steelDark, roughness: 0.82, metalness: 0.1, transparent: true }),
    grating: new THREE.MeshStandardMaterial({ color: C.grating, roughness: 0.85, metalness: 0.15, transparent: true }),
    rail: new THREE.MeshStandardMaterial({ color: C.handrail, roughness: 0.8, metalness: 0.2, transparent: true }),
    duct: new THREE.MeshStandardMaterial({ color: C.duct, roughness: 0.62, metalness: 0.18, envMapIntensity: 0.9, transparent: true }),
    ground: new THREE.MeshStandardMaterial({ color: '#2B2A24', roughness: 0.97, metalness: 0.0, transparent: true }),
  }), []);

  // Twelve columns on a believable industrial grid.
  const columns = useMemo(() => {
    const out = [];
    // Back row is complete; the camera-side row deliberately omits the bays
    // in front of the dryer so the hero object is never occluded.
    for (const x of [-30, -14, 2, 18, 34]) out.push([x, -16]);
    for (const x of [-30, 34]) out.push([x, 16]);
    out.push([-30, 0], [34, 0]);
    return out;
  }, []);

  const dustGeo = useMemo(() => {
    const n = b.dust;
    const g = new THREE.BufferGeometry();
    if (n === 0) {
      g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(0), 3));
      return g;
    }
    const pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i += 1) {
      pos[i * 3] = (Math.random() - 0.5) * 90;
      pos[i * 3 + 1] = 0.5 + Math.random() * 17;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 52;
    }
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    return g;
  }, [b.dust]);

  const dustMat = useMemo(() => new THREE.PointsMaterial({
    color: C.dustBright, size: 0.075, transparent: true, opacity: 0,
    depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true,
  }), []);

  useFrame((state, dt) => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.005;
      if (p <= 0.005) return;
    }
    for (const m of Object.values(mats)) m.opacity = p;
    mats.ground.opacity = p;

    if (dust.current && b.dust > 0) {
      dustMat.opacity = p * 0.45;
      // Dust drifts. It is the only thing in the hall that says "air moves".
      dust.current.rotation.y += dt * 0.006;
      dust.current.position.y = Math.sin(state.clock.elapsedTime * 0.08) * 0.6;
    }
  });

  return (
    <group ref={group}>
      {/* ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow material={mats.ground}>
        <planeGeometry args={[400, 220]} />
      </mesh>

      {/* structural columns + bracing */}
      {columns.map(([x, z]) => (
        <group key={`${x}:${z}`} position={[x, 0, z]}>
          <mesh position={[0, 8.5, 0]} castShadow receiveShadow material={mats.steel}>
            <boxGeometry args={[0.72, 17, 0.72]} />
          </mesh>
          <mesh position={[0, 0.35, 0]} castShadow material={mats.dark}>
            <boxGeometry args={[1.5, 0.7, 1.5]} />
          </mesh>
          {/* diagonal brace, the signature of the real structure */}
          <mesh position={[0, 9.0, z > 0 ? -2.6 : 2.6]} rotation={[z > 0 ? 0.72 : -0.72, 0, 0]} material={mats.steel}>
            <boxGeometry args={[0.34, 8.4, 0.34]} />
          </mesh>
        </group>
      ))}

      {/* cross beams at platform levels */}
      {[9.4, 16.2].map((y) => (
        <group key={y}>
          {[-16, 16].map((z) => (
            <mesh key={z} position={[2, y, z]} castShadow material={mats.steel}>
              <boxGeometry args={[70, 0.5, 0.5]} />
            </mesh>
          ))}
          {[-30, -14, 2, 18, 34].map((x) => (
            <mesh key={x} position={[x, y, 0]} castShadow material={mats.steel}>
              <boxGeometry args={[0.5, 0.5, 33]} />
            </mesh>
          ))}
        </group>
      ))}

      {/* grating platforms alongside the dryer */}
      {[-7.2, 7.2].map((z) => (
        <group key={z}>
          <mesh position={[0, 3.1, z]} receiveShadow material={mats.grating}>
            <boxGeometry args={[34, 0.12, 2.4]} />
          </mesh>
          {/* yellow handrail — small quantity, large realism payoff */}
          {[0.95, 1.55].map((h) => (
            <mesh key={h} position={[0, 3.1 + h, z + (z > 0 ? 1.1 : -1.1)]}
              rotation={[0, 0, Math.PI / 2]} material={mats.rail}>
              <cylinderGeometry args={[0.045, 0.045, 34, 8]} />
            </mesh>
          ))}
          {[-15, -7.5, 0, 7.5, 15].map((x) => (
            <mesh key={x} position={[x, 3.9, z + (z > 0 ? 1.1 : -1.1)]} material={mats.rail}>
              <cylinderGeometry args={[0.045, 0.045, 1.6, 8]} />
            </mesh>
          ))}
        </group>
      ))}

      {/* overhead ductwork running the length of the hall */}
      {[[-4.5, 13.4, -9.5, 62], [6.0, 15.1, 8.5, 54]].map(([x, y, z, len]) => (
        <mesh key={`${x}${z}`} position={[x, y, z]} rotation={[0, 0, Math.PI / 2]}
          castShadow material={mats.duct}>
          <cylinderGeometry args={[0.85, 0.85, len, 18]} />
        </mesh>
      ))}
      <mesh position={[24, 12.0, -9.5]} rotation={[Math.PI / 2, 0, 0]} castShadow material={mats.duct}>
        <cylinderGeometry args={[0.85, 0.85, 12, 18]} />
      </mesh>

      {/* roof — closes the hall so the dust reads as air, not as stars */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[2, 18.6, 0]} material={mats.dark}>
        <planeGeometry args={[120, 60]} />
      </mesh>

      {/* suspended dust */}
      {b.dust > 0 && <points ref={dust} geometry={dustGeo} material={dustMat} />}
    </group>
  );
}
