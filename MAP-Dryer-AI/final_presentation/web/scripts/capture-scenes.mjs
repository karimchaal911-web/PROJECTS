/**
 * Renders the built presentation in headless Chrome and captures one still per
 * presenter step, plus a console-error report.
 *
 * Used for the visual QA pass and to produce the PDF/PPTX fallback source
 * frames, so the static deliverables are literally the same experience.
 *
 *   node scripts/capture-scenes.mjs [--out ../exports/screenshots] [--settle 5200]
 */

import { spawn } from 'node:child_process';
import { mkdir, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import puppeteer from 'puppeteer-core';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
const argOf = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const OUT = path.resolve(ROOT, argOf('out', '../exports/screenshots'));
const SETTLE = Number(argOf('settle', 9000));
const WIDTH = Number(argOf('width', 1920));
const HEIGHT = Number(argOf('height', 1080));

const SAFE = args.includes('--safe');
const OFFLINE = args.includes('--offline');

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find((p) => existsSync(p));

/** Ask the OS for a free port rather than colliding with a stale preview. */
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

async function startServer(PORT) {
  // Not `npx vite preview`: on Windows that is a shim which exits at once and
  // leaves the real server running detached, so the harness cannot stop what it
  // started. Orphaned preview servers then hold the ports the next run needs.
  const proc = spawn(process.execPath, [path.join(ROOT, 'scripts/serve.mjs'), String(PORT)],
    { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('static server did not start')), 30000);
    proc.stdout.on('data', (d) => {
      if (String(d).includes('READY')) { clearTimeout(timer); resolve(); }
    });
    proc.stderr.on('data', (d) => process.stderr.write(String(d)));
  });
  return proc;
}

async function main() {
  if (!CHROME) throw new Error('No Chrome or Edge executable found.');
  await rm(OUT, { recursive: true, force: true });
  await mkdir(OUT, { recursive: true });

  const PORT = await freePort();
  const server = await startServer(PORT);
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: [
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--hide-scrollbars',
      '--disable-lcd-text',
      `--window-size=${WIDTH},${HEIGHT}`,
      '--force-device-scale-factor=1',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });

  const errors = [];

  // Offline proof: block every request that is not loopback. If the
  // presentation needs the network for anything — a font fallback, a CDN
  // script, a texture — it will fail here rather than in the room.
  if (OFFLINE) {
    await page.setRequestInterception(true);
    page.on('request', (req) => {
      const url = req.url();
      const local = url.startsWith('http://127.0.0.1')
        || url.startsWith('http://localhost')
        || url.startsWith('data:')
        || url.startsWith('blob:');
      if (local) { req.continue(); return; }
      errors.push(`BLOCKED EXTERNAL REQUEST: ${url}`);
      req.abort();
    });
  }
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(`console.error: ${m.text()}`);
    if (m.type() === 'warning' && /THREE|WebGL/i.test(m.text())) errors.push(`warn: ${m.text()}`);
  });
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
  page.on('requestfailed', (r) => errors.push(`requestfailed: ${r.url()}`));
  page.on('response', (r) => { if (r.status() >= 400) errors.push(`http ${r.status()}: ${r.url()}`); });

  // `degrade=off` stops the auto-degrade guard from firing. This harness runs
  // through SwiftShader, which is slow enough to trip the guard honestly, so
  // every "standard" capture used to be a safe-mode capture wearing the wrong
  // label. `capture=1` hides presenter-only chrome that is not part of the
  // audience frame.
  const q = `?capture=1${SAFE ? '' : '&degrade=off'}`;
  await page.goto(`http://127.0.0.1:${PORT}/${q}`, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.waitForFunction(
    () => !document.querySelector('.boot__start')?.disabled,
    { timeout: 60000 }
  );

  if (SAFE) await page.keyboard.press('s');
  await page.click('.boot__start');
  await new Promise((r) => setTimeout(r, 2000));

  const steps = await page.evaluate(() => {
    // Read the step table straight out of the bundle's module graph via the
    // rail: number of scenes and beats is derivable from the DOM.
    return window.__STEPS__ ?? null;
  });

  const total = steps ?? 34; // fallback: walk until the rail stops changing
  const manifest = [];
  let lastLabel = '';
  let stall = 0;

  for (let i = 0; i < total; i += 1) {
    await new Promise((r) => setTimeout(r, SETTLE));

    const info = await page.evaluate(() => {
      const n = document.querySelector('.rail__n')?.textContent ?? '??';
      const dots = document.querySelectorAll('.rail__beats i').length;
      const on = document.querySelectorAll('.rail__beats i.on').length;
      const hero = [...document.querySelectorAll('.hero__line')].map((e) => e.textContent).join(' / ');
      const eyebrow = document.querySelector('.eyebrow')?.textContent ?? '';
      return { n, dots, on, hero, eyebrow };
    });

    const label = `${info.n}-${info.on}`;
    if (label === lastLabel) {
      stall += 1;
      if (stall > 1) break;
    } else {
      stall = 0;
    }
    lastLabel = label;

    const name = `step-${String(i).padStart(2, '0')}_scene-${info.n}_beat-${info.on || 1}.png`;
    await page.screenshot({ path: path.join(OUT, name), type: 'png' });
    manifest.push({ index: i, file: name, ...info });
    process.stdout.write(`  captured ${name}  ${info.hero.slice(0, 52)}\n`);

    await page.keyboard.press('ArrowRight');
  }

  // The mode that actually ran, not the one that was requested.
  const ranSafe = await page.evaluate(() => Boolean(window.__SAFE__));
  if (ranSafe !== SAFE) errors.push(`mode drift: requested safe=${SAFE}, ran safe=${ranSafe}`);

  await writeFile(
    path.join(OUT, 'manifest.json'),
    JSON.stringify({
      capturedAt: new Date().toISOString(),
      width: WIDTH, height: HEIGHT,
      safeRequested: SAFE, safeActual: ranSafe,
      steps: manifest, errors,
    }, null, 2)
  );

  console.log(`\n${manifest.length} stills → ${OUT}`);
  if (errors.length) {
    console.log(`\n${errors.length} console problem(s):`);
    for (const e of [...new Set(errors)].slice(0, 25)) console.log(`  ${e}`);
  } else {
    console.log('\nNo console errors.');
  }

  await browser.close();
  server.kill();
  process.exit(errors.some((e) => e.startsWith('pageerror')) ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
