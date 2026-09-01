import { useEffect, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { useShow } from '../state/useShow.js';

/**
 * Ground-truth ambient occlusion.
 *
 * Everything in this film is welded, bolted, seated or stood on something else,
 * and until this pass existed none of that contact was visible: a skirt met a
 * plinth with no darkening, a nozzle entered a shell with no seat, a trunnion
 * touched a riding ring at exactly the same brightness as the air beside it.
 * The geometry was right and it still read as primitives, because contact —
 * not silhouette — is what the eye uses to decide that a thing has weight.
 *
 * GTAO rather than SSAO, and three's own implementation rather than a package:
 * the show must build and run with no network, and `three/examples/jsm` is
 * already in the bundle. SSAOPass in the same folder is cheaper but produces
 * the halo-and-hard-edge look this project would be embarrassed by; N8AO is
 * better again but is an external dependency for a gain nobody in the room
 * would name.
 *
 * Three things make it read as physical rather than as a video-game effect:
 *
 * 1. WORLD-SPACE radius. AO is a property of the geometry, so it shrinks with
 *    distance exactly as a real contact shadow does. From the scene-03 travel
 *    pose the chain is 100 units away and the AO correctly disappears.
 * 2. A WHITELISTED g-buffer. Only opaque physical surfaces contribute — see
 *    `contributesAO`. Text, traces, packets, evidence panels and the Power BI
 *    plane are graphics, not objects; letting them write depth and normals
 *    would have put occlusion under a chart axis.
 * 3. `blendIntensity` well under 1. The effect is a seat and a crevice, not a
 *    black outline. At 0.82 the darkest contact in the film sits around 0.5 of
 *    its unoccluded value, which survives a projector's black point.
 *
 * The pass also moves tone mapping from the material to `OutputPass`, because
 * a composer renders into a linear HDR target and three deliberately skips
 * in-material tone mapping there. AO therefore multiplies LINEAR light, before
 * ACES, which is where occlusion physically belongs.
 */

/** AO g-buffer scale. AO is low-frequency; a full-res normal pass is waste. */
const AO_SCALE = 0.55;

const AO = {
  radius: 1.45,          // world units — a flange seat, not a room
  distanceExponent: 1.0,
  thickness: 1.1,
  scale: 1.0,
  samples: 16,
  screenSpaceRadius: false,
};

/** Denoise: wide enough to kill the sample noise, tight enough to keep seats. */
const PD = { lumaPhi: 8, depthPhi: 2.2, normalPhi: 4, radius: 6, samples: 12 };

const BLEND_INTENSITY = 0.82;

/**
 * Does this object describe a physical surface?
 *
 * A whitelist, not a blacklist, and deliberately so: every graphic element in
 * this show is a Basic material, a troika text mesh, a Line or a Points cloud,
 * and every physical one is a Standard material. New graphics therefore stay
 * out of the g-buffer by default rather than by remembering to opt out.
 */
function contributesAO(o) {
  if (o.userData?.noAO === true) return false;
  if (o.isMesh !== true) return false;
  const m = o.material;
  if (!m) return false;
  const list = Array.isArray(m) ? m : [m];
  return list.some((mm) => (
    (mm.isMeshStandardMaterial === true || mm.isMeshPhysicalMaterial === true)
    && mm.wireframe !== true
    // A layer that has receded to 8 % is atmosphere. Letting it write a solid
    // depth would carve occlusion out of the scene that replaced it.
    && (mm.transparent !== true || mm.opacity >= 0.55)
  ));
}

export default function Post() {
  const { gl, scene, camera, size, viewport } = useThree();
  // Every buffer this component owns is a render target, so all of them come
  // back from a context loss empty. Rebuild rather than reuse.
  const epoch = useShow((s) => s.renderEpoch);

  /**
   * When the pass must not run.
   *
   * `?ao=off` is the manual switch. The interesting case is the automatic one:
   * a SOFTWARE renderer. The QA harness rasterises through SwiftShader, where
   * an extra full-scene geometry pass plus a horizon-scan costs whole SECONDS
   * per frame — slow enough that GSAP's ticker stops advancing between key
   * presses, so the DOM copy never finishes its swap and every captured still
   * came back with no headline on it. The same is true of a presentation
   * laptop that has fallen back to software GL, where post-processing is the
   * first thing that should go rather than the last.
   *
   * `?ao=force` overrides the detection, for deliberately capturing the pass.
   */
  const disabled = useMemo(() => {
    if (typeof window === 'undefined') return true;
    const want = new URLSearchParams(window.location.search).get('ao');
    if (want === 'off') return true;
    if (want === 'force') return false;
    let renderer = '';
    try {
      const ctx = gl.getContext();
      const dbg = ctx.getExtension('WEBGL_debug_renderer_info');
      renderer = String(dbg ? ctx.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : '');
    } catch {
      renderer = '';
    }
    return /swiftshader|llvmpipe|softpipe|software|basic render|microsoft basic/i.test(renderer);
  }, [gl]);

  const rig = useMemo(() => {
    if (disabled) return null;

    // MSAA has to be asked for explicitly once rendering goes through a target;
    // the canvas's own `antialias: true` stops applying the moment the default
    // framebuffer is no longer what the scene is drawn into.
    const target = new THREE.WebGLRenderTarget(1, 1, {
      type: THREE.HalfFloatType,
      samples: 4,
    });
    target.texture.name = 'Post.rt';

    const composer = new EffectComposer(gl, target);
    composer.addPass(new RenderPass(scene, camera));

    const gtao = new GTAOPass(scene, camera, 1, 1, undefined, AO, PD);
    gtao.blendIntensity = BLEND_INTENSITY;
    // Whitelist the g-buffer. GTAOPass only excludes points and lines; this
    // replaces that rule with "physical surfaces only".
    gtao.__hidden = [];
    gtao._overrideVisibility = function overrideVisibility() {
      const cache = this.__hidden;
      this.scene.traverse((o) => {
        if (o.visible !== true) return;
        if (o.isMesh || o.isPoints || o.isLine || o.isLine2 || o.isSprite) {
          if (!contributesAO(o)) { o.visible = false; cache.push(o); }
        }
      });
    };
    gtao._restoreVisibility = function restoreVisibility() {
      const cache = this.__hidden;
      for (let i = 0; i < cache.length; i += 1) cache[i].visible = true;
      cache.length = 0;
    };
    composer.addPass(gtao);

    composer.addPass(new OutputPass());

    return { composer, gtao, target };
  }, [gl, scene, camera, disabled, epoch]);

  // --- sizing ---------------------------------------------------------------
  useEffect(() => {
    if (!rig) return;
    const dpr = viewport.dpr || 1;
    rig.composer.setPixelRatio(dpr);
    rig.composer.setSize(size.width, size.height);
    // AFTER the composer, which resets every pass to full resolution.
    rig.gtao.setSize(
      Math.max(2, Math.round(size.width * dpr * AO_SCALE)),
      Math.max(2, Math.round(size.height * dpr * AO_SCALE))
    );
  }, [rig, size.width, size.height, viewport.dpr]);

  // --- teardown -------------------------------------------------------------
  useEffect(() => () => {
    if (!rig) return;
    for (const pass of rig.composer.passes) pass.dispose?.();
    rig.composer.renderTarget1.dispose();
    rig.composer.renderTarget2.dispose();
  }, [rig]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    // `epoch` is part of the diagnostic because the composer's render targets
    // do not survive a context loss either — scripts/qa-restore.mjs asserts
    // that this rig was REBUILT rather than merely still being present.
    window.__AO__ = rig
      ? { on: true, radius: AO.radius, intensity: BLEND_INTENSITY, epoch }
      : { on: false, epoch };
  }, [rig, epoch]);

  // Priority 1 takes the render away from r3f. Unmounting this component (safe
  // mode, or `?ao=off`) hands it straight back.
  useFrame(() => {
    if (!rig) { gl.render(scene, camera); return; }
    rig.composer.render();
  }, 1);

  return null;
}
