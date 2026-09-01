/**
 * The handover corridor, checked at four points along the scene-10 arrival.
 *
 * The beat opens nine units further back and settles onto the scene's own pose,
 * so everything in the corridor GROWS through the shot: an object placed for the
 * frame it starts in is a different size by the time the shot lands. The first
 * placement was already past the copy column and the frame edge by the time it
 * folded.
 *
 *   node scripts/_probe_handover.mjs
 */
import { report } from './_frame.mjs';

const W = 26, H = 14.625;
const pts = {
  cardC: [72, 9.4, 42],
  cardTL: [72 - 4.0, 9.4 + 2.4, 42],
  cardBR: [72 + 4.0, 9.4 - 2.4, 42],
  nodeC: [73.5, 9.1, 34],
  nodeTop: [73.5, 9.1 + 1.7 + 3.1, 34],
  nodeL: [73.5 - 1.7, 9.1, 34],
  nodeR: [73.5 + 1.7, 9.1, 34],
  sink: [72.5, 8.4, 26.4],
  planeTL: [76 - W / 2, 10 + H / 2, 26],
  planeBR: [76 + W / 2, 10 - H / 2, 26],
};

report('t=0.0  pulled back', [66, 11.2, 74], [66, 10, 26], 38, pts);
report('t=3.2  fold starts', [66, 10.45, 68.3], [66, 10, 26], 38, pts);
report('t=4.7  fold ends', [66, 10.14, 66.6], [66, 10, 26], 38, pts);
report('t=8.2  settled', [66, 10, 65], [66, 10, 26], 38, pts);
