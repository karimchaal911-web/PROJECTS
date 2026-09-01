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
  // near column, ordered by the height of the point each one comes from
  { key: 'air_flow_rate', label: 'AIR FLOW RATE', unit: 'm³/h', dec: 0, at: [-8.6, 13.6, 0], to: [13.4, 15.4, 9] },
  { key: 'wet_product_feed_rate', label: 'WET FEED RATE', unit: 'm³/h', dec: 2, at: [-12.9, 10.8, 0], to: [13.4, 12.6, 9] },
  { key: 'vacuum', label: 'VACUUM', unit: 'mmH2O', dec: 1, at: [-9.6, 8.0, 0], to: [13.4, 9.8, 9] },
  { key: 'dryer_air_temperature', label: 'DRYER AIR TEMP', unit: '°C', dec: 1, at: [-9.6, 3.4, 0.2], to: [13.4, 7.0, 9] },
  // far column, taken from the points further along the machine
  { key: 'fan_speed', label: 'FAN SPEED', unit: 'rpm', dec: 1, at: [24, 12.0, -9.5], to: [21.4, 15.4, 9] },
  { key: 'residence_time', label: 'RESIDENCE TIME', unit: 'min', dec: 2, at: [0, 7.6, 0], to: [21.4, 12.6, 9] },
  { key: 'steam_pressure', label: 'STEAM PRESSURE', unit: 'bar', dec: 2, at: [12.4, 2.4, 2.4], to: [21.4, 9.8, 9] },
];

export default function SensorNodes() {
  const group = useRef();
  const presence = useChannel('sensors');
  const reveal = useChannel('sensorReveal', 0);
  // The numeric chips are laid out for the DATA beat's framing. Seen from the
  // opening pose in scene 14 they are 60 degrees off-axis, foreshortened and
  // clipped by the frame edge, so the closing frame carried a wall of
  // unreadable telemetry. There, only the instrumented POINTS remain.
  const chips = useChannel('sensorChips', 1);
  const refs = useRef([]);
  const outRef = useRef();
  const leaderRefs = useRef([]);

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

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const r = reveal.current;
    const ch = chips.current;
    // No ambient pulse. Seven dots breathing in unison read as a blinking UI,
    // not as telemetry, and nothing about the process was changing to justify
    // it. Motion here would have to mean something.
    dotMat.opacity = p * r * 0.85;

    if (outRef.current) {
      outRef.current.visible = ch > 0.02 && r > 0.3;
      outRef.current.traverse((o) => {
        if (o.fillOpacity !== undefined) o.fillOpacity = (o.userData?.base ?? 1) * ch;
      });
    }

    refs.current.forEach((g, i) => {
      if (!g) return;
      // 0.09 s stagger, expressed as a slice of the reveal channel
      const local = THREE.MathUtils.clamp((r - i * 0.07) / 0.5, 0, 1);
      g.visible = local > 0.01;
      g.scale.setScalar(0.6 + local * 0.4);
      // The tether is set explicitly: the generic traverse below drove every
      // transparent material to full opacity, so the leader lines rendered at
      // 1.0 and read as bright scratches across the machine rather than as
      // faint tethers — and on the closing frame they pointed at chips that
      // are no longer there.
      const ld = leaderRefs.current[i];
      if (ld?.material) {
        ld.visible = ch > 0.02;
        ld.material.opacity = p * local * 0.16 * ch;
      }
      g.traverse((o) => {
        if (o.fillOpacity !== undefined) {
          o.visible = ch > 0.02;
          o.fillOpacity = (o.userData?.base ?? 1) * ch;
        } else if (o.material && o.material.transparent && o !== g && o !== ld) {
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
            <sphereGeometry args={[0.22, 14, 10]} />
          </mesh>
          {/* leader line: the chip belongs to that point */}
          <Line ref={(el) => { leaderRefs.current[i] = el; }} points={[n.at, n.to]}
            color={C.dataTeal} lineWidth={1} transparent opacity={0} />
          <WMono overlay position={[n.to[0] + 0.4, n.to[1] + 0.66, n.to[2]]} fontSize={0.46}
            color={C.dataTeal} fillOpacity={0.7} userData={{ base: 0.7 }}>
            {n.label}
          </WMono>
          <WMono overlay position={[n.to[0] + 0.4, n.to[1] - 0.36, n.to[2]]} fontSize={0.88}
            color={C.dataCyan} fillOpacity={0.95} userData={{ base: 0.95 }}>
            {`${values[i]} ${n.unit}`}
          </WMono>
        </group>
      ))}

      {/* the output side: the quality that is NOT measured continuously */}
      <group ref={outRef} position={[21.4, 7.0, 9]}>
        <WMono overlay position={[0.4, 0.66, 0]} fontSize={0.46} color={C.lab} fillOpacity={0.7}
          userData={{ base: 0.7 }}>
          FINAL MOISTURE
        </WMono>
        <WMono overlay position={[0.4, -0.36, 0]} fontSize={0.88} color={C.lab} fillOpacity={0.95}
          userData={{ base: 0.95 }}>
          LABORATORY ONLY
        </WMono>
      </group>
    </group>
  );
}
