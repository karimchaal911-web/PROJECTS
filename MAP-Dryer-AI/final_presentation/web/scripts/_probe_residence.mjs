/**
 * Where does the residence lane actually land in the frame?
 *
 * Composing a beat by arithmetic on paper is how this lane first shipped at
 * 103 % of frame width with SAMPLE TAKEN outside the frame. This projects every
 * element of three/layers/Residence.jsx through a candidate pose using three's
 * own camera, so the number that was checked is the number on screen.
 *
 *   node scripts/_probe_residence.mjs [fov]
 */
import { report } from './_frame.mjs';

const O = [-6, 16, -30];
const LEN = 15, HALF = LEN / 2, RAIL = 3.4;
const P = (dx, dy) => [O[0] + dx, O[1] + dy, O[2]];

const pts = {
  laneLeft: P(-HALF, 0),
  laneRight: P(HALF, 0),
  spanLabelL: P(-HALF, 2.5),
  spanLabelR: P(HALF, 2.5),
  spanCaption: P(0, -2.3),
  railTop: P(-HALF, RAIL),
  railBot: P(-HALF, -RAIL),
  qualityBlk: P(-HALF + (155 / 180) * LEN, -RAIL),
  processBlk: P(-HALF + (155 / 180 - 24.5 / 180) * LEN, RAIL),
  priorBlk: P(-HALF + (35 / 180) * LEN, -RAIL),
  tick0: P(-HALF, -RAIL - 1.05),
  tick3: P(HALF, -RAIL - 1.05),
  archTop: [-6, 26.5, -44],
  archBot: [-6, 2, -44],
};

const fov = Number(process.argv[2] ?? 44);
// As shipped — see the two scene-07 beats in state/scenes.js.
report('delay', [-13, 19.5, -6], [-13, 15.5, -30], fov, pts);
report('align', [-12, 18.6, -4], [-13.6, 15.4, -30], fov, pts);
