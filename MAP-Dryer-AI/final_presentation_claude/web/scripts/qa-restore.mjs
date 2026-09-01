/**
 * Proves the WebGL context-restoration path.
 *
 * A lost graphics context is the single most likely way this film dies in front
 * of a jury — a driver reset, an external display being re-plugged, a laptop
 * switching GPUs on battery. The recovery is claimed in App.jsx and in
 * useShow.renderEpoch, and a claim that is never exercised is a claim.
 *
 * This walks the show to a mid-film step, records what is on screen, kills the
 * context through WEBGL_lose_context, restores it, and asserts that:
 *
 *   1. the presenter's step did not move (no restart from scene 1);
 *   2. the camera pose came back — position, target and focal length;
 *   3. every presence channel came back, so the world is dressed exactly as it
 *      was rather than sitting at its default pose;
 *   4. the PMREM studio environment was regenerated (a restored context hands
 *      it back EMPTY, which renders every metal surface black);
 *   5. the post-processing / AO rig was rebuilt;
 *   6. the page is still drawing frames afterwards.
 *
 *   node scripts/qa-restore.mjs [--scene 10] [--beat 0]
 */

import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const SCENE = Number(args[args.indexOf('--scene') + 1] || 10) - 1;
const BEAT = Number(args[args.indexOf('--beat') + 1] || 0);

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function freePort() {
  return new Promise((res, rej) => {
    const s = createServer();
    s.on('error', rej);
    s.listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => res(port)); });
  });
}

const snapshot = () => ({
  step: window.__STEP__,
  cam: window.__CAM__,
  channels: window.__CHANNELS__?.() ?? {},
  ao: window.__AO__?.on ?? false,
  env: Boolean(window.__ENV__?.ready),
  envEpoch: window.__ENV__?.epoch ?? -1,
  aoEpoch: window.__AO__?.epoch ?? -1,
});

function compareChannels(a, b) {
  const bad = [];
  for (const k of Object.keys(a)) {
    // The camera breathes and several channels are mid-tween by design; the
    // question is whether the world came back DRESSED, not whether it came
    // back to four decimal places.
    if (Math.abs((b[k] ?? 0) - a[k]) > 0.02) bad.push(`${k}: ${a[k]} -> ${b[k] ?? 'MISSING'}`);
  }
  for (const k of Object.keys(b)) if (!(k in a)) bad.push(`${k}: NEW after restore`);
  return bad;
}

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
      '--window-size=1600,900', '--window-position=-4000,0', '--hide-scrollbars',
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 900 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });

  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForFunction(() => !document.querySelector('.boot__start')?.disabled, { timeout: 60000 });
  await page.click('.boot__start');
  await sleep(2200);

  // Reach the step by RANDOM ACCESS rather than by walking to it.
  //
  // This matters for what the test is able to prove. A restore puts the world
  // into the settled state of the current step, which is exactly what a
  // number-key jump does — so arriving the same way means any difference across
  // the loss is a genuine restore defect rather than the two paths disagreeing
  // about what "settled" means. Walking there instead leaves a dozen channels
  // belonging to hidden layers still drifting down from earlier scenes, and the
  // comparison drowns in false failures.
  //
  // G then a key: 1-9, 0, q, w, x, c map to scenes 01-14.
  const SCENE_KEY = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'q', 'w', 'x', 'c'];
  await page.keyboard.press('g');
  await sleep(120);
  await page.keyboard.press(SCENE_KEY[SCENE]);
  await sleep(600);
  for (let i = 0; i < BEAT; i += 1) {
    await page.keyboard.press('ArrowRight');
    await sleep(400);
  }
  // Let the step SETTLE before the baseline is taken. This matters: a restore
  // deliberately puts the world into the settled state of the step the presenter
  // is on, rather than freezing it wherever a half-finished tween happened to
  // be. Snapshotting mid-transition and then asserting equality would fail on
  // exactly the behaviour that is correct — the first run of this test reported
  // nineteen "lost" channels, every one of which was a value still travelling
  // down from the previous scene.
  await sleep(13000);

  const rafRate = async () => page.evaluate(async () => {
    const t0 = performance.now();
    let n = 0;
    await new Promise((res) => {
      const tick = () => { n += 1; if (performance.now() - t0 > 900) res(); else requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
    });
    return n;
  });

  const before = await page.evaluate(snapshot);
  // Frame rate BEFORE the loss, as the baseline for the frame rate after it.
  // An absolute threshold is not sound here: this harness runs headful in a
  // window parked off-screen at x = -4000 so it cannot steal focus, and Chrome
  // throttles requestAnimationFrame for a window it believes is not visible.
  // The question the test can honestly answer is whether the restored context
  // is drawing at the rate the same page drew at a moment earlier.
  const aliveBefore = await rafRate();
  console.log(`\nBEFORE  step=${before.step}  cam=${JSON.stringify(before.cam?.pos)}  fov=${before.cam?.fov}`);
  console.log(`        channels=${Object.keys(before.channels).length}  ao=${before.ao}  env=${before.env}`
    + `  epochs env/ao=${before.envEpoch}/${before.aoEpoch}`);

  // --- kill it -------------------------------------------------------------
  const lost = await page.evaluate(() => {
    const ctx = window.__GL__?.getContext();
    const ext = ctx?.getExtension('WEBGL_lose_context');
    if (!ext) return false;
    window.__LOSTAT__ = performance.now();
    ext.loseContext();
    setTimeout(() => ext.restoreContext(), 350);
    return true;
  });
  if (!lost) { console.log('WEBGL_lose_context unavailable — cannot test'); await browser.close(); server.kill(); process.exit(2); }

  console.log('\n  context lost, restore requested…');
  await page.waitForFunction(
    () => !document.querySelector('.recover'),
    { timeout: 15000 }
  ).catch(() => console.log('  ! recovery notice never cleared'));
  await sleep(2500);

  const after = await page.evaluate(snapshot);
  console.log(`AFTER   step=${after.step}  cam=${JSON.stringify(after.cam?.pos)}  fov=${after.cam?.fov}`);
  console.log(`        channels=${Object.keys(after.channels).length}  ao=${after.ao}  env=${after.env}`
    + `  epochs env/ao=${after.envEpoch}/${after.aoEpoch}`);

  const alive = await rafRate();

  const camDrift = before.cam && after.cam
    ? Math.max(...before.cam.pos.map((v, i) => Math.abs(v - after.cam.pos[i])))
    : Infinity;
  const chanBad = compareChannels(before.channels, after.channels);

  const checks = [
    ['step preserved (no restart)', after.step === before.step, `${before.step} -> ${after.step}`],
    ['camera pose restored (<=0.5 u incl. idle drift)', camDrift <= 0.5, `max axis drift ${camDrift.toFixed(3)} u`],
    ['focal length restored', Math.abs((before.cam?.fov ?? 0) - (after.cam?.fov ?? -1)) < 0.05, `${before.cam?.fov} -> ${after.cam?.fov}`],
    ['all presence channels restored', chanBad.length === 0, chanBad.length ? chanBad.join('; ') : `${Object.keys(after.channels).length} channels within 0.02`],
    ['studio environment regenerated', after.env && after.envEpoch > before.envEpoch, `epoch ${before.envEpoch} -> ${after.envEpoch}`],
    ['AO / post rig rebuilt', after.ao === before.ao && after.aoEpoch > before.aoEpoch, `epoch ${before.aoEpoch} -> ${after.aoEpoch}`],
    ['still rendering at the pre-loss rate', alive >= aliveBefore * 0.6 && alive > 12,
      `${aliveBefore} -> ${alive} frames in 0.9 s`],
    ['no page errors', errors.length === 0, errors.slice(0, 3).join(' | ') || 'none'],
  ];

  console.log('');
  let failed = 0;
  for (const [name, ok, detail] of checks) {
    if (!ok) failed += 1;
    console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(48)} ${detail}`);
  }
  console.log(`\n${failed === 0 ? 'CONTEXT RESTORATION OK' : `${failed} CHECK(S) FAILED`}`);

  await browser.close();
  server.kill();
  process.exit(failed === 0 ? 0 : 1);
}

main().catch((e) => { console.error(e); process.exit(1); });
