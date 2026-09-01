import { useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
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
  const { camera } = useThree();
  const group = useRef();
  const labels = useRef();
  const presence = useChannel('arch');
  const build = useChannel('archBuild', 0);
  const align = useChannel('alignPause', 0);
  const labelCh = useChannel('archLabels', 0);
  const labelRefs = useRef([]);
  // Each name turns to face the lens.
  //
  // The labels used to lie in the stack's own plane, so at any oblique beat
  // camera they skewed and swung: the bottom layer's sub-label ran off the
  // right AND bottom edges while the top layer's ran off the top, and no
  // amount of pulling back fixed it because the distortion is geometric, not
  // a framing problem.
  const billboards = useRef([]);
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

    for (const bb of billboards.current) {
      if (bb) bb.quaternion.copy(camera.quaternion);
    }
    // Labels used to be gated all-or-nothing on presence, so for the whole
    // 7 s build up to eight names floated beside empty space and the
    // label-to-layer mapping — the entire point of the scene — was unreadable.
    // Each name now resolves with its own slab.
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
      // The ALIGN layer answers the residence lane in front of it. That lane's
      // two beats hold the stack at 13 % presence so its slabs stop competing
      // with the lane's own horizontals, and at that opacity a 0.7 emissive
      // rise is invisible — so the acknowledgement is carried by emission,
      // which is not multiplied down by the slab's transparency.
      m.emissiveIntensity = i === 2 ? 0.05 + align.current * 1.35 : 0.05;

      const lg = labelRefs.current[i];
      if (lg) {
        const lit = THREE.MathUtils.clamp(local * labelCh.current, 0, 1);
        lg.visible = lit > 0.03;
        lg.traverse((o) => {
          if (o.fillOpacity !== undefined) o.fillOpacity = lit * (o.userData?.base ?? 0.9);
        });
      }
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
          <group key={layer.id} position={[0, i * ARCH_STEP, 0]}
            ref={(el) => { labelRefs.current[i] = el; }}>
            <group position={[W / 2 + 1.4, 0, 0]}
              ref={(el) => { billboards.current[i] = el; }}>
              <WLabel position={[0, 0.36, 0]} fontSize={0.86} color={C.dustBright} fillOpacity={0.92}>
                {layer.label}
              </WLabel>
              <WMono position={[0, -0.48, 0]} fontSize={0.46} color={C.dataTeal} fillOpacity={0.65}>
                {layer.sub}
              </WMono>
            </group>
          </group>
        ))}
      </group>
    </group>
  );
}
