import { useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { HANDOVER } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { useShow } from '../../state/useShow.js';
import { WLabel, WMono } from '../WorldText.jsx';

/**
 * The signature sequence: the model leaves the notebook.
 *
 * WHY THIS AND NOT SOMETHING GRANDER. The film used to promise a transformation
 * here and deliver a cross-fade. The honest reason it delivered a cross-fade is
 * that the spectacular version — a validation chart morphing into a dashboard —
 * was a lie about two different charts of two different windows, and retiring it
 * was correct. What was left was a beat with a keynote headline and nothing
 * happening under it.
 *
 * This is the transformation that IS true, and it happens to be the strongest
 * engineering claim the project can make:
 *
 *     the file the notebook wrote
 *       is the file the service loads
 *         is the thing answering into the operator's screen
 *
 * and it is not a claim about intent — it is checkable. `models/model_registry.json`
 * carries the SHA-256 of `quality_moisture_pipeline.joblib` and the flag
 * `runtime_uses_exact_notebook03_artifact: true`; `realtime_service.py`
 * `load_artifacts()` joblib-loads that exact path once at start and never
 * re-fits. Three objects, one continuity: an artifact, a process, a screen.
 *
 * THE CONTINUITY OBJECT. The cube the artifact folds into is deliberately the
 * same geometry, colour and material family as the runtime checkpoints in
 * three/layers/Runtime.jsx. One scene later the camera walks the runtime path
 * and meets it again, labelled PYTHON INFERENCE. It is the one object in the
 * film that survives a change of environment, which is the whole point: the
 * model did not get re-implemented on the way to production, it got loaded.
 *
 * WHAT IS NOT CLAIMED. No deployment. No control action. No closed loop. The
 * stream ends at a screen, the caption says the file is a prototype replay, and
 * the boundary badge is on screen throughout. The sequence is a HANDOVER, and
 * a handover is exactly as far as this project has gone.
 */

const CARD = HANDOVER.card;
const NODE = HANDOVER.node;
const SINK = HANDOVER.sink;

const _v = new THREE.Vector3();
const _o = new THREE.Object3D();

export default function Handover() {
  const { camera } = useThree();
  const group = useRef();
  const safeMode = useShow((s) => s.safeMode);

  const presence = useChannel('handover');
  /** The artifact resolves out of the dark. */
  const cardCh = useChannel('artifactCard', 0);
  /** It tips edge-on and compresses into the service node. */
  const foldCh = useChannel('artifactFold', 0);
  /** The service is running: loaded once, ticking. */
  const liveCh = useChannel('serviceLive', 0);
  /** Inference output travels to the report plane. */
  const streamCh = useChannel('inferStream', 0);

  const billboards = useRef([]);
  const cardGroup = useRef();
  const cardMesh = useRef();
  const cardEdge = useRef();
  const cardText = useRef();
  const nodeGroup = useRef();
  const nodeMesh = useRef();
  const nodeEdge = useRef();
  const nodeText = useRef();
  const beam = useRef();
  const packets = useRef();

  const cardMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.steelDark,
    roughness: 0.5,
    metalness: 0.15,
    emissive: new THREE.Color(C.ocpGreen),
    emissiveIntensity: 0.06,
    transparent: true,
    opacity: 0,
    fog: false,
    side: THREE.DoubleSide,
  }), []);

  // Deliberately identical to Runtime.jsx's checkpoint material. This is the
  // same object, met twice.
  const nodeMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.forest700,
    roughness: 0.42,
    metalness: 0.18,
    emissive: new THREE.Color(C.dataTeal),
    emissiveIntensity: 0.2,
    transparent: true,
    opacity: 0,
    fog: false,
  }), []);

  const packetMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.dataCyan, transparent: true, opacity: 0,
    depthWrite: false, blending: THREE.AdditiveBlending, fog: false,
  }), []);
  const packetGeo = useMemo(() => new THREE.BoxGeometry(0.16, 0.16, 0.5), []);

  const edgeCard = useMemo(
    () => new THREE.EdgesGeometry(new THREE.BoxGeometry(CARD.w, CARD.h, 0.22)),
    []
  );
  const edgeNode = useMemo(
    () => new THREE.EdgesGeometry(new THREE.BoxGeometry(3.4, 3.4, 3.4)),
    []
  );

  // A short, dense stream. This is one service writing one row every five
  // seconds, not a firehose — 90 instances read as a signal, 900 would read as
  // a special effect and would be a lie about the throughput.
  const count = safeMode ? 34 : 90;
  const seeds = useMemo(
    () => Float32Array.from({ length: count }, () => Math.random()),
    [count]
  );
  const phase = useRef(0);

  const cardPos = useMemo(() => new THREE.Vector3(...CARD.pos), []);
  const nodePos = useMemo(() => new THREE.Vector3(...NODE.pos), []);
  const sinkPos = useMemo(() => new THREE.Vector3(...SINK), []);

  useFrame((_s, dt) => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    for (const b of billboards.current) if (b) b.quaternion.copy(camera.quaternion);

    const c = THREE.MathUtils.clamp(cardCh.current, 0, 1);
    const f = THREE.MathUtils.clamp(foldCh.current, 0, 1);
    const l = THREE.MathUtils.clamp(liveCh.current, 0, 1);
    const st = THREE.MathUtils.clamp(streamCh.current, 0, 1);

    // --- the artifact --------------------------------------------------------
    // It arrives flat and face-on, the way a file is looked at, then TIPS and
    // compresses. The tip runs slightly ahead of the travel so the object
    // commits to the move before it makes it — anticipation, not decoration.
    if (cardGroup.current) {
      const tip = THREE.MathUtils.clamp(f * 1.25, 0, 1);
      cardGroup.current.position.copy(cardPos).lerp(nodePos, f * f);
      cardGroup.current.rotation.y = tip * -1.15;
      cardGroup.current.rotation.z = tip * 0.14;
      const shrink = 1 - f * 0.55;
      cardGroup.current.scale.set(shrink, shrink, 1);
      cardGroup.current.visible = c > 0.02 && f < 0.995;
    }
    cardMat.opacity = p * c * (1 - f * 0.9);
    if (cardEdge.current) cardEdge.current.material.opacity = p * c * (1 - f) * 0.85;
    if (cardText.current) {
      // The filenames leave BEFORE the geometry does. Type that shrinks and
      // rotates with a solid is the single clearest sign of a template
      // transition; the words are read, then they go, then the object moves.
      const textOn = p * c * THREE.MathUtils.clamp(1 - f * 2.2, 0, 1);
      cardText.current.visible = textOn > 0.03;
      cardText.current.traverse((o) => {
        if (o.fillOpacity !== undefined) o.fillOpacity = textOn * (o.userData?.base ?? 0.9);
      });
    }

    // --- the service ---------------------------------------------------------
    if (nodeGroup.current) {
      nodeGroup.current.visible = f > 0.25 && l > 0.02;
      // It lands with a small settle rather than popping to size.
      const arrive = THREE.MathUtils.clamp((f - 0.25) / 0.75, 0, 1);
      const overshoot = Math.sin(arrive * Math.PI) * 0.06;
      nodeGroup.current.scale.setScalar(0.72 + arrive * 0.28 + overshoot);
    }
    // The node exists once the fold has committed, and it is VISIBLE only while
    // the service is live. That coupling is what lets the whole corridor
    // dissolve into the report at the end of the beat: a 3.4-unit solid sitting
    // at 68 % of frame width is directly on top of the trend chart, and the
    // rule this film has held since the last pass is that nothing shares the
    // frame with the deliverable. The service dissolving as the screen it feeds
    // resolves is also the correct read — it is not gone, it is behind.
    const gate = THREE.MathUtils.clamp((f - 0.25) / 0.55, 0, 1);
    const nodeOn = p * gate * l;
    nodeMat.opacity = nodeOn;
    // The five-second tick. A running service is not a lit box; it is a box
    // that does something on a period, and the period is the one the project
    // actually runs at.
    nodeMat.emissiveIntensity = 0.2 + l * (0.28 + 0.22 * Math.pow(
      Math.max(0, Math.sin(_s.clock.elapsedTime * (Math.PI * 2) / 5)), 6
    ));
    if (nodeEdge.current) nodeEdge.current.material.opacity = nodeOn * 0.6;
    if (nodeText.current) {
      nodeText.current.visible = nodeOn > 0.03;
      nodeText.current.traverse((o) => {
        if (o.fillOpacity !== undefined) o.fillOpacity = nodeOn * (o.userData?.base ?? 0.9);
      });
    }

    // --- inference reaching the screen --------------------------------------
    if (beam.current) {
      beam.current.visible = st > 0.02;
      beam.current.material.opacity = p * st * 0.32;
    }
    packetMat.opacity = p * st * 0.9;
    if (packets.current) {
      packets.current.visible = st > 0.02;
      if (st > 0.02) {
        phase.current += dt * 0.34;
        for (let i = 0; i < count; i += 1) {
          // The stream FILLS the route rather than appearing along all of it:
          // `st` gates how far down the corridor a packet is allowed to be, so
          // the first inference visibly has to travel before the screen can
          // answer.
          const u = (seeds[i] + phase.current) % 1;
          const reach = u * Math.min(1, st * 1.35);
          _v.copy(nodePos).lerp(sinkPos, reach);
          _o.position.copy(_v);
          _o.lookAt(sinkPos);
          _o.scale.setScalar(0.9 + (1 - reach) * 0.5);
          _o.updateMatrix();
          packets.current.setMatrixAt(i, _o.matrix);
        }
        packets.current.instanceMatrix.needsUpdate = true;
      }
    }
  });

  return (
    <group ref={group}>
      {/* ------------------------------------------------------ the artifact */}
      <group ref={cardGroup} position={CARD.pos}>
        <mesh ref={cardMesh} material={cardMat}>
          <boxGeometry args={[CARD.w, CARD.h, 0.22]} />
        </mesh>
        <lineSegments ref={cardEdge} geometry={edgeCard}>
          <lineBasicMaterial color={C.ocpGreen} transparent opacity={0} fog={false} />
        </lineSegments>

        <group ref={cardText} position={[0, 0, 0.2]}>
          <WMono position={[-CARD.w / 2 + 0.6, CARD.h / 2 - 0.62, 0]} fontSize={0.34}
            color={C.ocpLime} fillOpacity={0}>
            TRAINED ARTIFACT
          </WMono>
          <WLabel position={[-CARD.w / 2 + 0.6, CARD.h / 2 - 1.55, 0]} fontSize={0.38}
            color={C.dustBright} fillOpacity={0}>
            quality_moisture_pipeline.joblib
          </WLabel>
          <WLabel position={[-CARD.w / 2 + 0.6, CARD.h / 2 - 2.25, 0]} fontSize={0.38}
            color={C.dustBright} fillOpacity={0}>
            anomaly_model.joblib
          </WLabel>
          <WMono position={[-CARD.w / 2 + 0.6, -CARD.h / 2 + 1.25, 0]} fontSize={0.32}
            color={C.dataTeal} fillOpacity={0}>
            sha256 b525c7b8 - Ridge 16 features
          </WMono>
          <WMono position={[-CARD.w / 2 + 0.6, -CARD.h / 2 + 0.68, 0]} fontSize={0.32}
            color={C.outline} fillOpacity={0}>
            notebooks/03_Model1_SoftSensor.ipynb
          </WMono>
        </group>
      </group>

      {/* -------------------------------------------------------- the service */}
      <group ref={nodeGroup} position={NODE.pos}>
        <mesh ref={nodeMesh} material={nodeMat}>
          <boxGeometry args={[3.4, 3.4, 3.4]} />
        </mesh>
        <lineSegments ref={nodeEdge} geometry={edgeNode}>
          <lineBasicMaterial color={C.dataTeal} transparent opacity={0} fog={false} />
        </lineSegments>
        {/* The name turns to face the lens. The camera crosses this corridor
            again in scene 11 from the far side, and a label baked into the
            node's own plane would be rendered mirrored there. */}
        <group
          position={[0, 3.1, 0]}
          ref={(el) => { nodeText.current = el; billboards.current[0] = el; }}
        >
          <WLabel fontSize={0.82} color={C.dustBright} anchorX="center" fillOpacity={0}>
            realtime_service.py
          </WLabel>
          <WMono position={[0, -0.95, 0]} fontSize={0.46} color={C.dataTeal}
            anchorX="center" fillOpacity={0}>
            LOADED ONCE - 9 ms AVERAGE CYCLE
          </WMono>
        </group>
      </group>

      {/* --------------------------------------------- inference to the screen */}
      <Line
        ref={beam}
        points={[nodePos, sinkPos]}
        color={C.dataTeal}
        lineWidth={1.3}
        transparent
        opacity={0}
      />
      <instancedMesh ref={packets} args={[packetGeo, packetMat, count]} frustumCulled={false} />
    </group>
  );
}
