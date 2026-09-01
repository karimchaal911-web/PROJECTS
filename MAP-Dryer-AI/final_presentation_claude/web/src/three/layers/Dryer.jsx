import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { DRYER, FEED_END, DISCHARGE_END } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { applySurface } from '../../lib/surfaces.js';

/**
 * The hero rotary dryer.
 *
 * Proportions and detailing follow final_report/figures/process_photos/
 * rotary_dryer_shell.jpeg: a large inclined shell on two riding rings carried
 * by trunnion rollers, a girth-gear drive, a feed chute at the high end, a
 * discharge hood at the low end and an exhaust duct rising to the extraction
 * path. Everything is dust-loaded — that is what the photograph shows and it is
 * what makes the material read as real steel rather than CAD.
 *
 * No PCS7 tag, equipment identity or dimension is asserted: the report
 * explicitly refuses that mapping and so does this model.
 */

const INCLINE = THREE.MathUtils.degToRad(DRYER.incline);

export default function Dryer({ layerKey = 'dryer' }) {
  const group = useRef();
  const drum = useRef();
  const gear = useRef();
  const presence = useChannel(layerKey);
  const wireCh = useChannel('dryerWire');

  const materials = useMemo(() => {
    const shell = new THREE.MeshStandardMaterial({
      color: C.shell, roughness: 0.58, metalness: 0.22, transparent: true,
      envMapIntensity: 0.9,
    });
    const ring = new THREE.MeshStandardMaterial({
      color: C.ring, roughness: 0.34, metalness: 0.65, transparent: true,
      envMapIntensity: 1.4,
    });
    const steel = new THREE.MeshStandardMaterial({
      color: C.steelGreen, roughness: 0.7, metalness: 0.12, transparent: true,
      envMapIntensity: 0.7,
    });
    const duct = new THREE.MeshStandardMaterial({
      color: C.duct, roughness: 0.62, metalness: 0.18, transparent: true,
      envMapIntensity: 0.9,
    });
    const wire = new THREE.MeshBasicMaterial({
      color: C.dataTeal, wireframe: true, transparent: true, opacity: 0,
      depthWrite: false,
    });

    // Four different fabrications, four different surfaces. The shell is a
    // welded plate cylinder, the rings and gear are ground steel, the plinths
    // and drive housing are painted section, the ducts are rolled sheet. Until
    // this line they were four numbers apart and read as one plastic.
    // Repeats are chosen against the real size of each part: the shell tiles
    // three times along a 24-unit drum, which puts a course seam roughly every
    // 2.7 units, the spacing plate actually comes in.
    applySurface(shell, 'paint', { repeat: [6, 3] });
    applySurface(ring, 'machined', { repeat: [8, 2] });
    applySurface(steel, 'struct', { repeat: 3 });
    applySurface(duct, 'pipe', { repeat: [3, 1] });

    return { shell, ring, steel, duct, wire };
  }, []);

  // Girth-gear teeth as one instanced mesh.
  const teeth = useMemo(() => {
    const n = 96;
    const m = new THREE.InstancedMesh(
      new THREE.BoxGeometry(0.16, 0.22, 0.34),
      materials.ring,
      n
    );
    const o = new THREE.Object3D();
    for (let i = 0; i < n; i += 1) {
      const a = (i / n) * Math.PI * 2;
      o.position.set(0, Math.cos(a) * 2.28, Math.sin(a) * 2.28);
      o.rotation.set(a, 0, 0);
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
    m.castShadow = true;
    return m;
  }, [materials.ring]);

  useFrame((_, dt) => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    // The dryer turns for the entire fourteen minutes. It is the one thing in
    // the film that never stops, and that is the point.
    if (drum.current) drum.current.rotation.x += dt * 0.30;
    if (gear.current) gear.current.rotation.x += dt * 0.30;

    const { shell, ring, steel, duct } = materials;
    const wireAmount = wireCh.current;
    // The shell used to fall to 18 % under the wireframe, which turned a
    // steel machine into a glass tube and let the whole plant ghost through
    // it. A section view still has to read as a section OF SOMETHING SOLID.
    shell.opacity = p * (1 - wireAmount * 0.55);
    ring.opacity = p * (1 - wireAmount * 0.35);
    steel.opacity = p * (1 - wireAmount * 0.3);
    duct.opacity = p * (1 - wireAmount * 0.4);
    materials.wire.opacity = p * wireAmount * 0.65;
  });

  return (
    <group ref={group} position={[DRYER.x, DRYER.y, DRYER.z]} rotation={[0, 0, INCLINE]}>
      {/* ---------------------------------------------------------- shell */}
      <group ref={drum} rotation={[0, 0, 0]}>
        <mesh castShadow receiveShadow rotation={[0, 0, Math.PI / 2]} material={materials.shell}>
          <cylinderGeometry args={[DRYER.radius, DRYER.radius, DRYER.length, 64, 1, true]} />
        </mesh>
        {/* wireframe twin, revealed in the PHYSICS beat and in scene 07 */}
        <mesh rotation={[0, 0, Math.PI / 2]} material={materials.wire}>
          <cylinderGeometry args={[DRYER.radius * 1.002, DRYER.radius * 1.002, DRYER.length, 28, 8, true]} />
        </mesh>

        {/* riding rings — polished by contact with the rollers */}
        {[-6.2, 6.2].map((x) => (
          <mesh key={x} position={[x, 0, 0]} rotation={[0, Math.PI / 2, 0]}
            castShadow material={materials.ring}>
            <torusGeometry args={[DRYER.radius + 0.12, 0.17, 12, 48]} />
          </mesh>
        ))}

        {/* shell stiffener bands */}
        {[-9.4, -2.6, 2.6, 9.4].map((x) => (
          <mesh key={x} position={[x, 0, 0]} rotation={[0, Math.PI / 2, 0]} material={materials.shell}>
            <torusGeometry args={[DRYER.radius + 0.04, 0.055, 8, 40]} />
          </mesh>
        ))}
      </group>

      {/* girth gear drive */}
      <group ref={gear} position={[3.4, 0, 0]}>
        <mesh rotation={[0, Math.PI / 2, 0]} castShadow material={materials.ring}>
          <torusGeometry args={[2.18, 0.12, 10, 56]} />
        </mesh>
        <primitive object={teeth} />
      </group>

      {/* pinion + drive housing */}
      <mesh position={[3.4, -2.62, 0.0]} rotation={[0, 0, Math.PI / 2]} castShadow material={materials.steel}>
        <cylinderGeometry args={[0.42, 0.42, 0.6, 16]} />
      </mesh>
      <mesh position={[3.4, -3.35, 0]} castShadow material={materials.steel}>
        <boxGeometry args={[1.8, 1.1, 1.4]} />
      </mesh>

      {/* --------------------------------------------- trunnion supports */}
      {[-6.2, 6.2].map((x) =>
        [-1, 1].map((s) => (
          <group key={`${x}:${s}`} position={[x, -DRYER.radius - 0.42, s * 1.35]}>
            <mesh rotation={[0, 0, Math.PI / 2]} castShadow material={materials.ring}>
              <cylinderGeometry args={[0.46, 0.46, 0.62, 20]} />
            </mesh>
            <mesh position={[0, -1.5, 0]} castShadow material={materials.steel}>
              <boxGeometry args={[1.3, 2.4, 0.9]} />
            </mesh>
          </group>
        ))
      )}
      {/* support plinths */}
      {[-6.2, 6.2].map((x) => (
        <mesh key={`p${x}`} position={[x, -DRYER.radius - 3.6, 0]} receiveShadow castShadow
          material={materials.steel}>
          <boxGeometry args={[3.6, 1.0, 4.4]} />
        </mesh>
      ))}

      {/* ------------------------------------------------------ feed end */}
      <group position={[FEED_END - 0.9, 0, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]} castShadow material={materials.duct}>
          <cylinderGeometry args={[DRYER.radius + 0.25, DRYER.radius + 0.25, 1.8, 32]} />
        </mesh>
        {/* inclined feed chute bringing wet crystals in from above */}
        <mesh position={[-1.1, 2.9, 0]} rotation={[0, 0, -0.62]} castShadow material={materials.duct}>
          <boxGeometry args={[1.5, 5.2, 1.5]} />
        </mesh>
        <mesh position={[-1.9, 5.6, 0]} castShadow material={materials.duct}>
          <boxGeometry args={[2.3, 1.4, 2.3]} />
        </mesh>
      </group>

      {/* ------------------------------------------------- discharge end */}
      <group position={[DISCHARGE_END + 1.1, 0, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]} castShadow material={materials.duct}>
          <cylinderGeometry args={[DRYER.radius + 0.45, DRYER.radius + 0.3, 2.2, 32]} />
        </mesh>
        {/* discharge hood — the warm mouth of the machine */}
        <mesh position={[1.6, -0.5, 0]} castShadow material={materials.steel}>
          <boxGeometry args={[2.2, 3.4, 3.6]} />
        </mesh>
        <mesh position={[2.4, -2.4, 0]} rotation={[0, 0, 0.35]} castShadow material={materials.duct}>
          <boxGeometry args={[1.4, 2.6, 2.0]} />
        </mesh>
      </group>

      {/* ---------------------------------------------------- exhaust duct */}
      <mesh position={[-9.6, 4.6, 0]} rotation={[0, 0, 0.14]} castShadow material={materials.duct}>
        <cylinderGeometry args={[1.05, 1.05, 7.4, 24]} />
      </mesh>
      <mesh position={[-8.6, 8.4, 0]} rotation={[0, 0, Math.PI / 2]} castShadow material={materials.duct}>
        <cylinderGeometry args={[1.05, 1.05, 9.0, 24]} />
      </mesh>

      {/* steam/air supply into the discharge end, counter-current */}
      <mesh position={[12.4, -3.0, 2.4]} rotation={[Math.PI / 2, 0, 0]} castShadow material={materials.duct}>
        <cylinderGeometry args={[0.72, 0.72, 5.0, 20]} />
      </mesh>
    </group>
  );
}
