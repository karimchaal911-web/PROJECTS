import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { AXIS, AXIS_LEN, timeToX, makeTimeMapper, makeMoistureMapper } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';
import { getData, extent } from '../../data/load.js';

/**
 * The time axis, the six laboratory markers and the continuous soft-sensor
 * trace — the geometry at the centre of the argument.
 *
 * These three live together because they share one mapping. The axis is not a
 * chart drawn in space: it is the material flow line after `straighten` has
 * gone 0 → 1, and every temporal object resolves its x from the same function,
 * so they are guaranteed to register with each other.
 *
 * Data: gap.json — a real 12-hour held-out TEST window, 695 soft-sensor
 * estimates reproducing the runtime residence-time alignment, and the six
 * laboratory samples that actually landed inside it.
 */

export default function TimeAxis() {
  const gap = getData().gap;

  const model = useMemo(() => {
    const t = gap.t ?? [];
    if (!t.length) return null;

    const toX = makeTimeMapper(gap.start, gap.end);
    const preds = gap.predicted ?? [];
    const labM = gap.lab?.moisture ?? [];
    const [lo, hi] = extent([...preds, ...labM]);
    // Pad the domain slightly so the extremes are not glued to the frame.
    const pad = (hi - lo) * 0.22 || 0.001;
    const toY = makeMoistureMapper(lo - pad, hi + pad, 9);

    const tracePts = t.map((iso, i) => new THREE.Vector3(toX(iso), toY(preds[i]), 0));
    const labs = (gap.lab?.t ?? []).map((iso, i) => ({
      iso,
      x: toX(iso),
      y: toY(labM[i]),
      moisture: labM[i],
      clock: iso.slice(11, 16),
    }));

    // Hour ticks across the 12-hour window.
    const ticks = [];
    for (let h = 0; h <= AXIS.hours; h += 2) {
      ticks.push({ x: timeToX(h / AXIS.hours), label: `${String(h).padStart(2, '0')}:00` });
    }

    return { tracePts, labs, ticks, lo: lo - pad, hi: hi + pad, toY };
  }, [gap]);

  return (
    <>
      <Axis ticks={model?.ticks ?? []} />
      <LabMarkers labs={model?.labs ?? []} />
      <PredictTrace points={model?.tracePts ?? []} />
    </>
  );
}

/* ------------------------------------------------------------------ axis --- */

function Axis({ ticks }) {
  const group = useRef();
  const lineRef = useRef();
  const presence = useChannel('axis');
  const draw = useChannel('axisDraw', 0);
  const matRef = useRef();

  const pts = useMemo(() => [
    new THREE.Vector3(AXIS.x0, AXIS.y, 0),
    new THREE.Vector3(AXIS.x1, AXIS.y, 0),
  ], []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    if (lineRef.current) {
      lineRef.current.material.opacity = p * 0.55;
      // the axis extends as the flow line straightens
      lineRef.current.scale.x = Math.max(0.001, draw.current);
    }
    if (matRef.current) matRef.current.opacity = p * 0.045;
  });

  return (
    <group ref={group}>
      {/* the axis itself, scaled from its origin so it grows to the right */}
      <group position={[AXIS.x0, 0, 0]}>
        <Line
          ref={lineRef}
          points={[[0, AXIS.y, 0], [AXIS_LEN, AXIS.y, 0]]}
          color={C.outline}
          lineWidth={1.5}
          transparent
          opacity={0}
        />
      </group>

      {/* the quality plane: visible as an emptiness, not as a surface */}
      <mesh position={[(AXIS.x0 + AXIS.x1) / 2, AXIS.y + 5.4, -0.05]}>
        <planeGeometry args={[AXIS_LEN, 10.8]} />
        <meshBasicMaterial
          ref={matRef}
          color={C.dataTeal}
          transparent
          opacity={0}
          depthWrite={false}
          side={THREE.DoubleSide}
        />
      </mesh>

      {ticks.map((t) => (
        <group key={t.label} position={[t.x, AXIS.y, 0]}>
          <Line points={[[0, -0.45, 0], [0, 0.45, 0]]} color={C.outline} lineWidth={1} transparent opacity={0.4} />
          <WMono position={[0, -1.7, 0]} fontSize={0.92} color={C.outline} anchorX="center" fillOpacity={0.7}>
            {t.label}
          </WMono>
        </group>
      ))}

      <WMono position={[AXIS.x0, AXIS.y - 3.4, 0]} fontSize={0.86} color={C.outline} fillOpacity={0.55}>
        HELD-OUT TEST · 2026-07-05 · 12 HOURS · PROTOTYPE REPLAY
      </WMono>
    </group>
  );
}

/* ------------------------------------------------------------ lab markers --- */

function LabMarkers({ labs }) {
  const group = useRef();
  const presence = useChannel('lab');
  const rise = useChannel('labRise', 0);
  const refs = useRef([]);

  const sphereMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.lab,
    emissive: new THREE.Color(C.lab),
    emissiveIntensity: 0.9,
    roughness: 0.3,
    transparent: true,
    opacity: 0,
  }), []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    sphereMat.opacity = p;
    const r = rise.current;
    refs.current.forEach((g, i) => {
      if (!g) return;
      // staggered arrival: each marker gets its own slice of the rise channel
      const local = THREE.MathUtils.clamp((r - i * 0.09) / 0.5, 0, 1);
      g.scale.setScalar(local);
      g.visible = local > 0.001;
    });
  });

  return (
    <group ref={group}>
      {labs.map((lab, i) => (
        <group key={lab.iso} ref={(el) => { refs.current[i] = el; }} position={[lab.x, 0, 0]}>
          {/* drop line to the axis: the measurement is anchored in time */}
          <Line
            points={[[0, AXIS.y, 0], [0, lab.y, 0]]}
            color={C.lab}
            lineWidth={1}
            transparent
            opacity={0.35}
          />
          <mesh position={[0, lab.y, 0]} material={sphereMat}>
            <sphereGeometry args={[0.4, 16, 12]} />
          </mesh>
          <WMono position={[0.62, lab.y + 1.3, 0]} fontSize={0.95} color={C.lab} fillOpacity={0.95}>
            {lab.moisture?.toFixed(4)}
          </WMono>
          <WMono position={[0.62, lab.y + 0.38, 0]} fontSize={0.6} color={C.lab} fillOpacity={0.55}>
            {`LAB ${lab.clock}`}
          </WMono>
        </group>
      ))}
    </group>
  );
}

/* ----------------------------------------------------------- predict trace --- */

function PredictTrace({ points }) {
  const ref = useRef();
  const presence = useChannel('trace');
  const draw = useChannel('traceDraw', 0);

  const flat = useMemo(() => points.map((p) => [p.x, p.y, p.z]), [points]);

  useFrame(() => {
    const p = presence.current;
    const line = ref.current;
    if (!line) return;
    line.visible = p > 0.01 && flat.length > 1;
    if (!line.visible) return;
    line.material.opacity = p;
    // The trace is written left to right at reading speed, driven by the
    // arriving signals rather than by a timer.
    const n = Math.max(1, Math.floor(draw.current * (flat.length - 1)));
    if (line.geometry?.instanceCount !== undefined) line.geometry.instanceCount = n;
  });

  if (flat.length < 2) return null;

  return (
    <Line
      ref={ref}
      points={flat}
      color={C.predict}
      lineWidth={2.4}
      transparent
      opacity={0}
    />
  );
}
