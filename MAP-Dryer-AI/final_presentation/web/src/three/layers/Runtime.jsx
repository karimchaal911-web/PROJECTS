import { useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { RUNTIME_NODES, OPERATOR_NODE } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';

/**
 * What is behind the dashboard — as a path the camera travels, not a stack it
 * looks at.
 *
 * Scene 07 already owns the stacked-layer metaphor for the architecture. Using
 * it a second time here made the two scenes read as the same idea, and the
 * slabs occluded four of their own five labels. The runtime is now five
 * checkpoints along a line laid out in DATA-FLOW ORDER: the camera enters at
 * the replay end and travels forward with the data, so the direction the
 * viewer moves is the direction the data moves.
 *
 * The line stops at the operator. It does not continue back into the process,
 * because nothing in this project writes back to the process.
 */

const _v = new THREE.Vector3();

export default function Runtime() {
  const { camera } = useThree();
  const group = useRef();
  const presence = useChannel('runtime');
  const reveal = useChannel('runtimeReveal', 0);
  const walk = useChannel('runtimePath', 0);
  const operator = useChannel('operatorReveal', 0);

  const nodeRefs = useRef([]);
  const opRef = useRef();
  // Every in-world caption in this scene turns to face the lens.
  //
  // The route is walked from the deep end forward, so the camera spends the
  // whole scene on the far side of labels that faced +Z: REPLAY, POSTGRESQL
  // and POWER BI were all rendered back-to-front, i.e. mirrored. Reversed
  // type in the middle of the film's end-to-end integration proof reads as a
  // rendering bug, which is the one thing this scene cannot afford.
  const billboards = useRef([]);

  const points = useMemo(
    () => [...RUNTIME_NODES.map((n) => n.pos), OPERATOR_NODE.pos]
      .map((p) => new THREE.Vector3(...p)),
    []
  );

  const spineRef = useRef();
  const ghostRef = useRef();
  const ghostRefs = useRef([]);
  const solidRefs = useRef([]);

  const ghostGeo = useMemo(
    () => new THREE.EdgesGeometry(new THREE.BoxGeometry(3.4, 3.4, 3.4)),
    []
  );
  const ghostMat = useMemo(() => new THREE.LineBasicMaterial({
    color: C.dataTeal, transparent: true, opacity: 0, fog: false,
  }), []);

  const nodeMat = useMemo(
    () => RUNTIME_NODES.map(() => new THREE.MeshStandardMaterial({
      color: C.forest700,
      roughness: 0.42,
      metalness: 0.18,
      emissive: new THREE.Color(C.dataTeal),
      emissiveIntensity: 0.2,
      transparent: true,
      opacity: 0,
      fog: false,
    })),
    []
  );

  // The operator terminal is deliberately a different material and a different
  // colour from every runtime node: the last step is not another service.
  const opMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.ocpLime,
    roughness: 0.35,
    metalness: 0.1,
    emissive: new THREE.Color(C.ocpLime),
    emissiveIntensity: 0.35,
    transparent: true,
    opacity: 0,
    fog: false,
  }), []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const r = reveal.current;
    const w = walk.current;

    for (const b of billboards.current) {
      if (b) b.quaternion.copy(camera.quaternion);
    }

    // The whole route exists faintly from the moment we arrive at the deep
    // end, so the first frame of the scene shows a corridor to travel rather
    // than a single lit box in an empty void. Checkpoints not yet reached are
    // an outline; reaching one fills it.
    ghostMat.opacity = p * r * 0.5;
    if (ghostRef.current) ghostRef.current.material.opacity = p * r * 0.34;

    if (spineRef.current) {
      spineRef.current.material.opacity = p * r * 0.55;
      // The spine draws itself forward as we travel it.
      const n = points.length;
      const shown = Math.max(2, Math.floor(THREE.MathUtils.clamp(w, 0, 1) * (n - 1)) + 1);
      spineRef.current.geometry.setDrawRange?.(0, shown);
      if (spineRef.current.geometry.instanceCount !== undefined) {
        spineRef.current.geometry.instanceCount = Math.max(1, shown - 1);
      }
    }

    RUNTIME_NODES.forEach((_, i) => {
      const g = nodeRefs.current[i];
      if (!g) return;
      // Each checkpoint resolves as the journey reaches its depth.
      const local = THREE.MathUtils.clamp(w * RUNTIME_NODES.length - i + 0.35, 0, 1);
      const on = r * local;
      // The GROUP stays visible for the whole scene; only its contents come
      // and go. Hiding the group on `on > 0.02` also hid the outline inside
      // it, so a checkpoint the camera had not reached yet rendered as
      // nothing at all — which is why the first frame of this scene was two
      // lit boxes in an empty void instead of a corridor to travel.
      g.visible = r > 0.02;
      g.scale.setScalar(0.88 + on * 0.12);

      const gh = ghostRefs.current[i];
      if (gh) gh.visible = on < 0.98;
      const solid = solidRefs.current[i];
      if (solid) solid.visible = on > 0.02;
      nodeMat[i].opacity = p * on;

      // Once the route has receded to a trail behind the report, the
      // checkpoint names have done their job. Leaving them up wrote five
      // faint captions across the corner of the dashboard.
      const lb = billboards.current[i];
      if (lb) lb.visible = r > 0.6 && on > 0.02;
      g.traverse((o) => {
        if (o.material && o.material.transparent
            && o.material !== nodeMat[i] && o !== gh) {
          o.material.opacity = Math.min(o.material.userData.max ?? 1, p * on);
        }
      });
    });

    if (opRef.current) {
      const o = operator.current;
      opRef.current.visible = o > 0.02;
      opMat.opacity = p * o;
      opRef.current.traverse((n) => {
        if (n.material && n.material.transparent && n.material !== opMat) {
          n.material.opacity = Math.min(n.material.userData.max ?? 1, p * o);
        }
      });
    }
  });

  return (
    <group ref={group}>
      {/* the route, faint, entire: where we are going, before we go */}
      <Line
        ref={ghostRef}
        points={points}
        color={C.dataTeal}
        lineWidth={1.4}
        dashed
        dashSize={1.2}
        gapSize={1.6}
        transparent
        opacity={0}
      />

      {/* the spine: one continuous line, drawn in data-flow order */}
      <Line
        ref={spineRef}
        points={points}
        color={C.dataTeal}
        lineWidth={1.6}
        transparent
        opacity={0}
      />

      {RUNTIME_NODES.map((node, i) => (
        <group key={node.id} ref={(el) => { nodeRefs.current[i] = el; }} position={node.pos}>
          <lineSegments
            ref={(el) => { ghostRefs.current[i] = el; }}
            geometry={ghostGeo}
            material={ghostMat}
          />
          <mesh ref={(el) => { solidRefs.current[i] = el; }} material={nodeMat[i]}>
            <boxGeometry args={[3.4, 3.4, 3.4]} />
          </mesh>
          {/* The name sits directly above its own checkpoint and turns to
              face the lens, so it can neither be mirrored by a camera on the
              far side nor occluded by the box in front of it. */}
          <group
            position={[0, 3.5, 0]}
            ref={(el) => { billboards.current[i] = el; }}
          >
            <WLabel fontSize={1.15} color={C.dustBright} anchorX="center" fillOpacity={0.96}>
              {node.label}
            </WLabel>
            <WMono position={[0, -1.3, 0]} fontSize={0.58} color={C.dataTeal}
              anchorX="center" fillOpacity={0.85}>
              {node.sub}
            </WMono>
            <WMono position={[0, 1.55, 0]} fontSize={0.62} color={C.outline}
              anchorX="center" fillOpacity={0.75}>
              {`0${i + 1}`}
            </WMono>
          </group>
        </group>
      ))}

      {/* The end of the chain: a person, not an actuator. */}
      <group ref={opRef} position={OPERATOR_NODE.pos}>
        {/* An operator station, not a disc and not a figure. A screen on a
            stand is enough to read as "a person works here" without inventing
            a control room the project does not have. */}
        <mesh material={opMat} position={[0, -1.5, 0]}>
          <boxGeometry args={[4.0, 0.3, 2.4]} />
        </mesh>
        <mesh material={opMat} position={[0, -0.9, 0]}>
          <boxGeometry args={[0.45, 1.2, 0.45]} />
        </mesh>
        <mesh material={opMat} position={[0, 0.4, 0.15]} rotation={[-0.16, 0, 0]}>
          <boxGeometry args={[3.8, 2.3, 0.2]} />
        </mesh>
        <group ref={(el) => { billboards.current[RUNTIME_NODES.length] = el; }}
          position={[0, 3.2, 0]}>
          <WLabel fontSize={1.5} color={C.ocpLime} anchorX="center" fillOpacity={0.98}>
            {OPERATOR_NODE.label}
          </WLabel>
          <WMono position={[0, -1.5, 0]} fontSize={0.66} color={C.dustBright}
            anchorX="center" fillOpacity={0.9}>
            {OPERATOR_NODE.sub}
          </WMono>
        </group>
        {/* "Nothing writes back to the process" is already the scene's note
            AND its caption, both in the DOM where they have a scrim and the
            full font. A third copy, skewed across the dashboard, was noise. */}
      </group>
    </group>
  );
}
