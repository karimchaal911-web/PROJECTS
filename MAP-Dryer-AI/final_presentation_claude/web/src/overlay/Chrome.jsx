import { useEffect, useState } from 'react';
import { useShow, selScene, selSceneIndex, selBeatIndex } from '../state/useShow.js';
import { SCENES, TOTAL_SECONDS } from '../state/scenes.js';

/**
 * Persistent chrome and presenter aids.
 *
 * The progress rail is the only thing on screen at all times, borrowed from
 * OCP's own `01 —— 05` pattern. Everything else here is either transient or
 * presenter-only and never reaches the audience by default.
 */

export function ProgressRail() {
  const scene = useShow(selScene);
  const index = useShow(selSceneIndex);
  const beatIndex = useShow(selBeatIndex);
  const started = useShow((s) => s.started);
  const [bright, setBright] = useState(false);

  useEffect(() => {
    setBright(true);
    const id = setTimeout(() => setBright(false), 1200);
    return () => clearTimeout(id);
  }, [index, beatIndex]);

  if (!started) return null;
  const pct = ((index + 1) / SCENES.length) * 100;
  const beats = scene.beats?.length ?? 0;
  const light = scene.mode === 'editorial';

  return (
    <div className={`rail ${bright ? 'is-bright' : ''} ${light ? 'is-light' : ''}`}>
      <span className="rail__n">{scene.n}</span>
      <span className="rail__track">
        <span className="rail__fill" style={{ width: `${pct}%` }} />
      </span>
      <span className="rail__total">{String(SCENES.length).padStart(2, '0')}</span>
      {beats > 1 && (
        <span className="rail__beats">
          {Array.from({ length: beats }, (_, i) => (
            <i key={i} className={i <= beatIndex ? 'on' : ''} />
          ))}
        </span>
      )}
    </div>
  );
}

/**
 * The honesty contract, visible whenever a model result is on screen.
 * Non-negotiable: it is part of the design system, not a disclaimer bolted on.
 */
export function BoundaryBadge() {
  const scene = useShow(selScene);
  const started = useShow((s) => s.started);
  const show = ['evidence', 'supervision', 'through', 'pathways', 'response'].includes(scene.id);
  if (!started || !show) return null;
  const light = scene.mode === 'editorial';
  return (
    <div className={`boundary ${light ? 'is-light' : ''}`}>
      PROTOTYPE · SYNTHETIC DATA · ADVISORY · LABORATORY REMAINS THE REFERENCE
    </div>
  );
}

export function PresenterHud() {
  const hud = useShow((s) => s.hud);
  const index = useShow(selSceneIndex);
  const beatIndex = useShow(selBeatIndex);
  const startedAt = useShow((s) => s.startedAt);
  const safeMode = useShow((s) => s.safeMode);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (!hud) return undefined;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [hud]);

  if (!hud) return null;

  const scene = SCENES[index];
  const nextScene = SCENES[index + 1];
  const elapsed = startedAt ? Math.floor((now - startedAt) / 1000) : 0;
  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
  const ss = String(elapsed % 60).padStart(2, '0');
  const budgetMin = Math.floor(TOTAL_SECONDS / 60);

  return (
    <aside className="hud">
      <header>
        <span className="hud__n">{scene.n}</span>
        <span className="hud__title">{scene.title}</span>
        <span className="hud__clock">{mm}:{ss}<i> / ~{budgetMin} min</i></span>
      </header>
      <p className="hud__act">{scene.act}{safeMode ? ' · SAFE MODE' : ''}</p>
      {scene.beats?.length > 1 && (
        <p className="hud__beat">
          BEAT {beatIndex + 1}/{scene.beats.length} — {scene.beats[beatIndex]?.label}
        </p>
      )}
      <ul className="hud__cues">
        {(CUES[scene.id] ?? []).map((c) => <li key={c}>{c}</li>)}
      </ul>
      {nextScene && <p className="hud__next">NEXT · {nextScene.n} {nextScene.title}</p>}
    </aside>
  );
}

/** Three to five cues per scene. The full script lives in speaker_notes/. */
const CUES = {
  awakening: [
    'Continuous process. It is running right now.',
    'Soluble MAP, Jorf Lasfar context.',
    'Three things: predict quality, detect abnormality, supervise.',
  ],
  material: [
    'Three beats, YOUR pace: phosphorus / nutrition / soluble MAP.',
    'Real product photographed at the site.',
    'Land on: moisture is what keeps it soluble. Then move.',
  ],
  chain: [
    'We travel WITH the material — four stops.',
    'Neutralization: name the mother-liquor return (green loop).',
    'Crystallization: buffering mixes and delays disturbances.',
    'Land it: a deviation at the end belongs to no one stage.',
  ],
  dryer: [
    'MACHINE: inclined shell, riding rings, feed high, discharge low.',
    'PHYSICS: we go inside. Solids one way, air the other way.',
    'Say "schematic, not CFD".',
    'DATA: nine variables, 5-second prototype grid.',
  ],
  gap: [
    'The path is now twelve hours of held-out TEST.',
    'Six laboratory results — all six are in frame. Let them count.',
    'Let the travel play. Do not talk over it.',
    '0.0054 % moisture of movement, unmeasured.',
  ],
  response: [
    'Not more sampling — inference from what is already continuous.',
    'Residence-time alignment + previous lab result.',
    'Laboratory remains the reference.',
    'Mention the second question here; scene 08 answers it.',
  ],
  digital: [
    'Nine variables leave the equipment.',
    'The stack builds from arriving packets — each layer names itself.',
    'ALIGN: point at the held packet. 24.5 min. Causal by construction.',
  ],
  pathways: [
    '16 features for quality; 15 process-only for behaviour.',
    'Ridge won against four alternatives.',
    '2,400 states; the cloud DIMS and 136 support vectors come up.',
    'Then the point leaves the region. Unsupervised, no label.',
  ],
  evidence: [
    'R2 0.8245, MAE 0.00107, RMSE 0.00140 %, n = 165.',
    'Chronological hold-out. Point at the date axis.',
    'Risk 0.804 inside the labelled event, 0.235 outside. 73 of 79.',
    'LIMITS: read the four boundaries. State them before the jury does.',
  ],
  supervision: [
    'Same models, same artifacts — now answering into an operator screen.',
    'Five regions, slowly: predicted, lab, anomaly state, trend, diagnosis.',
    'This is a LIVE replay capture: anomaly 0.95, HIGH, fresh timestamp.',
    'Page 2: ranked contributors, evidence not causality.',
  ],
  through: [
    'We are behind the plane now, at the deep end.',
    'We travel FORWARD with the data: replay, inference, PostgreSQL, views, Power BI.',
    'Power BI reads five views. No model, no inference.',
    'The chain ends at a person. Nothing writes back to the process.',
  ],
  value: [
    'Six stages, one loop. Watch the signal travel it once.',
    'Three defensible statements only.',
    'No ROI. No control action. The operator closes the loop.',
  ],
  roadmap: [
    'TODAY first, large enough to read. Solid = built.',
    'Then pull back: outline = not built. Faintest two are conditional.',
    'Say plainly: closed-loop does not exist here.',
  ],
  return: [
    'Same frame as scene 01 — let them notice.',
    'Every one of those points is now a signal the system reads.',
    'Then QUESTIONS. Stop talking.',
  ],
};

export function HelpPanel() {
  const help = useShow((s) => s.help);
  if (!help) return null;
  return (
    <div className="help">
      <h2>Presenter controls</h2>
      <dl>
        <dt>→ / Space / Page Down</dt><dd>next beat</dd>
        <dt>← / Page Up</dt><dd>previous beat</dd>
        <dt>G then 1–9, 0</dt><dd>go to scene (0 = 10)</dd>
        <dt>G then Q, W, X, C</dt><dd>go to scene 11, 12, 13, 14</dd>
        <dt>Home / End</dt><dd>first / last step</dd>
        <dt>F</dt><dd>fullscreen</dd>
        <dt>P</dt><dd>presenter notes</dd>
        <dt>S</dt><dd>safe mode (reduced performance)</dd>
        <dt>H / ?</dt><dd>this panel</dd>
      </dl>
      <p>Runs entirely offline. Nothing is fetched from the network.</p>
    </div>
  );
}
