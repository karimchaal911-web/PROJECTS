import { useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { useShow } from '../state/useShow.js';
import { makeFpsWatch } from '../lib/perf.js';

/**
 * Automatic degradation.
 *
 * `makeFpsWatch` existed, was exported and was documented as the application's
 * protection against a slow projector laptop — and was never called anywhere.
 * The only degrade path was a boot probe requiring BOTH four cores or fewer
 * AND four gigabytes or less, so a typical eight-core machine with weak
 * integrated graphics, or any machine that thermally throttles ten minutes
 * into a defence, would never degrade however badly it was running.
 *
 * It watches a sustained collapse rather than a single hitch — ninety
 * consecutive frames slower than 1/30 s, with recovery credited back — so one
 * stall during a transition cannot trip it. It fires once.
 *
 * `?degrade=off` disables it. That exists for the QA harness, which renders
 * through SwiftShader: software rasterisation is slow enough to trip the guard
 * legitimately, so every "standard mode" capture was silently a safe-mode
 * capture and the manifest recorded the wrong mode. It is not a presenter
 * control and is not documented in the help panel.
 */
export default function PerfGuard() {
  const safeMode = useShow((s) => s.safeMode);
  const setSafe = useShow((s) => s.setSafe);
  const started = useShow((s) => s.started);

  const disabled = useMemo(
    () => typeof window !== 'undefined'
      && new URLSearchParams(window.location.search).get('degrade') === 'off',
    []
  );

  const watch = useMemo(
    () => makeFpsWatch(() => {
      // eslint-disable-next-line no-console
      console.warn('[perf] sustained frame collapse — entering safe mode');
      setSafe(true);
    }, { threshold: 30, frames: 90 }),
    [setSafe]
  );

  useFrame(() => {
    if (!started || safeMode || disabled) return;
    watch();
  });

  return null;
}
