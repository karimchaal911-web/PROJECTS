import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { WLabel } from '../WorldText.jsx';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { STATIONS, chainCurve } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';

/**
 * The seven upstream stations of the verified soluble-MAP sequence, plus the
 * mother-liquor recycle line.
 *
 * Deliberately not a P&ID. Each station is a simplified credible vessel form
 * that lights when the material stream reaches it — the audience should read a
 * journey through a coupled chain, not decode a diagram. No tag, dimension or
 * equipment identity is claimed; the report explicitly refuses that mapping.
 */

export default function ProcessChain() {
  const group = useRef();
  const labels = useRef();
  const presence = useChannel('chain');
  const headRef = useChannel('chainHead', 0);

  const mats = useMemo(() => {
    const body = new THREE.MeshStandardMaterial({
      color: C.duct, roughness: 0.68, metalness: 0.45, transparent: true, opacity: 0,
    });
    const frame = new THREE.MeshStandardMaterial({
      color: C.steelGreen, roughness: 0.75, metalness: 0.3, transparent: true, opacity: 0,
    });
    return { body, frame };
  }, []);

  // Per-station emissive materials so each can light independently.
  const stationMats = useMemo(
    () => STATIONS.filter((s) => s.r > 0).map(() => new THREE.MeshStandardMaterial({
      color: C.duct,
      roughness: 0.65,
      metalness: 0.45,
      emissive: new THREE.Color(C.processWarm),
      emissiveIntensity: 0,
      transparent: true,
      opacity: 0,
    })),
    []
  );

  const positions = useMemo(
    () => STATIONS.filter((s) => s.r > 0).map((s) => chainCurve.getPoint(s.t / 0.98)),
    []
  );

  const pipeGeo = useMemo(() => new THREE.TubeGeometry(chainCurve, 120, 0.13, 8, false), []);
  const pipeMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.duct, roughness: 0.7, metalness: 0.5, transparent: true, opacity: 0,
  }), []);

  // Mother-liquor recycle: centrifugation back to neutralization.
  const recycle = useMemo(() => {
    const from = chainCurve.getPoint(STATIONS[5].t / 0.98);
    const to = chainCurve.getPoint(STATIONS[2].t / 0.98);
    const curve = new THREE.CatmullRomCurve3([
      from.clone().add(new THREE.Vector3(0, -1.6, 2.5)),
      new THREE.Vector3((from.x + to.x) / 2, 1.2, 9),
      to.clone().add(new THREE.Vector3(0, -1.4, 2.5)),
    ]);
    return new THREE.TubeGeometry(curve, 60, 0.09, 6, false);
  }, []);
  const recycleMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.ocpLeaf, roughness: 0.6, metalness: 0.3, transparent: true, opacity: 0,
  }), []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    mats.body.opacity = p;
    mats.frame.opacity = p;
    pipeMat.opacity = p * 0.8;
    recycleMat.opacity = p * 0.55;

    // Station names are only legible when the chain is the subject. Below
    // that they would float over the dryer as orphaned text.
    if (labels.current) labels.current.visible = p > 0.55;

    const head = headRef.current;
    stationMats.forEach((m, i) => {
      m.opacity = p;
      const st = STATIONS[i].t;
      // A station lights because the material arrived, not because time passed.
      const reached = THREE.MathUtils.clamp((head - st + 0.10) / 0.10, 0, 1);
      m.emissiveIntensity = reached * 0.22 * p;
    });
  });

  return (
    <group ref={group}>
      <mesh geometry={pipeGeo} material={pipeMat} />
      <mesh geometry={recycle} material={recycleMat} />

      {STATIONS.filter((s) => s.r > 0).map((s, i) => {
        const pos = positions[i];
        return (
          <group key={s.id} position={[pos.x, 0, pos.z]}>
            {/* vessel body — a lathe-like silhouette, simplified but plausible */}
            <mesh position={[0, s.h / 2, 0]} castShadow receiveShadow material={stationMats[i]}>
              <cylinderGeometry args={[s.r, s.r * 0.94, s.h, 24]} />
            </mesh>
            <mesh position={[0, s.h + s.r * 0.34, 0]} castShadow material={stationMats[i]}>
              <sphereGeometry args={[s.r, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2]} />
            </mesh>
            <mesh position={[0, 0.45, 0]} castShadow material={mats.frame}>
              <cylinderGeometry args={[s.r * 1.14, s.r * 1.14, 0.9, 20]} />
            </mesh>
            {/* support legs */}
            {[0, 1, 2, 3].map((k) => {
              const a = (k / 4) * Math.PI * 2 + Math.PI / 4;
              return (
                <mesh key={k} position={[Math.cos(a) * s.r * 0.9, s.h * 0.3, Math.sin(a) * s.r * 0.9]}
                  material={mats.frame}>
                  <boxGeometry args={[0.26, s.h * 0.6, 0.26]} />
                </mesh>
              );
            })}
          </group>
        );
      })}

      {/* Station names live in one group so they can be switched off wholesale
          when the chain recedes — otherwise they float over the dryer in later
          scenes as orphaned text. */}
      <group ref={labels}>
        {STATIONS.filter((s) => s.r > 0).map((s, i) => {
          const pos = positions[i];
          return (
            <WLabel
              key={s.id}
              position={[pos.x, s.h + s.r * 0.34 + 1.9, pos.z]}
              fontSize={0.86}
              color={C.dust}
              anchorX="center"
              anchorY="bottom"
              maxWidth={12}
              textAlign="center"
              outlineWidth={0}
              fillOpacity={0.72}
            >
              {s.label}
            </WLabel>
          );
        })}
      </group>
    </group>
  );
}
