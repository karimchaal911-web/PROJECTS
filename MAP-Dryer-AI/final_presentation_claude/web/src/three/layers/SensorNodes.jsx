import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { DRYER } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WMono } from '../WorldText.jsx';
import { getData } from '../../data/load.js';

/**
 * Telemetry anchored to the physical thing that produces it.
 *
 * Every number here is a real value read from the held-out TEST replay window
 * (gap.json), and every chip is attached by a leader line to the point on the
 * equipment where that variable is measured. Nothing floats.
 */

// Ordered so the leader lines fan out without crossing: sources are read left
// to right along the machine and land top to bottom down the two columns.
const NODES = [
  { key: 'wet_product_feed_rate', label: 'WET FEED RATE', unit: 'm3/h', dec: 2, at: [-12.9, 10.8, 0], to: [15.5, 13.6, 6] },
  { key: 'dryer_air_temperature', label: 'DRYER AIR TEMP', unit: 'C', dec: 1, at: [-9.6, 3.4, 0.2], to: [15.5, 10.4, 6] },
  { key: 'vacuum', label: 'VACUUM', unit: 'mmH2O', dec: 1, at: [-9.6, 8.0, 0], to: [15.5, 7.2, 6] },
  { key: 'air_flow_rate', label: 'AIR FLOW RATE', unit: 'm3/h', dec: 0, at: [-8.6, 13.6, 0], to: [26.5, 13.6, 6] },
  { key: 'residence_time', label: 'RESIDENCE TIME', unit: 'min', dec: 2, at: [0, 7.6, 0], to: [26.5, 10.4, 6] },
  { key: 'steam_pressure', label: 'STEAM PRESSURE', unit: 'bar', dec: 2, at: [12.4, 2.4, 2.4], to: [26.5, 7.2, 6] },
  { key: 'fan_speed', label: 'FAN SPEED', unit: 'rpm', dec: 1, at: [24, 12.0, -9.5], to: [26.5, 4.0, 6] },
];

export default function SensorNodes() {
  const group = useRef();
  const presence = useChannel('sensors');
  const reveal = useChannel('sensorReveal', 0);
  const refs = useRef([]);

  const values = useMemo(() => {
    const gap = getData().gap;
    const sig = gap.signals ?? {};
    const i = Math.floor((gap.t?.length ?? 1) * 0.36); // a representative moment
    return NODES.map((n) => {
      const series = sig[n.key];
      const v = Array.isArray(series) && series.length ? series[Math.min(i, series.length - 1)] : null;
      return v == null ? '—' : v.toLocaleString('en-US', {
        minimumFractionDigits: n.dec, maximumFractionDigits: n.dec,
      });
    });
  }, []);

  const dotMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.dataCyan, transparent: true, opacity: 0, depthWrite: false,
  }), []);

  useFrame((state) => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const r = reveal.current;
    const t = state.clock.elapsedTime;
    dotMat.opacity = p * r * (0.72 + Math.sin(t * 1.6) * 0.14);

    refs.current.forEach((g, i) => {
      if (!g) return;
      // 0.09 s stagger, expressed as a slice of the reveal channel
      const local = THREE.MathUtils.clamp((r - i * 0.07) / 0.5, 0, 1);
      g.visible = local > 0.01;
      g.scale.setScalar(0.6 + local * 0.4);
      g.traverse((o) => {
        if (o.material && o.material.transparent && o !== g) {
          o.material.opacity = Math.min(o.material.userData.max ?? 1, local * p);
        }
      });
    });
  });

  return (
    <group ref={group}>
      {NODES.map((n, i) => (
        <group key={n.key} ref={(el) => { refs.current[i] = el; }}>
          {/* the emitting point on the equipment */}
          <mesh position={n.at} material={dotMat}>
            <sphereGeometry args={[0.16, 12, 8]} />
          </mesh>
          {/* leader line: the chip belongs to that point */}
          <Line points={[n.at, n.to]} color={C.dataTeal} lineWidth={1} transparent opacity={0.22} />
          <WMono position={[n.to[0] + 0.4, n.to[1] + 0.66, n.to[2]]} fontSize={0.46}
            color={C.dataTeal} fillOpacity={0.7}>
            {n.label}
          </WMono>
          <WMono position={[n.to[0] + 0.4, n.to[1] - 0.36, n.to[2]]} fontSize={0.88}
            color={C.dataCyan} fillOpacity={0.95}>
            {`${values[i]} ${n.unit}`}
          </WMono>
        </group>
      ))}

      {/* the output side: the quality that is NOT measured continuously */}
      <group position={[15.5, 1.2, 6]}>
        <WMono position={[0, 1.0, 0]} fontSize={0.46} color={C.lab} fillOpacity={0.65}>
          FINAL MOISTURE
        </WMono>
        <WMono position={[0, 0.0, 0]} fontSize={0.88} color={C.lab} fillOpacity={0.95}>
          %H2O — LABORATORY ONLY
        </WMono>
      </group>
    </group>
  );
}
