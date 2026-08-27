import { Component, useCallback, useEffect, useRef, useState } from 'react';
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
  const safeMode = useShow((s) => s.safeMode);
  const setSafe = useShow((s) => s.setSafe);
  const started = useShow((s) => s.started);
  const begin = useShow((s) => s.begin);
  const b = budget(safeMode);

  // Boot: probe the device, then load the six verified payloads.
  useEffect(() => {
    // Exposed for the capture/QA harness so it can walk the exact step table
    // rather than guessing how many presses the show takes.
    window.__STEPS__ = STEPS.length;
    const probe = probeDevice();
    if (probe.suggestSafe) setSafe(true);
    loadShowData(setProgress).then(() => setLoaded(true));
  }, [setSafe]);

  useKeyboard();

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
            const canvas = gl.domElement;
            canvas.addEventListener('webglcontextlost', (e) => {
              e.preventDefault();
              setContextLost(true);
            });
            canvas.addEventListener('webglcontextrestored', () => setContextLost(false));
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

      {!started && <BootGate loaded={loaded} progress={progress} onStart={begin} />}
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

function BootGate({ loaded, progress, onStart }) {
  const [warmed, setWarmed] = useState(false);

  useEffect(() => {
    if (!loaded) return undefined;
    // Give the world two frames to compile shaders before we fade from black,
    // so no scene stutters the first time it is reached.
    const id = requestAnimationFrame(() =>
      requestAnimationFrame(() => setWarmed(true))
    );
    return () => cancelAnimationFrame(id);
  }, [loaded]);

  const ready = loaded && warmed;

  return (
    <div className={`boot ${ready ? 'is-ready' : ''}`}>
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

      switch (k) {
        case 'ArrowRight': case ' ': case 'PageDown':
          e.preventDefault(); advance(next); break;
        case 'ArrowLeft': case 'PageUp':
          e.preventDefault(); advance(prev); break;
        case 'f': case 'F':
          toggleFullscreen(); break;
        case 'p': case 'P':
          toggleHud(); break;
        case 's': case 'S':
          toggleSafe(); break;
        case 'h': case 'H': case '?':
          toggleHelp(); break;
        default: {
          // 1–9, 0 → scenes 1–10; Shift+1–4 → scenes 11–14
          if (/^[0-9]$/.test(k)) {
            const n = k === '0' ? 10 : Number(k);
            goScene(n - 1);
          } else if (e.shiftKey && /^[!@#$]$/.test(k)) {
            const map = { '!': 10, '@': 11, '#': 12, $: 13 };
            goScene(map[k]);
          }
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [advance, next, prev, goScene, toggleSafe, toggleHud, toggleHelp, begin, started]);

  // Click / tap advances too, but never on the presenter chrome.
  useEffect(() => {
    const onClick = (e) => {
      if (!started) return;
      if (e.target.closest('.hud, .help, .boot')) return;
      advance(next);
    };
    window.addEventListener('click', onClick);
    return () => window.removeEventListener('click', onClick);
  }, [advance, next, started]);
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
