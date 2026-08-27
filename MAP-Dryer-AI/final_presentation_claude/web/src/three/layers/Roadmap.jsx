import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { ROADMAP } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';

/**
 * Built versus not built.
 *
 * This is the most important honesty signal in the presentation, so the
 * distinction is carried by four redundant channels at once: material (solid
 * versus outline), opacity, line style, and position along the path. Even in
 * greyscale, on a bad projector, from the back of the room, a solid block and a
 * dashed outline cannot be confused.
 *
 * The last two stages are dimmer still, because they are conditional and do not
 * exist in any form today.
 */

const ORIGIN = new THREE.Vector3(-19, 19, 0);
const STEP = 4.0;

export default function Roadmap() {
  const group = useRef();
  const presence = useChannel('roadmap');
  const today = useChannel('roadmapToday', 0);
  const next = useChannel('roadmapNext', 0);
  const refs = useRef([]);

  const built = ROADMAP.filter((r) => r.built);
  const future = ROADMAP.filter((r) => !r.built);

  const solidMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.ocpGreen, roughness: 0.5, metalness: 0.2,
    emissive: new THREE.Color(C.ocpGreen), emissiveIntensity: 0.1,
    transparent: true, opacity: 0,
  }), []);

  const outlineMat = useMemo(() => new THREE.LineBasicMaterial({
    color: C.outline, transparent: true, opacity: 0,
  }), []);
  const outlineDim = useMemo(() => new THREE.LineBasicMaterial({
    color: C.outline, transparent: true, opacity: 0,
  }), []);

  const boxGeo = useMemo(() => new THREE.BoxGeometry(3.0, 1.0, 1.0), []);
  const edgeGeo = useMemo(() => new THREE.EdgesGeometry(boxGeo), [boxGeo]);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    solidMat.opacity = p * today.current;
    outlineMat.opacity = p * next.current * 0.75;
    outlineDim.opacity = p * next.current * 0.34;

    refs.current.forEach((g, i) => {
      if (!g) return;
      const isBuilt = i < built.length;
      const drive = isBuilt ? today.current : next.current;
      const localIndex = isBuilt ? i : i - built.length;
      const span = isBuilt ? built.length : future.length;
      const local = THREE.MathUtils.clamp(drive * span - localIndex, 0, 1);
      g.visible = local > 0.01;
      g.scale.setScalar(local);
    });
  });

  return (
    <group ref={group} position={ORIGIN}>
      <WLabel position={[0, 5.0, 0]} fontSize={1.0} color={C.ocpGreen} anchorX="center" fillOpacity={0.95}>
        TODAY
      </WLabel>
      <WLabel position={[built.length * STEP + 2.0, 5.0, 0]} fontSize={1.0}
        color={C.outline} anchorX="center" fillOpacity={0.9}>
        NEXT
      </WLabel>

      {ROADMAP.map((stage, i) => {
        const x = i * STEP + (stage.built ? 0 : 2.0);
        return (
          <group key={stage.label} position={[x, 0, 0]}>
            <group ref={(el) => { refs.current[i] = el; }}>
              {stage.built ? (
                <mesh geometry={boxGeo} material={solidMat} castShadow />
              ) : (
                <lineSegments
                  geometry={edgeGeo}
                  material={stage.conditional ? outlineDim : outlineMat}
                />
              )}
            </group>
            {/* Horizontal, centred, alternating above and below the rail.
                Diagonal labels collided with each other and with the headers. */}
            <WMono
              position={[0, i % 2 ? 1.5 : -1.6, 0]}
              fontSize={0.36}
              anchorX="center"
              anchorY={i % 2 ? 'bottom' : 'top'}
              textAlign="center"
              color={stage.built ? C.inkEditorial : C.outline}
              fillOpacity={stage.built ? 0.95 : stage.conditional ? 0.6 : 0.85}
              maxWidth={3.7}
            >
              {stage.label}
            </WMono>
          </group>
        );
      })}

      <Line
        points={[[-1.6, 0, 0], [ROADMAP.length * STEP + 2.6, 0, 0]]}
        color={C.rule}
        lineWidth={1}
        transparent
        opacity={0.35}
      />

    </group>
  );
}
