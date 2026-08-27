import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { gsap } from 'gsap';
import { createWorld } from './world.js';
import { scenes } from './scenes.js';
import './style.css';

const params = new URLSearchParams(location.search);
const captureMode = params.get('capture') === '1' || params.has('shot');
const filmMode = params.get('film') === '1';
const requestedScene = Number(params.get('shot') || params.get('scene') || 1) - 1;
const pace = Math.min(2, Math.max(0.35, Number(params.get('pace') || 1)));
let safeMode = params.get('safe') === '1';
let sceneIndex = Math.max(0, Math.min(scenes.length - 1, Number.isFinite(requestedScene) ? requestedScene : 0));
let presenterMode = false;
let transition = null;
let holdTween = null;
let autoplay = !captureMode && params.get('auto') !== '0';
let transitionActive = false;
let holdProgress = 0;
let completed = false;

const reducedQuery = matchMedia('(prefers-reduced-motion: reduce)');
let reducedMotion = reducedQuery.matches;
reducedQuery.addEventListener('change', (event) => {
  reducedMotion = event.matches;
  document.body.classList.toggle('reduced-motion', reducedMotion);
});

const mount = document.querySelector('#world');
const renderer = new THREE.WebGLRenderer({
  antialias: !safeMode,
  alpha: false,
  powerPreference: safeMode ? 'low-power' : 'high-performance'
});
renderer.setPixelRatio(Math.min(devicePixelRatio, safeMode ? 1 : 1.6));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.02;
renderer.shadowMap.enabled = !safeMode;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.domElement.setAttribute('role', 'img');
renderer.domElement.setAttribute('aria-label', 'A continuous three-dimensional journey from the soluble MAP process and rotary dryer through digital-twin, AI, validation, and operator-supervision layers.');
mount.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x050b09);
scene.fog = new THREE.FogExp2(0x07110e, 0.018);

const camera = new THREE.PerspectiveCamera(43, innerWidth / innerHeight, 0.08, 220);
const cameraBase = new THREE.Vector3();
const targetBase = new THREE.Vector3();
let cameraRoll = 0;

const ambient = new THREE.HemisphereLight(0xcfe5d8, 0x030806, safeMode ? 1.2 : 1.55);
scene.add(ambient);
const key = new THREE.DirectionalLight(0xf3f6ef, safeMode ? 2.25 : 3.0);
key.position.set(-11, 23, 15);
key.castShadow = !safeMode;
key.shadow.mapSize.set(safeMode ? 512 : 1024, safeMode ? 512 : 1024);
key.shadow.camera.left = -38;
key.shadow.camera.right = 38;
key.shadow.camera.top = 28;
key.shadow.camera.bottom = -20;
scene.add(key);
const greenLight = new THREE.PointLight(0x55e293, 28, 34, 1.8);
greenLight.position.set(6.5, 7.2, 3.2);
scene.add(greenLight);
const warmLight = new THREE.PointLight(0xf2a33a, 15, 30, 1.9);
warmLight.position.set(8, 4.5, 1.5);
scene.add(warmLight);
const blueLight = new THREE.PointLight(0x4fc7d7, 8, 36, 1.9);
blueLight.position.set(3, 5, -30);
scene.add(blueLight);

const world = createWorld(scene, safeMode);
const clock = new THREE.Clock();

let composer = null;
let bloomPass = null;
let bokehPass = null;
if (!safeMode) {
  try {
    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    bokehPass = new BokehPass(scene, camera, {
      focus: 22,
      aperture: 0.000035,
      maxblur: 0.0035,
      width: innerWidth,
      height: innerHeight
    });
    composer.addPass(bokehPass);
    bloomPass = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.36, 0.55, 0.72);
    composer.addPass(bloomPass);
  } catch (error) {
    composer = null;
    bloomPass = null;
    bokehPass = null;
    console.warn('Post-processing disabled:', error);
  }
}

const ui = {
  copy: document.querySelector('#copy'),
  eyebrow: document.querySelector('#eyebrow'),
  title: document.querySelector('#title'),
  subtitle: document.querySelector('#subtitle'),
  detail: document.querySelector('#detail'),
  labels: document.querySelector('#scene-labels'),
  number: document.querySelector('#scene-number'),
  progress: document.querySelector('#progress'),
  mode: document.querySelector('#mode-label'),
  play: document.querySelector('#play-pause'),
  controls: document.querySelector('#controls'),
  presenter: document.querySelector('#presenter'),
  presenterNext: document.querySelector('#presenter-next'),
  presenterCue: document.querySelector('#presenter-cue'),
  travel: document.querySelector('#travel-sheen'),
  fallback: document.querySelector('#fallback')
};

function modeText() {
  if (captureMode) return `CAPTURE / ${safeMode ? 'SAFE' : 'STANDARD'}`;
  if (completed) return 'TOUR COMPLETE';
  return `${autoplay ? 'AUTO TOUR' : 'PAUSED'} / ${safeMode ? 'SAFE' : 'CINEMATIC'}`;
}

function updateMode() {
  ui.mode.textContent = modeText();
  ui.play.textContent = autoplay ? 'II' : '▶';
  ui.play.setAttribute('aria-label', autoplay ? 'Pause cinematic tour' : 'Play cinematic tour');
  document.body.classList.toggle('is-paused', !autoplay);
}

function updateProgress() {
  const sceneFraction = transitionActive ? 0 : holdProgress;
  const progress = Math.min(1, Math.max(0, (sceneIndex + sceneFraction) / scenes.length));
  ui.progress.style.transform = `scaleX(${progress})`;
}

function setLabelMarkup(labels = []) {
  ui.labels.innerHTML = labels.map((label, index) => (
    `<span style="--x:${label.x}%;--y:${label.y}%;--delay:${index * 55}ms">${label.text}</span>`
  )).join('');
}

function updateUI(state, immediate = false) {
  const change = () => {
    document.body.dataset.scene = state.id;
    ui.copy.className = `copy ${state.align}`;
    ui.eyebrow.textContent = state.eyebrow;
    ui.title.innerHTML = state.title;
    ui.subtitle.textContent = state.subtitle;
    ui.detail.innerHTML = state.detail || '';
    setLabelMarkup(state.labels);
    ui.number.textContent = `${String(sceneIndex + 1).padStart(2, '0')} / ${String(scenes.length).padStart(2, '0')}`;
    const next = scenes[Math.min(sceneIndex + 1, scenes.length - 1)];
    ui.presenterNext.textContent = next.title.replace(/<[^>]+>/g, ' ');
    ui.presenterCue.textContent = state.cue;
    updateMode();
  };

  if (immediate || reducedMotion) {
    change();
    gsap.set([ui.copy, ui.labels], { opacity: 1, y: 0 });
    return;
  }

  gsap.timeline({ defaults: { overwrite: true } })
    .to([ui.copy, ui.labels], { opacity: 0, y: -9, duration: 0.32, ease: 'power2.out', stagger: 0.035 })
    .add(change)
    .fromTo(ui.eyebrow, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.62, ease: 'power4.out' })
    .fromTo(ui.title, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.82, ease: 'power4.out' }, '-=.46')
    .fromTo(ui.subtitle, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.72, ease: 'power4.out' }, '-=.58')
    .fromTo(ui.detail, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.68, ease: 'power4.out' }, '-=.52')
    .fromTo(ui.labels.children, { opacity: 0, scale: 0.94 }, { opacity: 1, scale: 1, duration: 0.62, stagger: 0.055, ease: 'power4.out' }, '-=.6');
}

function applyWorldState(state, immediate = false) {
  const duration = immediate || reducedMotion ? 0 : Math.min(2.4, state.transition * 0.72) * pace;
  for (const [channel, value] of Object.entries(state.world)) {
    for (const mat of world.channels[channel] || []) {
      const base = mat.userData.channelOpacity ?? 1;
      gsap.to(mat, {
        opacity: value * base,
        duration,
        ease: 'power3.inOut',
        overwrite: true,
        onStart: () => { mat.visible = true; },
        onUpdate: () => { mat.visible = mat.opacity > 0.0015; }
      });
    }
  }
}

function applyEnvironment(state, immediate = false) {
  const duration = immediate || reducedMotion ? 0 : Math.min(2.7, state.transition * 0.76) * pace;
  const background = new THREE.Color(state.environment.background);
  const fog = new THREE.Color(state.environment.fog);
  gsap.to(scene.background, { r: background.r, g: background.g, b: background.b, duration, ease: 'power3.inOut', overwrite: true });
  gsap.to(scene.fog.color, { r: fog.r, g: fog.g, b: fog.b, duration, ease: 'power3.inOut', overwrite: true });
  gsap.to(scene.fog, { density: state.environment.fogDensity, duration, ease: 'power3.inOut', overwrite: true });
  gsap.to(renderer, { toneMappingExposure: state.environment.exposure, duration, ease: 'power3.inOut', overwrite: true });
  gsap.to(key, { intensity: state.environment.key, duration, ease: 'power3.inOut', overwrite: true });
  gsap.to(greenLight, { intensity: state.environment.green, duration, ease: 'power3.inOut', overwrite: true });
  gsap.to(warmLight, { intensity: state.environment.warm, duration, ease: 'power3.inOut', overwrite: true });
  gsap.to(blueLight, { intensity: state.environment.blue, duration, ease: 'power3.inOut', overwrite: true });
  if (bloomPass) gsap.to(bloomPass, { strength: state.lens.bloom * 0.32, duration, ease: 'power3.inOut', overwrite: true });
  if (bokehPass?.uniforms?.focus) gsap.to(bokehPass.uniforms.focus, { value: state.lens.focus, duration, ease: 'power3.inOut', overwrite: true });
}

function makeTravelCurve(start, end, via = [0, 0, 0]) {
  const middle = start.clone().lerp(end, 0.5).add(new THREE.Vector3(...via));
  const early = start.clone().lerp(middle, 0.48);
  const late = middle.clone().lerp(end, 0.52);
  return new THREE.CatmullRomCurve3([start.clone(), early, middle, late, end.clone()], false, 'catmullrom', 0.38);
}

function clearHold() {
  if (holdTween) {
    holdTween.kill();
    holdTween = null;
  }
}

function scheduleHold() {
  clearHold();
  holdProgress = 0;
  updateProgress();
  if (!autoplay || captureMode) return;
  const duration = scenes[sceneIndex].hold * pace;
  const meter = { value: 0 };
  holdTween = gsap.to(meter, {
    value: 1,
    duration,
    ease: 'none',
    onUpdate: () => {
      holdProgress = meter.value;
      updateProgress();
    },
    onComplete: () => {
      holdTween = null;
      if (sceneIndex < scenes.length - 1) {
        gotoScene(sceneIndex + 1, { source: 'auto' });
      } else {
        holdProgress = 1;
        completed = true;
        autoplay = false;
        updateProgress();
        updateMode();
      }
    }
  });
}

function gotoScene(nextIndex, options = {}) {
  const immediate = options.immediate ?? false;
  const bounded = Math.max(0, Math.min(scenes.length - 1, nextIndex));
  if (bounded === sceneIndex && !immediate) return;

  clearHold();
  completed = false;
  sceneIndex = bounded;
  holdProgress = 0;
  const state = scenes[sceneIndex];

  if (transition) transition.kill();
  document.body.classList.toggle('is-capture', captureMode);
  document.body.classList.add('is-travelling');
  transitionActive = true;
  updateProgress();

  const duration = immediate || reducedMotion ? 0 : state.transition * pace;
  const endPosition = new THREE.Vector3(...state.camera.position);
  const endTarget = new THREE.Vector3(...state.camera.target);

  if (duration === 0) {
    cameraBase.copy(endPosition);
    targetBase.copy(endTarget);
    camera.fov = state.camera.fov;
    camera.updateProjectionMatrix();
    cameraRoll = state.camera.roll ?? 0;
    applyWorldState(state, true);
    applyEnvironment(state, true);
    updateUI(state, true);
    transitionActive = false;
    document.body.classList.remove('is-travelling');
    scheduleHold();
  } else {
    const positionCurve = makeTravelCurve(cameraBase, endPosition, state.camera.via);
    const targetCurve = makeTravelCurve(targetBase, endTarget, state.camera.via.map((value) => value * 0.12));
    const travel = { value: 0 };
    const startFov = camera.fov;
    const startRoll = cameraRoll;
    transition = gsap.timeline({
      defaults: { ease: 'power4.inOut', overwrite: true },
      onComplete: () => {
        cameraBase.copy(endPosition);
        targetBase.copy(endTarget);
        cameraRoll = state.camera.roll ?? 0;
        transitionActive = false;
        document.body.classList.remove('is-travelling');
        transition = null;
        scheduleHold();
      }
    });
    transition.to(travel, {
      value: 1,
      duration,
      onUpdate: () => {
        positionCurve.getPoint(travel.value, cameraBase);
        targetCurve.getPoint(travel.value, targetBase);
        const zoomPulse = Math.sin(Math.PI * travel.value) * Math.min(4.5, Math.abs(state.camera.fov - startFov) * 0.35 + 1.6);
        camera.fov = THREE.MathUtils.lerp(startFov, state.camera.fov, travel.value) + zoomPulse;
        cameraRoll = THREE.MathUtils.lerp(startRoll, state.camera.roll ?? 0, travel.value);
        camera.updateProjectionMatrix();
      }
    }, 0);
    transition.fromTo(ui.travel, { opacity: 0 }, { opacity: 0.78, duration: duration * 0.34, yoyo: true, repeat: 1, ease: 'sine.inOut' }, 0);
    applyWorldState(state, false);
    applyEnvironment(state, false);
    updateUI(state, false);
  }

  const query = new URLSearchParams();
  query.set('scene', String(sceneIndex + 1));
  if (!autoplay) query.set('auto', '0');
  if (captureMode) query.set('capture', '1');
  if (safeMode) query.set('safe', '1');
  if (pace !== 1) query.set('pace', String(pace));
  history.replaceState(null, '', `${location.pathname}?${query}`);
}

function setAutoplay(value) {
  autoplay = value;
  completed = false;
  updateMode();
  if (autoplay) {
    if (transition?.paused()) transition.resume();
    else if (holdTween?.paused()) holdTween.resume();
    else scheduleHold();
  } else {
    if (transition) transition.pause();
    if (holdTween) holdTween.pause();
  }
}

function manualAdvance(step) {
  setAutoplay(false);
  if (transition) {
    transition.kill();
    transition = null;
    transitionActive = false;
  }
  gotoScene(sceneIndex + step, { source: 'manual' });
}

document.querySelector('#previous').addEventListener('click', () => manualAdvance(-1));
document.querySelector('#next').addEventListener('click', () => manualAdvance(1));
ui.play.addEventListener('click', () => setAutoplay(!autoplay));

window.addEventListener('keydown', (event) => {
  if (event.key === ' ') {
    event.preventDefault();
    setAutoplay(!autoplay);
  }
  if (['ArrowRight', 'Enter', 'PageDown'].includes(event.key)) {
    event.preventDefault();
    manualAdvance(1);
  }
  if (['ArrowLeft', 'PageUp'].includes(event.key)) {
    event.preventDefault();
    manualAdvance(-1);
  }
  if (event.key === 'Home') { setAutoplay(false); gotoScene(0); }
  if (event.key === 'End') { setAutoplay(false); gotoScene(scenes.length - 1); }
  if (event.key.toLowerCase() === 'r') { autoplay = true; gotoScene(0); updateMode(); }
  if (event.key.toLowerCase() === 'p') {
    presenterMode = !presenterMode;
    ui.presenter.hidden = !presenterMode;
  }
  if (event.key.toLowerCase() === 's') {
    const query = new URLSearchParams(location.search);
    if (safeMode) query.delete('safe'); else query.set('safe', '1');
    location.search = query.toString();
  }
  if (event.key.toLowerCase() === 'f') {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  }
});

let touchStart = null;
window.addEventListener('pointerdown', (event) => { touchStart = { x: event.clientX, y: event.clientY }; });
window.addEventListener('pointerup', (event) => {
  if (!touchStart) return;
  const dx = event.clientX - touchStart.x;
  const dy = event.clientY - touchStart.y;
  if (Math.abs(dx) > 78 && Math.abs(dx) > Math.abs(dy)) manualAdvance(dx < 0 ? 1 : -1);
  touchStart = null;
});

let hideControlsTimer = null;
function revealControls() {
  document.body.classList.remove('controls-idle');
  clearTimeout(hideControlsTimer);
  hideControlsTimer = setTimeout(() => {
    if (!presenterMode && autoplay) document.body.classList.add('controls-idle');
  }, 2600);
}
window.addEventListener('pointermove', revealControls, { passive: true });
window.addEventListener('keydown', revealControls);

window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(devicePixelRatio, safeMode ? 1 : 1.6));
  renderer.setSize(innerWidth, innerHeight);
  if (composer) composer.setSize(innerWidth, innerHeight);
});

renderer.domElement.addEventListener('webglcontextlost', (event) => {
  event.preventDefault();
  if (captureMode) return;
  setAutoplay(false);
  document.body.classList.add('webgl-lost');
  ui.fallback.hidden = false;
});

renderer.domElement.addEventListener('webglcontextrestored', () => {
  document.body.classList.remove('webgl-lost');
  ui.fallback.hidden = true;
});

function frame() {
  const elapsed = clock.getElapsedTime();
  world.animate(elapsed, reducedMotion);

  const state = scenes[sceneIndex];
  const drift = state.camera.drift ?? [0, 0, 0];
  const driftFactor = reducedMotion || captureMode || transitionActive ? 0 : 1;
  camera.position.set(
    cameraBase.x + Math.sin(elapsed * 0.19) * drift[0] * driftFactor,
    cameraBase.y + Math.sin(elapsed * 0.23 + 1.3) * drift[1] * driftFactor,
    cameraBase.z + Math.cos(elapsed * 0.17) * drift[2] * driftFactor
  );
  const target = targetBase.clone();
  if (driftFactor) target.y += Math.sin(elapsed * 0.15) * 0.04;
  camera.lookAt(target);
  camera.rotateZ(cameraRoll);

  if (!reducedMotion) {
    const pulse = Math.sin(elapsed * 0.78) * 2.8;
    greenLight.intensity = Math.max(0, scenes[sceneIndex].environment.green + pulse);
  }

  if (composer) composer.render();
  else renderer.render(scene, camera);
  requestAnimationFrame(frame);
}

document.body.classList.toggle('is-capture', captureMode);
document.body.classList.toggle('is-film', filmMode);
document.body.classList.toggle('reduced-motion', reducedMotion);
gotoScene(sceneIndex, { immediate: true, source: 'boot' });
updateMode();
updateProgress();
revealControls();
frame();

window.__director = {
  scenes,
  gotoScene: (index) => gotoScene(index, { source: 'api' }),
  play: () => setAutoplay(true),
  pause: () => setAutoplay(false),
  getState: () => ({ sceneIndex, autoplay, completed, transitionActive, holdProgress }),
  stats: world.stats
};

Promise.all([
  world.ready,
  ...Array.from(document.images).map((img) => img.complete ? Promise.resolve() : img.decode().catch(() => undefined))
]).then(() => {
  setTimeout(() => {
    window.__PRESENTATION_READY__ = true;
    document.documentElement.dataset.ready = 'true';
  }, captureMode ? 900 : 180);
});
