/**
 * Records the emergency cinematic backup: one uninterrupted run of the whole
 * presentation, driven at rehearsal pace.
 *
 * Runs headful so the page renders on the real GPU — headless SwiftShader is
 * far too slow to record smooth motion. The window is positioned off-screen so
 * it does not steal focus while it works.
 *
 *   node scripts/record-tour.mjs [--fps 30] [--scale 1] [--pace 1]
 */

import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, rmSync, readdirSync, writeFileSync, statSync } from 'node:fs';
import { createServer } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';
import ffmpegPath from 'ffmpeg-static';
import { SCENES, TOTAL_SECONDS } from '../src/state/scenes.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const argOf = (n, d) => {
  const i = args.indexOf(`--${n}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : d;
};

const FPS = Number(argOf('fps', 25));
const PACE = Number(argOf('pace', 1)); // 1 = rehearsal pace
const WIDTH = 1920;
const HEIGHT = 1080;
// A run-scoped directory: two runs cleaning up the same folder raced and one
// failed with EPERM while the other was still deleting 18,000 files.
const FRAMES = path.join(ROOT, '..', 'exports', 'video', `frames-${Date.now()}`);
const OUT = path.join(ROOT, '..', 'FINAL_MAP_Soluble_Digitalization_Soutenance_Claude_Backup.mp4');

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);

/**
 * Seconds to hold each step, taken from the per-scene budgets in
 * speaker_notes/full_script.md and divided across that scene's beats.
 *
 * The backup is meant to be narrated over, so it runs at the scene table's own
 * declared pace — 790 s, 13 min 10 s — not at the pace the animation alone
 * would need.
 */
//
// DERIVED from the scene table, not transcribed from it. The hardcoded version
// still described fourteen scenes with 35 beats and the old durations, so the
// backup video would have held the wrong frame for the wrong length on almost
// every scene after cutting four beats and adding six.
const HOLD = Object.fromEntries(SCENES.map((sc) => {
  const n = sc.beats?.length || 1;
  const each = sc.seconds / n;
  // 05c is the 6.5 s constant-velocity gap travel: it must play out before the
  // frame is held, and it is the one moment the speaker is told not to talk over.
  return [sc.n, Array.from({ length: n }, (_, i) => Math.round(
    each + (sc.id === 'gap' && i === n - 1 ? 4 : 0)
  ))];
}));

async function freePort() {
  return new Promise((resolve, reject) => {
    const srv = createServer();
    srv.on('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

async function startServer(port) {
  const proc = spawn('npx.cmd', ['vite', 'preview', '--host', '127.0.0.1', '--port', String(port)],
    { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'], shell: true });
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('preview did not start')), 30000);
    proc.stdout.on('data', (d) => String(d).includes('Local') && (clearTimeout(t), resolve()));
  });
  return proc;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  if (!CHROME) throw new Error('No Chrome or Edge found.');
  mkdirSync(FRAMES, { recursive: true });

  const port = await freePort();
  const server = await startServer(port);

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: false,
    defaultViewport: null,
    args: [
      `--window-size=${WIDTH},${HEIGHT + 120}`,
      '--window-position=-4000,0',   // off-screen: do not steal the desktop
      '--hide-scrollbars',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-infobars',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });
  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0', timeout: 90000 });
  await page.waitForFunction(() => !document.querySelector('.boot__start')?.disabled, { timeout: 90000 });

  const client = await page.createCDPSession();
  let n = 0;
  let capturing = true;

  // Written synchronously and in order: an async write queue left gaps in the
  // numbering, and ffmpeg's image2 demuxer stops at the first gap, which is why
  // the first attempt produced a 17 KB file.
  client.on('Page.screencastFrame', ({ data, sessionId }) => {
    if (capturing) {
      writeFileSync(path.join(FRAMES, `f${String(n).padStart(6, '0')}.jpg`),
        Buffer.from(data, 'base64'));
      n += 1;
    }
    client.send('Page.screencastFrameAck', { sessionId }).catch(() => {});
  });

  // Chrome renders far above 25 fps here; take every third frame so the frame
  // budget stays sane and the capture rate lands near the target.
  await client.send('Page.startScreencast', {
    format: 'jpeg', quality: 80, maxWidth: WIDTH, maxHeight: HEIGHT, everyNthFrame: 4,
  });

  const t0 = Date.now();
  await page.click('.boot__start');

  const steps = await page.evaluate(() => window.__STEPS__ ?? 35);
  console.log(`recording ${steps} steps at ~${FPS} fps…`);

  for (let i = 0; i < steps; i += 1) {
    const info = await page.evaluate(() => ({
      n: document.querySelector('.rail__n')?.textContent ?? '01',
      on: document.querySelectorAll('.rail__beats i.on').length || 1,
    }));
    const hold = (HOLD[info.n]?.[info.on - 1] ?? 7) * PACE;
    process.stdout.write(`  scene ${info.n} beat ${info.on} — ${hold.toFixed(1)} s  (${n} frames)\n`);
    await sleep(hold * 1000);
    if (i < steps - 1) await page.keyboard.press('ArrowRight');
  }

  await sleep(2500); // let the closing frame breathe
  capturing = false;
  try { await client.send('Page.stopScreencast'); } catch { /* ignore */ }
  await sleep(400);
  await browser.close();
  server.kill();

  const count = readdirSync(FRAMES).length;
  const elapsed = (Date.now() - t0) / 1000;
  // Encode at the rate the frames were actually produced, so the backup plays
  // at the speed the presenter rehearsed rather than in slow motion. Encoding
  // 20k frames at a nominal 25 fps stretched a 4-minute run to 14 minutes.
  const realFps = Math.max(8, Math.min(60, count / elapsed));
  console.log(`\ncaptured ${count} frames over ${elapsed.toFixed(0)} s `
    + `→ encoding at ${realFps.toFixed(2)} fps`);

  const res = spawnSync(ffmpegPath, [
    '-y',
    '-framerate', realFps.toFixed(4),
    '-start_number', '0',
    '-i', path.join(FRAMES, 'f%06d.jpg'),
    '-c:v', 'libx264',
    '-preset', 'slow',
    '-crf', '20',
    '-pix_fmt', 'yuv420p',
    '-vf', `scale=${WIDTH}:${HEIGHT}:flags=lanczos`,
    '-movflags', '+faststart',
    OUT,
  ], { stdio: ['ignore', 'ignore', 'pipe'] });

  if (res.status !== 0) {
    console.error(String(res.stderr).slice(-3000));
    console.error(`Frames kept at ${FRAMES} for diagnosis.`);
    throw new Error('ffmpeg failed');
  }

  const mb = statSync(OUT).size / 1e6;
  if (mb < 1) {
    console.error(String(res.stderr).slice(-3000));
    console.error(`Suspiciously small output; frames kept at ${FRAMES}.`);
    throw new Error(`encode produced only ${mb.toFixed(3)} MB`);
  }
  console.log(`wrote ${path.basename(OUT)}  (${(elapsed / 60).toFixed(1)} min, ${mb.toFixed(1)} MB)`);
  rmSync(FRAMES, { recursive: true, force: true });
  process.exit(0);
}

main().catch((e) => { console.error(e); process.exit(1); });
