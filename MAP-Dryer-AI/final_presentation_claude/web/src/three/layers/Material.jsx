import { useMemo, useRef } from 'react';
import { useFrame, useLoader, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { C } from '../../lib/palette.js';
import { useChannel } from '../usePresence.js';
import { WMono } from '../WorldText.jsx';

/**
 * The product itself — photographed, not modelled.
 *
 * WHY THE PLATE IS THIS SIZE
 * --------------------------
 * The photograph is 1280 x 960: a phone frame taken in the storage hall. It
 * used to be drawn 25.5 world units wide at a camera distance of 18 on a 30 mm
 * lens, which is about 2 860 pixels across a 1920-wide frame. The browser was
 * therefore magnifying the source 2.2x with a bilinear filter, and that — not
 * the grade, not the crop, not a CSS filter — is the entire reason the scene
 * looked soft at presentation scale. There is no higher-resolution copy of this
 * photograph anywhere in the project; 1280 x 960 is the original.
 *
 * So the plate is now drawn at a size the source can actually carry. At the
 * closest beat it covers about 52 % of the frame width — roughly 1 000 screen
 * pixels from a 2048-pixel delivered file — which is a MINIFICATION at every
 * beat, on a projector and on a retina panel alike. The delivered file is a
 * measured Lanczos resample of the original with unsharp either side
 * (data_build/restore_plates.py); nothing in it is generated.
 *
 * The composition follows from that. The photograph is hung as an editorial
 * print against a wall wash, on the right of the frame, and the copy column
 * gets real negative space on the left instead of sitting on top of the
 * pallets. Which is also the better frame: the title no longer covers the
 * material it is naming.
 */

// x is offset +3.26 from the camera's own axis (x = -46), which is what puts
// the print on the right of the frame and leaves the left clear for type.
const POS = [-42.74, 9.8, 22];
const W = 9.41;
const H = 7.06; // 4:3, the source's true aspect

export default function Material() {
  const group = useRef();
  const presence = useChannel('material');
  const reveal = useChannel('materialReveal', 0);
  const plate = useRef();
  const { gl } = useThree();

  const tex = useLoader(
    THREE.TextureLoader,
    `${import.meta.env.BASE_URL}img/soluble_map_storage.jpg`
  );

  useMemo(() => {
    tex.colorSpace = THREE.SRGBColorSpace;
    // The plate is minified at every beat, so trilinear + full anisotropy is
    // doing real work here rather than being a default.
    tex.anisotropy = gl.capabilities.getMaxAnisotropy();
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    tex.magFilter = THREE.LinearFilter;
    tex.generateMipmaps = true;
    tex.needsUpdate = true;
  }, [tex, gl]);

  // fog:false — a photograph is not a surface in the room's atmosphere.
  const mat = useMemo(() => new THREE.MeshBasicMaterial({
    map: tex, transparent: true, opacity: 0, toneMapped: false, fog: false,
  }), [tex]);

  // A hairline edge so the print reads as an object with a boundary rather
  // than as an image pasted over the film.
  const edgeMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.dust, transparent: true, opacity: 0, fog: false,
  }), []);

  const matteMat = useMemo(() => new THREE.MeshBasicMaterial({
    color: C.inkVoid, transparent: true, opacity: 0, fog: false,
  }), []);

  /**
   * The wall the print hangs on. Without it the plate floated in pure black,
   * which is exactly the "image pasted over the film" the scene was trying to
   * avoid — the old full-bleed framing hid the problem by covering the frame.
   */
  const wallMat = useMemo(() => {
    const s = 256;
    const cv = document.createElement('canvas');
    cv.width = s; cv.height = s;
    const ctx = cv.getContext('2d');
    const g = ctx.createRadialGradient(s * 0.5, s * 0.46, 0, s * 0.5, s * 0.46, s * 0.56);
    g.addColorStop(0, '#16241E');
    g.addColorStop(0.5, '#0C1712');
    g.addColorStop(1, '#05100D');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, s, s);
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    return new THREE.MeshBasicMaterial({ map: t, transparent: true, opacity: 0, fog: false });
  }, []);

  useFrame(() => {
    const p = presence.current;
    if (group.current) {
      group.current.visible = p > 0.01;
      if (p <= 0.01) return;
    }
    const r = THREE.MathUtils.clamp(reveal.current, 0, 1);
    mat.opacity = p * r;
    matteMat.opacity = p * r * 0.92;
    edgeMat.opacity = p * r * 0.30;
    wallMat.opacity = p * r * 0.95;
    if (plate.current) {
      // A 1.5 % settle, nothing more. The photograph is the subject; it does
      // not need to perform.
      const s = 0.985 + r * 0.015;
      plate.current.scale.set(s, s, 1);
    }
  });

  return (
    <group ref={group}>
      {/* the wall wash, centred behind the print and reaching across the frame */}
      <mesh position={[POS[0] - 3.0, POS[1] - 0.6, POS[2] - 1.4]} material={wallMat}>
        <planeGeometry args={[52, 30]} />
      </mesh>

      <group position={POS}>
        <group ref={plate}>
          <mesh position={[0, 0, 0.004]} material={edgeMat}>
            <planeGeometry args={[W + 0.10, H + 0.10]} />
          </mesh>
          <mesh position={[0, 0, 0.002]} material={matteMat}>
            <planeGeometry args={[W + 0.06, H + 0.06]} />
          </mesh>
          <mesh position={[0, 0, 0.01]} material={mat}>
            <planeGeometry args={[W, H]} />
          </mesh>
        </group>
        <WMono
          position={[-W / 2, -H / 2 - 0.46, 0.1]}
          fontSize={0.15}
          color={C.dust}
          fillOpacity={0.66}
          letterSpacing={0.05}
        >
          SOLUBLE MAP IN STORAGE - PHOTOGRAPHED AT THE SITE
        </WMono>
      </group>
    </group>
  );
}
