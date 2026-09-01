import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C, riskColor } from '../../lib/palette.js';
import { EVIDENCE_PANELS } from '../../lib/curves.js';
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
 * The four panels used to be stacked on one vertical wall, which forced the
 * camera to make three identical downward drops — scrolling, not filming.
 * They are now four stations along a corridor that runs from the model region
 * to the operator's screen, each with its own position and heading, so the
 * camera can approach, truck, arc and pull back. Panel geometry is authored in
 * LOCAL coordinates and placed by EVIDENCE_PANELS.
 */

const PW = 28;     // panel content width, local
const CHART_H = 7;

/** Each panel is on screen for its own beat only. */
function usePanel(index) {
  const ref = useRef();
  const presence = useChannel('evidence');
  const beat = useChannel('evidenceBeat', 0);
  useFrame(() => {
    const g = ref.current;
    if (!g) return;
    // Distance from this panel's own beat number, so a panel fades out as the
    // next fades in instead of popping off at the midpoint of a tween — and
    // no panel survives into a beat that is not about it.
    const d = Math.abs(beat.current - (index + 1));
    const near = THREE.MathUtils.clamp(1 - d, 0, 1);
    const p = presence.current * near;
    g.visible = p > 0.02;
    if (!g.visible) return;
    g.traverse((o) => {
      if (o.material && o.material.transparent) {
        const max = o.material.userData.maxOpacity ?? 1;
        o.material.opacity = max * p;
      }
      if (o.isMesh === undefined && o.fillOpacity !== undefined) o.fillOpacity = p;
    });
  });
  return ref;
}

function Panel({ index, children }) {
  const anchor = EVIDENCE_PANELS[index];
  const ref = usePanel(index);
  return (
    <group position={anchor.pos} rotation={[0, anchor.yaw, 0]}>
      <group ref={ref}>{children}</group>
    </group>
  );
}

export default function Evidence() {
  return (
    <group>
      <PanelA />
      <Candidates />
      <PanelB />
      <Limits />
    </group>
  );
}

/* --------------------------------------------------------------- panel A --- */

function PanelA() {
  const lineRef = useRef();
  const draw = useChannel('evidencePoints', 0);
  const done = useRef(false);

  const model = useMemo(() => {
    const h = getData().holdout;
    const actual = h.actual ?? [];
    const pred = h.predicted ?? [];
    if (!actual.length) return null;
    const [lo, hi] = extent([...actual, ...pred]);
    const pad = (hi - lo) * 0.12 || 0.001;
    const y0 = lo - pad;
    const y1 = hi + pad;
    const toX = (i) => -PW / 2 + (i / (actual.length - 1)) * PW;
    const toY = (v) => -CHART_H / 2 + ((v - y0) / (y1 - y0)) * CHART_H;

    // Round tick values rather than 15/50/85 % of the range, which produced
    // unreadable numbers like 0.0801 / 0.0734 / 0.0666.
    const step = 0.005;
    const ticks = [];
    for (let v = Math.ceil(y0 / step) * step; v <= y1; v += step) {
      ticks.push({ v, y: toY(v) });
    }

    // An x-axis. The scene's whole claim is that the hold-out is
    // CHRONOLOGICAL, and the chart had no time axis of any kind.
    const times = h.t ?? [];
    const xTicks = [];
    if (times.length) {
      for (let k = 0; k <= 4; k += 1) {
        const i = Math.round((k / 4) * (times.length - 1));
        xTicks.push({ x: toX(i), label: String(times[i] ?? '').slice(5, 10) });
      }
    }

    return {
      n: actual.length,
      metrics: h.metrics ?? {},
      start: h.start, end: h.end,
      predPts: pred.map((v, i) => [toX(i), toY(v), 0]),
      actualPts: actual.map((v, i) => [toX(i), toY(v)]),
      ticks, xTicks,
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
    // Once the 165 points have arrived they never change again. This loop used
    // to rebuild and re-upload all 165 instance matrices every frame for the
    // rest of the show, including the scenes where the layer is invisible.
    if (done.current && u >= 1) return;
    done.current = u >= 1;
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

  return (
    <Panel index={0}>
      <WLabel position={[-PW / 2, CHART_H / 2 + 2.6, 0]} fontSize={1.15}
        color={C.inkEditorial} fillOpacity={1}>
        MOISTURE SOFT SENSOR - HELD-OUT TEST
      </WLabel>
      <WMono position={[-PW / 2, CHART_H / 2 + 1.5, 0]} fontSize={0.46}
        color={C.ocpGreen} fillOpacity={0.85}>
        {`n = ${model.n} LABORATORY TARGETS - ${model.start?.slice(0, 10)} -> ${model.end?.slice(0, 10)} - CHRONOLOGICAL`}
      </WMono>

      {model.ticks.map((t) => (
        <group key={t.v}>
          <Line points={[[-PW / 2, t.y, -0.02], [PW / 2, t.y, -0.02]]}
            color={C.rule} lineWidth={1} transparent opacity={0.45} />
          <WMono position={[-PW / 2 - 0.5, t.y, 0]} fontSize={0.44} color={C.outline}
            anchorX="right" fillOpacity={0.85}>
            {t.v.toFixed(3)}
          </WMono>
        </group>
      ))}

      {/* the x-axis the chart never had */}
      <Line points={[[-PW / 2, -CHART_H / 2, 0], [PW / 2, -CHART_H / 2, 0]]}
        color={C.rule} lineWidth={1.4} transparent opacity={0.7} />
      {model.xTicks.map((t) => (
        <group key={t.label + t.x}>
          <Line points={[[t.x, -CHART_H / 2, 0], [t.x, -CHART_H / 2 - 0.32, 0]]}
            color={C.rule} lineWidth={1} transparent opacity={0.6} />
          <WMono position={[t.x, -CHART_H / 2 - 0.95, 0]} fontSize={0.44}
            color={C.outline} anchorX="center" fillOpacity={0.85}>
            {t.label}
          </WMono>
        </group>
      ))}

      {/* C.predict on cream is ~1.6:1 — the most important line in the act was
          the least legible element on screen. This is the same hue, taken dark
          enough to survive a projector. */}
      <Line ref={lineRef} points={model.predPts} color={C.predictInk} lineWidth={3.0}
        transparent opacity={0.98} />
      <instancedMesh ref={dots} args={[dotGeo, dotMat, model.n]} frustumCulled={false} />

      <group position={[-PW / 2, -CHART_H / 2 - 2.2, 0]}>
        <mesh position={[0.15, 0, 0]} material={dotMat}>
          <circleGeometry args={[0.17, 12]} />
        </mesh>
        <WMono position={[0.6, 0, 0]} fontSize={0.44} color={C.inkEditorial} fillOpacity={0.8}>
          LABORATORY MEASUREMENT
        </WMono>
        <Line points={[[9.0, 0, 0], [10.2, 0, 0]]} color={C.predictInk} lineWidth={3.0} transparent opacity={0.98} />
        <WMono position={[10.6, 0, 0]} fontSize={0.44} color={C.inkEditorial} fillOpacity={0.8}>
          PREDICTED MOISTURE - %
        </WMono>
      </group>

      <group position={[-PW / 2, -CHART_H / 2 - 4.4, 0]}>
        {[
          ['R2', m.r2?.toFixed(4)],
          ['MAE', `${m.mae?.toFixed(5)} %`],
          ['RMSE', `${m.rmse?.toFixed(5)} %`],
        ].map(([k, v], i) => (
          <group key={k} position={[i * 10.2, 0, 0]}>
            <WMono fontSize={0.44} color={C.ocpGreen} fillOpacity={0.85}>{k}</WMono>
            <WMono position={[0, -1.15, 0]} fontSize={1.05} color={C.inkEditorial} fillOpacity={1}>
              {v ?? '—'}
            </WMono>
          </group>
        ))}
      </group>
    </Panel>
  );
}

/* ------------------------------------------------------------ candidates --- */

function Candidates() {
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
    m.userData.maxOpacity = 0.5;
    return m;
  }, []);

  if (!rows.length) return null;

  return (
    <Panel index={1}>
      <group position={[-PW / 2, 4, 0]}>
        <WLabel fontSize={1.15} color={C.inkEditorial} fillOpacity={1}>
          WHY RIDGE
        </WLabel>
        <WMono position={[0, -1.3, 0]} fontSize={0.5} color={C.ocpGreen} fillOpacity={0.85}>
          VALIDATION RMSE - TIME-AWARE TUNING ON TRAIN ONLY
        </WMono>
        {rows.map((r, i) => (
          <group key={r.name} position={[0, -3.0 - i * 1.3, 0]}>
            <WMono position={[9.2, 0, 0]} fontSize={0.5} anchorX="right"
              color={r.selected ? C.inkEditorial : C.outline} fillOpacity={r.selected ? 1 : 0.8}>
              {r.name}
            </WMono>
            <mesh position={[9.8 + (r.norm * 15) / 2, 0, 0]} material={r.selected ? barMat : dimMat}>
              <boxGeometry args={[r.norm * 15, 0.46, 0.02]} />
            </mesh>
            <WMono position={[25.4, 0, 0]} fontSize={0.5}
              color={r.selected ? C.ocpGreen : C.outline} fillOpacity={r.selected ? 1 : 0.75}>
              {r.valRmse.toFixed(6)}
            </WMono>
          </group>
        ))}
        <WMono position={[0, -3.0 - rows.length * 1.3 - 1.0, 0]} fontSize={0.5}
          color={C.inkEditorial} fillOpacity={0.75}>
          The regularised linear model won. Nothing here needed to be complicated.
        </WMono>
      </group>
    </Panel>
  );
}

/* --------------------------------------------------------------- panel B --- */

function PanelB() {
  const model = useMemo(() => {
    const a = getData().anomaly;
    const ev = a.event ?? {};
    const t = ev.t ?? [];
    const risk = ev.risk ?? [];
    if (!t.length) return null;

    const toX = (i) => -PW / 2 + (i / (t.length - 1)) * PW;
    const toY = (v) => -CHART_H / 2 + THREE.MathUtils.clamp(v, 0, 1) * CHART_H;

    const pts = risk.map((v, i) => [toX(i), toY(v ?? 0), 0]);
    const colors = risk.map((v) => new THREE.Color(riskColor(v ?? 0)));

    const inEvent = ev.inEvent ?? [];
    let s = inEvent.indexOf(true);
    let e = inEvent.lastIndexOf(true);
    if (s < 0) { s = 0; e = 0; }

    const xTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => {
      const i = Math.round(f * (t.length - 1));
      return { x: toX(i), label: String(t[i] ?? '').slice(11, 16) };
    });

    return {
      pts, colors,
      warnY: toY(a.warning ?? 0.5),
      critY: toY(a.critical ?? 0.8),
      eventX0: toX(s), eventX1: toX(e),
      ev, xTicks,
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
    const mk = (color, max) => {
      const m = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, depthWrite: false });
      m.userData.maxOpacity = max;
      return m;
    };
    return { warn: mk(C.warn, 0.10), crit: mk(C.critical, 0.10), ev: mk(C.critical, 0.15) };
  }, []);

  if (!model) return null;
  const ev = model.ev;

  return (
    <Panel index={2}>
      <WLabel position={[-PW / 2, CHART_H / 2 + 2.6, 0]} fontSize={1.15}
        color={C.inkEditorial} fillOpacity={1}>
        ANOMALY DETECTOR - HELD-OUT TEST
      </WLabel>
      <WMono position={[-PW / 2, CHART_H / 2 + 1.5, 0]} fontSize={0.46}
        color={C.ocpGreen} fillOpacity={0.85}>
        {`${model.date} - DISPLAY RISK, NOT A PROBABILITY`}
      </WMono>

      <mesh position={[0, (model.warnY + model.critY) / 2, -0.03]} material={bandMat.warn}>
        <planeGeometry args={[PW, model.critY - model.warnY]} />
      </mesh>
      <mesh position={[0, (model.critY + CHART_H / 2) / 2, -0.03]} material={bandMat.crit}>
        <planeGeometry args={[PW, CHART_H / 2 - model.critY]} />
      </mesh>

      <mesh position={[(model.eventX0 + model.eventX1) / 2, 0, -0.02]} material={bandMat.ev}>
        <planeGeometry args={[Math.max(0.2, model.eventX1 - model.eventX0), CHART_H]} />
      </mesh>
      <WMono position={[model.eventX0, CHART_H / 2 + 0.5, 0]} fontSize={0.46}
        color={C.critical} fillOpacity={0.95}>
        {`LABELLED ${String(ev.label ?? '').toUpperCase()} - ${ev.durationMinutes ?? '—'} min`}
      </WMono>

      <Line points={[[-PW / 2, model.warnY, 0], [PW / 2, model.warnY, 0]]}
        color={C.warn} lineWidth={1.3} dashed dashSize={0.5} gapSize={0.35}
        transparent opacity={0.85} />
      <Line points={[[-PW / 2, model.critY, 0], [PW / 2, model.critY, 0]]}
        color={C.critical} lineWidth={1.3} dashed dashSize={0.5} gapSize={0.35}
        transparent opacity={0.85} />
      <WMono position={[-PW / 2 + 0.4, model.warnY + 0.44, 0]} fontSize={0.44}
        color={C.warn} fillOpacity={1}>
        WARNING 0.50
      </WMono>
      <WMono position={[-PW / 2 + 0.4, model.critY + 0.44, 0]} fontSize={0.44}
        color={C.critical} fillOpacity={1}>
        CRITICAL 0.80
      </WMono>

      <Line points={[[-PW / 2, -CHART_H / 2, 0], [PW / 2, -CHART_H / 2, 0]]}
        color={C.rule} lineWidth={1.4} transparent opacity={0.7} />
      {model.xTicks.map((t) => (
        <WMono key={t.label + t.x} position={[t.x, -CHART_H / 2 - 0.9, 0]} fontSize={0.44}
          color={C.outline} anchorX="center" fillOpacity={0.85}>
          {t.label}
        </WMono>
      ))}

      {riskGeo && <line geometry={riskGeo} material={riskMat} frustumCulled={false} />}

      <group position={[-PW / 2, -CHART_H / 2 - 2.6, 0]}>
        <WMono fontSize={0.52} color={C.critical} fillOpacity={1}>
          THE DETECTOR IS UNSUPERVISED AND NEVER SAW THIS LABEL
        </WMono>
        <group position={[0, -1.6, 0]}>
          {[
            ['MEAN RISK IN EVENT', ev.riskInEventMean?.toFixed(3)],
            ['MEAN RISK OUTSIDE', ev.riskOutEventMean?.toFixed(3)],
            ['WARNING POINTS INSIDE', `${ev.warningPointsInsideEvent ?? '—'}/${ev.warningPointsTotal ?? '—'}`],
          ].map(([k, v], i) => (
            <group key={k} position={[i * 10.2, 0, 0]}>
              <WMono fontSize={0.42} color={C.ocpGreen} fillOpacity={0.85}>{k}</WMono>
              <WMono position={[0, -1.1, 0]} fontSize={1.05} color={C.inkEditorial} fillOpacity={1}>
                {v ?? '—'}
              </WMono>
            </group>
          ))}
        </group>
      </group>
    </Panel>
  );
}

/* ---------------------------------------------------------------- limits --- */

function Limits() {
  // Four boundaries, not five, and the overlay no longer repeats them: this
  // frame used to print "WHAT THIS EVIDENCE IS WORTH." twice — once in the DOM
  // and once in the world — with three of its bullets restated in the DOM note
  // directly beside them.
  const lines = [
    ['PROVES', 'A regularised linear soft sensor tracks 165 unseen laboratory targets, chronologically held out.'],
    ['PROVES', 'An unsupervised detector raises risk inside a disturbance whose label it never saw.'],
    ['DOES NOT PROVE', 'Plant performance. The dataset is a synthetic prototype; disturbances come from the generator.'],
    ['DOES NOT PROVE', 'Root cause. Diagnosis localises evidence and stays advisory. The laboratory remains the reference.'],
  ];
  return (
    <Panel index={3}>
      <group position={[-PW / 2, 4.4, 0.3]}>
        {lines.map(([kind, text], i) => (
          <group key={text} position={[0, -i * 2.5, 0]}>
            <WMono fontSize={0.5} color={kind === 'PROVES' ? C.ocpGreen : C.critical}
              fillOpacity={1}>
              {kind}
            </WMono>
            <WLabel position={[0, -1.1, 0]} fontSize={0.78} color={C.inkEditorial}
              fillOpacity={0.92} maxWidth={PW}>
              {text}
            </WLabel>
          </group>
        ))}
      </group>
    </Panel>
  );
}
