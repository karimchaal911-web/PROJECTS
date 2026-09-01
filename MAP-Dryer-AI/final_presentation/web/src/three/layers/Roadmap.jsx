import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { ROADMAP, ROADMAP_ORIGIN, ROADMAP_STEP } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';

/**
 * Built versus not built.
 *
 * This is the most important honesty signal in the presentation, so the
 * distinction is carried by four independent channels at once:
 *
 *   form      a solid volume versus a flat dashed outline
 *   line      continuous versus dashed
 *   colour    OCP green built, grey not built, amber conditional
 *   position  built first, along the rail, with a visible gap at the boundary
 *
 * Even in greyscale, on a bad projector, from the back of the room, a solid
 * block and a dashed outline cannot be confused. The two conditional stages
 * are amber rather than merely fainter: at 0.34 opacity they disappeared
 * instead of reading as conditional.
 *
 * LAYOUT. Twelve stages cannot be labelled at a projector-legible size inside
 * one 16:9 frame — the geometry does not allow it, and raising the type
 * without changing the layout simply traded 9 px labels for large ones that
 * overlapped each other and the band headers. The rail is therefore 72 units
 * long and the scene TRAVELS it: beat one frames what is built at ~36 px,
 * beat two trucks right and pulls back to place it against what is not, at
 * ~22 px. Each name arrives with its own block, never before it.
 */

const ORIGIN = new THREE.Vector3(...ROADMAP_ORIGIN);
const STEP = ROADMAP_STEP;

/** The gap that marks the boundary between delivered and not delivered. */
const FUTURE_OFFSET = 2.0;

/** A flat rectangle, dashed — deliberately NOT a volume. */
const OUTLINE_PTS = [
  [-1.5, -0.7, 0], [1.5, -0.7, 0], [1.5, 0.7, 0], [-1.5, 0.7, 0], [-1.5, -0.7, 0],
];

const xOf = (i) => i * STEP + (ROADMAP[i].built ? 0 : FUTURE_OFFSET);

export default function Roadmap() {
  const group = useRef();
  const presence = useChannel('roadmap');
  const today = useChannel('roadmapToday', 0);
  const next = useChannel('roadmapNext', 0);
  const refs = useRef([]);
  const labelRefs = useRef([]);
  const headToday = useRef();
  const headNext = useRef();
  const note = useRef();

  const built = ROADMAP.filter((r) => r.built);
  const future = ROADMAP.filter((r) => !r.built);

  const solidMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.ocpGreen, roughness: 0.5, metalness: 0.2,
    emissive: new THREE.Color(C.ocpGreen), emissiveIntensity: 0.1,
    transparent: true, opacity: 0,
  }), []);

  const boxGeo = useMemo(() => new THREE.BoxGeometry(3.0, 1.4, 1.0), []);
  const outlineRefs = useRef([]);

  const setText = (node, v) => {
    if (!node) return;
    node.visible = v > 0.03;
    node.traverse((o) => {
      if (o.fillOpacity !== undefined) o.fillOpacity = v * (o.userData?.base ?? 1);
    });
  };

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const t = today.current;
    const n = next.current;

    // On the second beat the built half is context, not subject: its blocks
    // stay solid — that contrast IS the honesty signal — but they step back so
    // the future half and the copy column both have room.
    solidMat.opacity = p * t * (1 - 0.45 * n);
    outlineRefs.current.forEach((l, i) => {
      if (!l?.material) return;
      l.material.opacity = p * n * (ROADMAP[i]?.conditional ? 0.9 : 1);
    });

    // The TODAY header steps back once the camera has travelled past its half
    // of the rail, so it never sits under the copy column in the wide framing.
    setText(headToday.current, p * t * (1 - n));
    setText(headNext.current, p * n);
    setText(note.current, p * n);

    ROADMAP.forEach((stage, i) => {
      const isBuilt = stage.built;
      const drive = isBuilt ? t : n;
      const localIndex = isBuilt ? i : i - built.length;
      const span = isBuilt ? built.length : future.length;
      const local = THREE.MathUtils.clamp(drive * span - localIndex, 0, 1);

      const g = refs.current[i];
      if (g) {
        g.visible = local > 0.01;
        g.scale.setScalar(Math.max(0.001, local));
      }
      // The name resolves with its own block. It used to be a sibling of the
      // staged group and was therefore always on, which is why every future
      // stage was already labelled during the "solid means built" beat.
      //
      // The built names also retire on the wide beat. Held at full strength
      // they landed underneath the headline and the note — "MEANS NOT YET."
      // was printed straight through "Causal alignment" and "Both models &
      // diagnosis" — on the one slide in the film that must be unambiguous.
      setText(labelRefs.current[i], p * local * (isBuilt ? 1 - n : 1));
    });
  });

  const builtMidX = (xOf(0) + xOf(built.length - 1)) / 2;
  const futureMidX = (xOf(built.length) + xOf(ROADMAP.length - 1)) / 2;
  const conditionalMidX = (xOf(ROADMAP.length - 2) + xOf(ROADMAP.length - 1)) / 2;

  return (
    <group ref={group} position={ORIGIN}>
      <group ref={headToday}>
        <WLabel position={[builtMidX, 5.8, 0]} fontSize={1.6}
          color={C.ocpGreen} anchorX="center" fillOpacity={1} userData={{ base: 1 }}>
          TODAY - BUILT
        </WLabel>
      </group>
      <group ref={headNext}>
        <WLabel position={[futureMidX, 5.8, 0]} fontSize={1.6}
          color="#4A5D55" anchorX="center" fillOpacity={1} userData={{ base: 1 }}>
          NEXT - NOT BUILT
        </WLabel>
      </group>
      <group ref={note}>
        <WMono position={[conditionalMidX, -6.6, 0]} fontSize={0.66}
          color={C.warn} anchorX="center" fillOpacity={1} userData={{ base: 1 }}>
          AMBER = CONDITIONAL, MAY NEVER BE BUILT
        </WMono>
      </group>

      {ROADMAP.map((stage, i) => (
        <group key={stage.label} position={[xOf(i), 0, 0]}>
          <group ref={(el) => { refs.current[i] = el; }}>
            {stage.built ? (
              <mesh geometry={boxGeo} material={solidMat} castShadow />
            ) : (
              <Line
                points={OUTLINE_PTS}
                color={stage.conditional ? C.warn : C.outline}
                lineWidth={stage.conditional ? 1.8 : 2.2}
                dashed
                dashSize={0.34}
                gapSize={0.26}
                transparent
                opacity={0}
                ref={(el) => { if (el) outlineRefs.current[i] = el; }}
              />
            )}
          </group>

          {/* Horizontal, centred, alternating above and below the rail, with
              a band deep enough for two lines and no deeper. Labels are short
              by construction; the full inventory is in the scene's note. */}
          <group ref={(el) => { labelRefs.current[i] = el; }}>
            <WLabel
              position={[0, i % 2 ? 2.0 : -2.0, 0]}
              fontSize={0.95}
              anchorX="center"
              anchorY={i % 2 ? 'bottom' : 'top'}
              textAlign="center"
              color={stage.built ? C.inkEditorial : stage.conditional ? '#8A5B10' : '#46584F'}
              fillOpacity={1}
              userData={{ base: 1 }}
              maxWidth={8.0}
            >
              {stage.label}
            </WLabel>
          </group>
        </group>
      ))}

      <Line
        points={[[xOf(0) - 3.2, 0, 0], [xOf(ROADMAP.length - 1) + 3.2, 0, 0]]}
        color={C.rule}
        lineWidth={1}
        transparent
        opacity={0.35}
      />
    </group>
  );
}
