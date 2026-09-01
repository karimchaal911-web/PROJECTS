import { useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { STATIONS, RECYCLE, chainCurve } from '../../lib/curves.js';
import { useChannel } from '../usePresence.js';
import { WLabel, WMono } from '../WorldText.jsx';
import { applySurface } from '../../lib/surfaces.js';

/**
 * The six upstream unit operations of the verified soluble-MAP sequence, the
 * material line that connects them, and the mother-liquor recycle.
 *
 * What changed, and why:
 *
 * 1. SILHOUETTE. Every station used to be a cylinder with a cap. A jury of
 *    chemical engineers reads that as "these seven things are the same
 *    machine". Each operation is now built from the KIND of equipment it
 *    needs — a receiver feeding two horizontal shell-and-tube vaporizers, a
 *    train of three agitated reactors, a row of agitated buffer tanks, a
 *    crystalliser with an external forced-circulation loop and a vapour
 *    condenser, two parallel horizontal centrifuges on a skid. The forms come
 *    from the site's own PCS7 mimics in `assets/process/`; see the STATIONS
 *    comment in lib/curves.js for the reference behind each one and for what
 *    is deliberately NOT claimed (no tag, no dimension, no equipment identity).
 *
 * 2. MATERIAL. One beige standard material lit only by a hemisphere is why
 *    everything read as unlit clay. There are now six surfaces — painted
 *    vessel steel, stainless, dark machine metal, green structural steel,
 *    yellow handrail, lagged pipe — with roughness and metalness that actually
 *    differ, and each station's paint carries a small hue offset so a row of
 *    tanks is not one flat mass.
 *
 * 3. LIGHT. The hall's key light is frustum-fitted to the dryer at the origin.
 *    The chain lives at x -96..-16, i.e. entirely outside it, so it was lit by
 *    ambient alone. A key and a rim now TRACK the material down the chain, so
 *    the stage the material is in is the stage that is lit and the ones behind
 *    it fall away — the "one active stage dominates" rule enforced by the
 *    lighting rather than by hiding geometry. Contact shadows are decals, not
 *    a second shadow map, so the boot-window performance guarantee is intact.
 *
 * 4. LABELS. 1.15-unit world text floating over the equipment collided with
 *    every dome and got cut by the frame edge. Labels are now small, screen
 *    facing, drawn in front of the world, anchored to the equipment by a real
 *    leader line, and only the active station's label is at full strength.
 */

const ACTIVE = STATIONS.filter((s) => s.r > 0);
const AT = (id) => ACTIVE.find((s) => s.id === id);

// How far the leader lifts the type block off the equipment, in world units.
const LEAD_UP = 3.1;

export default function ProcessChain() {
  const group = useRef();
  const presence = useChannel('chain');
  const headRef = useChannel('chainHead', 0);

  const labelRefs = useRef([]);
  const leaderRefs = useRef([]);
  const recycleLabel = useRef();
  const recycleLeader = useRef();
  const keyLight = useRef();
  const rimLight = useRef();

  /* ------------------------------------------------------------ surfaces --- */
  const M = useMemo(() => {
    const mk = (o) => new THREE.MeshStandardMaterial({ transparent: true, opacity: 0, ...o });
    const M = {
      // painted carbon-steel vessel shell
      paint: mk({ color: '#A7ACA2', roughness: 0.56, metalness: 0.18, envMapIntensity: 0.8 }),
      // stainless: nozzles, flanges, agitator shafts
      steel: mk({ color: '#C6CAC7', roughness: 0.29, metalness: 0.86, envMapIntensity: 1.1 }),
      // dark machine metal: motors, gearboxes, drive housings, skids
      machine: mk({ color: '#39413B', roughness: 0.44, metalness: 0.72, envMapIntensity: 0.9 }),
      // the plant's structural steel is painted green
      struct: mk({ color: C.steelGreen, roughness: 0.72, metalness: 0.12, envMapIntensity: 0.5 }),
      // and its handrails are yellow
      rail: mk({ color: C.handrail, roughness: 0.68, metalness: 0.22, envMapIntensity: 0.6 }),
      // lagged / insulated process line
      lag: mk({ color: '#B0ADA2', roughness: 0.88, metalness: 0.04, envMapIntensity: 0.4 }),
      // the recycle line: a painted pipe, not a glowing tube
      recycle: mk({ color: '#3F6B47', roughness: 0.52, metalness: 0.28, envMapIntensity: 0.7 }),
      grating: mk({ color: C.grating, roughness: 0.9, metalness: 0.14 }),
    };

    // Eight fabrications, eight surfaces. The point of the chain scene is that
    // a chemical engineer can tell a vaporizer from a reactor from a
    // centrifuge; that argument is weakened if all eight are the same plastic.
    // Stainless keeps the tightest treatment and the strongest dust term —
    // dust on a mirror is the one place metalness has to fall or the surface
    // goes on reflecting the room through the dirt.
    applySurface(M.paint, 'paint', { repeat: [4, 3] });
    applySurface(M.steel, 'machined', { repeat: [6, 3] });
    applySurface(M.machine, 'machined', { repeat: 4 });
    applySurface(M.struct, 'struct', { repeat: 4 });
    applySurface(M.rail, 'paint', { repeat: [8, 2] });
    applySurface(M.lag, 'lagged', { repeat: [2, 3] });
    applySurface(M.recycle, 'pipe', { repeat: [2, 4] });
    applySurface(M.grating, 'grating', { repeat: 7 });

    return M;
  }, []);

  /**
   * One paint material per station, so the row does not read as one mass and
   * so a station can warm slightly as the material reaches it.
   */
  const shellMats = useMemo(
    () => ACTIVE.map((s, i) => {
      const m = M.paint.clone();
      m.color = new THREE.Color(M.paint.color).offsetHSL((i - 2.5) * 0.010, 0.02, (i % 2 ? 0.018 : -0.014));
      m.emissive = new THREE.Color(C.processWarm);
      m.emissiveIntensity = 0;
      m.transparent = true;
      m.opacity = 0;
      return m;
    }),
    [M]
  );

  /* ---------------------------------------------------------- geometries --- */
  // Unit primitives, scaled per mesh. Seven geometries carry the whole chain.
  const G = useMemo(() => ({
    cyl: new THREE.CylinderGeometry(1, 1, 1, 28),
    cyl14: new THREE.CylinderGeometry(1, 1, 1, 14),
    cone: new THREE.ConeGeometry(1, 1, 26),
    dome: new THREE.SphereGeometry(1, 24, 10, 0, Math.PI * 2, 0, Math.PI / 2),
    box: new THREE.BoxGeometry(1, 1, 1),
    disc: new THREE.CircleGeometry(1, 40),
  }), []);

  /* ------------------------------------------------------ contact shadow --- */
  const shadowMat = useMemo(() => {
    const s = 128;
    const cv = document.createElement('canvas');
    cv.width = s; cv.height = s;
    const ctx = cv.getContext('2d');
    const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
    g.addColorStop(0, 'rgba(0,0,0,0.85)');
    g.addColorStop(0.55, 'rgba(0,0,0,0.36)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, s, s);
    const tex = new THREE.CanvasTexture(cv);
    tex.colorSpace = THREE.SRGBColorSpace;
    return new THREE.MeshBasicMaterial({
      map: tex, transparent: true, opacity: 0, depthWrite: false, fog: false,
    });
  }, []);

  /* --------------------------------------------------------- annotations --- */
  // Drawn in front of the world so a pipe can never cut a name in half.
  const leaderMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.dataTeal, transparent: true, opacity: 0, depthTest: false,
    depthWrite: false, fog: false,
  }), []);

  const positions = useMemo(
    () => ACTIVE.map((s) => chainCurve.getPoint(s.t / 0.98)),
    []
  );

  /* --------------------------------------------------- the material line --- */
  const pipe = useMemo(() => {
    const geo = new THREE.TubeGeometry(chainCurve, 140, 0.27, 10, false);
    // Flanged joints and stanchions: the line used to float with nothing
    // holding it up, which is what made it read as a drawn line rather than
    // as pipework.
    const joints = [];
    const stanchions = [];
    for (let k = 1; k < 14; k += 1) {
      const u = k / 14;
      const p = chainCurve.getPoint(u);
      const t = chainCurve.getTangent(u).normalize();
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), t);
      joints.push({ pos: p.toArray(), quat: q.toArray() });
      if (k % 3 === 0) stanchions.push({ x: p.x, y: p.y, z: p.z });
    }
    // Flow-direction placards, the way a real line carries them.
    const arrows = [0.12, 0.29, 0.45, 0.60, 0.75, 0.90].map((u) => {
      const p = chainCurve.getPoint(u);
      const t = chainCurve.getTangent(u).normalize();
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), t);
      return { pos: [p.x, p.y + 0.44, p.z], quat: q.toArray() };
    });
    return { geo, joints, stanchions, arrows };
  }, []);

  const arrowMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: C.dustBright, roughness: 0.6, metalness: 0.1, transparent: true, opacity: 0,
  }), []);

  /* --------------------------------------------- mother-liquor recycle ----- */
  /**
   * Verified: the mother liquor separated at centrifugation returns upstream to
   * neutralization (RESOURCE_AUDIT section 5; the site's "Essorage" mimic shows
   * "Eaux Meres" leaving the centrifuges, and the "Neutralisation" mimic shows
   * "Eaux Meres" arriving).
   *
   * It used to be an emissive green tube cutting diagonally across the frame
   * with its label rotated off the edge of the screen. It is now a painted
   * pipe running LOW and slightly behind the vessels, parallel to the material
   * line and in the opposite direction — which is both what a plant looks like
   * and unambiguous in a still frame.
   */
  const recycle = useMemo(() => {
    // Named, not indexed: RECYCLE lives beside STATIONS in lib/curves.js, so a
    // reordering of the sequence cannot silently re-point the loop.
    const from = chainCurve.getPoint(AT(RECYCLE.from).t / 0.98);
    const to = chainCurve.getPoint(AT(RECYCLE.to).t / 0.98);
    const low = 1.55;
    const back = -4.2;
    const pts = [
      new THREE.Vector3(from.x, from.y - 2.2, from.z + 0.6),
      new THREE.Vector3(from.x - 1.6, low, from.z + back * 0.45),
      new THREE.Vector3((from.x + to.x) * 0.5, low, (from.z + to.z) * 0.5 + back),
      new THREE.Vector3(to.x + 2.0, low, to.z + back * 0.5),
      new THREE.Vector3(to.x, to.y - 2.6, to.z + 0.6),
    ];
    const curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.25);
    const chevrons = [0.24, 0.42, 0.60, 0.78].map((u) => {
      const p = curve.getPoint(u);
      const t = curve.getTangent(u).normalize();
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), t);
      return { pos: [p.x, p.y + 0.36, p.z], quat: q.toArray() };
    });
    const supports = [0.3, 0.5, 0.7].map((u) => curve.getPoint(u));
    return {
      geo: new THREE.TubeGeometry(curve, 90, 0.21, 8, false),
      chevrons,
      supports,
      // Labelled where it LEAVES, so origin, direction and destination are
      // readable without following the pipe across the room.
      tap: [from.x - 1.0, from.y - 1.4, from.z + 1.2],
    };
  }, []);

  /* --------------------------------------------------- tracking key light --- */
  const keyTarget = useMemo(() => new THREE.Object3D(), []);
  const rimTarget = useMemo(() => new THREE.Object3D(), []);
  const _head = useMemo(() => new THREE.Vector3(), []);
  const { camera } = useThree();

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }

    for (const m of Object.values(M)) m.opacity = p;
    M.lag.opacity = p * 0.96;
    arrowMat.opacity = p * 0.85;
    shadowMat.opacity = p * 0.62;
    leaderMat.opacity = p * 0.85;

    const head = THREE.MathUtils.clamp(headRef.current, 0, 1);

    // The key and the rim ride the material. Everything the material has not
    // reached yet, and everything it has left, falls into the dark on its own.
    chainCurve.getPoint(THREE.MathUtils.clamp(head, 0.02, 0.99), _head);
    keyTarget.position.copy(_head);
    rimTarget.position.copy(_head);
    keyTarget.updateMatrixWorld();
    rimTarget.updateMatrixWorld();
    if (keyLight.current) {
      keyLight.current.position.set(_head.x - 7, _head.y + 20, _head.z + 15);
      keyLight.current.intensity = 3.4 * p;
    }
    if (rimLight.current) {
      rimLight.current.position.set(_head.x + 11, _head.y + 7, _head.z - 17);
      rimLight.current.intensity = 2.6 * p;
    }

    for (let i = 0; i < ACTIVE.length; i += 1) {
      const st = ACTIVE[i].t;
      const m = shellMats[i];
      m.opacity = p;

      // Reached: the material has arrived. Focus: the material is HERE.
      const reached = THREE.MathUtils.clamp((head - st + 0.10) / 0.10, 0, 1);
      const focus = THREE.MathUtils.clamp(1 - Math.abs(head - st) / 0.14, 0, 1);
      m.emissiveIntensity = (reached * 0.02 + focus * 0.06) * p;

      // ONE stage is named. Carrying the other five at 20 % opacity put five
      // grey ghosts across every frame, two of them cut in half by the frame
      // edge -- exactly the clutter this pass exists to remove.
      const strength = focus;
      const lg = labelRefs.current[i];
      if (lg) {
        lg.visible = strength > 0.03;
        if (lg.visible) {
          // World text lies in the XY plane. Seen from a camera that is both
          // off to one side and looking down, that reads as skewed italics --
          // which is why every equipment name in the previous cut was slanted.
          // The type block faces the lens; only the leader stays in the world.
          lg.quaternion.copy(camera.quaternion);
          lg.traverse((o) => {
            if (o.fillOpacity !== undefined) o.fillOpacity = strength;
          });
        }
      }
      const ld = leaderRefs.current[i];
      if (ld) ld.visible = strength > 0.03;
    }

    // The recycle is named only once the material has actually been separated.
    if (recycleLabel.current) {
      const on = THREE.MathUtils.clamp((head - 0.74) / 0.06, 0, 1);
      recycleLabel.current.visible = on > 0.03;
      if (recycleLabel.current.visible) {
        recycleLabel.current.quaternion.copy(camera.quaternion);
        recycleLabel.current.traverse((o) => {
          if (o.fillOpacity !== undefined) o.fillOpacity = on;
        });
      }
      if (recycleLeader.current) recycleLeader.current.visible = on > 0.03;
    }
  });

  return (
    <group ref={group}>
      {/* --- equipment-hero lighting that follows the material -------------- */}
      <primitive object={keyTarget} />
      <primitive object={rimTarget} />
      <spotLight
        ref={keyLight}
        color={C.keyLight}
        intensity={0}
        angle={0.62}
        penumbra={0.8}
        decay={0}
        distance={0}
        target={keyTarget}
      />
      <spotLight
        ref={rimLight}
        color={C.rimLight}
        intensity={0}
        angle={0.85}
        penumbra={1}
        decay={0}
        distance={0}
        target={rimTarget}
      />

      {/* --- the material line ---------------------------------------------- */}
      <mesh geometry={pipe.geo} material={M.lag} />
      {pipe.joints.map((j) => (
        <mesh key={`j${j.pos.join()}`} position={j.pos} quaternion={j.quat}
          geometry={G.cyl14} material={M.steel} scale={[0.37, 0.11, 0.37]} />
      ))}
      {pipe.stanchions.map((s) => (
        <group key={`s${s.x.toFixed(2)}`}>
          <mesh position={[s.x, s.y / 2, s.z]} geometry={G.box} material={M.struct}
            scale={[0.24, s.y, 0.24]} />
          <mesh position={[s.x, s.y - 0.32, s.z]} geometry={G.box} material={M.struct}
            scale={[1.0, 0.16, 0.5]} />
        </group>
      ))}
      {pipe.arrows.map((a) => (
        <group key={`a${a.pos.join()}`} position={a.pos} quaternion={a.quat}>
          <mesh geometry={G.box} material={arrowMat} scale={[0.7, 0.05, 0.30]} position={[0, 0, 0]} />
          <mesh geometry={G.cone} material={arrowMat} scale={[0.22, 0.5, 0.09]} position={[0, 0.42, 0]} />
        </group>
      ))}

      {/* --- the mother-liquor recycle -------------------------------------- */}
      <mesh geometry={recycle.geo} material={M.recycle} />
      {recycle.supports.map((s) => (
        <mesh key={`rs${s.x.toFixed(2)}`} position={[s.x, s.y / 2, s.z]}
          geometry={G.box} material={M.struct} scale={[0.2, s.y, 0.2]} />
      ))}
      {recycle.chevrons.map((c) => (
        <mesh key={`rc${c.pos.join()}`} position={c.pos} quaternion={c.quat}
          geometry={G.cone} material={M.recycle} scale={[0.20, 0.44, 0.08]} />
      ))}

      {/* --- the six upstream unit operations -------------------------------- */}
      {ACTIVE.map((s, i) => {
        const pos = positions[i];
        return (
          <group key={s.id} position={[pos.x, 0, pos.z]}>
            <mesh
              rotation={[-Math.PI / 2, 0, 0]}
              position={[0, 0.03, 0]}
              geometry={G.disc}
              material={shadowMat}
              scale={[s.r * 3.4, s.r * 2.6, 1]}
            />
            <Unit station={s} G={G} M={M} shell={shellMats[i]} />
          </group>
        );
      })}

      {/* --- annotation ------------------------------------------------------ */}
      {ACTIVE.map((st, i) => {
        const pos = positions[i];
        const ax = pos.x + st.anchor[0] * st.r;
        const ay = st.anchor[1];
        const az = pos.z;
        return (
          <group key={`lab-${st.id}`}>
            <group ref={(el) => { leaderRefs.current[i] = el; }}>
              {/* a small anchor ON the equipment, then one vertical leader */}
              <mesh position={[ax, ay, az]} geometry={G.cyl14} material={leaderMat}
                renderOrder={12} scale={[0.09, 0.14, 0.09]} />
              <mesh position={[ax, ay + LEAD_UP / 2, az]} geometry={G.box} material={leaderMat}
                renderOrder={12} scale={[0.035, LEAD_UP, 0.035]} />
            </group>

            <group ref={(el) => { labelRefs.current[i] = el; }} position={[ax, ay + LEAD_UP, az]}>
              <WMono
                overlay
                position={[0, 1.02, 0]}
                fontSize={0.30}
                color={C.dataTeal}
                anchorX="center"
                anchorY="middle"
                letterSpacing={0.2}
              >
                {st.n}
              </WMono>
              <WLabel
                overlay
                position={[0, 0.42, 0]}
                fontSize={0.46}
                color={C.dustBright}
                anchorX="center"
                anchorY="middle"
                maxWidth={13}
                lineHeight={1.2}
                textAlign="center"
                letterSpacing={0.03}
              >
                {st.label}
              </WLabel>
            </group>
          </group>
        );
      })}

      <group ref={recycleLeader}>
        <mesh position={recycle.tap} geometry={G.cyl14} material={leaderMat}
          renderOrder={12} scale={[0.09, 0.14, 0.09]} />
        <mesh position={[recycle.tap[0] - 2.6, recycle.tap[1] + 0.1, recycle.tap[2]]}
          geometry={G.box} material={leaderMat} renderOrder={12} scale={[5.2, 0.035, 0.035]} />
      </group>
      <group ref={recycleLabel} position={[recycle.tap[0] - 10.6, recycle.tap[1] + 0.1, recycle.tap[2]]}>
        <WMono
          overlay
          position={[0, 0, 0]}
          fontSize={0.36}
          color={C.ocpLime}
          anchorX="center"
          anchorY="middle"
          letterSpacing={0.08}
        >
          MOTHER LIQUOR -&gt; NEUTRALIZATION
        </WMono>
      </group>
    </group>
  );
}

/* ====================================================================== */
/* One unit operation. `form` chooses the KIND of machine; nothing here    */
/* asserts a real machine, a tag or a dimension.                           */
/* ====================================================================== */

function Unit({ station: s, G, M, shell }) {
  switch (s.form) {
    case 'vaporizer': return <Vaporizer s={s} G={G} M={M} shell={shell} />;
    case 'reactors': return <Reactors s={s} G={G} M={M} shell={shell} />;
    case 'tankfarm': return <TankFarm s={s} G={G} M={M} shell={shell} />;
    case 'crystalliser': return <Crystalliser s={s} G={G} M={M} shell={shell} />;
    case 'centrifuges': return <Centrifuges s={s} G={G} M={M} shell={shell} />;
    default: return <Vessel s={s} G={G} M={M} shell={shell} />;
  }
}

/* ---------------------------------------------------------------- parts --- */

/** A flanged nozzle: stub plus face. The single most useful industrial tell. */
function Nozzle({ G, M, position, rotation = [0, 0, 0], len = 0.9, r = 0.22 }) {
  return (
    <group position={position} rotation={rotation}>
      <mesh geometry={G.cyl14} material={M.steel} scale={[r, len, r]} position={[0, len / 2, 0]} />
      <mesh geometry={G.cyl14} material={M.steel} scale={[r * 1.9, 0.11, r * 1.9]} position={[0, len, 0]} />
    </group>
  );
}

/** A short run of pipe between two points, with a flange at each end. */
function Run({ G, M, from, to, r = 0.16, mat }) {
  const a = new THREE.Vector3(...from);
  const b = new THREE.Vector3(...to);
  const mid = a.clone().add(b).multiplyScalar(0.5);
  const dir = b.clone().sub(a);
  const len = dir.length();
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  return (
    <mesh position={mid.toArray()} quaternion={q.toArray()} geometry={G.cyl14}
      material={mat ?? M.lag} scale={[r, len, r]} />
  );
}

/**
 * Access platform with a yellow handrail.
 *
 * Deliberately small, and always set BEHIND the equipment. At their first size
 * these decks were sixteen units wide and stood in FRONT of the vessels: a
 * grey slab cutting diagonally across the frame was the largest object in the
 * neutralization shot, in front of the three reactors it was there to serve.
 */
function Platform({ G, M, y, w, d, x = 0, z = 0 }) {
  return (
    <group position={[x, y, z]}>
      <mesh geometry={G.box} material={M.grating} scale={[w, 0.09, d]} />
      {[0.55, 0.98].map((h) => (
        <mesh key={h} geometry={G.box} material={M.rail}
          position={[0, h, -d / 2]} scale={[w, 0.05, 0.05]} />
      ))}
      {[-w / 2 + 0.2, 0, w / 2 - 0.2].map((px) => (
        <mesh key={px} geometry={G.box} material={M.rail}
          position={[px, 0.5, -d / 2]} scale={[0.06, 1.0, 0.06]} />
      ))}
      {[-w / 2 + 0.15, w / 2 - 0.15].map((px) => (
        <mesh key={`br${px}`} geometry={G.box} material={M.struct}
          position={[px, -0.5, 0]} scale={[0.14, 1.0, d * 0.7]} />
      ))}
    </group>
  );
}

/** Agitator drive: pedestal, gearbox, motor, shaft into the vessel. */
function Agitator({ G, M, y, r, scale = 1 }) {
  return (
    <group position={[0, y, 0]} scale={scale}>
      <mesh geometry={G.cyl14} material={M.struct} scale={[r * 0.44, 0.9, r * 0.44]} position={[0, 0.45, 0]} />
      <mesh geometry={G.box} material={M.machine} scale={[r * 0.72, 0.86, r * 0.72]} position={[0, 1.33, 0]} />
      <mesh geometry={G.cyl14} material={M.machine} rotation={[0, 0, Math.PI / 2]}
        scale={[0.44, 1.25, 0.44]} position={[r * 0.62, 1.55, 0]} />
      <mesh geometry={G.cyl14} material={M.steel} scale={[0.09, 1.1, 0.09]} position={[0, -0.5, 0]} />
    </group>
  );
}

/* --------------------------------------------------------- 01 · VESSEL --- */
/**
 * Phosphoric-acid pretreatment. A vertical vessel with a dished head on a
 * skirt: nozzles top and side, girth flanges, a caged ladder, a top platform.
 */
function Vessel({ s, G, M, shell }) {
  const base = 1.1;
  const body = s.h - base;
  return (
    <>
      <mesh geometry={G.cyl} material={M.struct} scale={[s.r * 1.02, base, s.r * 1.02]} position={[0, base / 2, 0]} />
      <mesh geometry={G.cyl} material={M.machine} scale={[s.r * 1.16, 0.22, s.r * 1.16]} position={[0, 0.11, 0]} />
      <mesh geometry={G.cyl} material={shell} castShadow receiveShadow
        scale={[s.r, body, s.r]} position={[0, base + body / 2, 0]} />
      <mesh geometry={G.dome} material={shell} castShadow
        scale={[s.r, s.r * 0.52, s.r]} position={[0, base + body, 0]} />
      {[0.3, 0.66].map((f) => (
        <mesh key={f} geometry={G.cyl} material={M.steel}
          scale={[s.r * 1.035, 0.13, s.r * 1.035]} position={[0, base + body * f, 0]} />
      ))}
      <Nozzle G={G} M={M} position={[0, base + body + s.r * 0.5, 0]} len={1.1} r={0.26} />
      <Nozzle G={G} M={M} position={[s.r * 0.94, base + body * 0.80, 0]} rotation={[0, 0, -Math.PI / 2]} len={1.0} />
      <Nozzle G={G} M={M} position={[-s.r * 0.94, base + body * 0.34, 0]} rotation={[0, 0, Math.PI / 2]} len={1.0} />
      <Run G={G} M={M} from={[s.r * 1.6, base + body * 0.80, -s.r * 0.5]} to={[s.r * 1.6, s.h + 0.8, -s.r * 0.5]} />
      <Nozzle G={G} M={M} position={[0, base - 0.05, 0]} rotation={[Math.PI, 0, 0]} len={0.8} r={0.2} />
      <Platform G={G} M={M} y={base + body * 0.92} w={s.r * 1.9} d={1.3} z={-s.r * 1.15} />
    </>
  );
}

/* ------------------------------------------------------ 02 · VAPORIZER --- */
/**
 * Ammonia vaporization. Not a trayed column — the site's own mimic shows a
 * vertical receiver on a skirt feeding TWO HORIZONTAL SHELL-AND-TUBE
 * EXCHANGERS on saddle supports, with the glycol service lines running
 * alongside. That silhouette — one upright, two horizontals low down — is
 * unmistakable next to a row of tanks.
 */
function Vaporizer({ s, G, M, shell }) {
  const base = 1.0;
  const body = s.h - base - s.r * 0.5;
  const ex = (dz, y) => (
    <group position={[s.r * 2.6, y, dz]}>
      {/* shell */}
      <mesh geometry={G.cyl} material={shell} castShadow receiveShadow
        rotation={[0, 0, Math.PI / 2]} scale={[0.86, 5.4, 0.86]} />
      {/* channel heads, bolted */}
      {[-1, 1].map((k) => (
        <group key={k}>
          <mesh geometry={G.cyl} material={M.steel} rotation={[0, 0, Math.PI / 2]}
            scale={[0.96, 0.16, 0.96]} position={[k * 2.7, 0, 0]} />
          <mesh geometry={G.dome} material={M.steel} rotation={[0, 0, k * Math.PI / 2]}
            scale={[0.86, 0.5, 0.86]} position={[k * 2.95, 0, 0]} />
        </group>
      ))}
      {/* saddles */}
      {[-1.5, 1.5].map((k) => (
        <mesh key={k} geometry={G.box} material={M.struct}
          scale={[0.6, 1.5, 1.7]} position={[k, -1.45, 0]} />
      ))}
      {/* service nozzles */}
      <Nozzle G={G} M={M} position={[-1.6, 0.84, 0]} len={0.7} r={0.16} />
      <Nozzle G={G} M={M} position={[1.6, 0.84, 0]} len={0.7} r={0.16} />
    </group>
  );
  return (
    <>
      {/* receiver */}
      <mesh geometry={G.cyl} material={M.struct} scale={[s.r * 0.98, base, s.r * 0.98]} position={[0, base / 2, 0]} />
      <mesh geometry={G.cyl} material={shell} castShadow receiveShadow
        scale={[s.r, body, s.r]} position={[0, base + body / 2, 0]} />
      <mesh geometry={G.dome} material={shell} castShadow
        scale={[s.r, s.r * 0.5, s.r]} position={[0, base + body, 0]} />
      <mesh geometry={G.dome} material={shell} rotation={[Math.PI, 0, 0]}
        scale={[s.r, s.r * 0.5, s.r]} position={[0, base, 0]} />
      {[0.34, 0.7].map((f) => (
        <mesh key={f} geometry={G.cyl} material={M.steel}
          scale={[s.r * 1.04, 0.12, s.r * 1.04]} position={[0, base + body * f, 0]} />
      ))}
      <Nozzle G={G} M={M} position={[0, base + body + s.r * 0.48, 0]} len={1.0} r={0.24} />
      <Nozzle G={G} M={M} position={[s.r * 0.92, base + body * 0.18, 0]} rotation={[0, 0, -Math.PI / 2]} len={0.9} />

      {/* two horizontal vaporizers on saddles */}
      {ex(-1.9, 3.3)}
      {ex(1.9, 6.6)}

      {/* the runs that make them one unit */}
      <Run G={G} M={M} from={[s.r * 1.5, base + body * 0.18, 0]} to={[s.r * 2.6, 3.3, -1.9]} r={0.18} />
      <Run G={G} M={M} from={[s.r * 2.6, 4.2, -1.9]} to={[s.r * 2.6, 5.7, 1.9]} r={0.18} />
      <Run G={G} M={M} from={[s.r * 2.6 + 3.1, 6.6, 1.9]} to={[s.r * 2.6 + 3.1, s.h + 1.2, 1.9]} r={0.2} />
      <Platform G={G} M={M} y={1.9} w={6.4} d={1.6} x={s.r * 2.4} z={-2.7} />
    </>
  );
}

/* -------------------------------------------------------- 03 · REACTORS --- */
/**
 * Neutralization. Three agitated reactors in series on a common platform — the
 * arrangement the site's mimic shows, with the acid and ammonia feeds entering
 * the first and the solution overflowing stage to stage. A train of three
 * cannot be confused with a single tank, which is the whole point: this is the
 * reaction that makes the salt.
 */
function Reactors({ s, G, M, shell }) {
  const r = s.r * 0.78;
  const h = s.h;
  const xs = [-r * 2.5, 0, r * 2.5];
  return (
    <>
      <Platform G={G} M={M} y={h - 0.9} w={r * 6.8} d={1.5} z={-r * 1.9} />
      {xs.map((x, k) => (
        <group key={x} position={[x, 0, 0]}>
          <mesh geometry={G.cyl} material={M.struct} scale={[r * 1.06, 0.8, r * 1.06]} position={[0, 0.4, 0]} />
          <mesh geometry={G.cyl} material={shell} castShadow receiveShadow
            scale={[r, h - 0.8, r]} position={[0, 0.8 + (h - 0.8) / 2, 0]} />
          <mesh geometry={G.dome} material={shell} rotation={[Math.PI, 0, 0]}
            scale={[r, r * 0.42, r]} position={[0, 0.8, 0]} />
          <mesh geometry={G.cyl} material={M.steel}
            scale={[r * 1.05, 0.14, r * 1.05]} position={[0, h - 0.1, 0]} />
          <Agitator G={G} M={M} y={h} r={r} scale={0.92} />
          {/* the overflow to the next reactor in the train */}
          {k < 2 && (
            <Run G={G} M={M} from={[r * 0.9, h - 1.0, 0]} to={[r * 2.5 - r * 0.9, h - 1.4, 0]} r={0.17} />
          )}
          {k === 0 && (
            <>
              <Nozzle G={G} M={M} position={[-r * 0.55, h + 0.1, r * 0.45]} len={0.8} r={0.18} />
              <Nozzle G={G} M={M} position={[-r * 0.9, h - 1.6, 0]} rotation={[0, 0, Math.PI / 2]} len={0.9} />
            </>
          )}
          {k === 2 && (
            <Nozzle G={G} M={M} position={[r * 0.9, 1.5, 0]} rotation={[0, 0, -Math.PI / 2]} len={0.9} />
          )}
          {/* the gas offtake that goes to the acid wash */}
          {k === 1 && (
            <Run G={G} M={M} from={[r * 0.66, h - 0.1, -r * 0.4]} to={[r * 0.66, h + 4.8, -r * 0.4]} r={0.19} />
          )}
        </group>
      ))}
    </>
  );
}

/* -------------------------------------------------------- 04 · TANKFARM --- */
/**
 * Buffer / stabilization. "Reservoirs tampons": a row of flat-roofed agitated
 * tanks sharing an access platform and a header. Four tanks in a line is the
 * silhouette, and the repetition is the point — this is the stage that
 * deliberately mixes and delays every disturbance before it reaches the dryer.
 */
function TankFarm({ s, G, M, shell }) {
  const r = s.r * 0.72;
  const h = s.h;
  const xs = [-r * 3.6, -r * 1.2, r * 1.2, r * 3.6];
  return (
    <>
      <Platform G={G} M={M} y={h - 0.8} w={r * 9.0} d={1.4} z={-r * 1.8} />
      {/* the header that ties the row together */}
      <Run G={G} M={M} from={[-r * 4.6, h + 2.0, -r * 1.0]} to={[r * 4.6, h + 2.0, -r * 1.0]} r={0.2} />
      {xs.map((x, k) => (
        <group key={x} position={[x, 0, 0]}>
          <mesh geometry={G.cyl} material={M.struct} scale={[r * 1.05, 0.7, r * 1.05]} position={[0, 0.35, 0]} />
          <mesh geometry={G.cyl} material={shell} castShadow receiveShadow
            scale={[r, h - 0.7, r]} position={[0, 0.7 + (h - 0.7) / 2, 0]} />
          {/* flat roof with a kerb — NOT a dome */}
          <mesh geometry={G.cyl} material={M.steel}
            scale={[r * 1.06, 0.18, r * 1.06]} position={[0, h + 0.03, 0]} />
          <mesh geometry={G.cyl} material={M.steel}
            scale={[r * 0.55, 0.2, r * 0.55]} position={[r * 0.42, h + 0.12, r * 0.3]} />
          <Agitator G={G} M={M} y={h} r={r} scale={0.78} />
          <Run G={G} M={M} from={[0, h + 1.9, 0]} to={[0, h + 2.1, -r * 1.1]} r={0.14} />
          {k === 0 && <Nozzle G={G} M={M} position={[-r * 0.92, h * 0.78, 0]} rotation={[0, 0, Math.PI / 2]} len={0.9} />}
          {k === 3 && <Nozzle G={G} M={M} position={[r * 0.92, h * 0.30, 0]} rotation={[0, 0, -Math.PI / 2]} len={0.9} />}
        </group>
      ))}
    </>
  );
}

/* ---------------------------------------------------- 05 · CRYSTALLISER --- */
/**
 * Concentration & crystallization. The body sits over a conical draw-off, and
 * the identifying feature is the EXTERNAL FORCED-CIRCULATION LOOP: liquor
 * leaves the cone, runs down to a circulation pump, through a heat exchanger
 * and back up into the body. A slender vapour condenser stands alongside,
 * fed from the top head. That loop is what makes this read as an evaporative
 * crystalliser rather than as a tall tank.
 */
function Crystalliser({ s, G, M, shell }) {
  const r = s.r;
  const bodyH = s.h * 0.54;
  const coneH = s.h * 0.30;
  const y0 = 2.2;
  const zb = r * 1.15; // how far behind the body the service equipment sits
  return (
    <>
      {/* legs */}
      {[0, 1, 2, 3].map((k) => {
        const a = (k / 4) * Math.PI * 2 + Math.PI / 4;
        return (
          <mesh key={k} geometry={G.box} material={M.struct} scale={[0.3, y0 + coneH * 0.6, 0.3]}
            position={[Math.cos(a) * r * 0.92, (y0 + coneH * 0.6) / 2, Math.sin(a) * r * 0.92]} />
        );
      })}
      <mesh geometry={G.cone} material={shell} rotation={[Math.PI, 0, 0]} castShadow
        scale={[r, coneH, r]} position={[0, y0 + coneH / 2, 0]} />
      <mesh geometry={G.cyl} material={shell} castShadow receiveShadow
        scale={[r, bodyH, r]} position={[0, y0 + coneH + bodyH / 2, 0]} />
      <mesh geometry={G.dome} material={shell} castShadow
        scale={[r, r * 0.55, r]} position={[0, y0 + coneH + bodyH, 0]} />
      {[0.3, 0.68].map((f) => (
        <mesh key={f} geometry={G.cyl} material={M.steel}
          scale={[r * 1.03, 0.14, r * 1.03]} position={[0, y0 + coneH + bodyH * f, 0]} />
      ))}

      {/* forced-circulation loop, routed behind the body */}
      <Run G={G} M={M} from={[0, y0 + 0.1, 0]} to={[0, 1.2, -zb]} r={0.34} />
      <Run G={G} M={M} from={[0, 1.2, -zb]} to={[-r * 1.7, 1.2, -zb]} r={0.34} />
      <mesh geometry={G.box} material={M.machine} scale={[1.4, 0.85, 1.1]} position={[-r * 1.7, 0.78, -zb]} />
      <mesh geometry={G.cyl14} material={M.machine} rotation={[0, 0, Math.PI / 2]}
        scale={[0.4, 1.4, 0.4]} position={[-r * 1.7 - 1.1, 1.05, -zb]} />
      <Run G={G} M={M} from={[-r * 1.7, 1.4, -zb]} to={[-r * 1.7, 5.4, -zb]} r={0.32} />
      {/* the exchanger the loop runs through */}
      <mesh geometry={G.cyl} material={shell} castShadow
        scale={[0.68, 3.8, 0.68]} position={[-r * 1.7, 7.3, -zb]} />
      <mesh geometry={G.dome} material={M.steel} scale={[0.68, 0.38, 0.68]} position={[-r * 1.7, 9.2, -zb]} />
      <Run G={G} M={M} from={[-r * 1.7, 9.2, -zb]} to={[-r * 0.5, y0 + coneH + bodyH * 0.66, -zb * 0.4]} r={0.28} />

      {/* vapour line to the condenser, also behind */}
      <Run G={G} M={M} from={[r * 0.4, y0 + coneH + bodyH + r * 0.3, 0]} to={[r * 0.4, s.h + 2.4, -zb * 0.25]} r={0.3} />
      <Run G={G} M={M} from={[r * 0.4, s.h + 2.4, -zb * 0.25]} to={[r * 2.1, s.h + 2.4, -zb]} r={0.3} />
      <mesh geometry={G.cyl} material={shell} castShadow
        scale={[0.72, 4.2, 0.72]} position={[r * 2.1, s.h - 0.2, -zb]} />
      <mesh geometry={G.dome} material={M.steel} scale={[0.72, 0.4, 0.72]} position={[r * 2.1, s.h + 1.9, -zb]} />
      <mesh geometry={G.dome} material={M.steel} rotation={[Math.PI, 0, 0]}
        scale={[0.72, 0.4, 0.72]} position={[r * 2.1, s.h - 2.3, -zb]} />
      {[-0.8, 0.8].map((k) => (
        <mesh key={k} geometry={G.box} material={M.struct} scale={[0.2, s.h - 2.3, 0.2]}
          position={[r * 2.1 + k, (s.h - 2.3) / 2, -zb + k * 0.5]} />
      ))}
      <Platform G={G} M={M} y={y0 + coneH + bodyH * 0.5} w={r * 2.2} d={1.4} z={-r * 1.5} />
    </>
  );
}

/* ---------------------------------------------------- 06 · CENTRIFUGES --- */
/**
 * Centrifugation. Two parallel horizontal machines on a common skid, each fed
 * from a hopper above, each discharging solids down a chute and mother liquor
 * out to the recycle. Two identical machines side by side is exactly what the
 * site's "Essorage" mimic shows, and a horizontal machine on a skid can never
 * be mistaken for a tank.
 */
function Centrifuges({ s, G, M, shell }) {
  const machine = (dz) => (
    <group position={[0, 0, dz]}>
      {/* skid */}
      <mesh geometry={G.box} material={M.struct} scale={[6.2, 0.42, 2.3]} position={[0, 1.0, 0]} />
      {[-2.6, 2.6].map((x) => (
        <mesh key={x} geometry={G.box} material={M.struct} scale={[0.34, 1.0, 1.9]} position={[x, 0.5, 0]} />
      ))}
      {/* stepped casing: big basket section, small drive section */}
      <mesh geometry={G.cyl} material={shell} castShadow receiveShadow
        rotation={[0, 0, Math.PI / 2]} scale={[1.34, 3.0, 1.34]} position={[0.5, 2.6, 0]} />
      <mesh geometry={G.cyl} material={M.steel} rotation={[0, 0, Math.PI / 2]}
        scale={[1.42, 0.16, 1.42]} position={[-1.0, 2.6, 0]} />
      <mesh geometry={G.cyl} material={shell} rotation={[0, 0, Math.PI / 2]}
        scale={[0.86, 1.5, 0.86]} position={[-1.85, 2.6, 0]} />
      {/* drive end: motor and belt guard */}
      <mesh geometry={G.box} material={M.machine} scale={[1.5, 1.2, 1.1]} position={[-2.55, 1.95, 0]} />
      <mesh geometry={G.cyl14} material={M.machine} rotation={[0, 0, Math.PI / 2]}
        scale={[0.62, 1.4, 0.62]} position={[-2.55, 2.9, 0.5]} />
      {/* casing lid, hinged */}
      <mesh geometry={G.box} material={M.steel} scale={[3.0, 0.1, 1.5]} position={[0.5, 3.98, 0]} />
      {/* feed hopper above */}
      <mesh geometry={G.cone} material={M.steel} rotation={[Math.PI, 0, 0]}
        scale={[1.15, 1.5, 1.15]} position={[0.5, 5.3, 0]} />
      <mesh geometry={G.cyl} material={M.steel} scale={[1.15, 0.7, 1.15]} position={[0.5, 6.35, 0]} />
      <Run G={G} M={M} from={[0.5, 4.55, 0]} to={[0.5, 4.0, 0]} r={0.26} />
      {/* solids chute down to the dryer feed */}
      <mesh geometry={G.box} material={M.steel} rotation={[0, 0, 0.26]}
        scale={[1.0, 2.0, 1.3]} position={[1.9, 1.5, 0]} />
      {/* mother-liquor outlet */}
      <Nozzle G={G} M={M} position={[0.5, 2.6, -1.34]} rotation={[Math.PI / 2, 0, 0]} len={0.7} r={0.2} />
    </group>
  );
  return (
    <>
      {machine(-2.0)}
      {machine(2.0)}
      <Platform G={G} M={M} y={1.35} w={1.7} d={4.0} x={-4.2} z={-0.4} />
      <Run G={G} M={M} from={[0.5, 6.8, -2.0]} to={[0.5, 7.6, 0]} r={0.26} />
      <Run G={G} M={M} from={[0.5, 6.8, 2.0]} to={[0.5, 7.6, 0]} r={0.26} />
      <Run G={G} M={M} from={[0.5, 7.6, 0]} to={[-s.r * 2.6, 8.4, 0]} r={0.28} />
    </>
  );
}
