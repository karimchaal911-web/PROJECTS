import { useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { RESIDENCE } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';

/**
 * Residence-time alignment, in two beats.
 *
 * This is the smartest idea in the project and it used to get one sentence over
 * a glowing slab. It is also the idea a chemical-engineering jury is most
 * likely to probe, because getting it wrong is the classic way a plant soft
 * sensor is silently trained on the future.
 *
 * The argument only works if it is made in two halves, and they are different
 * kinds of claim:
 *
 *   BEAT 1 — PHYSICAL. Material takes time to cross the dryer. A sample
 *   analysed at 09:00 describes material that entered at 08:35. Nothing here
 *   is about data; it is about a machine with a length.
 *
 *   BEAT 2 — DATA. Therefore the process variables at the lab timestamp
 *   describe the WRONG material. The naive pairing is drawn first, in the
 *   colour the film uses for a fault, and then the process rail is shifted by
 *   the measured residence time until the two describe the same material.
 *
 * WHAT IS ASSERTED. Residence time is a measured process variable in the
 * canonical dataset — mean 24.54 min over 1,589,760 rows, 24.15 to 24.89 min
 * range, and 24.44 min mean across the twelve-hour window this film replays.
 * The runtime shifts by the value AT EACH TIMESTAMP, not by a constant, and the
 * copy says so. Density and product temperature come from the most recent
 * strictly PREVIOUS laboratory sample, which is what makes the feature set
 * causal; that is drawn as a separate, backward-pointing link so it cannot be
 * confused with the process shift.
 *
 * Nothing here is decorative. There is one moving marker, two rails, one shift
 * and one span label, and everything on screen is load-bearing.
 */

const LEN = RESIDENCE.length;
const X0 = -LEN / 2;
const X1 = LEN / 2;

/** The shift, as a fraction of the lane, at the lane's own time scale. */
const SHIFT = RESIDENCE.shiftFraction;

export default function Residence() {
  const { camera } = useThree();
  const group = useRef();
  const presence = useChannel('residence');
  // Beat 1: the marker crosses the dryer span.
  const travel = useChannel('residenceTravel', 0);
  // Beat 2: 0 = naive same-timestamp pairing, 1 = shifted into alignment.
  const align = useChannel('residenceAlign', 0);
  // Beat 2 only: the two rails and their links exist.
  const rails = useChannel('residenceRails', 0);

  const billboards = useRef([]);
  const marker = useRef();
  const markerMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.granule, roughness: 0.55, metalness: 0.0,
    emissive: new THREE.Color(C.processWarm), emissiveIntensity: 0.35,
    transparent: true, opacity: 0, fog: false,
  }), []);

  // --- beat 1: the physical span -------------------------------------------
  const spanRef = useRef();
  const inTick = useRef();
  const outTick = useRef();
  const spanLabel = useRef();

  // --- beat 2: two rails ----------------------------------------------------
  const processRail = useRef();
  const qualityRail = useRef();
  const naiveLink = useRef();
  const alignedLink = useRef();
  const priorLink = useRef();
  const processBlock = useRef();
  const qualityBlock = useRef();

  const railMat = useMemo(() => ({
    process: new THREE.MeshStandardMaterial({
      color: C.dataTeal, roughness: 0.4, metalness: 0.1,
      emissive: new THREE.Color(C.dataTeal), emissiveIntensity: 0.25,
      transparent: true, opacity: 0, fog: false,
    }),
    quality: new THREE.MeshStandardMaterial({
      color: C.lab, roughness: 0.35, metalness: 0.0,
      emissive: new THREE.Color(C.lab), emissiveIntensity: 0.18,
      transparent: true, opacity: 0, fog: false,
    }),
  }), []);

  const railY = RESIDENCE.railGap;

  /**
   * Hour ticks on the quality rail.
   *
   * Without them the shift is a distance, and a distance is not an argument.
   * With them the audience can read 24.5 minutes off a three-hour lane and see
   * for themselves that it is small, real, and larger than nothing.
   */
  const hourTicks = useMemo(
    () => Array.from({ length: RESIDENCE.hours + 1 }, (_, h) => ({
      h,
      x: X0 + (h / RESIDENCE.hours) * LEN,
    })),
    []
  );
  const tickGroup = useRef();
  const railLabels = useRef();
  const shiftLabel = useRef();
  const priorLabel = useRef();

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    for (const b of billboards.current) if (b) b.quaternion.copy(camera.quaternion);

    const t = THREE.MathUtils.clamp(travel.current, 0, 1);
    const a = THREE.MathUtils.clamp(align.current, 0, 1);
    const r = THREE.MathUtils.clamp(rails.current, 0, 1);

    // ---- beat 1 -----------------------------------------------------------
    // TWO different recessions, not one.
    //
    // The span LINE is the dryer, and the rails of beat 2 hang off it, so it
    // stays — faintly — as the thing the second beat is a consequence of. The
    // span's TYPE and its marker do not: they occupy exactly the band the
    // quality rail, the hour ticks and the sample block move into, and holding
    // them at even a third of their strength put MATERIAL ENTERS across
    // PROCESS VARIABLES and RESIDENCE TIME 24.5 min across the 2 h tick. The
    // number is in the copy column and comes back on the shift itself.
    const physical = p * (1 - r * 0.78);
    const beat1 = p * Math.max(0, 1 - r * 1.35);
    if (spanRef.current) spanRef.current.material.opacity = physical * 0.9;
    for (const tick of [inTick.current, outTick.current]) {
      if (tick) tick.material.opacity = physical * 0.85;
    }
    if (spanLabel.current) {
      spanLabel.current.visible = beat1 > 0.03;
      spanLabel.current.traverse((o) => {
        if (o.fillOpacity !== undefined) o.fillOpacity = beat1 * (o.userData?.base ?? 0.9);
      });
    }
    if (marker.current) {
      // The marker crosses at constant speed. This is a machine with a length,
      // not a UI element: it must not ease.
      marker.current.position.x = THREE.MathUtils.lerp(X0, X1, t);
      // A little bounce as it tumbles down the shell — the only secondary
      // motion in this layer, and it is what stops the marker reading as a
      // slider handle.
      marker.current.position.y = Math.sin(t * Math.PI * 7) * 0.16 * (t > 0 && t < 1 ? 1 : 0);
      markerMat.opacity = beat1 * (t > 0.001 ? 1 : 0);
      marker.current.visible = markerMat.opacity > 0.02;
    }

    // ---- beat 2 -----------------------------------------------------------
    railMat.process.opacity = p * r;
    railMat.quality.opacity = p * r;
    for (const rail of [processRail.current, qualityRail.current]) {
      if (rail) rail.material.opacity = p * r * 0.5;
    }
    if (processRail.current) processRail.current.visible = r > 0.02;
    if (qualityRail.current) qualityRail.current.visible = r > 0.02;
    if (railLabels.current) {
      railLabels.current.visible = r > 0.04;
      railLabels.current.traverse((o) => {
        if (o.fillOpacity !== undefined) o.fillOpacity = p * r * 0.85;
      });
    }
    if (tickGroup.current) {
      tickGroup.current.visible = r > 0.04;
      tickGroup.current.traverse((o) => {
        if (o.fillOpacity !== undefined) o.fillOpacity = p * r * 0.55;
        else if (o.material && o.material.transparent && o.isLine) o.material.opacity = p * r * 0.3;
      });
    }

    // The quality sample sits at a fixed time on the lower rail. The process
    // block starts underneath it — the naive pairing — and SLIDES BACK by the
    // residence time until it describes the same material.
    const qx = RESIDENCE.sampleAt * LEN + X0;
    if (qualityBlock.current) {
      qualityBlock.current.position.x = qx;
      qualityBlock.current.visible = r > 0.02;
    }
    if (processBlock.current) {
      processBlock.current.position.x = qx - a * SHIFT * LEN;
      processBlock.current.visible = r > 0.02;
    }

    // Three links, and only ever two of them lit: the naive pairing fades out
    // exactly as the aligned one arrives, so the audience sees a correction
    // rather than two coexisting claims.
    if (naiveLink.current) {
      naiveLink.current.visible = r > 0.02 && a < 0.98;
      naiveLink.current.material.opacity = p * r * (1 - a) * 0.9;
    }
    if (alignedLink.current) {
      alignedLink.current.visible = r > 0.02 && a > 0.02;
      alignedLink.current.material.opacity = p * r * a * 0.95;
      const g = alignedLink.current.geometry;
      if (g?.setPositions) {
        g.setPositions([
          processBlock.current?.position.x ?? qx, railY, 0,
          qx, -railY, 0,
        ]);
      }
    }
    if (shiftLabel.current) {
      // The one number beat 2 needs, and it appears ON the shift rather than
      // beside the lane: 24.5 minutes is not a property of the picture, it is
      // the size of the correction being made.
      const on = p * r * THREE.MathUtils.clamp((a - 0.35) / 0.4, 0, 1);
      shiftLabel.current.visible = on > 0.03;
      shiftLabel.current.position.x = qx - (a * SHIFT * LEN) / 2;
      shiftLabel.current.traverse((o) => {
        if (o.fillOpacity !== undefined) o.fillOpacity = on * 0.95;
      });
    }
    if (priorLink.current) {
      // The previous laboratory sample, reaching FORWARD in time into the
      // feature vector. Drawn only once the shift has landed, because it is a
      // second, different claim and stacking them makes neither readable.
      const on = THREE.MathUtils.clamp((a - 0.55) / 0.4, 0, 1);
      priorLink.current.visible = r > 0.02 && a > 0.55;
      priorLink.current.material.opacity = p * r * on * 0.55;
      if (priorLabel.current) {
        // And it is NAMED. An unlabelled dashed diagonal is decoration, which
        // is the one thing this beat cannot afford: the previous laboratory
        // sample is why the feature vector is causal, and the copy column says
        // so in words the audience has to map onto something.
        priorLabel.current.visible = r > 0.02 && on > 0.05;
        priorLabel.current.traverse((o) => {
          if (o.fillOpacity !== undefined) o.fillOpacity = p * r * on * 0.7;
        });
      }
    }
  });

  const railLine = (y) => [
    new THREE.Vector3(X0, y, 0), new THREE.Vector3(X1, y, 0),
  ];

  return (
    <group ref={group} position={RESIDENCE.origin}>
      {/* ---------------------------------------------------------- beat 1 */}
      {/* The dryer, as a span of TIME rather than a picture of a machine. */}
      <Line
        ref={spanRef}
        points={[new THREE.Vector3(X0, 0, 0), new THREE.Vector3(X1, 0, 0)]}
        color={C.outline}
        lineWidth={2}
        transparent
        opacity={0}
      />
      <Line
        ref={inTick}
        points={[new THREE.Vector3(X0, -0.9, 0), new THREE.Vector3(X0, 1.5, 0)]}
        color={C.dust}
        lineWidth={2}
        transparent
        opacity={0}
      />
      <Line
        ref={outTick}
        points={[new THREE.Vector3(X1, -0.9, 0), new THREE.Vector3(X1, 1.5, 0)]}
        color={C.lab}
        lineWidth={2}
        transparent
        opacity={0}
      />

      <mesh ref={marker} material={markerMat} position={[X0, 0, 0.35]}>
        <boxGeometry args={[1.15, 1.15, 1.15]} />
      </mesh>

      <group ref={spanLabel}>
        <group position={[X0 + 0.35, 2.5, 0]} ref={(el) => { billboards.current[0] = el; }}>
          <WLabel fontSize={0.56} color={C.dust} anchorX="left" fillOpacity={0.9}>
            MATERIAL ENTERS
          </WLabel>
        </group>
        {/* Anchored to the RIGHT of its own tick rather than centred on it.
            Centred, the label's outer half hung past the end of the lane and
            straight off the frame edge. */}
        <group position={[X1 - 0.35, 2.5, 0]} ref={(el) => { billboards.current[1] = el; }}>
          <WLabel fontSize={0.56} color={C.lab} anchorX="right" fillOpacity={0.95}>
            SAMPLE TAKEN
          </WLabel>
        </group>
        <group position={[0, -2.3, 0]} ref={(el) => { billboards.current[2] = el; }}>
          <WMono fontSize={0.6} color={C.processWarm} anchorX="center" fillOpacity={0.95}>
            RESIDENCE TIME 24.5 min
          </WMono>
          <WMono position={[0, -0.95, 0]} fontSize={0.4} color={C.outline}
            anchorX="center" fillOpacity={0.7}>
            MEASURED PER SAMPLE - 24.15 to 24.89 min
          </WMono>
        </group>
      </group>

      {/* ---------------------------------------------------------- beat 2 */}
      {/* Two rails: what the process was doing, and what the laboratory
          eventually reported. Same clock, different material. */}
      <Line
        ref={processRail}
        points={railLine(railY)}
        color={C.dataTeal}
        lineWidth={1.6}
        transparent
        opacity={0}
      />
      <Line
        ref={qualityRail}
        points={railLine(-railY)}
        color={C.lab}
        lineWidth={1.6}
        transparent
        opacity={0}
      />

      {/* The rail names belong to beat 2 and are gated with the rails they
          name. They used to carry a static fillOpacity, so both were legible
          during beat 1 — two labels for an idea the audience had not been
          shown yet, over a lane that had no rails on it. */}
      <group ref={railLabels}>
        <group position={[0, railY, 0]} ref={(el) => { billboards.current[3] = el; }}>
          <WMono position={[X0 - 0.4, 1.0, 0]} fontSize={0.46} color={C.dataTeal} fillOpacity={0}>
            PROCESS VARIABLES
          </WMono>
        </group>
        {/* Below the hour ticks, not level with them. At -1.35 it shared a band
            with the 0 h and 1 h labels and the three overprinted. */}
        <group position={[0, -railY, 0]} ref={(el) => { billboards.current[4] = el; }}>
          <WMono position={[X0 - 0.4, -2.35, 0]} fontSize={0.46} color={C.lab} fillOpacity={0}>
            LABORATORY QUALITY
          </WMono>
        </group>
      </group>

      <group ref={tickGroup}>
        {hourTicks.map((tk) => (
          <group key={tk.h}>
            <Line
              points={[
                new THREE.Vector3(tk.x, -railY - 0.45, 0),
                new THREE.Vector3(tk.x, railY + 0.45, 0),
              ]}
              color={C.outline}
              lineWidth={1}
              transparent
              opacity={0}
            />
            <group position={[tk.x, -railY - 1.05, 0]}>
              <WMono fontSize={0.44} color={C.outline} anchorX="center" fillOpacity={0}>
                {`${tk.h} h`}
              </WMono>
            </group>
          </group>
        ))}
      </group>

      <mesh ref={processBlock} material={railMat.process} position={[0, railY, 0]}>
        <boxGeometry args={[1.5, 1.0, 1.0]} />
      </mesh>
      <mesh ref={qualityBlock} material={railMat.quality} position={[0, -railY, 0]}>
        <boxGeometry args={[1.5, 1.0, 1.0]} />
      </mesh>

      {/* The wrong pairing: straight down, same timestamp, in the film's
          fault colour. It is shown because it is the mistake this method
          exists to prevent, and an unshown mistake is not a correction. */}
      <Line
        ref={naiveLink}
        points={[
          new THREE.Vector3(RESIDENCE.sampleAt * LEN + X0, railY - 0.5, 0),
          new THREE.Vector3(RESIDENCE.sampleAt * LEN + X0, -railY + 0.5, 0),
        ]}
        color={C.critical}
        lineWidth={2}
        dashed
        dashSize={0.5}
        gapSize={0.4}
        transparent
        opacity={0}
      />
      <Line
        ref={alignedLink}
        points={[
          new THREE.Vector3(RESIDENCE.sampleAt * LEN + X0 - SHIFT * LEN, railY, 0),
          new THREE.Vector3(RESIDENCE.sampleAt * LEN + X0, -railY, 0),
        ]}
        color={C.predict}
        lineWidth={2.4}
        transparent
        opacity={0}
      />
      <group ref={shiftLabel} position={[0, railY + 0.05, 0]}>
        <group ref={(el) => { billboards.current[5] = el; }} position={[0, 1.05, 0]}>
          <WMono fontSize={0.5} color={C.predict} anchorX="center" fillOpacity={0}>
            SHIFTED BACK 24.5 min
          </WMono>
        </group>
      </group>

      <group
        ref={(el) => { priorLabel.current = el; billboards.current[6] = el; }}
        position={[RESIDENCE.priorAt * LEN + X0, -RESIDENCE.railGap - 3.4, 0]}
      >
        <WMono fontSize={0.44} color={C.outline} anchorX="center" fillOpacity={0}>
          PREVIOUS LAB SAMPLE
        </WMono>
        <WMono position={[0, -0.7, 0]} fontSize={0.36} color={C.outline}
          anchorX="center" fillOpacity={0}>
          density + product temperature
        </WMono>
      </group>

      {/* The previous laboratory result, carried forward into the feature
          vector. Backward-pointing, dimmer, and a different colour, so it is
          never read as part of the shift. */}
      <Line
        ref={priorLink}
        points={[
          new THREE.Vector3(RESIDENCE.sampleAt * LEN + X0 - SHIFT * LEN, railY - 0.2, 0),
          new THREE.Vector3(RESIDENCE.priorAt * LEN + X0, -railY + 0.2, 0),
        ]}
        color={C.outline}
        lineWidth={1.4}
        dashed
        dashSize={0.4}
        gapSize={0.5}
        transparent
        opacity={0}
      />
    </group>
  );
}
