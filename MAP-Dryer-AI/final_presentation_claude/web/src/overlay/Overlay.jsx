import { useEffect, useMemo, useRef, useState } from 'react';
import gsap from 'gsap';
import { useShow, selScene, selBeat, selSceneIndex, selBeatIndex } from '../state/useShow.js';
import { tierFor } from '../state/scenes.js';

/**
 * The DOM overlay.
 *
 * Text sits on the world, not in a card. Contrast is guaranteed by a gradient
 * scrim rather than by a shadow or a panel, so the composition underneath is
 * never boxed in. Copy occupies at most five of twelve columns and is anchored
 * to one side — the subject owns the centre.
 *
 * Copy is SEQUENCED AGAINST THE WORLD, not swapped underneath it. The overlay
 * used to re-key on scene+beat, which destroyed the old copy on the frame the
 * step changed and played a 0.7 s entrance while the world was still 2 s from
 * arriving — so for well over a second the next scene's headline was fully
 * legible over the previous scene's world, on every transition in the film.
 *
 * Now: the old copy leaves first, the world travels, and the new copy resolves
 * as the world settles. The delay is a fraction of the transition's own tier,
 * so a micro-beat stays snappy and an act change gets room.
 */

const OUT_SECONDS = 0.34;
const ENTER_AT = 0.46; // fraction of the world transition

export default function Overlay() {
  const scene = useShow(selScene);
  const beat = useShow(selBeat);
  const sceneIndex = useShow(selSceneIndex);
  const beatIndex = useShow(selBeatIndex);
  const started = useShow((s) => s.started);

  const target = useMemo(() => {
    const c = scene.copy ?? {};
    const merged = c.byBeat && beat ? { ...c, ...(c.byBeat[beat.id] ?? {}) } : c;
    return { content: merged, key: `${sceneIndex}:${beat?.id ?? '_'}`, editorial: scene.mode === 'editorial' };
  }, [scene, beat, sceneIndex]);

  // What is actually on screen right now, which lags `target` by design.
  const [shown, setShown] = useState(target);
  const [phase, setPhase] = useState('in');
  const first = useRef(true);

  useEffect(() => {
    if (first.current) {
      first.current = false;
      return undefined;
    }
    setPhase('out');
    // gsap.delayedCall rather than setTimeout: the whole show runs on one
    // ticker, and the copy must not drift away from the camera on a laptop
    // that is dropping frames.
    const swapAt = Math.max(OUT_SECONDS, tierFor(sceneIndex, beatIndex) * ENTER_AT);
    const call = gsap.delayedCall(swapAt, () => {
      setShown(target);
      setPhase('in');
    });
    return () => call.kill();
  }, [target, sceneIndex, beatIndex]);

  if (!started) return null;

  const { content, key, editorial } = shown;

  return (
    <div className={`overlay ${editorial ? 'is-editorial' : 'is-dark'}`}>
      <div className={`scrim scrim--${content.align ?? 'left'}`} />

      <div className={`copy copy--${content.align ?? 'left'} is-${phase}`} key={key}>
        {content.eyebrow && <p className="eyebrow anim" style={{ '--i': 0 }}>{content.eyebrow}</p>}

        {content.hero && (
          <h1
            className={`hero ${content.heroScale === 'xl' ? 'hero--xl' : ''}`}
            style={{ '--hero-fit': heroFit(content) }}
          >
            {content.hero.map((line, i) => (
              <span className="hero__line anim" style={{ '--i': i + 1 }} key={line}>{line}</span>
            ))}
          </h1>
        )}

        {content.sub && <p className="sub anim" style={{ '--i': 3 }}>{content.sub}</p>}

        {content.mono && <p className="mono anim" style={{ '--i': 4 }}>{content.mono}</p>}

        {content.list && (
          <ul className="list">
            {content.list.map((item, i) => (
              <li className="anim" style={{ '--i': i + 3 }} key={item}>{item}</li>
            ))}
          </ul>
        )}

        {content.note && <p className="note anim" style={{ '--i': 5 }}>{content.note}</p>}
        {content.caption && <p className="caption anim" style={{ '--i': 6 }}>{content.caption}</p>}
      </div>

      {content.identity && <Identity />}
    </div>
  );
}

/**
 * A headline whose line does not fit the copy column is re-broken by the
 * browser, so a two-line idea arrives as a five-line stack covering half the
 * frame. Lines are written to fit; this is the guard that stops a late edit
 * from silently producing that stack again. The title card opts out — it is
 * the one place where a tall block is the design.
 *
 * The two columns are not the same width: `copy--bottom` is 640 px against the
 * side column's 720, which is why "ESTIMATE MOISTURE / BETWEEN SAMPLES." was
 * arriving as four lines while the same string would have fitted on the left.
 */
const FITS = { bottom: 14 };
const FITS_DEFAULT = 16;

function heroFit(content) {
  if (content.heroScale) return 1;
  const room = FITS[content.align] ?? FITS_DEFAULT;
  const longest = content.hero.reduce((m, l) => Math.max(m, l.length), 0);
  if (longest <= room) return 1;
  return Math.max(0.78, room / longest);
}

function Identity() {
  const base = import.meta.env.BASE_URL;
  return (
    <div className="identity">
      <img src={`${base}img/ocp.png`} alt="OCP" />
      <span className="identity__rule" />
      <img src={`${base}img/ensam_umi.png`} alt="ENSAM — Université Moulay Ismaïl" />
    </div>
  );
}
