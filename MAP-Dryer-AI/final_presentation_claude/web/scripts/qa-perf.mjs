/**
 * Measures real frame rate per scene on the GPU.
 *
 * Runs headful, because headless SwiftShader frame times say nothing about
 * what a projector laptop will do. Samples rAF deltas for a fixed window on
 * every step and reports mean / p95 / worst, plus the slowest single frame.
 *
 *   node scripts/qa-perf.mjs [--safe] [--hold 2600] [--q ao=off]
 *
 * `--q` appends a query string verbatim, which is how the cost of a single
 * render feature is isolated: the same build, the same host, the same walk,
 * measured with the feature on and off. Guessing at the cost of post-processing
 * from a frame-time budget is how a presentation ends up shipping a technique
 * nobody measured.
 */

import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const SAFE = args.includes('--safe');
const HOLD = Number(args[args.indexOf('--hold') + 1] || 2600);
const QI = args.indexOf('--q');
const EXTRA = QI >= 0 && args[QI + 1] ? `?${args[QI + 1]}` : '';

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);

async function freePort() {
  return new Promise((res, rej) => {
    const s = createServer();
    s.on('error', rej);
    s.listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => res(port)); });
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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
      '--window-size=1920,1080', '--window-position=-4000,0', '--hide-scrollbars',
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto(`http://127.0.0.1:${port}/${EXTRA}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForFunction(() => !document.querySelector('.boot__start')?.disabled, { timeout: 60000 });

  if (SAFE) await page.keyboard.press('s');
  await page.click('.boot__start');
  await sleep(2500);

  await page.evaluate(() => {
    window.__fps = { samples: [], on: false };
    let last = performance.now();
    const tick = (t) => {
      if (window.__fps.on) window.__fps.samples.push(t - last);
      last = t;
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  const steps = await page.evaluate(() => window.__STEPS__ ?? 35);
  const rows = [];

  for (let i = 0; i < steps; i += 1) {
    // Skip the transition itself; measure the settled state the audience holds on.
    await sleep(2400);
    await page.evaluate(() => { window.__fps.samples = []; window.__fps.on = true; });
    await sleep(HOLD);
    const r = await page.evaluate(() => {
      window.__fps.on = false;
      const s = window.__fps.samples.slice().sort((a, b) => a - b);
      const n = s.length;
      const scene = document.querySelector('.rail__n')?.textContent ?? '??';
      const beat = document.querySelectorAll('.rail__beats i.on').length || 1;
      if (!n) return { scene, beat, n: 0 };
      const mean = s.reduce((a, b) => a + b, 0) / n;
      return {
        scene, beat, n,
        meanFps: 1000 / mean,
        p95Ms: s[Math.floor(n * 0.95)],
        worstMs: s[n - 1],
      };
    });
    rows.push(r);
    console.log(`  scene ${r.scene} beat ${r.beat}  mean ${(r.meanFps ?? 0).toFixed(1)} fps` +
      `  p95 ${(r.p95Ms ?? 0).toFixed(1)} ms  worst ${(r.worstMs ?? 0).toFixed(1)} ms`);
    if (i < steps - 1) await page.keyboard.press('ArrowRight');
  }

  const valid = rows.filter((r) => r.n > 0);
  const mean = valid.reduce((a, r) => a + r.meanFps, 0) / valid.length;
  const worstScene = valid.slice().sort((a, b) => a.meanFps - b.meanFps)[0];
  const worstFrame = valid.slice().sort((a, b) => b.worstMs - a.worstMs)[0];

  console.log(`\nMODE            ${SAFE ? 'SAFE' : 'STANDARD'}`);
  console.log(`mean across all ${mean.toFixed(1)} fps`);
  console.log(`slowest scene   ${worstScene.scene}.${worstScene.beat} at ${worstScene.meanFps.toFixed(1)} fps`);
  console.log(`worst frame     ${worstFrame.worstMs.toFixed(1)} ms in scene ${worstFrame.scene}.${worstFrame.beat}`);
  console.log(`scenes < 50 fps ${valid.filter((r) => r.meanFps < 50).map((r) => `${r.scene}.${r.beat}`).join(', ') || 'none'}`);
  console.log(`scenes < 30 fps ${valid.filter((r) => r.meanFps < 30).map((r) => `${r.scene}.${r.beat}`).join(', ') || 'none'}`);

  await browser.close();
  server.kill();
  process.exit(0);
}

main().catch((e) => { console.error(e); process.exit(1); });
