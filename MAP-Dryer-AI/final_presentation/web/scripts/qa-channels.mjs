/**
 * Does random access land the world where the ordinary path lands it?
 *
 * The show has two ways of reaching a settled step. The presenter's arrow key
 * plays `buildTransition`, which animates channels into place. A number-key
 * jump — and a WebGL context restore — instead SETS them from
 * `sceneChannelState`. Those two tables were written at different times, and
 * nothing had ever compared them.
 *
 * This walks the film one step at a time, lets each step settle, and diffs the
 * live channel values against what a jump to the same step would produce. A
 * disagreement means the film looks different depending on how you got there —
 * which is exactly the failure a presenter hits when they jump back to answer a
 * question, and exactly what a context loss reproduces.
 *
 *   node scripts/qa-channels.mjs [--hold 4200]
 */
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const HOLD = Number(args[args.indexOf('--hold') + 1] || 4200);
const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const freePort = () => new Promise((res, rej) => {
  const s = createServer();
  s.on('error', rej);
  s.listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => res(port)); });
});

// Channels whose owning layer is not on screen at the step in question do not
// change what the audience sees, so a disagreement there is noise rather than a
// defect. This is the map from a channel to the layer that reads it.
const OWNER = {
  chainHead: 'chain', straighten: 'granules', flowSpeed: 'granules', granuleSize: 'granules',
  dryerWire: 'internals', axisDraw: 'axis', labRise: 'lab', traceDraw: 'trace',
  sensorReveal: 'sensors', sensorChips: 'sensors', packetFlow: 'packets',
  archBuild: 'arch', archLabels: 'arch', alignPause: 'arch',
  residenceTravel: 'residence', residenceRails: 'residence', residenceAlign: 'residence',
  laneSplit: 'packets', laneFocus: 'lanes',
  manifoldReveal: 'manifold', supportReveal: 'manifold', supportFocus: 'manifold', trajectory: 'manifold',
  evidence: 'evidence', evidenceBeat: 'evidence', evidencePoints: 'evidence',
  dashAssemble: 'dashboard', dashPage: 'dashboard', dashHighlight: 'dashboard',
  artifactCard: 'handover', artifactFold: 'handover', serviceLive: 'handover', inferStream: 'handover',
  runtimeReveal: 'runtime', runtimePath: 'runtime', operatorReveal: 'runtime', loopClose: 'packets',
  ringReveal: 'ring', ringTravel: 'ring',
  roadmapToday: 'roadmap', roadmapNext: 'roadmap',
  materialReveal: 'material',
};

async function main() {
  const port = await freePort();
  const server = spawn('node', [path.join(ROOT, 'scripts/serve.mjs'), String(port)],
    { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
  await new Promise((r) => server.stdout.on('data', (d) => String(d).includes('READY') && r()));

  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: false, defaultViewport: null,
    args: [
      '--disable-background-timer-throttling',
      '--disable-backgrounding-occluded-windows',
      '--disable-renderer-backgrounding',
      '--window-size=1280,720', '--window-position=-4000,0', '--hide-scrollbars',
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto(`http://127.0.0.1:${port}/?degrade=off`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForFunction(() => !document.querySelector('.boot__start')?.disabled, { timeout: 60000 });
  await page.evaluate((o) => { window.__OWNER__ = o; }, OWNER);
  await page.click('.boot__start');
  await sleep(2500);

  const steps = await page.evaluate(() => window.__STEPS__);
  const rows = [];
  for (let i = 0; i < steps; i += 1) {
    await sleep(HOLD);
    const r = await page.evaluate(() => {
      const live = window.__CHANNELS__();
      const step = window.__STEP__;
      const { scene, beat } = window.__STEPTABLE__[step];
      const want = window.__SETTLED__(scene, beat);
      const layers = window.__LAYERS__(step);
      const owner = window.__OWNER__;
      const bad = [];
      for (const k of Object.keys(want)) {
        if (Math.abs((live[k] ?? 0) - want[k]) <= 0.02) continue;
        const lname = owner[k];
        const layer = lname === undefined ? null : (layers[lname] ?? 0);
        bad.push({ k, live: +(live[k] ?? 0).toFixed(3), want: want[k], layer });
      }
      return { step, scene, beat, bad };
    });
    rows.push(r);
    if (i < steps - 1) await page.keyboard.press('ArrowRight');
  }

  let visible = 0;
  let hidden = 0;
  for (const r of rows) {
    const vis = r.bad.filter((b) => b.layer === null || b.layer > 0.02);
    const hid = r.bad.length - vis.length;
    hidden += hid;
    visible += vis.length;
    if (vis.length) {
      console.log(`  step ${String(r.step).padStart(2)}  scene ${String(r.scene + 1).padStart(2)}.${r.beat + 1}  `
        + vis.map((b) => `${b.k}: settled ${b.live} vs jump ${b.want} (layer ${b.layer})`).join('; '));
    }
  }
  console.log(`\n${visible} disagreement(s) on a VISIBLE layer`);
  console.log(`${hidden} on hidden layers (no visual consequence)`);
  await browser.close();
  server.kill();
  process.exit(visible === 0 ? 0 : 1);
}
main().catch((e) => { console.error(e); process.exit(1); });
