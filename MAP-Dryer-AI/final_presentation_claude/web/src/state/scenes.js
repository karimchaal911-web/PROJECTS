import { LENS } from '../lib/curves.js';

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
 *   tier    transition class used to REACH this scene/beat — see TIERS below
 *
 * Focal lengths come from LENS, never from a literal, so the lens language is
 * enforced by construction rather than by discipline.
 *
 * See design/THREEJS_SCENE_PLAN.md §5–6 and design/MOTION_SPEC.md.
 */

/**
 * Transition classes.
 *
 * Duration follows narrative weight first and spatial distance second. A beat
 * that refines an idea must not take as long as a beat that changes where we
 * are, and the two transformations the film is built around get their own
 * class so they can breathe.
 */
export const TIERS = {
  micro: 1.5,      // a small adjustment inside one idea
  standard: 1.9,   // a normal beat change
  act: 3.1,        // a new place, a new act, or a lighting change
  signature: 3.5,  // the two transformations the film is built on
  return: 3.6,     // the one journey home
};

/**
 * The camera curve per tier.
 *
 * Every one of the forty-one moves used to be `power2.inOut`, which is the
 * single clearest sign that a film was assembled from a template rather than
 * directed: a nudge inside one idea and the journey home cannot share a curve
 * and still mean different things.
 *
 * The grammar is deliberate and it is the same grammar a camera operator uses:
 *
 *   micro      no wind-up at all. A refinement inside one idea should already
 *              be moving on the first frame and simply settle.
 *   standard   the neutral shot change.
 *   act        a longer acceleration and a longer settle, because the move is
 *              long enough that the audience can see the camera think.
 *   signature  the most deliberate curve in the film — slow to leave, decisive
 *              through the middle, slow to arrive. Used twice.
 *   return     arrival, not travel. Weighted almost entirely into the settle.
 */
export const TIER_EASE = {
  micro: 'power2.out',
  standard: 'power2.inOut',
  act: 'power3.inOut',
  signature: 'power4.inOut',
  return: 'power3.out',
};

// Layer presence: 0 hidden, 1 full. Anything between is "receded, not removed".
const HIDDEN = {
  plant: 0, dryer: 0, internals: 0, granules: 0, chain: 0, axis: 0,
  lab: 0, trace: 0, sensors: 0, packets: 0, arch: 0, lanes: 0,
  manifold: 0, evidence: 0, dashboard: 0, runtime: 0, ring: 0, roadmap: 0,
  material: 0, residence: 0, handover: 0,
};

const L = (o) => ({ ...HIDDEN, ...o });

export const SCENES = [
  {
    id: 'awakening',
    n: '01',
    title: 'Awakening',
    act: 'I — PURPOSE',
    seconds: 30,
    mode: 'dark',
    camera: { pos: [-30, 4.6, 27], target: [-2, 6.6, 0], fov: LENS.ESTABLISH },
    layers: L({ plant: 1, dryer: 1, granules: 0.35 }),
    copy: {
      hero: ['INTELLIGENT DIGITALIZATION', 'OF SOLUBLE MAP PRODUCTION'],
      heroScale: 'title',
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
    seconds: 21,
    mode: 'focus',
    // The product is shown as the product: a photograph of MAP in storage at
    // the site, hung as an editorial print. The previous macro granule put the
    // camera inside its own geometry and showed a grey wall.
    //
    // The push is bounded by the source, not by taste. The photograph is
    // 1280 x 960 and there is no larger copy in the project, so the plate is
    // sized and the camera stopped at the point where it is still a
    // MINIFICATION on screen (about 1 000 px at the closest beat). The old
    // pose magnified it 2.2x, which is what the audience was seeing as blur.
    // See three/layers/Material.jsx and data_build/restore_plates.py.
    camera: { pos: [-46, 9.3, 48], target: [-46, 9.3, 22], fov: LENS.MATERIAL },
    layers: L({ plant: 0.35, dryer: 0.35, granules: 0.5, material: 1 }),
    beats: [
      { id: 'phosphorus', label: 'PHOSPHORUS', tier: 'act', camera: { pos: [-46, 9.3, 48], target: [-46, 9.3, 22], fov: LENS.MATERIAL } },
      { id: 'nutrition', label: 'PLANT NUTRITION', tier: 'micro', camera: { pos: [-46, 9.3, 44.5], target: [-46, 9.3, 22], fov: LENS.MATERIAL } },
      { id: 'product', label: 'SOLUBLE MAP', tier: 'micro', camera: { pos: [-46, 9.3, 41], target: [-46, 9.4, 22], fov: LENS.MATERIAL } },
    ],
    copy: {
      eyebrow: 'THE PRODUCT THIS PROJECT SUPERVISES',
      byBeat: {
        phosphorus: { hero: ['PHOSPHORUS'], note: 'The reason the plant exists.' },
        nutrition: { hero: ['PLANT NUTRITION'], note: 'Phosphorus and nitrogen, delivered in a form a crop can take up.' },
        product: {
          hero: ['SOLUBLE MAP'],
          mono: 'MAP · MONOAMMONIUM PHOSPHATE · 12-61-00 · SOLUBLE IN WATER',
          note: 'Photographed on product stored at the site. Final moisture is what decides whether it stays this way.',
        },
      },
      align: 'left',
    },
  },

  {
    id: 'chain',
    n: '03',
    title: 'Follow the material',
    act: 'II — INDUSTRY',
    seconds: 78,
    mode: 'dark',
    // We travel WITH the material, and we stop at every stage it passes
    // through. The previous cut had four stops for seven stations, so
    // pretreatment, ammonia vaporization, the buffer tanks and centrifugation
    // were named in passing at 40 units of camera speed and never seen. A jury
    // cannot follow a process it is flown past.
    //
    // Constant lens (TRAVEL), consistent +X direction, and every pose framed
    // so the copy column owns the left and the equipment owns the right.
    camera: { pos: [-117, 23, 17], target: [-88, 8, -12], fov: LENS.TRAVEL },
    track: true,
    layers: L({ plant: 0.4, dryer: 0.6, granules: 1, chain: 1 }),
    beats: [
      { id: 'enter', label: 'THE CHAIN', tier: 'act', camera: { pos: [-117, 23, 17], target: [-88, 8, -12], fov: LENS.TRAVEL } },
      { id: 'acid', label: '01 PRETREATMENT', tier: 'standard', camera: { pos: [-107.8, 12.8, 3.6], target: [-98.9, 6.5, -14.4], fov: LENS.TRAVEL } },
      { id: 'vapor', label: '02 AMMONIA VAPORIZATION', tier: 'standard', camera: { pos: [-94.4, 15, 6.4], target: [-84.4, 7.4, -14.4], fov: LENS.TRAVEL } },
      { id: 'neutral', label: '03 NEUTRALIZATION', tier: 'act', camera: { pos: [-82.4, 15.3, 6.5], target: [-72.7, 8.4, -13.2], fov: LENS.TRAVEL } },
      { id: 'buffer', label: '04 BUFFER / STABILIZATION', tier: 'standard', camera: { pos: [-71.4, 16.1, 13.7], target: [-60.4, 8.2, -8.6], fov: LENS.TRAVEL } },
      { id: 'crystal', label: '05 CRYSTALLIZATION', tier: 'act', camera: { pos: [-58.8, 19.7, 20.3], target: [-47, 11.2, -3.7], fov: LENS.TRAVEL } },
      { id: 'centri', label: '06 CENTRIFUGATION', tier: 'standard', camera: { pos: [-40.8, 15, 17.8], target: [-31.6, 8.4, -0.9], fov: LENS.TRAVEL } },
      // The one pose that looks BACK up the chain. The thesis of the scene is
      // that the whole chain sets the outcome, so the frame that carries it
      // shows the whole chain, not the last object in it.
      { id: 'todryer', label: 'INTO THE DRYER', tier: 'act', camera: { pos: [-12, 20, 26], target: [-46, 8, -6], fov: LENS.TRAVEL } },
    ],
    copy: {
      eyebrow: 'SOLUBLE MAP PRODUCTION — SIMPLIFIED FOR SUPERVISION',
      align: 'left',
      byBeat: {
        enter: {
          hero: ['SEVEN STAGES,', 'ONE CHAIN.'],
          mono: 'H3PO4 + NH3 <=> NH4H2PO4',
          note: 'Phosphoric acid and ammonia go in at this end. From here the material never stops moving.',
        },
        acid: {
          hero: ['PHOSPHORIC ACID', 'IS PRETREATED.'],
          note: 'The first of the two feeds. It is conditioned here before it reaches the reaction.',
        },
        vapor: {
          hero: ['AMMONIA', 'IS VAPORISED.'],
          note: 'The second feed. Liquid ammonia is vaporised in heat exchangers and enters the reaction as a gas.',
        },
        neutral: {
          hero: ['ACID AND AMMONIA', 'REACT HERE.'],
          mono: 'H3PO4 + NH3 <=> NH4H2PO4',
          note: 'The product is monoammonium phosphate in solution. Mother liquor from downstream comes back to this stage — the lower line.',
        },
        buffer: {
          hero: ['THE BUFFER TANKS', 'MIX AND DELAY.'],
          note: 'Solution is held and blended before crystallization. Anything unusual upstream arrives downstream spread out in time.',
        },
        crystal: {
          hero: ['SOLIDS FORM HERE.'],
          note: 'The solution is concentrated and crystallised. From this point the product is a wet solid, not a liquid.',
        },
        centri: {
          hero: ['CRYSTALS AND LIQUOR', 'SEPARATE.'],
          note: 'The crystals go on to the dryer. The mother liquor goes back to neutralization, which is what makes this a loop rather than a line.',
        },
        todryer: {
          hero: ['THE DRYER IS', 'THE LAST STAGE.'],
          note: 'Not the only cause. Because the stages are coupled and the mother liquor recycles, final moisture cannot be attributed to any one of them.',
        },
      },
    },
  },

  {
    id: 'dryer',
    n: '04',
    title: 'Enter the dryer',
    act: 'II — INDUSTRY',
    seconds: 57,
    // 57 s, not 63. The push across the machine was thirteen seconds and
    // is now eight and a half; the shot said what it had to say two thirds
    // of the way through the old move.
    mode: 'focus',
    camera: { pos: [6, 10.5, 46], target: [-4, 6.2, -2], fov: LENS.EQUIPMENT },
    layers: L({ plant: 0.45, dryer: 1, granules: 1, chain: 0.1 }),
    beats: [
      { id: 'machine', label: 'MACHINE', tier: 'act', layers: { internals: 0, sensors: 0 }, camera: { pos: [6, 10.5, 46], target: [-4, 6.2, -2], fov: LENS.EQUIPMENT } },
      // Close enough that a flight, a falling bed and a counter-current
      // stream are separable. At the old distance they were 2-3 px each.
      { id: 'physics', label: 'PHYSICS', tier: 'act', layers: { internals: 1, plant: 0.15 }, camera: { pos: [7, 6.4, 10.5], target: [-3, 5.3, 0], fov: LENS.INTERIOR } },
      { id: 'data', label: 'DATA', tier: 'act', layers: { internals: 0.4, sensors: 1 }, camera: { pos: [0, 10, 46], target: [11, 8, 0], fov: LENS.EQUIPMENT } },
    ],
    copy: {
      eyebrow: 'ROTARY DRYER — THE STAGE THAT SETS FINAL MOISTURE',
      byBeat: {
        machine: { hero: ['MACHINE'], note: 'Inclined shell on riding rings. Wet crystals enter high, dry product leaves low.' },
        physics: {
          hero: ['PHYSICS'],
          note: 'Flights lift the bed and drop it through hot air travelling the other way. Moisture leaves with the exhaust.',
          caption: 'SCHEMATIC — NOT A CFD RESULT',
        },
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
    seconds: 56,
    // 56 s, not 69. Two dead holds came out: the beat that turns distance
    // into time had eleven seconds of nothing after the transformation
    // landed, and the truck down the axis ran 1.3 s past its own point.
    mode: 'dark',
    camera: { pos: [46, 18, 62], target: [64, 5, 0], fov: LENS.TRAVEL },
    layers: L({ plant: 0, dryer: 1, granules: 1, axis: 1, lab: 1 }),
    beats: [
      { id: 'form', label: 'DISTANCE BECOMES TIME', tier: 'signature', camera: { pos: [46, 18, 62], target: [64, 5, 0], fov: LENS.TRAVEL } },
      // Framed so all six laboratory results are inside the frame. The old
      // pose held four while the headline said six.
      { id: 'markers', label: 'SIX LABORATORY RESULTS', tier: 'act', camera: { pos: [79, 30, 90], target: [79, 6, 0], fov: LENS.TRAVEL } },
      { id: 'travel', label: 'THROUGH THE INTERVAL', tier: 'act', camera: { pos: [32, 11, 26], target: [48, 5, 0], fov: LENS.TRAVEL } },
    ],
    copy: {
      eyebrow: 'HELD-OUT TEST · 2026-07-05 00:00 → 12:00 · PROTOTYPE REPLAY',
      align: 'bottom',
      byBeat: {
        form: { hero: ['TWELVE HOURS', 'OF PRODUCTION'], note: 'The material path is now a time axis. The process does not pause.' },
        markers: { hero: ['SIX RESULTS.'], note: 'Every laboratory sample in this window. Two hours apart. All six are on screen.', caption: 'LABORATORY INTERVAL ≈ 2 h' },
        travel: { hero: ['TWO HOURS.', 'NO MEASUREMENT.'], note: 'Between the 00:00 and 02:00 results the product moved by 0.0054 % moisture. Nothing measured it.' },
      },
    },
  },

  {
    id: 'response',
    n: '06',
    title: 'The engineering response',
    act: 'III — THE GAP',
    seconds: 38,
    mode: 'dark',
    camera: { pos: [70, 20, 78], target: [74, 0, 0], fov: LENS.TRAVEL },
    layers: L({ plant: 0, dryer: 0.7, granules: 1, axis: 1, lab: 1, trace: 1, sensors: 0.6 }),
    beats: [
      { id: 'question', label: 'THE QUESTION', tier: 'act', camera: { pos: [58, 16, 46], target: [72, 4, 0], fov: LENS.TRAVEL } },
      // Aimed below the axis so the trace sits clear of the copy column's
      // eyebrow, which it used to run straight through.
      { id: 'fill', label: 'ESTIMATE BETWEEN MEASUREMENTS', tier: 'standard', camera: { pos: [70, 20, 78], target: [74, 0, 0], fov: LENS.TRAVEL } },
    ],
    copy: {
      eyebrow: 'MOISTURE SOFT SENSOR · 695 ESTIMATES · SAME WINDOW',
      align: 'bottom',
      byBeat: {
        question: { hero: ['HOW DO WE SEE', 'IN BETWEEN?'], note: 'Not by sampling more often. By inferring from what is already measured continuously.' },
        fill: {
          hero: ['ESTIMATE MOISTURE', 'BETWEEN SAMPLES.'],
          note: 'Process variables, aligned to the product they describe, plus the previous laboratory result. A second question — is the process behaving unusually — is answered by a separate model.',
          caption: 'LABORATORY ANALYSIS REMAINS THE REFERENCE',
        },
      },
    },
  },

  {
    id: 'digital',
    n: '07',
    title: 'Physical becomes digital',
    act: 'IV — DIGITALIZATION',
    seconds: 78,
    // 78 s, not 66 — the one scene that got LONGER. Residence-time
    // alignment is two claims, a physical one and a data one, and it was
    // being made in a single sentence over a glowing slab. It now has a
    // beat each. Every second of this came out of scenes 04, 05, 12 and 14.
    mode: 'dark',
    camera: { pos: [2, 18, 6], target: [-14, 16, -44], fov: LENS.SYSTEM },
    layers: L({ plant: 0.08, dryer: 0.4, granules: 0.3, axis: 0.1, trace: 0.1, sensors: 1, packets: 1, arch: 1 }),
    beats: [
      { id: 'sense', label: 'SENSORS', tier: 'act', camera: { pos: [8, 13, 32], target: [-2, 9, 0], fov: LENS.SYSTEM } },
      { id: 'stack', label: 'THE STACK BUILDS', tier: 'standard', camera: { pos: [2, 18, 6], target: [-14, 16, -44], fov: LENS.SYSTEM } },
      // Residence-time alignment now gets TWO beats, because it is two claims.
      //
      // The first is about a machine: material takes time to cross the dryer,
      // so a laboratory result describes material that entered twenty-four
      // minutes earlier. The second is about the data that follows from it:
      // pairing process variables with quality at the SAME timestamp describes
      // the wrong material, and every input is therefore shifted back.
      //
      // Compressed into one beat, the physical fact and its data consequence
      // arrived in the same sentence over a glowing slab, and the jury had to
      // take the most defensible idea in the project on trust. The camera
      // leaves the stack and comes to the lane that shows it — see
      // three/layers/Residence.jsx — with the stack still behind, because the
      // lane is an explanation OF the stack.
      // Both poses sit BEYOND the dryer, looking further into -Z, so the
      // machine is behind the lens rather than lying across the frame.
      //
      // The lane is placed by TRANSLATING the camera sideways rather than by
      // aiming at it, which is the only way to hold a horizontal object off
      // centre without foreshortening it. Aiming the camera left of the lane —
      // the obvious way to clear the copy column — rotates the view, and a
      // rotated view turns a timeline into a road running away from the lens:
      // the first cut of this beat put the lane's far end at 103 % of frame
      // width with the SAMPLE TAKEN label outside the frame entirely.
      //
      // Verified with scripts/_probe_residence.mjs rather than by arithmetic:
      // the lane spans 48.6 % to 91.6 % of frame width, dead level, and the
      // 24.5-minute shift between the two blocks is 4.3 % of frame width —
      // eighty pixels at 1080p, which is a shift a jury can see.
      { id: 'delay', label: 'THE DELAY IS PHYSICAL', tier: 'act', layers: { residence: 1, arch: 0.13, packets: 0.12, dryer: 0.12, granules: 0.08 }, camera: { pos: [-13, 19.5, -6], target: [-13, 15.5, -30], fov: LENS.SYSTEM } },
      // A lateral settle, not a push. Same distance, so the lane cannot grow
      // out of the frame, but the rails re-centre and the level horizon picks
      // up a slight tilt — enough that the two beats are not one locked-off
      // frame with different things switched on inside it.
      { id: 'align', label: 'RESIDENCE-TIME ALIGNMENT', tier: 'standard', layers: { residence: 1, arch: 0.13, packets: 0.12, dryer: 0.12, granules: 0.08 }, camera: { pos: [-12, 18.6, -4], target: [-13.6, 15.4, -30], fov: LENS.SYSTEM } },
    ],
    copy: {
      eyebrow: 'FROM PROCESS TO SUPERVISION',
      byBeat: {
        sense: { hero: ['NINE VARIABLES', 'LEAVE THE PROCESS.'], note: 'Sampled on the prototype 5-second grid. Everything above this point is built from them.' },
        stack: { hero: ['NOTHING IS DRAWN', 'BEFORE ITS DATA.'], note: 'The stack assembles itself out of the arriving signals, in the order they reach it, and each layer is named only once it exists.' },
        delay: {
          hero: ['THE DRYER', 'HAS A LENGTH.'],
          note: 'Material takes about 24.5 minutes to cross it. The sample the laboratory analyses at nine o’clock describes product that entered the dryer at 8:35 — and residence time is measured continuously, not assumed.',
          caption: 'RESIDENCE TIME · 24.15 → 24.89 min · ONE OF THE NINE MEASURED VARIABLES',
        },
        align: {
          hero: ['ALIGN THE DATA', 'TO THE PRODUCT.'],
          note: 'Pairing process variables with the quality result at the same timestamp describes the wrong material. Every input is shifted back by the residence time at that moment; density and temperature come from the previous laboratory sample. Nothing in the vector is from the future.',
          caption: 'CAUSAL BY CONSTRUCTION — NO FUTURE INFORMATION',
        },
      },
      align: 'left',
    },
  },

  {
    id: 'pathways',
    n: '08',
    title: 'Two intelligence pathways',
    act: 'IV — DIGITALIZATION',
    seconds: 68,
    mode: 'dark',
    camera: { pos: [0, 20, -16], target: [0, 14, -70], fov: LENS.SYSTEM },
    layers: L({ dryer: 0.1, packets: 1, arch: 0.05, lanes: 1, manifold: 1 }),
    beats: [
      { id: 'split', label: 'THE SPLIT', tier: 'act', camera: { pos: [0, 20, -16], target: [0, 14, -70], fov: LENS.SYSTEM } },
      // Aimed LEFT of the lane so the coefficient names clear the copy column,
      // and close enough that they hold ~20 px rather than ~17.
      { id: 'quality', label: 'QUALITY INTELLIGENCE', tier: 'act', camera: { pos: [-34.5, 13.5, -50], target: [-34.5, 13, -78], fov: LENS.SYSTEM } },
      // The trajectory used to be its own beat with a 6-unit camera move.
      // It is now a sub-reveal inside this one.
      { id: 'process', label: 'PROCESS INTELLIGENCE', tier: 'act', camera: { pos: [14, 15, -40], target: [26, 14, -76], fov: LENS.SYSTEM } },
    ],
    copy: {
      eyebrow: 'ONE INPUT STREAM · TWO QUESTIONS',
      byBeat: {
        split: { hero: ['ONE STREAM.', 'TWO MODELS.'], note: '16 features for quality. 15 process-only features for behaviour. Neither model sees the other’s answer.' },
        quality: { hero: ['WHAT IS THE', 'MOISTURE NOW?'], note: 'Ridge regression, alpha = 10, selected on validation RMSE against four alternatives. A regularised linear model — and it won.' },
        process: {
          hero: ['IS THIS PROCESS', 'STATE UNUSUAL?'],
          note: '2,400 training states from the prototype dataset, projected. The 136 bright points are the model’s own support vectors — they define the learned boundary. The moving point follows a real recorded trajectory out of the region.',
          caption: 'ONE-CLASS SVM · nu = 0.02 · UNSUPERVISED · NO ANOMALY LABEL IN TRAINING',
        },
      },
      align: 'left',
    },
  },

  {
    id: 'evidence',
    n: '09',
    title: 'Prove it',
    act: 'V — EVIDENCE',
    seconds: 98,
    // 98 s, not 104. The four evidence beats keep their generous pacing;
    // what came out was the settle after WHAT IT IS WORTH, which is a
    // held frame the presenter speaks over rather than a beat.
    mode: 'editorial',
    camera: { pos: [32.2, 12.5, -16.7], target: [19.2, 12.5, -58.7], fov: LENS.EDITORIAL },
    layers: L({ evidence: 1 }),
    // Four distinct spatial relationships instead of three identical drops:
    // approach level, truck with a rise, arc down, then pull back for air. The
    // gallery runs from the model region to the operator's screen, so walking
    // the evidence is walking from the model to the dashboard.
    //
    // Every pose is aimed LEFT of its panel's centre. The panels used to be
    // centred in frame, which put their titles, y-axis ticks and first metric
    // underneath the copy column on all four beats.
    beats: [
      { id: 'moisture', label: 'MOISTURE HOLD-OUT', tier: 'act', camera: { pos: [32.2, 12.5, -16.7], target: [19.2, 12.5, -58.7], fov: LENS.EDITORIAL } },
      { id: 'candidates', label: 'WHY RIDGE', tier: 'standard', camera: { pos: [45.5, 13.6, 1.3], target: [35.0, 11.1, -41.3], fov: LENS.EDITORIAL } },
      { id: 'anomaly', label: 'ANOMALY EVIDENCE', tier: 'standard', camera: { pos: [55.9, 11.7, 21.1], target: [48.9, 6.7, -22.2], fov: LENS.EDITORIAL } },
      { id: 'limits', label: 'WHAT IT IS WORTH', tier: 'act', camera: { pos: [63.1, 5.6, 46.0], target: [59.2, 3.6, -3.1], fov: LENS.EDITORIAL } },
    ],
    copy: {
      eyebrow: 'EVIDENCE',
      byBeat: {
        moisture: { hero: ['165 HELD-OUT', 'LAB RESULTS.'], note: 'Chronological hold-out: the model never saw any of this period during training or selection.' },
        candidates: { hero: ['THE SIMPLE MODEL', 'WON.'], note: 'Five candidates, tuned with time-aware cross-validation on TRAIN only, compared on VALIDATION RMSE.' },
        anomaly: { hero: ['IT FOUND', 'THE DISTURBANCE.'], note: 'The detector is unsupervised. This label exists only in the prototype generator and was never shown to the model.' },
        // The world text carries the limits; the overlay must not repeat them.
        limits: { hero: ['WHAT IT PROVES.', 'WHAT IT DOES NOT.'] },
      },
      align: 'left',
    },
  },

  {
    id: 'supervision',
    n: '10',
    title: 'The model leaves the notebook',
    act: 'V — EVIDENCE',
    seconds: 76,
    // 76 s, not 72. The extra four seconds are the handover sequence —
    // artifact, service, inference, screen — which replaces a two-second
    // cross-fade under the film's biggest headline.
    mode: 'supervision',
    // Aimed LEFT of the plane's centre so the report occupies the right of the
    // frame and the copy column owns the left. Centring it put the headline
    // across the trend chart on the film's most important deliverable.
    camera: { pos: [66, 10, 65], target: [66, 10, 26], fov: LENS.EDITORIAL },
    layers: L({ dashboard: 1 }),
    beats: [
      // The signature sequence lives here — see three/layers/Handover.jsx. It
      // is staged INSIDE this beat's own frame rather than beside it: the
      // artifact and the service occupy the corridor in front of the report
      // while the report is still at zero, and by the time the page is legible
      // they have receded. The pose is unchanged, so the two beats that make
      // the report readable are untouched.
      { id: 'become', label: 'ARTIFACT → SERVICE → SCREEN', tier: 'signature', layers: { handover: 1 }, camera: { pos: [66, 10, 65], target: [66, 10, 26], fov: LENS.EDITORIAL } },
      // Scene 10 holds ONE distance and moves laterally and vertically only.
      // Pushing in cropped the report: at this plane size anything closer than
      // ~38 units puts the right edge of the page — the diagnosis and operator
      // guidance panels — outside the frame, which is where they were.
      { id: 'assemble', label: 'WHAT THE OPERATOR READS', tier: 'micro', camera: { pos: [65, 12, 66], target: [66, 11, 26], fov: LENS.EDITORIAL } },
      // A real move, not a static cut: the camera leans down and across to the
      // second page rather than the page swapping underneath a locked-off lens.
      { id: 'diagnostics', label: 'DIAGNOSTICS PAGE', tier: 'standard', camera: { pos: [67, 8, 66], target: [66, 9, 26], fov: LENS.EDITORIAL } },
    ],
    copy: {
      eyebrow: 'POWER BI · POSTGRESQL DIRECTQUERY · 5 s REPLAY TICK',
      byBeat: {
        become: {
          hero: ['THE MODEL LEAVES', 'THE NOTEBOOK.'],
          note: 'Not a rewrite for production — a load. The service opens the exact files notebook 03 wrote, once at start, and answers every five seconds into the operator’s screen instead of into a validation figure.',
          caption: 'THE FILE THE NOTEBOOK WROTE IS THE FILE THE SERVICE LOADS · sha256 IN models/model_registry.json',
        },
        assemble: {
          hero: ['OPERATIONS', 'OVERVIEW.'],
          note: 'Predicted moisture, the laboratory reference, validated error, anomaly state, and the ranked evidence behind it. This capture is a live replay state, not a mock-up.',
        },
        diagnostics: {
          hero: ['DIAGNOSTICS', 'AND ROOT CAUSE.'],
          note: 'Ranked abnormal contributors with normalised deviation, likely subsystem, and the checks to perform. Evidence, not proven causality.',
          caption: 'PROTOTYPE · REPLAY · ADVISORY',
        },
      },
      align: 'left',
    },
  },

  {
    id: 'through',
    n: '11',
    title: 'Behind the dashboard',
    act: 'V — EVIDENCE',
    seconds: 60,
    // 60 s, not 63. The runtime path lit its five checkpoints over 3.6 s
    // and now does it in 3.0; the camera is travelling with them either way.
    mode: 'supervision',
    camera: { pos: [36, 8, -46], target: [78, 3, -16], fov: LENS.SYSTEM },
    layers: L({ dashboard: 1, runtime: 1 }),
    // The camera passes THROUGH the report plane and comes to rest ACROSS the
    // runtime rather than along it, then trucks forward in the direction the
    // data travels, then returns to the front of the plane for the handover.
    //
    // Riding the centre line of the route put all five checkpoints on the same
    // screen position — one silhouette, four hidden labels — and left the
    // first frame of the scene 90 % empty. Watching the route from the side
    // spreads the checkpoints across the right of the frame in flow order.
    beats: [
      { id: 'push', label: 'THROUGH THE PLANE', tier: 'signature', camera: { pos: [36, 8, -46], target: [78, 3, -16], fov: LENS.SYSTEM } },
      { id: 'path', label: 'THE RUNTIME PATH', tier: 'act', camera: { pos: [34, 6, -28], target: [80, 2, -6], fov: LENS.SYSTEM } },
      // Out in front of the plane at last: the report above, the person who
      // reads it below, and the route arriving from behind both.
      // The hall does NOT come back for this beat. Its ground plane is 400 x 220
      // at y = -0.02 and writes depth even at 5 % opacity, so the operator
      // terminal — which sits below the report, below y = 0 — was rendered
      // underneath the floor and simply never appeared. The frame is also
      // stronger without it: the report, the person who reads it, and the
      // route arriving from behind, and nothing else.
      { id: 'loop', label: 'IT ENDS WITH A PERSON', tier: 'act', layers: { packets: 0.6, dashboard: 1 }, camera: { pos: [56, 6, 76], target: [66, 5, 26], fov: LENS.TRAVEL } },
    ],
    copy: {
      eyebrow: 'END-TO-END RUNTIME',
      byBeat: {
        push: { hero: ['BEHIND', 'THE DASHBOARD.'], note: 'Power BI reads five semantic SQL views. It never loads a model and never runs inference.' },
        path: { hero: ['REPLAY. INFER.', 'PERSIST. SERVE.'], note: 'A single Python service loads the exact notebook artifacts once and writes idempotently. 9 ms average inference cycle, 47 ms maximum. We are travelling in the direction the data travels.' },
        loop: {
          hero: ['THE CHAIN ENDS', 'AT A PERSON.'],
          note: 'The last step is not an actuator. It is an operator reading evidence and deciding. Nothing in this system writes back to the process.',
          caption: 'PROTOTYPE REPLAY - 5 s TICK · NO CONTROL ACTION IS TAKEN',
        },
      },
      align: 'left',
    },
  },

  {
    id: 'value',
    n: '12',
    title: 'What this is worth',
    act: 'VI — VALUE',
    seconds: 18,
    // 18 s, not 24. One signal travelling the loop was given 5.5 s to make
    // a point it makes in 4. This is a synthesis scene, and synthesis
    // should feel brisk.
    mode: 'editorial',
    // 66 units of travel AND the dark -> cream chapter flip arrive together
    // here. A scene with no beats falls back to the standard tier, which gave
    // that move 1.9 s — the fastest act change in the film, on the biggest
    // tonal shift in it.
    tier: 'act',
    // Aimed left of the ring so the loop sits clear of the copy column.
    camera: { pos: [18, 46, 40], target: [16, 28, 2], fov: LENS.EDITORIAL },
    layers: L({ ring: 1 }),
    copy: {
      eyebrow: 'OPERATIONAL VALUE',
      // Six words for six nodes. The headline used to name four and the ring
      // showed six.
      hero: ['PROCESS. SENSE.', 'PREDICT. DETECT.', 'SUPERVISE. DECIDE.'],
      list: [
        'More continuous moisture visibility between laboratory results.',
        'Earlier awareness of unusual multivariable process behaviour.',
        'Ranked, operator-readable evidence instead of raw alarms.',
      ],
      caption: 'NO ROI IS CLAIMED · NO CONTROL ACTION IS TAKEN · THE OPERATOR CLOSES THE LOOP',
      align: 'left',
    },
  },

  {
    id: 'roadmap',
    n: '13',
    title: 'Today → next',
    act: 'VI — VALUE',
    seconds: 48,
    mode: 'editorial',
    camera: { pos: [13, 30, 72], target: [13, 21, 0], fov: LENS.EDITORIAL_WIDE },
    layers: L({ roadmap: 1 }),
    // The scene TRAVELS the rail rather than trying to frame all twelve
    // stages at once. Twelve labelled stages cannot exceed ~16 px in a single
    // 16:9 framing; walking them keeps the built half at ~36 px and the wide
    // placement shot at ~22 px, both projector-safe. The move is a truck
    // along +X — the same left-to-right reading the rail itself asks for.
    beats: [
      { id: 'today', label: 'IMPLEMENTED TODAY', tier: 'act', camera: { pos: [-15, 27, 43], target: [-15, 21, 0], fov: LENS.EDITORIAL_WIDE } },
      { id: 'next', label: 'WHAT COMES NEXT', tier: 'act', camera: { pos: [13, 30, 72], target: [13, 21, 0], fov: LENS.EDITORIAL_WIDE } },
    ],
    copy: {
      eyebrow: 'BOUNDARY',
      byBeat: {
        today: { hero: ['SOLID', 'MEANS BUILT.'], note: 'Canonical dataset, causal alignment, both models with the diagnosis engine, PostgreSQL persistence with five semantic views, a two-page Power BI report on a 5-second replay runtime, and 33 automated tests.' },
        next: { hero: ['OUTLINED', 'MEANS NOT YET.'], note: 'Representative plant historian data, data-quality validation, shadow mode, operator feedback, then governed advisory deployment. The two amber stages are conditional and may never be built.', caption: 'CLOSED-LOOP CONTROL DOES NOT EXIST IN THIS PROJECT' },
      },
    },
  },

  {
    id: 'return',
    n: '14',
    title: 'Return',
    act: 'VI — VALUE',
    seconds: 32,
    // 32 s, not 40. The closing QUESTIONS card was budgeted as if the
    // Q&A that follows it were part of the film. It is not: the card is a
    // held frame, and the clock the presenter watches should say so.
    mode: 'dark',
    // Identical to scene 01. Both beats hold it: the rhyme is the ending, and
    // the two micro-dollies that used to follow it only diluted it.
    camera: { pos: [-30, 4.6, 27], target: [-2, 6.6, 0], fov: LENS.ESTABLISH },
    layers: L({ plant: 1, dryer: 1, granules: 1, sensors: 1, packets: 0.3, trace: 0 }),
    beats: [
      { id: 'visible', label: 'MORE OF IT VISIBLE', tier: 'return', camera: { pos: [-30, 4.6, 27], target: [-2, 6.6, 0], fov: LENS.ESTABLISH } },
      { id: 'questions', label: 'QUESTIONS', tier: 'standard', camera: { pos: [-30, 4.6, 27], target: [-2, 6.6, 0], fov: LENS.ESTABLISH } },
    ],
    copy: {
      byBeat: {
        visible: {
          hero: ['THE PROCESS', 'NEVER STOPPED.'],
          note: 'The same frame as the opening. The difference is that every one of those points is now a signal the system reads — and that is the whole project.',
        },
        questions: {
          hero: ['QUESTIONS'],
          heroScale: 'xl',
          sub: 'From process monitoring to intelligent industrial operation.',
        },
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

/**
 * Diagnostics for scripts/qa-channels.mjs: the step table, and the merged layer
 * presence a step settles to. The audit needs the layer map to tell a channel
 * disagreement that changes what is on screen from one that does not.
 */
if (typeof window !== 'undefined') {
  window.__STEPTABLE__ = STEPS;
  window.__LAYERS__ = (step) => {
    const { scene: si, beat: bi } = STEPS[step];
    const scene = SCENES[si];
    const merged = { ...scene.layers, ...(scene.beats?.[bi]?.layers ?? {}) };
    // Re-key from layer name to the channels that layer owns is the caller's
    // job; this returns presence by layer name.
    return merged;
  };
}

/** The transition tier name for a step. */
export function tierName(sceneIndex, beatIndex) {
  const scene = SCENES[sceneIndex];
  const beat = scene.beats?.[beatIndex];
  const name = beat?.tier ?? scene.tier ?? 'standard';
  return TIERS[name] ? name : 'standard';
}

/** Seconds the transition INTO this step should take. */
export function tierFor(sceneIndex, beatIndex) {
  return TIERS[tierName(sceneIndex, beatIndex)];
}

/** The camera curve the transition INTO this step should use. */
export function easeFor(sceneIndex, beatIndex) {
  return TIER_EASE[tierName(sceneIndex, beatIndex)];
}
