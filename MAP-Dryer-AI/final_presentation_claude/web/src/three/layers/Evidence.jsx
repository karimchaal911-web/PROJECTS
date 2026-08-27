import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C, riskColor } from '../../lib/palette.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';
import { getData, extent } from '../../data/load.js';

/**
 * The evidence, rebuilt as geometry from the verified artifacts.
 *
 * The charts are native, animatable and projector-legible, but every value is
 * byte-identical to the notebook output: holdout.json and anomaly.json are
 * produced by data_build/extract_presentation_data.py, which re-derives the
 * metrics from the exact model artifacts and asserts them against
 * artifacts/notebook03_model_evaluation.json.
 *
 * Panel A — 165 chronological held-out laboratory targets, actual vs predicted.
 * Panel B — the four-hour close-up in which the unsupervised detector's risk
 *           rises inside a labelled disturbance it never saw.
 */

const PANEL = {
  x0: 68, x1: 96,
  aY0: 15.4, aY1: 22.4,   // moisture hold-out
  bY0: -19.6, bY1: -12.6, // anomaly close-up
  side: 68,
};
const CANDIDATES_Y = 6.0;
const LIMITS_Y = -27.0;

export default function Evidence() {
  const group = useRef();
  const presence = useChannel('evidence');
  const beat = useChannel('evidenceBeat', 0);

  return (
    <group ref={group}>
      <PanelA presence={presence} beat={beat} />
      <Candidates presence={presence} beat={beat} />
      <PanelB presence={presence} beat={beat} />
      <Limits presence={presence} beat={beat} />
    </group>
  );
}

function useFade(presence, beat, from, to = 99) {
  const ref = useRef();
  useFrame(() => {
    const g = ref.current;
    if (!g) return;
    const b = beat.current;
    // Blocks the camera is not looking at are hidden outright. Dimming them
    // was not enough on a cream ground: they read as ghosting.
    const on = b >= from - 0.5 && b <= to + 0.5;
    const p = on ? presence.current : 0;
    g.visible = p > 0.02;
    g.traverse((o) => {
      if (o.material && o.material.transparent) {
        const max = o.material.userData.maxOpacity ?? 1;
        o.material.opacity = max * p;
      }
    });
  });
  return ref;
}

/* --------------------------------------------------------------- panel A --- */

function PanelA({ presence, beat }) {
  const ref = useFade(presence, beat, 1);
  const lineRef = useRef();
  const draw = useChannel('evidencePoints', 0);

  const model = useMemo(() => {
    const h = getData().holdout;
    const actual = h.actual ?? [];
    const pred = h.predicted ?? [];
    if (!actual.length) return null;
    const [lo, hi] = extent([...actual, ...pred]);
    const pad = (hi - lo) * 0.12 || 0.001;
    const y0 = lo - pad;
    const y1 = hi + pad;
    const toX = (i) => PANEL.x0 + (i / (actual.length - 1)) * (PANEL.x1 - PANEL.x0);
    const toY = (v) => PANEL.aY0 + ((v - y0) / (y1 - y0)) * (PANEL.aY1 - PANEL.aY0);

    return {
      n: actual.length,
      metrics: h.metrics ?? {},
      start: h.start, end: h.end,
      predPts: pred.map((v, i) => [toX(i), toY(v), 0]),
      actualPts: actual.map((v, i) => [toX(i), toY(v)]),
      yTicks: [y0 + (y1 - y0) * 0.15, (y0 + y1) / 2, y1 - (y1 - y0) * 0.15]
        .map((v) => ({ v, y: toY(v) })),
    };
  }, []);

  const dotMat = useMemo(() => {
    const m = new THREE.MeshBasicMaterial({
      color: C.inkEditorial, transparent: true, opacity: 0, depthWrite: false,
    });
    m.userData.maxOpacity = 0.95;
    return m;
  }, []);
  const dots = useRef();
  const dotGeo = useMemo(() => new THREE.CircleGeometry(0.17, 12), []);

  useFrame(() => {
    const n = model?.n ?? 0;
    if (!n) return;
    const u = THREE.MathUtils.clamp(draw.current, 0, 1);
    if (lineRef.current?.geometry?.instanceCount !== undefined) {
      lineRef.current.geometry.instanceCount = Math.max(1, Math.floor(u * (n - 1)));
    }
    if (dots.current) {
      const shown = Math.floor(u * n);
      const o = new THREE.Object3D();
      for (let i = 0; i < n; i += 1) {
        const p = model.actualPts[i];
        o.position.set(p[0], p[1], 0.02);
        o.scale.setScalar(i < shown ? 1 : 0.0001);
        o.updateMatrix();
        dots.current.setMatrixAt(i, o.matrix);
      }
      dots.current.instanceMatrix.needsUpdate = true;
    }
  });

  if (!model) return null;
  const m = model.metrics;
  // In-world mono labels avoid the subscript glyph; the DOM overlay, which
  // uses the full Inter subset, still writes the proper % H₂O.

  return (
    <group ref={ref}>
      <Frame x0={PANEL.x0} x1={PANEL.x1} y0={PANEL.aY0} y1={PANEL.aY1} />

      <WLabel position={[PANEL.x0, PANEL.aY1 + 2.5, 0]} fontSize={1.15}
        color={C.inkEditorial} fillOpacity={1}>
        MOISTURE SOFT SENSOR — HELD-OUT TEST
      </WLabel>
      <WMono position={[PANEL.x0, PANEL.aY1 + 1.4, 0]} fontSize={0.46}
        color={C.ocpGreen} fillOpacity={0.85}>
        {`n = ${model.n} LABORATORY TARGETS · ${model.start?.slice(0, 10)} → ${model.end?.slice(0, 10)} · CHRONOLOGICAL`}
      </WMono>

      {model.yTicks.map((t) => (
        <group key={t.v}>
          <Line points={[[PANEL.x0, t.y, -0.02], [PANEL.x1, t.y, -0.02]]}
            color={C.rule} lineWidth={1} transparent opacity={0.45} />
          <WMono position={[PANEL.x0 - 0.5, t.y, 0]} fontSize={0.42} color={C.outline}
            anchorX="right" fillOpacity={0.8}>
            {t.v.toFixed(4)}
          </WMono>
        </group>
      ))}

      <Line ref={lineRef} points={model.predPts} color={C.predict} lineWidth={2.6}
        transparent opacity={0.95} />
      <instancedMesh ref={dots} args={[dotGeo, dotMat, model.n]} frustumCulled={false} />

      {/* legend, in the terms the project uses */}
      <group position={[PANEL.x0, PANEL.aY0 - 1.1, 0]}>
        <mesh position={[0.15, 0, 0]} material={dotMat}>
          <circleGeometry args={[0.17, 12]} />
        </mesh>
        <WMono position={[0.6, 0, 0]} fontSize={0.42} color={C.inkEditorial} fillOpacity={0.75}>
          LABORATORY MEASUREMENT
        </WMono>
        <Line points={[[8.6, 0, 0], [9.8, 0, 0]]} color={C.predict} lineWidth={2.6} transparent opacity={0.95} />
        <WMono position={[10.2, 0, 0]} fontSize={0.42} color={C.inkEditorial} fillOpacity={0.75}>
          PREDICTED · % H2O
        </WMono>
      </group>

      {/* the three headline metrics — and only three */}
      <group position={[PANEL.x0, PANEL.aY0 - 3.4, 0]}>
        {[
          ['R²', m.r2?.toFixed(4)],
          ['MAE', `${m.mae?.toFixed(5)} % H2O`],
          ['RMSE', `${m.rmse?.toFixed(5)} % H2O`],
        ].map(([k, v], i) => (
          <group key={k} position={[i * 10.2, 0, 0]}>
            <WMono fontSize={0.44} color={C.ocpGreen} fillOpacity={0.8}>{k}</WMono>
            <WMono position={[0, -1.15, 0]} fontSize={1.05} color={C.inkEditorial} fillOpacity={1}>
              {v ?? '—'}
            </WMono>
          </group>
        ))}
      </group>
    </group>
  );
}

/* ------------------------------------------------------------ candidates --- */

function Candidates({ presence, beat }) {
  const ref = useFade(presence, beat, 2, 2);

  const rows = useMemo(() => {
    const c = getData().candidates?.candidates ?? [];
    if (!c.length) return [];
    const max = Math.max(...c.map((r) => r.valRmse));
    return c.map((r) => ({ ...r, norm: r.valRmse / max }));
  }, []);

  const barMat = useMemo(() => {
    const m = new THREE.MeshBasicMaterial({ color: C.ocpGreen, transparent: true, opacity: 0 });
    m.userData.maxOpacity = 0.9;
    return m;
  }, []);
  const dimMat = useMemo(() => {
    const m = new THREE.MeshBasicMaterial({ color: C.outline, transparent: true, opacity: 0 });
    m.userData.maxOpacity = 0.45;
    return m;
  }, []);

  if (!rows.length) return null;

  return (
    <group ref={ref} position={[PANEL.x0, CANDIDATES_Y, 0]}>
      <WMono fontSize={0.5} color={C.ocpGreen} fillOpacity={0.85}>
        CANDIDATE SELECTION — VALIDATION RMSE, TIME-AWARE TUNING ON TRAIN ONLY
      </WMono>
      {rows.map((r, i) => (
        <group key={r.name} position={[0, -1.5 - i * 1.15, 0]}>
          <WMono position={[9.2, 0, 0]} fontSize={0.46} anchorX="right"
            color={r.selected ? C.inkEditorial : C.outline} fillOpacity={r.selected ? 1 : 0.75}>
            {r.name}
          </WMono>
          <mesh position={[9.8 + (r.norm * 16) / 2, 0, 0]} material={r.selected ? barMat : dimMat}>
            <boxGeometry args={[r.norm * 16, 0.42, 0.02]} />
          </mesh>
          <WMono position={[26.4, 0, 0]} fontSize={0.46}
            color={r.selected ? C.ocpGreen : C.outline} fillOpacity={r.selected ? 1 : 0.7}>
            {r.valRmse.toFixed(6)}
          </WMono>
        </group>
      ))}
      <WMono position={[0, -1.5 - rows.length * 1.15 - 0.8, 0]} fontSize={0.44}
        color={C.inkEditorial} fillOpacity={0.7}>
        The regularised linear model won. Nothing here needed to be complicated.
      </WMono>
    </group>
  );
}

/* --------------------------------------------------------------- panel B --- */

function PanelB({ presence, beat }) {
  const ref = useFade(presence, beat, 3);

  const model = useMemo(() => {
    const a = getData().anomaly;
    const ev = a.event ?? {};
    const t = ev.t ?? [];
    const risk = ev.risk ?? [];
    if (!t.length) return null;

    const toX = (i) => PANEL.x0 + (i / (t.length - 1)) * (PANEL.x1 - PANEL.x0);
    const toY = (v) => PANEL.bY0 + THREE.MathUtils.clamp(v, 0, 1) * (PANEL.bY1 - PANEL.bY0);

    const pts = risk.map((v, i) => [toX(i), toY(v ?? 0), 0]);
    const colors = risk.map((v) => new THREE.Color(riskColor(v ?? 0)));

    const inEvent = ev.inEvent ?? [];
    let s = inEvent.indexOf(true);
    let e = inEvent.lastIndexOf(true);
    if (s < 0) { s = 0; e = 0; }

    return {
      pts, colors,
      warnY: toY(a.warning ?? 0.5),
      critY: toY(a.critical ?? 0.8),
      eventX0: toX(s), eventX1: toX(e),
      ev,
      startClock: t[0]?.slice(11, 16),
      endClock: t[t.length - 1]?.slice(11, 16),
      date: t[0]?.slice(0, 10),
    };
  }, []);

  const riskGeo = useMemo(() => {
    if (!model) return null;
    const g = new THREE.BufferGeometry();
    const pos = new Float32Array(model.pts.length * 3);
    const col = new Float32Array(model.pts.length * 3);
    model.pts.forEach((p, i) => {
      pos[i * 3] = p[0]; pos[i * 3 + 1] = p[1]; pos[i * 3 + 2] = 0.02;
      const c = model.colors[i];
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    });
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    return g;
  }, [model]);

  const riskMat = useMemo(() => {
    const m = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0 });
    m.userData.maxOpacity = 1;
    return m;
  }, []);

  const bandMat = useMemo(() => {
    const warn = new THREE.MeshBasicMaterial({ color: C.warn, transparent: true, opacity: 0, depthWrite: false });
    warn.userData.maxOpacity = 0.09;
    const crit = new THREE.MeshBasicMaterial({ color: C.critical, transparent: true, opacity: 0, depthWrite: false });
    crit.userData.maxOpacity = 0.09;
    const ev = new THREE.MeshBasicMaterial({ color: C.critical, transparent: true, opacity: 0, depthWrite: false });
    ev.userData.maxOpacity = 0.14;
    return { warn, crit, ev };
  }, []);

  if (!model) return null;
  const ev = model.ev;

  return (
    <group ref={ref}>
      <Frame x0={PANEL.x0} x1={PANEL.x1} y0={PANEL.bY0} y1={PANEL.bY1} />

      <WLabel position={[PANEL.x0, PANEL.bY1 + 2.5, 0]} fontSize={1.15}
        color={C.inkEditorial} fillOpacity={1}>
        ANOMALY DETECTOR — HELD-OUT TEST
      </WLabel>
      <WMono position={[PANEL.x0, PANEL.bY1 + 1.4, 0]} fontSize={0.46}
        color={C.ocpGreen} fillOpacity={0.85}>
        {`${model.date} · ${model.startClock} → ${model.endClock} · DISPLAY RISK, NOT A PROBABILITY`}
      </WMono>

      {/* threshold bands */}
      <mesh position={[(PANEL.x0 + PANEL.x1) / 2, (model.warnY + model.critY) / 2, -0.03]} material={bandMat.warn}>
        <planeGeometry args={[PANEL.x1 - PANEL.x0, model.critY - model.warnY]} />
      </mesh>
      <mesh position={[(PANEL.x0 + PANEL.x1) / 2, (model.critY + PANEL.bY1) / 2, -0.03]} material={bandMat.crit}>
        <planeGeometry args={[PANEL.x1 - PANEL.x0, PANEL.bY1 - model.critY]} />
      </mesh>

      {/* the labelled synthetic disturbance */}
      <mesh position={[(model.eventX0 + model.eventX1) / 2, (PANEL.bY0 + PANEL.bY1) / 2, -0.02]}
        material={bandMat.ev}>
        <planeGeometry args={[Math.max(0.2, model.eventX1 - model.eventX0), PANEL.bY1 - PANEL.bY0]} />
      </mesh>
      <WMono position={[model.eventX0, PANEL.bY1 + 0.45, 0]} fontSize={0.44}
        color={C.critical} fillOpacity={0.9}>
        {`LABELLED ${String(ev.label ?? '').toUpperCase()} · ${ev.durationMinutes ?? '—'} min`}
      </WMono>

      <Line points={[[PANEL.x0, model.warnY, 0], [PANEL.x1, model.warnY, 0]]}
        color={C.warn} lineWidth={1.2} dashed dashSize={0.5} gapSize={0.35}
        transparent opacity={0.8} />
      <Line points={[[PANEL.x0, model.critY, 0], [PANEL.x1, model.critY, 0]]}
        color={C.critical} lineWidth={1.2} dashed dashSize={0.5} gapSize={0.35}
        transparent opacity={0.8} />
      {/* Inside the plot: at the frame edge these were clipped by the 16:9
          safe area on the exported stills. */}
      <WMono position={[PANEL.x0 + 0.4, model.warnY + 0.42, 0]} fontSize={0.42}
        color={C.warn} fillOpacity={0.95}>
        WARNING 0.50
      </WMono>
      <WMono position={[PANEL.x0 + 0.4, model.critY + 0.42, 0]} fontSize={0.42}
        color={C.critical} fillOpacity={0.95}>
        CRITICAL 0.80
      </WMono>

      {riskGeo && <line geometry={riskGeo} material={riskMat} frustumCulled={false} />}

      {/* the finding, stated with its qualifier attached */}
      <group position={[PANEL.x0, PANEL.bY0 - 3.2, 0]}>
        {[
          ['MEAN RISK IN EVENT', ev.riskInEventMean?.toFixed(3)],
          ['MEAN RISK OUTSIDE', ev.riskOutEventMean?.toFixed(3)],
          ['WARNING POINTS INSIDE', `${ev.warningPointsInsideEvent ?? '—'}/${ev.warningPointsTotal ?? '—'}`],
        ].map(([k, v], i) => (
          <group key={k} position={[i * 10.2, 0, 0]}>
            <WMono fontSize={0.42} color={C.ocpGreen} fillOpacity={0.8}>{k}</WMono>
            <WMono position={[0, -1.1, 0]} fontSize={1.05} color={C.inkEditorial} fillOpacity={1}>
              {v ?? '—'}
            </WMono>
          </group>
        ))}
      </group>

      <WMono position={[PANEL.x0, PANEL.bY0 - 1.4, 0]} fontSize={0.5}
        color={C.critical} fillOpacity={0.95}>
        THE DETECTOR IS UNSUPERVISED AND NEVER SAW THIS LABEL
      </WMono>
    </group>
  );
}

/* ---------------------------------------------------------------- limits --- */

function Limits({ presence, beat }) {
  const ref = useFade(presence, beat, 4, 4);
  const lines = [
    'Synthetic prototype dataset — disturbances and labels come from the generator.',
    'Chronological hold-out: no future information reaches training or selection.',
    'Anomaly risk is a calibrated display score, not a probability of failure.',
    'Diagnosis localises evidence; it does not prove root cause.',
    'Advisory only. This is not plant validation.',
  ];
  return (
    <group ref={ref} position={[PANEL.x0, LIMITS_Y, 0.3]}>
      <WLabel fontSize={1.15} color={C.inkEditorial} fillOpacity={1}>
        WHAT THIS EVIDENCE IS WORTH
      </WLabel>
      {lines.map((l, i) => (
        <WMono key={l} position={[0, -1.9 - i * 1.25, 0]} fontSize={0.52}
          color={C.inkEditorial} fillOpacity={0.82}>
          {`— ${l}`}
        </WMono>
      ))}
    </group>
  );
}

/* ----------------------------------------------------------------- frame --- */

function Frame({ x0, x1, y0, y1 }) {
  return (
    <Line
      points={[[x0, y0, 0], [x1, y0, 0]]}
      color={C.rule}
      lineWidth={1.4}
      transparent
      opacity={0.7}
    />
  );
}
