import { useEffect, useMemo, useRef, useState } from 'react';
import { useShow, selScene, selBeat, selSceneIndex } from '../state/useShow.js';
import { SCENES } from '../state/scenes.js';

/**
 * The DOM overlay.
 *
 * Text sits on the world, not in a card. Contrast is guaranteed by a gradient
 * scrim rather than by a shadow or a panel, so the composition underneath is
 * never boxed in. Copy occupies at most five of twelve columns and is anchored
 * to one side — the subject owns the centre.
 */

export default function Overlay() {
  const scene = useShow(selScene);
  const beat = useShow(selBeat);
  const sceneIndex = useShow(selSceneIndex);
  const started = useShow((s) => s.started);

  const content = useMemo(() => {
    const c = scene.copy ?? {};
    if (c.byBeat && beat) return { ...c, ...(c.byBeat[beat.id] ?? {}) };
    return c;
  }, [scene, beat]);

  // Re-key on scene+beat so the CSS entrance animation replays.
  const key = `${sceneIndex}:${beat?.id ?? '_'}`;

  if (!started) return null;

  const editorial = scene.mode === 'editorial';

  return (
    <div className={`overlay ${editorial ? 'is-editorial' : 'is-dark'}`}>
      <div className={`scrim scrim--${content.align ?? 'left'}`} />

      <div className={`copy copy--${content.align ?? 'left'}`} key={key}>
        {content.eyebrow && <p className="eyebrow anim" style={{ '--i': 0 }}>{content.eyebrow}</p>}

        {content.steps && <StepWord words={content.steps} />}

        {content.hero && (
          <h1 className="hero">
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

/** Scene 02: three words arrive and leave in the same position. */
function StepWord({ words }) {
  const [i, setI] = useState(0);
  const timer = useRef(null);

  useEffect(() => {
    setI(0);
    let n = 0;
    timer.current = setInterval(() => {
      n += 1;
      if (n >= words.length) {
        clearInterval(timer.current);
        return;
      }
      setI(n);
    }, 1900);
    return () => clearInterval(timer.current);
  }, [words]);

  return (
    <h1 className="hero hero--steps">
      <span className="hero__line anim" key={words[i]}>{words[i]}</span>
    </h1>
  );
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

export function sceneTitle(i) {
  return SCENES[i]?.title ?? '';
}
