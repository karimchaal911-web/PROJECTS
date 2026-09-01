import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C, riskColor } from '../../lib/palette.js';
import { useChannel } from '../usePresence.js';
import { useShow } from '../../state/useShow.js';
import { budget } from '../../lib/perf.js';
import { WLabel, WMono } from '../WorldText.jsx';
import { getData } from '../../data/load.js';

/**
 * The two intelligence pathways.
 *
 * Left: the moisture soft sensor — 16 standardised coefficients entering a
 * compact solid, one continuous estimate leaving it. It is a 16-coefficient
 * linear model, so it is drawn as one, not as a neural network.
 *
 * Right: the learned normal operating region, rendered from real geometry.
 * 2,400 TRAIN process states projected by PCA (93.7 % of variance in three
 * components), the model's own 136 support vectors on the outer shell, and the
 * recorded trajectory of the labelled disturbance leaving the region.
 *
 * Nothing here is a metaphor except the tether line, and the tether is honest:
 * it is the distance the detector actually measures.
 */

const LANE_A = new THREE.Vector3(-26, 14, -78);
const LANE_B = new THREE.Vector3(28, 15, -78);
const SCALE = 1.55;

export default function Pathways() {
  return (
    <>
      <QualityLane />
      <ManifoldCloud />
    </>
  );
}

/* ------------------------------------------------------------ lane A ---- */

function QualityLane() {
  const group = useRef();
  const labels = useRef();
  const presence = useChannel('lanes');
  const focus = useChannel('laneFocus', 0);

  const coefs = useMemo(() => {
    const list = getData().coefficients?.features ?? [];
    const max = list.reduce((m, f) => Math.max(m, Math.abs(f.coef ?? 0)), 0) || 1;
    return list.map((f) => ({ ...f, norm: Math.abs(f.coef ?? 0) / max }));
  }, []);

  const barMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.dataTeal, transparent: true, opacity: 0, depthWrite: false,
  }), []);
  const solidMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.forest700, roughness: 0.4, metalness: 0.3,
    emissive: new THREE.Color(C.ocpGreen), emissiveIntensity: 0.12,
    transparent: true, opacity: 0,
  }), []);
  const outMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.predict, transparent: true, opacity: 0, depthWrite: false,
  }), []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    // laneFocus: -1 favours quality, +1 favours process, 0 is neutral
    const f = THREE.MathUtils.clamp(1 - Math.max(0, focus.current), 0.2, 1);
    if (labels.current) labels.current.visible = p > 0.4;
    barMat.opacity = p * 0.75 * f;
    solidMat.opacity = p * f;
    outMat.opacity = p * 0.9 * f;
    // The model does NOT rotate. A perpetually spinning crystal is the exact
    // "AI black box" trope this scene exists to refuse; it also contradicted
    // the object's own brief — compact, solid, unmysterious.
  });

  return (
    <group ref={group} position={LANE_A}>
      <group ref={labels}>
      <WLabel overlay position={[-7.5, 8.4, 0]} fontSize={1.05} color={C.dustBright} fillOpacity={0.95}>
        QUALITY INTELLIGENCE
      </WLabel>
      <WMono overlay position={[-7.5, 7.1, 0]} fontSize={0.5} color={C.dataTeal} fillOpacity={0.8}>
        RIDGE - alpha = 10 - 16 FEATURES
      </WMono>
      </group>

      {/* the 16 standardised coefficients arriving */}
      {coefs.map((f, i) => {
        const y = 5.6 - i * 0.72;
        const len = 0.8 + f.norm * 6.4;
        return (
          <group key={f.name} position={[-7.5, y, 0]}>
            <mesh position={[len / 2, 0, 0]} material={barMat}>
              <boxGeometry args={[len, 0.13, 0.13]} />
            </mesh>
            <WMono position={[-0.35, 0, 0]} fontSize={0.42} color={C.dataTeal}
              anchorX="right" fillOpacity={0.62}>
              {f.name}
            </WMono>
          </group>
        );
      })}

      {/* the model itself: compact, solid, unmysterious */}
      {/* A stable, faceted solid at a fixed attitude: sixteen coefficients in,
          one estimate out. It is a linear model and it is drawn as one. */}
      <mesh position={[2.4, 0.6, 0]} rotation={[0.32, 0.62, 0]} material={solidMat} castShadow>
        <icosahedronGeometry args={[1.9, 1]} />
      </mesh>

      {/* One continuous estimate leaving. The label sits UNDER the endpoint
          rather than beyond it: read out to the right it made the lane 31
          world units wide, which cannot fit beside the copy column at any
          focal length — so the sixteen coefficient names were pushed under
          the headline and six of them became unreadable. */}
      <Line points={[[4.4, 0.6, 0], [6.7, 0.6, 0]]} color={C.predict} lineWidth={2.2}
        transparent opacity={0.85} />
      <mesh position={[7.0, 0.6, 0]} material={outMat}>
        <sphereGeometry args={[0.26, 14, 10]} />
      </mesh>
      <WMono overlay position={[7.0, -0.9, 0]} fontSize={0.52} color={C.predict}
        anchorX="center" fillOpacity={0.95}>
        PREDICTED MOISTURE
      </WMono>
    </group>
  );
}

/* ------------------------------------------------------------ lane B ---- */

function ManifoldCloud() {
  const group = useRef();
  const labels = useRef();
  const presence = useChannel('lanes');
  const reveal = useChannel('manifoldReveal', 0);
  const supportReveal = useChannel('supportReveal', 0);
  const supportFocus = useChannel('supportFocus', 0);
  const traj = useChannel('trajectory', 0);
  const focus = useChannel('laneFocus', 0);
  const safeMode = useShow((s) => s.safeMode);
  const maxPoints = budget(safeMode).manifold;

  const marker = useRef();
  const tether = useRef();

  const model = useMemo(() => {
    const m = getData().manifold;
    const all = m.normal?.points ?? [];
    // The caption states the size of the TRAINING SET, which is a fact about
    // the model. `maxPoints` only decides how many of them are drawn, and safe
    // mode draws fewer. Deriving the printed number from the rendered subset
    // meant a graphics budget silently rewrote a claim on screen: the same
    // frame read "2,400 TRAIN STATES" on one machine and "900" on another.
    const normalTotal = all.length;
    const normal = all.slice(0, maxPoints);
    const support = m.support?.points ?? [];
    const path = m.trajectory?.points ?? [];
    const risk = m.trajectory?.risk ?? [];
    const inEvent = m.trajectory?.inEvent ?? [];

    const toWorld = (p) => new THREE.Vector3(p[0] * SCALE, p[1] * SCALE, p[2] * SCALE);

    const normalGeo = new THREE.BufferGeometry();
    const np = new Float32Array(normal.length * 3);
    normal.forEach((p, i) => {
      np[i * 3] = p[0] * SCALE; np[i * 3 + 1] = p[1] * SCALE; np[i * 3 + 2] = p[2] * SCALE;
    });
    normalGeo.setAttribute('position', new THREE.BufferAttribute(np, 3));

    const supportGeo = new THREE.BufferGeometry();
    const sp = new Float32Array(support.length * 3);
    support.forEach((p, i) => {
      sp[i * 3] = p[0] * SCALE; sp[i * 3 + 1] = p[1] * SCALE; sp[i * 3 + 2] = p[2] * SCALE;
    });
    supportGeo.setAttribute('position', new THREE.BufferAttribute(sp, 3));

    const worldPath = path.map(toWorld);
    const centroid = new THREE.Vector3();
    if (normal.length) {
      normal.forEach((p) => centroid.add(new THREE.Vector3(p[0], p[1], p[2])));
      centroid.multiplyScalar(SCALE / normal.length);
    }

    return {
      normalGeo, supportGeo, worldPath, risk, inEvent,
      supportCount: support.length,
      normalCount: normalTotal,
      drawnCount: normal.length,
      centroid,
      variance: m.explainedVariance ?? [],
    };
  }, [maxPoints]);

  const normalMat = useMemo(() => new THREE.PointsMaterial({
    color: C.dataTeal, size: 0.34, transparent: true, opacity: 0,
    // Normal blending, not additive: 2,400 additive points accumulate into a
    // brightness that no 136-point highlight can win against.
    depthWrite: false, sizeAttenuation: true, fog: false,
  }), []);
  const supportMat = useMemo(() => new THREE.PointsMaterial({
    color: C.dataCyan, size: 0.62, transparent: true, opacity: 0,
    depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true, fog: false,
  }), []);
  const markerMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.dataCyan, transparent: true, opacity: 0, depthWrite: false, fog: false,
  }), []);
  const tetherMat = useMemo(() => new THREE.LineBasicMaterial({
    color: C.warn, transparent: true, opacity: 0,
  }), []);

  const tetherGeo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(6), 3));
    return g;
  }, []);

  const trailGeo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const n = model.worldPath.length;
    const pos = new Float32Array(Math.max(n, 2) * 3);
    const col = new Float32Array(Math.max(n, 2) * 3);
    const c = new THREE.Color();
    model.worldPath.forEach((p, i) => {
      pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z;
      c.set(riskColor(model.risk[i] ?? 0));
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    });
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    return g;
  }, [model]);

  const trailMat = useMemo(() => new THREE.LineBasicMaterial({
    vertexColors: true, transparent: true, opacity: 0, fog: false,
  }), []);
  const trail = useRef();

  useFrame((state) => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const f = THREE.MathUtils.clamp(1 + Math.min(0, focus.current), 0.35, 1);
    const r = reveal.current;
    if (labels.current) labels.current.visible = p > 0.4 && r > 0.3;
    // The claim "these 136 points define the learned boundary" has to be
    // VERIFIABLE. With 2,400 additively-blended points behind them, the
    // support vectors were simply a denser part of the same cloud. So the
    // cloud recedes as they arrive, and they get scale as well as brightness.
    const sf = THREE.MathUtils.clamp(supportFocus.current, 0, 1);
    normalMat.opacity = p * r * f * (0.8 - sf * 0.55);
    normalMat.size = 0.34 - sf * 0.10;
    supportMat.opacity = p * supportReveal.current * f;
    supportMat.size = 0.62 + sf * 0.42;

    const u = THREE.MathUtils.clamp(traj.current, 0, 1);
    const n = model.worldPath.length;
    if (n > 1) {
      const idx = Math.min(n - 1, Math.floor(u * (n - 1)));
      const point = model.worldPath[idx];
      const risk = model.risk[idx] ?? 0;

      if (marker.current) {
        marker.current.position.copy(point);
        marker.current.visible = u > 0.001;
        const pulse = 1 + Math.sin(state.clock.elapsedTime * 4) * 0.12 * (risk > 0.5 ? 1 : 0.2);
        marker.current.scale.setScalar(pulse * (0.9 + risk * 0.7));
      }
      markerMat.color.set(riskColor(risk));
      markerMat.opacity = p * (u > 0.001 ? 1 : 0) * f;

      // The tether is the distance the model is actually measuring.
      const tp = tetherGeo.attributes.position.array;
      tp[0] = model.centroid.x; tp[1] = model.centroid.y; tp[2] = model.centroid.z;
      tp[3] = point.x; tp[4] = point.y; tp[5] = point.z;
      tetherGeo.attributes.position.needsUpdate = true;
      tetherMat.color.set(riskColor(risk));
      tetherMat.opacity = p * u * 0.5 * f;

      trailMat.opacity = p * u * 0.75 * f;
      if (trail.current) trailGeo.setDrawRange(0, Math.max(2, idx + 1));
    }
  });

  return (
    <group ref={group} position={LANE_B}>
      <group ref={labels}>
      <WLabel overlay position={[-14, 11.6, 0]} fontSize={1.05} color={C.dustBright} fillOpacity={0.95}>
        PROCESS INTELLIGENCE
      </WLabel>
      {/* The model spec lives in the DOM caption, which has the full font
          subset and a scrim. Repeating it in perspective here only produced a
          second, less legible copy of the same line. */}
      {/* Provenance sits directly under the cloud rather than at the foot of
          the lane, where it used to be overwritten by the persistent boundary
          badge and skewed to the point of illegibility. */}
      <WMono overlay position={[-14, -9.4, 0]} fontSize={0.62} color={C.dustBright} fillOpacity={0.95}>
        {`${model.normalCount.toLocaleString('en-US')} TRAIN STATES · PCA(3) · ${
          model.variance.length
            ? `${(model.variance.reduce((a, b) => a + b, 0) * 100).toFixed(1)} % OF VARIANCE`
            : ''
        }`}
      </WMono>
      <WMono overlay position={[-14, -10.6, 0]} fontSize={0.62} color={C.dataCyan} fillOpacity={1}>
        {`${model.supportCount} SUPPORT VECTORS — THE LEARNED BOUNDARY`}
      </WMono>
      </group>

      <points geometry={model.normalGeo} material={normalMat} frustumCulled={false} />
      <points geometry={model.supportGeo} material={supportMat} frustumCulled={false} />
      <line ref={trail} geometry={trailGeo} material={trailMat} frustumCulled={false} />
      <lineSegments geometry={tetherGeo} material={tetherMat} frustumCulled={false} />
      <mesh ref={marker} material={markerMat}>
        <sphereGeometry args={[0.72, 16, 12]} />
      </mesh>
    </group>
  );
}
