import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { C, MODES } from '../lib/palette.js';
import { DRYER } from '../lib/curves.js';
import { useChannel } from './usePresence.js';
import { useShow } from '../state/useShow.js';
import { budget } from '../lib/perf.js';

/**
 * Premium industrial-product cinematography, not sci-fi.
 *
 * Four lights do all the work: one key that casts the only shadow, one cool rim
 * that separates the dryer shell from the dark air (the single most important
 * light in the film), a hemisphere fill so shadows stay readable, and one warm
 * point inside the discharge hood that varies slightly — the only "alive" light,
 * and the reason the machine reads as running rather than parked.
 *
 * Mode changes are exposure changes on the same world, never cuts. The channels
 * below are tweened by the Rig on the same timeline as the camera.
 */

export default function Lighting() {
  const { gl, scene } = useThree();
  const key = useRef();
  const rim = useRef();
  const hemi = useRef();
  const warm = useRef();
  const safeMode = useShow((s) => s.safeMode);
  const b = budget(safeMode);

  const ambientCh = useChannel('lightAmbient', MODES.dark.ambient);
  const keyCh = useChannel('lightKey', MODES.dark.key);
  const rimCh = useChannel('lightRim', MODES.dark.rim);
  const exposureCh = useChannel('exposure', MODES.dark.exposure);
  const fogDensityCh = useChannel('fogDensity', MODES.dark.fogDensity);
  const fogMixCh = useChannel('fogMix', 0); // 0 = dark fog colour, 1 = cream

  const fog = useMemo(() => new THREE.FogExp2(C.inkDeep, MODES.dark.fogDensity), []);
  const darkFog = useMemo(() => new THREE.Color(C.inkDeep), []);
  const lightFog = useMemo(() => new THREE.Color(C.cream), []);
  const bgColor = useMemo(() => new THREE.Color(C.inkVoid), []);
  const darkBg = useMemo(() => new THREE.Color(C.inkVoid), []);
  const lightBg = useMemo(() => new THREE.Color(C.cream), []);

  useEffect(() => {
    scene.fog = fog;
    scene.background = bgColor;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.shadowMap.enabled = b.shadows;
    gl.shadowMap.type = THREE.PCFSoftShadowMap;
    return () => { scene.fog = null; };
  }, [scene, gl, fog, bgColor, b.shadows]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;

    if (hemi.current) hemi.current.intensity = ambientCh.current;
    if (key.current) key.current.intensity = keyCh.current;
    if (rim.current) rim.current.intensity = rimCh.current;
    if (warm.current) {
      // ±8 % on a slow sine. This is the plant breathing.
      warm.current.intensity = 2.6 * (1 + Math.sin(t * 0.55) * 0.08);
    }

    gl.toneMappingExposure = exposureCh.current;

    const mix = fogMixCh.current;
    fog.density = fogDensityCh.current;
    fog.color.copy(darkFog).lerp(lightFog, mix);
    bgColor.copy(darkBg).lerp(lightBg, mix);
  });

  return (
    <>
      <hemisphereLight
        ref={hemi}
        args={['#22392F', '#0C1A15', MODES.dark.ambient]}
      />

      {/* key — the only shadow caster, frustum fitted to the dryer */}
      <directionalLight
        ref={key}
        color={C.keyLight}
        intensity={MODES.dark.key}
        position={[-30, 34, 16]}
        castShadow={b.shadows}
        shadow-mapSize-width={b.shadowMap}
        shadow-mapSize-height={b.shadowMap}
        shadow-camera-near={1}
        shadow-camera-far={90}
        shadow-camera-left={-20}
        shadow-camera-right={20}
        shadow-camera-top={16}
        shadow-camera-bottom={-10}
        shadow-bias={-0.0007}
        shadow-normalBias={0.03}
      />

      {/* rim — separates the shell from the dark air */}
      <directionalLight
        ref={rim}
        color={C.rimLight}
        intensity={MODES.dark.rim}
        position={[28, 14, -30]}
      />

      {/* process warmth inside the discharge hood */}
      <pointLight
        ref={warm}
        color={C.processWarm}
        intensity={2.6}
        distance={26}
        decay={2}
        position={[DRYER.length / 2 + 2.4, DRYER.y - 1.0, 0]}
      />

      {/* a second, weaker warmth at the feed end so the drum reads end-to-end */}
      <pointLight
        color={C.processWarm}
        intensity={0.9}
        distance={18}
        decay={2}
        position={[-DRYER.length / 2 - 1.5, DRYER.y + 1.2, 0]}
      />
    </>
  );
}
