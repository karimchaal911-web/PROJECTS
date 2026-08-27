import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { DRYER } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';

/**
 * What happens inside the shell: lifting flights, the cascading material bed,
 * counter-current hot air, and moisture leaving toward the exhaust.
 *
 * This is a schematic transfer picture, not a CFD result, and the overlay says
 * so on screen. Its job is to make "heat and mass transfer over a residence
 * time" into something the jury can watch rather than take on trust.
 */

const INCLINE = THREE.MathUtils.degToRad(DRYER.incline);
const N_FLIGHTS = 12;
const N_BED = 900;
const N_AIR = 420;
const N_VAPOUR = 260;

export default function DryerInternals() {
  const group = useRef();
  const flights = useRef();
  const bed = useRef();
  const air = useRef();
  const vapour = useRef();
  const presence = useChannel('internals');

  const flightMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.ring, roughness: 0.6, metalness: 0.7, transparent: true, opacity: 0,
    side: THREE.DoubleSide,
  }), []);

  // Lifting flights: instanced blades on the inner wall.
  const flightMesh = useMemo(() => {
    const m = new THREE.InstancedMesh(
      new THREE.BoxGeometry(DRYER.length * 0.92, 0.5, 0.06),
      flightMat,
      N_FLIGHTS
    );
    const o = new THREE.Object3D();
    for (let i = 0; i < N_FLIGHTS; i += 1) {
      const a = (i / N_FLIGHTS) * Math.PI * 2;
      o.position.set(0, Math.cos(a) * (DRYER.radius - 0.28), Math.sin(a) * (DRYER.radius - 0.28));
      o.rotation.set(a + Math.PI / 2, 0, 0);
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
    return m;
  }, [flightMat]);

  // Material bed: particles that are lifted by the flights and cascade back.
  const bedData = useMemo(() => {
    const seeds = new Float32Array(N_BED * 3);
    for (let i = 0; i < N_BED; i += 1) {
      seeds[i * 3] = Math.random();                    // axial progress
      seeds[i * 3 + 1] = Math.random() * Math.PI * 2;  // phase
      seeds[i * 3 + 2] = 0.35 + Math.random() * 0.65;  // radius factor
    }
    return seeds;
  }, []);

  const bedGeo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N_BED * 3), 3));
    return g;
  }, []);

  const bedMat = useMemo(() => new THREE.PointsMaterial({
    color: C.granule, size: 0.11, transparent: true, opacity: 0,
    depthWrite: false, sizeAttenuation: true,
  }), []);

  // Counter-current hot air: moves from the discharge end back to the feed end.
  const airGeo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N_AIR * 3), 3));
    return g;
  }, []);
  const airMat = useMemo(() => new THREE.PointsMaterial({
    color: C.processWarm, size: 0.085, transparent: true, opacity: 0,
    depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true,
  }), []);
  const airSeeds = useMemo(() => {
    const s = new Float32Array(N_AIR * 3);
    for (let i = 0; i < N_AIR; i += 1) {
      s[i * 3] = Math.random();
      s[i * 3 + 1] = Math.random() * Math.PI * 2;
      s[i * 3 + 2] = Math.random() * 0.8;
    }
    return s;
  }, []);

  // Moisture leaving with the exhaust.
  const vapGeo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N_VAPOUR * 3), 3));
    return g;
  }, []);
  const vapMat = useMemo(() => new THREE.PointsMaterial({
    color: C.dataCyan, size: 0.13, transparent: true, opacity: 0,
    depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true,
  }), []);
  const vapSeeds = useMemo(() => {
    const s = new Float32Array(N_VAPOUR * 2);
    for (let i = 0; i < N_VAPOUR; i += 1) {
      s[i * 2] = Math.random();
      s[i * 2 + 1] = Math.random();
    }
    return s;
  }, []);

  useFrame((state, dt) => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const t = state.clock.elapsedTime;
    flightMat.opacity = p * 0.85;
    bedMat.opacity = p * 0.9;
    airMat.opacity = p * 0.55;
    vapMat.opacity = p * 0.5;

    if (flights.current) flights.current.rotation.x += dt * 0.30;

    // --- cascading bed ----------------------------------------------------
    const bp = bedGeo.attributes.position.array;
    const half = DRYER.length / 2;
    for (let i = 0; i < N_BED; i += 1) {
      let axial = (bedData[i * 3] + t * 0.026) % 1;
      bedData[i * 3] = axial;
      const phase = bedData[i * 3 + 1] + t * 0.30;
      const rf = bedData[i * 3 + 2];

      // Flights lift material up one side; it falls through the airstream.
      const lifted = ((phase % (Math.PI * 2)) / (Math.PI * 2));
      let y;
      let z;
      if (lifted < 0.5) {
        // riding the wall upward
        const a = -Math.PI * 0.75 + lifted * 2 * Math.PI * 0.9;
        y = Math.cos(a) * (DRYER.radius - 0.34) * rf;
        z = Math.sin(a) * (DRYER.radius - 0.34) * rf;
      } else {
        // falling curtain
        const f = (lifted - 0.5) * 2;
        y = (DRYER.radius - 0.5) * rf - f * f * (DRYER.radius * 1.7) * rf;
        z = (0.5 - rf) * 1.4 + f * 0.35;
      }
      bp[i * 3] = -half + axial * DRYER.length;
      bp[i * 3 + 1] = y;
      bp[i * 3 + 2] = z;
    }
    bedGeo.attributes.position.needsUpdate = true;

    // --- counter-current air ---------------------------------------------
    const ap = airGeo.attributes.position.array;
    for (let i = 0; i < N_AIR; i += 1) {
      const axial = (airSeeds[i * 3] - t * 0.10 + 10) % 1; // note the sign: opposite the bed
      airSeeds[i * 3] = (airSeeds[i * 3] + 0) % 1;
      const a = airSeeds[i * 3 + 1] + t * 0.5;
      const r = airSeeds[i * 3 + 2] * (DRYER.radius - 0.5);
      ap[i * 3] = -half + axial * DRYER.length;
      ap[i * 3 + 1] = Math.cos(a) * r;
      ap[i * 3 + 2] = Math.sin(a) * r;
    }
    airGeo.attributes.position.needsUpdate = true;

    // --- moisture to the exhaust -----------------------------------------
    const vp = vapGeo.attributes.position.array;
    for (let i = 0; i < N_VAPOUR; i += 1) {
      const u = (vapSeeds[i * 2] + t * 0.13) % 1;
      const spread = vapSeeds[i * 2 + 1];
      // rises out of the feed end and into the exhaust duct
      vp[i * 3] = -half - u * 2.2;
      vp[i * 3 + 1] = -0.4 + u * 7.4 + spread * 0.5;
      vp[i * 3 + 2] = (spread - 0.5) * 1.6 * (1 - u * 0.5);
    }
    vapGeo.attributes.position.needsUpdate = true;
  });

  return (
    <group ref={group} position={[DRYER.x, DRYER.y, DRYER.z]} rotation={[0, 0, INCLINE]}>
      <group ref={flights}>
        <primitive object={flightMesh} />
      </group>
      <points ref={bed} geometry={bedGeo} material={bedMat} />
      <points ref={air} geometry={airGeo} material={airMat} />
      <points ref={vapour} geometry={vapGeo} material={vapMat} />
    </group>
  );
}
