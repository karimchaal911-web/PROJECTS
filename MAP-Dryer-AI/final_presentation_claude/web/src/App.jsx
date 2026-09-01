import { Component, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import * as THREE from 'three';
import World from './three/World.jsx';
import Overlay from './overlay/Overlay.jsx';
import { ProgressRail, BoundaryBadge, PresenterHud, HelpPanel } from './overlay/Chrome.jsx';
import { useShow } from './state/useShow.js';
import { SCENES, STEPS } from './state/scenes.js';
import { loadShowData } from './data/load.js';
import { budget, probeDevice, prefersReducedMotion } from './lib/perf.js';
import { C } from './lib/palette.js';

export default function App() {
  const [progress, setProgress] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [contextLost, setContextLost] = useState(false);
  const [gateGone, setGateGone] = useState(false);
  const safeMode = useShow((s) => s.safeMode);
  const setSafe = useShow((s) => s.setSafe);
  const started = useShow((s) => s.started);
  const begin = useShow((s) => s.begin);
  const contextRestored = useShow((s) => s.contextRestored);
  const b = budget(safeMode);

  // The QA harness reads this to record the mode a capture ACTUALLY ran in,
  // rather than the mode it asked for. Auto-degrade can change it mid-run.
  useEffect(() => { window.__SAFE__ = safeMode; }, [safeMode]);

  // Diagnostics: the step the presenter is on. scripts/qa-restore.mjs asserts
  // that a context loss does not move it.
  const stepNow = useShow((s) => s.step);
  useEffect(() => { window.__STEP__ = stepNow; }, [stepNow]);

  // Boot: probe the device, then load the six verified payloads.
  useEffect(() => {
    // Exposed for the capture/QA harness so it can walk the exact step table
    // rather than guessing how many presses the show takes.
    window.__STEPS__ = STEPS.length;
    const probe = probeDevice();
    if (probe.suggestSafe) setSafe(true);
    loadShowData(setProgress).then(() => setLoaded(true));
  }, [setSafe]);

  const goArmedNow = useKeyboard();

  return (
    <div className="app">
      <ErrorBoundary>
        <Canvas
          dpr={[1, b.dpr]}
          gl={{
            antialias: b.antialias,
            powerPreference: safeMode ? 'low-power' : 'high-performance',
            alpha: false,
            stencil: false,
          }}
          camera={{ position: [-34, 2.4, 26], fov: 38, near: 0.5, far: 620 }}
          shadows={b.shadows}
          onCreated={({ gl }) => {
            gl.setClearColor(new THREE.Color(C.inkVoid), 1);
            // Diagnostics only. The QA harness drives WEBGL_lose_context
            // through this to prove the recovery path, which is otherwise
            // impossible to test on demand.
            window.__GL__ = gl;
            const canvas = gl.domElement;
            canvas.addEventListener('webglcontextlost', (e) => {
              // Without preventDefault the browser never offers a restore at
              // all, and the film is over.
              e.preventDefault();
              setContextLost(true);
            });
            canvas.addEventListener('webglcontextrestored', () => {
              // three re-initialises the context on its own, but two things
              // it hands back are EMPTY rather than restored: the PMREM studio
              // environment and the post-processing buffers, because their
              // contents were rendered rather than uploaded. Bumping the epoch
              // rebuilds both and re-settles the world into the step the
              // presenter is currently on — see useShow.renderEpoch.
              contextRestored();
              // Hold the notice for a beat. Every shader program is recompiled
              // on first use after a restore, and that cost belongs behind the
              // panel rather than in front of the audience.
              setTimeout(() => setContextLost(false), 400);
            });
          }}
        >
          <World />
        </Canvas>
      </ErrorBoundary>

      <div className="vignette" aria-hidden />
      <Overlay />
      <ProgressRail />
      <BoundaryBadge />
      <PresenterHud />
      <HelpPanel />

      {!gateGone && <BootGate loaded={loaded} progress={progress} onStart={begin} leaving={started} onGone={() => setGateGone(true)} />}
      <FullscreenNotice />
      <TapZone />
      {goArmedNow && <div className="gohint mono">GO TO SCENE — 1-9, 0, or Q W X C</div>}
      {contextLost && (
        <div className="recover">
          <p>Graphics context lost. Restoring…</p>
          <p className="mono">The presentation will resume at the current scene.</p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------- boot gate --- */

function BootGate({ loaded, progress, onStart, leaving, onGone }) {
  const [warmed, setWarmed] = useState(false);

  useEffect(() => {
    if (!loaded) return undefined;
    // Hold the gate long enough for <Prewarm> to finish BOTH of its offscreen
    // warm passes. It needs twelve frames after the payloads land — one pass
    // for the geometry React has built, a second for troika's text, which is
    // generated on a worker and is not in the graph yet during the first.
    // Eight frames covered neither reliably, and the cost of getting it wrong
    // was a measured 1310 ms freeze on the scene-03 act change.
    let raf = 0;
    let n = 0;
    const tick = () => {
      n += 1;
      if (n >= 16) { setWarmed(true); return; }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [loaded]);

  // The gate used to be unmounted the instant `started` flipped, so the show
  // hard-cut from a black panel into the opening frame.
  useEffect(() => {
    if (!leaving) return undefined;
    const id = setTimeout(onGone, 850);
    return () => clearTimeout(id);
  }, [leaving, onGone]);

  const ready = loaded && warmed;

  return (
    <div className={`boot ${ready ? 'is-ready' : ''} ${leaving ? 'is-leaving' : ''}`}>
      <div
        className="boot__plate"
        aria-hidden
        style={{ backgroundImage: `url(${import.meta.env.BASE_URL}img/dryer_hero_plate.jpg)` }}
      />
      <div className="boot__inner">
        <p className="eyebrow">OCP · ENSAM — SOLUBLE MAP DIGITALIZATION</p>
        <h1>Intelligent digitalization<br />of soluble MAP production</h1>
        <p className="boot__meta mono">
          {ready
            ? `${SCENES.length} scenes · presenter-controlled · runs offline`
            : `loading verified project data — ${Math.round(progress * 100)} %`}
        </p>
        <button type="button" className="boot__start" onClick={onStart} disabled={!ready}>
          {ready ? 'Begin' : 'Preparing…'}
        </button>
        <p className="boot__hint mono">→ or Space advances · H for controls · F for fullscreen</p>
      </div>
    </div>
  );
}

/**
 * A quiet presenter-side reminder. Every size in the show is viewport-relative,
 * so a windowed run silently shrinks all of it — including the roadmap, which
 * is the one thing that must stay readable.
 */
function FullscreenNotice() {
  const started = useShow((s) => s.started);
  const [full, setFull] = useState(true);
  // The QA harness cannot enter fullscreen, so the notice was burned into
  // every exported still — chrome the audience never sees.
  const capture = useMemo(
    () => new URLSearchParams(window.location.search).has('capture'),
    []
  );
  useEffect(() => {
    const check = () => setFull(Boolean(document.fullscreenElement));
    check();
    document.addEventListener('fullscreenchange', check);
    return () => document.removeEventListener('fullscreenchange', check);
  }, []);
  if (!started || full || capture) return null;
  return <div className="fsnotice mono">NOT FULLSCREEN — press F</div>;
}

/* -------------------------------------------------------------- keyboard --- */

function useKeyboard() {
  const next = useShow((s) => s.next);
  const prev = useShow((s) => s.prev);
  const goScene = useShow((s) => s.goScene);
  const toggleSafe = useShow((s) => s.toggleSafe);
  const toggleHud = useShow((s) => s.toggleHud);
  const toggleHelp = useShow((s) => s.toggleHelp);
  const begin = useShow((s) => s.begin);
  const started = useShow((s) => s.started);
  const last = useRef(0);
  const goArmed = useRef(false);
  const [armed, setArmed] = useState(false);

  const advance = useCallback((fn) => {
    // Rapid presses queue at most one step ahead, so hammering the arrow key
    // cannot desynchronise the show.
    const now = performance.now();
    if (now - last.current < 120) return;
    last.current = now;
    fn();
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key;

      if (!started && (k === 'ArrowRight' || k === ' ' || k === 'Enter')) {
        e.preventDefault();
        begin();
        return;
      }

      // --- "go to scene": a G prefix, then a key ---------------------------
      // The old mapping was bare digits (so a mistyped key jumped the show
      // mid-sentence) plus Shift+!@#$ for scenes 11-14, which is a US-layout
      // assumption. On the AZERTY keyboards this will likely be presented on,
      // those characters are unshifted and the mapping broke entirely.
      if (goArmed.current) {
        goArmed.current = false;
        setArmed(false);
        const map = {
          1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 0: 9,
          q: 10, w: 11, x: 12, c: 13,
        };
        const targetScene = map[k.toLowerCase()];
        if (targetScene !== undefined) {
          e.preventDefault();
          goScene(targetScene);
        }
        return;
      }

      switch (k) {
        case 'ArrowRight': case ' ': case 'PageDown':
          e.preventDefault(); advance(next); break;
        case 'ArrowLeft': case 'PageUp':
          e.preventDefault(); advance(prev); break;
        case 'Home':
          e.preventDefault(); goScene(0); break;
        case 'End':
          e.preventDefault(); goScene(SCENES.length - 1); break;
        case 'g': case 'G':
          e.preventDefault();
          goArmed.current = true;
          setArmed(true);
          break;
        case 'Escape':
          goArmed.current = false; setArmed(false); break;
        case 'f': case 'F':
          toggleFullscreen(); break;
        case 'p': case 'P':
          toggleHud(); break;
        case 's': case 'S':
          toggleSafe(); break;
        case 'h': case 'H': case '?':
          toggleHelp(); break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [advance, next, prev, goScene, toggleSafe, toggleHud, toggleHelp, begin, started]);

  // Click-to-advance is deliberately NOT bound to the whole window any more.
  // A trackpad tap, a click to focus the window, or a click to dismiss a
  // notification all used to skip a beat with no undo but the left arrow.
  // Advancing is a keyboard action, or a click on the explicit tap zone.
  return armed;
}

/**
 * A narrow strip along the bottom of the frame that advances the show.
 * Deliberate to hit, impossible to hit by accident, invisible to the audience.
 */
function TapZone() {
  const next = useShow((s) => s.next);
  const started = useShow((s) => s.started);
  if (!started) return null;
  return (
    <button
      type="button"
      className="tapzone"
      aria-label="Next"
      onClick={() => next()}
    />
  );
}

function toggleFullscreen() {
  const el = document.documentElement;
  if (!document.fullscreenElement) el.requestFullscreen?.().catch(() => {});
  else document.exitFullscreen?.().catch(() => {});
}

/* -------------------------------------------------------- error boundary --- */

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    console.error('[world] render failed — falling back to static mode', error, info);
  }

  render() {
    if (this.state.failed) {
      // Degrade to a legible static ground rather than a blank screen. The
      // overlay copy, the rail and the keyboard all keep working.
      return <div className="fallback" role="img" aria-label="Static fallback" />;
    }
    return this.props.children;
  }
}

export { prefersReducedMotion };
