/**
 * How much bigger could the Power BI page be without cropping it?
 *
 * The answer, recorded in qa/PRESENTATION_REMEDIATION_REPORT.md section 11.9, is
 * about 10 % of linear scale — and it costs a bespoke narrower copy column on two
 * beats plus the one-distance rule that exists because pushing in once cropped
 * the diagnosis and operator-guidance panels off the frame. It was not taken.
 * This script is the measurement the refusal rests on.
 *
 *   node scripts/_probe_pbi.mjs
 */
import { report } from './_frame.mjs';

const W = 26, H = 14.625, CX = 76, CY = 10, CZ = 26;
const px = (u) => CX - W / 2 + u * W;
const py = (v) => CY + H / 2 - v * H;

const pts = {
  planeL: [px(0), CY, CZ],
  planeR: [px(1), CY, CZ],
  planeT: [CX, py(0), CZ],
  planeB: [CX, py(1), CZ],
  diagnosisR: [px(1584 / 1600), py(218 / 900), CZ],
  diagnosisB: [px(1584 / 1600), py(884 / 900), CZ],
  predictedL: [px(110 / 1600), py(86 / 900), CZ],
  trendB: [px(110 / 1600), py(472 / 900), CZ],
};

report('assemble  AS SHIPPED', [65, 12, 66], [66, 11, 26], 38, pts);
report('assemble  candidate (rejected)', [65, 11.6, 62], [69.5, 11, 26], 38, pts);
report('diagnostics candidate (rejected)', [67, 8.4, 62], [69.5, 9.2, 26], 38, pts);
