/**
 * The fourteen scenes. Single source of truth for the whole show.
 *
 * Each scene declares:
 *   camera  settled pose { pos, target, fov }
 *   mode    lighting state key into MODES
 *   layers  visibility/presence 0..1 per world layer
 *   copy    DOM overlay content (staged beats)
 *   beats   optional in-scene sub-steps the presenter can step through;
 *           each may carry its own `camera` and a `layers` patch merged over
 *           the scene's own layer state
 *
 * See design/THREEJS_SCENE_PLAN.md §5–6 and design/MOTION_SPEC.md.
 */

// Layer presence: 0 hidden, 1 full. Anything between is "receded, not removed".
const HIDDEN = {
  plant: 0, dryer: 0, internals: 0, granules: 0, chain: 0, axis: 0,
  lab: 0, trace: 0, sensors: 0, packets: 0, arch: 0, lanes: 0,
  manifold: 0, evidence: 0, dashboard: 0, runtime: 0, ring: 0, roadmap: 0,
};

const L = (o) => ({ ...HIDDEN, ...o });

export const SCENES = [
  {
    id: 'awakening',
    n: '01',
    title: 'Awakening',
    act: 'I — PURPOSE',
    seconds: 50,
    mode: 'dark',
    camera: { pos: [-30, 4.6, 27], target: [-2, 6.6, 0], fov: 40 },
    layers: L({ plant: 1, dryer: 1, granules: 0.35 }),
    copy: {
      hero: ['INTELLIGENT DIGITALIZATION', 'OF SOLUBLE MAP PRODUCTION'],
      sub: 'Predictive quality · Early anomaly detection · Real-time supervision',
      align: 'left',
      identity: true,
    },
  },

  {
    id: 'material',
    n: '02',
    title: 'Why this material',
    act: 'I — PURPOSE',
    seconds: 35,
    mode: 'focus',
    camera: { pos: [-13.0, 5.86, 7.7], target: [-12.15, 5.72, 4.4], fov: 22 },
    layers: L({ plant: 0.25, dryer: 0.6, granules: 1, hero: 1 }),
    copy: {
      steps: ['PHOSPHORUS', 'PLANT NUTRITION', 'SOLUBLE MAP'],
      mono: 'MAP · MONOAMMONIUM PHOSPHATE · 12-61-00 · SOLUBLE IN WATER',
      note: 'Observed on product stored at the site.',
      align: 'left',
    },
  },

  {
    id: 'chain',
    n: '03',
    title: 'Follow the material',
    act: 'II — INDUSTRY',
    seconds: 60,
    mode: 'dark',
    camera: { pos: [-56, 23, 46], target: [-52, 6.5, -6], fov: 50 },
    track: true,
    layers: L({ plant: 1, dryer: 1, granules: 1, chain: 1 }),
    copy: {
      eyebrow: 'SOLUBLE MAP PRODUCTION — SIMPLIFIED FOR SUPERVISION',
      hero: ['ONE CONTINUOUS', 'COUPLED CHAIN'],
      mono: 'H₃PO₄ + NH₃ ⇌ NH₄H₂PO₄',
      note: 'Mother liquor returns to neutralization. A moisture deviation at the end cannot be attributed to one component.',
      align: 'left',
    },
  },

  {
    id: 'dryer',
    n: '04',
    title: 'Enter the dryer',
    act: 'II — INDUSTRY',
    seconds: 75,
    mode: 'focus',
    camera: { pos: [6, 10.5, 46], target: [-4, 6.2, -2], fov: 34 },
    layers: L({ plant: 0.45, dryer: 1, granules: 1, chain: 0.1 }),
    beats: [
      { id: 'machine', label: 'MACHINE', layers: { internals: 0, sensors: 0 }, camera: { pos: [6, 10.5, 46], target: [-4, 6.2, -2], fov: 34 } },
      { id: 'physics', label: 'PHYSICS', layers: { internals: 1 }, camera: { pos: [4, 8.4, 31], target: [-4, 5.8, -1], fov: 40 } },
      { id: 'data', label: 'DATA', layers: { internals: 0.45, sensors: 1 }, camera: { pos: [4, 10, 44], target: [9, 8, 0], fov: 40 } },
    ],
    copy: {
      eyebrow: 'ROTARY DRYER — THE STAGE THAT SETS FINAL MOISTURE',
      byBeat: {
        machine: { hero: ['MACHINE'], note: 'Inclined shell on riding rings. Wet crystals enter high, dry product leaves low.' },
        physics: { hero: ['PHYSICS'], note: 'Flights lift and cascade the bed through counter-current hot air. Moisture leaves with the exhaust.', caption: 'SCHEMATIC — NOT A CFD RESULT' },
        data: { hero: ['DATA'], note: 'Nine process variables, recorded on the prototype 5-second grid.' },
      },
      align: 'left',
    },
  },

  {
    id: 'gap',
    n: '05',
    title: 'The visibility gap',
    act: 'III — THE GAP',
    seconds: 80,
    mode: 'dark',
    camera: { pos: [46, 18, 62], target: [64, 5, 0], fov: 48 },
    layers: L({ plant: 0.3, dryer: 1, granules: 1, axis: 1, lab: 1 }),
    beats: [
      { id: 'form', label: 'DISTANCE BECOMES TIME', camera: { pos: [46, 18, 62], target: [64, 5, 0], fov: 48 } },
      { id: 'markers', label: 'SIX LABORATORY RESULTS', camera: { pos: [44, 20, 58], target: [58, 4, 0], fov: 44 } },
      { id: 'travel', label: 'THROUGH THE INTERVAL', camera: { pos: [32, 11, 26], target: [48, 5, 0], fov: 42 } },
    ],
    copy: {
      eyebrow: 'HELD-OUT TEST · 2026-07-05 00:00 → 12:00',
      align: 'bottom',
      byBeat: {
        form: { hero: ['TWELVE HOURS', 'OF PRODUCTION'], note: 'The material path is now a time axis. The process does not pause.' },
        markers: { hero: ['SIX RESULTS.'], note: 'Every laboratory sample in this window. Two hours apart.', caption: 'LAB Δt ≈ 2 h' },
        travel: { hero: ['THE PROCESS NEVER STOPS.', 'LAB VISIBILITY DOES.'], note: 'Between the 00:00 and 02:00 results the product moved by 0.0054 % H₂O. Nothing measured it.' },
      },
    },
  },

  {
    id: 'response',
    n: '06',
    title: 'The engineering response',
    act: 'III — THE GAP',
    seconds: 60,
    mode: 'dark',
    camera: { pos: [78, 26, 100], target: [78, 4, 0], fov: 46 },
    layers: L({ plant: 0.15, dryer: 0.7, granules: 1, axis: 1, lab: 1, trace: 1, sensors: 0.6 }),
    beats: [
      { id: 'question', label: 'THE QUESTION', camera: { pos: [58, 16, 46], target: [72, 4, 0], fov: 44 } },
      { id: 'fill', label: 'ESTIMATE BETWEEN MEASUREMENTS', camera: { pos: [70, 20, 78], target: [74, 5, 0], fov: 46 } },
      { id: 'two', label: 'TWO QUESTIONS', camera: { pos: [78, 26, 100], target: [78, 4, 0], fov: 46 } },
    ],
    copy: {
      eyebrow: 'MOISTURE SOFT SENSOR · 695 ESTIMATES · SAME WINDOW',
      align: 'bottom',
      byBeat: {
        question: { hero: ['HOW DO WE SEE', 'BETWEEN MEASUREMENTS?'], note: 'Not by sampling more often. By inferring from what is already measured continuously.' },
        fill: { hero: ['PREDICT QUALITY', 'BETWEEN MEASUREMENTS.'], note: 'Process variables, aligned to the product they describe, plus the previous laboratory result.', caption: 'LABORATORY ANALYSIS REMAINS THE REFERENCE' },
        two: { hero: ['TWO QUESTIONS.', 'ONE SUPERVISION SYSTEM.'], note: 'What is the likely moisture now — and is the process behaving unusually? They are not the same question.' },
      },
    },
  },

  {
    id: 'digital',
    n: '07',
    title: 'Physical becomes digital',
    act: 'IV — DIGITALIZATION',
    seconds: 70,
    mode: 'dark',
    camera: { pos: [2, 18, 6], target: [-14, 16, -44], fov: 40 },
    layers: L({ plant: 0.2, dryer: 0.55, internals: 0.3, granules: 0.4, axis: 0.15, trace: 0.15, sensors: 1, packets: 1, arch: 1 }),
    beats: [
      { id: 'sense', label: 'SENSORS', camera: { pos: [8, 13, 32], target: [-2, 9, 0], fov: 44 } },
      { id: 'stack', label: 'THE STACK BUILDS', camera: { pos: [2, 18, 6], target: [-14, 16, -44], fov: 40 } },
      { id: 'align', label: 'RESIDENCE-TIME ALIGNMENT', camera: { pos: [22, 13, -14], target: [-6, 9.5, -44], fov: 42 } },
    ],
    copy: {
      eyebrow: 'FROM PROCESS TO SUPERVISION',
      byBeat: {
        sense: { hero: ['THE PROCESS', 'BECOMES DATA.'], note: 'Nine variables leave the equipment on the prototype 5-second grid.' },
        stack: { hero: ['THE SIGNALS', 'BUILD THE SYSTEM.'], note: 'Nothing here is drawn in advance. Each layer forms when its data arrives.' },
        align: { hero: ['ALIGNMENT', 'IS THE METHOD.'], note: 'The product sampled now left the dryer 24.5 minutes ago. The model reads the process as it was then, plus the previous laboratory density and temperature.', caption: 'CAUSAL BY CONSTRUCTION — NO FUTURE INFORMATION' },
      },
      align: 'left',
    },
  },

  {
    id: 'pathways',
    n: '08',
    title: 'Two intelligence pathways',
    act: 'IV — DIGITALIZATION',
    seconds: 80,
    mode: 'dark',
    camera: { pos: [0, 20, -16], target: [0, 14, -70], fov: 56 },
    layers: L({ dryer: 0.12, packets: 1, arch: 0.06, lanes: 1, manifold: 1 }),
    beats: [
      { id: 'split', label: 'THE SPLIT', camera: { pos: [0, 20, -16], target: [0, 14, -70], fov: 56 } },
      { id: 'quality', label: 'QUALITY INTELLIGENCE', camera: { pos: [-34, 13, -44], target: [-34, 12.5, -78], fov: 44 } },
      { id: 'process', label: 'PROCESS INTELLIGENCE', camera: { pos: [12, 16, -34], target: [26, 14, -74], fov: 42 } },
      { id: 'leave', label: 'LEAVING THE REGION', camera: { pos: [8, 18, -38], target: [26, 13, -76], fov: 44 } },
    ],
    copy: {
      eyebrow: 'ONE INPUT STREAM · TWO QUESTIONS',
      byBeat: {
        split: { hero: ['ONE STREAM.', 'TWO MODELS.'], note: '16 features for quality. 15 process-only features for behaviour. Neither model sees the other’s answer.' },
        quality: { hero: ['WHAT IS THE LIKELY', 'FINAL MOISTURE NOW?'], note: 'Ridge regression, α = 10, selected on validation RMSE against four alternatives. A regularised linear model — and it won.' },
        process: { hero: ['IS THE PROCESS', 'BEHAVING UNUSUALLY?'], note: '2,400 real training states, projected. The 136 brighter points are the model’s own support vectors — they define the learned boundary.', caption: 'ONE-CLASS SVM · ν = 0.02 · UNSUPERVISED · LEARNS NORMAL ONLY' },
        leave: { hero: ['NOVELTY', 'IS DISTANCE.'], note: 'The current process state, following its real recorded trajectory, leaving the region the model learned.', caption: 'NO ANOMALY LABEL IS USED IN TRAINING' },
      },
      align: 'left',
    },
  },

  {
    id: 'evidence',
    n: '09',
    title: 'Prove it',
    act: 'V — EVIDENCE',
    seconds: 90,
    mode: 'editorial',
    camera: { pos: [72, 19, 40], target: [72, 19, 0], fov: 40 },
    layers: L({ plant: 0, dryer: 0, axis: 0, lab: 0, trace: 0, evidence: 1 }),
    beats: [
      { id: 'moisture', label: 'MOISTURE HOLD-OUT', camera: { pos: [72, 18, 40], target: [72, 18, 0], fov: 40 } },
      { id: 'candidates', label: 'WHY RIDGE', camera: { pos: [72, 3, 38], target: [72, 3, 0], fov: 40 } },
      { id: 'anomaly', label: 'ANOMALY EVIDENCE', camera: { pos: [72, -16, 40], target: [72, -16, 0], fov: 40 } },
      { id: 'limits', label: 'WHAT IT IS WORTH', camera: { pos: [72, -31, 36], target: [72, -31, 0], fov: 38 } },
    ],
    copy: {
      eyebrow: 'EVIDENCE',
      byBeat: {
        moisture: { hero: ['165 HELD-OUT', 'LABORATORY TARGETS.'], note: 'Chronological hold-out: the model never saw any of this period during training or selection.' },
        candidates: { hero: ['THE SIMPLE MODEL', 'WON.'], note: 'Five candidates, tuned with time-aware cross-validation on TRAIN only, compared on VALIDATION RMSE.' },
        anomaly: { hero: ['IT FOUND', 'THE DISTURBANCE.'], note: 'The detector is unsupervised. This label exists only in the synthetic generator and was never shown to the model.' },
        limits: { hero: ['WHAT THIS', 'EVIDENCE IS WORTH.'], note: 'Synthetic prototype data. Chronological hold-out. Advisory. This is not plant validation.' },
      },
      align: 'left',
    },
  },

  {
    id: 'supervision',
    n: '10',
    title: 'Validation becomes supervision',
    act: 'V — EVIDENCE',
    seconds: 65,
    mode: 'supervision',
    camera: { pos: [70, 10, 57], target: [70, 10, 26], fov: 40 },
    layers: L({ dryer: 0, evidence: 0, dashboard: 1 }),
    beats: [
      { id: 'become', label: 'THE CHART BECOMES THE VISUAL', camera: { pos: [70, 12, 46], target: [70, 12, 26], fov: 40 } },
      { id: 'assemble', label: 'THE DASHBOARD', camera: { pos: [70, 10, 57], target: [70, 10, 26], fov: 40 } },
      { id: 'diagnostics', label: 'DIAGNOSTICS PAGE', camera: { pos: [70, 10, 57], target: [70, 10, 26], fov: 40 } },
    ],
    copy: {
      eyebrow: 'POWER BI · POSTGRESQL DIRECTQUERY · ~5 s PAGE REFRESH',
      byBeat: {
        become: { hero: ['THE SAME CHART.', 'AN OPERATOR’S SCREEN.'], note: 'The hold-out trend is not a report figure. It is already the visual the operator reads.' },
        assemble: { hero: ['OPERATIONS', 'OVERVIEW.'], note: 'Predicted moisture, latest laboratory result, validated error, anomaly risk, process status, contributors and guidance.' },
        diagnostics: { hero: ['DIAGNOSTICS', 'AND ROOT CAUSE.'], note: 'Ranked abnormal contributors with normalised deviation, likely subsystem, and the checks to perform. Evidence, not proven causality.', caption: 'PROTOTYPE · REPLAY · ADVISORY' },
      },
      align: 'left',
    },
  },

  {
    id: 'through',
    n: '11',
    title: 'Through the dashboard',
    act: 'V — EVIDENCE',
    seconds: 65,
    mode: 'supervision',
    camera: { pos: [72, 12, 48], target: [73, 11, 20], fov: 44 },
    layers: L({ plant: 0.15, dryer: 0.8, granules: 0.7, sensors: 0.5, packets: 0.8, dashboard: 0.35, runtime: 1 }),
    beats: [
      { id: 'push', label: 'THROUGH THE PLANE', camera: { pos: [72, 12, 48], target: [73, 11, 20], fov: 44 } },
      { id: 'stack', label: 'THE RUNTIME', camera: { pos: [52, 22, 34], target: [74, 4, -16], fov: 46 } },
      { id: 'loop', label: 'THE LOOP CLOSES', camera: { pos: [40, 26, 54], target: [42, 6, -10], fov: 52 } },
    ],
    copy: {
      eyebrow: 'END-TO-END RUNTIME',
      byBeat: {
        push: { hero: ['BEHIND', 'THE DASHBOARD.'], note: 'Power BI reads five semantic SQL views. It never loads a model and never runs inference.' },
        stack: { hero: ['FIVE VIEWS.', 'THREE TABLES.', 'ONE SERVICE.'], note: 'A single Python service loads the exact notebook artifacts once and writes idempotently. 9 ms average inference cycle, 47 ms maximum.' },
        loop: { hero: ['THE LOOP', 'IS CLOSED.'], note: 'Replay, inference, persistence, semantic layer, dashboard — and back to the process it describes.', caption: 'PROTOTYPE REPLAY Δt = 5 s' },
      },
      align: 'left',
    },
  },

  {
    id: 'value',
    n: '12',
    title: 'What this is worth',
    act: 'VI — VALUE',
    seconds: 50,
    mode: 'editorial',
    camera: { pos: [-9, 44, 33], target: [-9, 24, 0], fov: 44 },
    layers: L({ plant: 0.12, dryer: 0.3, granules: 0.5, packets: 0.2, runtime: 0, ring: 1 }),
    copy: {
      eyebrow: 'OPERATIONAL VALUE',
      hero: ['SENSE. PREDICT.', 'DETECT. SUPERVISE.'],
      list: [
        'More continuous moisture visibility between laboratory results.',
        'Earlier awareness of unusual multivariable process behaviour.',
        'Ranked, operator-readable evidence instead of raw alarms.',
        'A supervision layer that supports production continuity.',
      ],
      caption: 'NO ROI IS CLAIMED · NO CONTROL ACTION IS TAKEN · THE LABORATORY REMAINS THE REFERENCE',
      align: 'left',
    },
  },

  {
    id: 'roadmap',
    n: '13',
    title: 'Today → next',
    act: 'VI — VALUE',
    seconds: 55,
    mode: 'editorial',
    camera: { pos: [-2, 27, 52], target: [-2, 19, 0], fov: 46 },
    layers: L({ plant: 0.1, dryer: 0.22, granules: 0.35, ring: 0, roadmap: 1 }),
    beats: [
      { id: 'today', label: 'IMPLEMENTED TODAY', camera: { pos: [-14, 24, 40], target: [-11, 19, 0], fov: 42 } },
      { id: 'next', label: 'WHAT COMES NEXT', camera: { pos: [-2, 27, 52], target: [-2, 19, 0], fov: 46 } },
    ],
    copy: {
      eyebrow: 'BOUNDARY',
      byBeat: {
        today: { hero: ['SOLID', 'MEANS BUILT.'], note: 'Canonical dataset, causal alignment, both models, diagnosis engine, PostgreSQL persistence, five views, a two-page Power BI report, a 5-second replay runtime and 33 automated tests.' },
        next: { hero: ['OUTLINED', 'MEANS NOT YET.'], note: 'Representative plant data, data-quality validation, shadow mode, operator feedback, then governed advisory deployment.', caption: 'CLOSED-LOOP CONTROL DOES NOT EXIST IN THIS PROJECT' },
      },
      align: 'left',
    },
  },

  {
    id: 'return',
    n: '14',
    title: 'Return',
    act: 'VI — VALUE',
    seconds: 45,
    mode: 'dark',
    camera: { pos: [-30, 4.6, 27], target: [-2, 6.6, 0], fov: 40 },
    layers: L({ plant: 1, dryer: 1, granules: 1, sensors: 0.4, packets: 0.25, trace: 0.25 }),
    beats: [
      { id: 'visible', label: 'MORE OF IT VISIBLE', camera: { pos: [-30, 4.6, 27], target: [-2, 6.6, 0], fov: 40 } },
      { id: 'forward', label: 'FROM MONITORING TO OPERATION', camera: { pos: [-26, 6.2, 24], target: [-1, 7.0, 0], fov: 40 } },
      { id: 'questions', label: 'QUESTIONS', camera: { pos: [-22, 7.4, 22], target: [0, 7.4, 0], fov: 42 } },
    ],
    copy: {
      byBeat: {
        visible: { hero: ['THE PHYSICAL PROCESS', 'NEVER STOPPED.'], note: 'Digitalization made more of it visible.' },
        forward: { hero: ['FROM PROCESS MONITORING', 'TO INTELLIGENT', 'INDUSTRIAL OPERATION.'] },
        questions: { mono: 'QUESTIONS', align: 'left' },
      },
      align: 'left',
      identity: true,
    },
  },
];

export const TOTAL_SECONDS = SCENES.reduce((a, s) => a + s.seconds, 0);

/** Flat list of (sceneIndex, beatIndex) steps the presenter walks through. */
export const STEPS = SCENES.flatMap((s, i) =>
  (s.beats && s.beats.length ? s.beats : [null]).map((_, b) => ({ scene: i, beat: b }))
);

export function stepIndexOf(scene, beat) {
  return STEPS.findIndex((s) => s.scene === scene && s.beat === beat);
}
