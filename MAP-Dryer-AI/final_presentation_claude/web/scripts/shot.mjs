/**
 * Capture named steps only, so a single scene can be iterated on without
 * walking the whole film.
 *
 *   node scripts/shot.mjs 29 30 31        (step indices)
 *   node scripts/shot.mjs --safe 29
 *   node scripts/shot.mjs --out ../exports/wip 12
 */
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import puppeteer from 'puppeteer-core';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const argOf = (n, d) => { const i = args.indexOf(`--${n}`); return i >= 0 && args[i + 1] ? args[i + 1] : d; };
const OUT = path.resolve(ROOT, argOf('out', '../exports/wip'));
const SETTLE = Number(argOf('settle', 5200));
const SAFE = args.includes('--safe');
// Extra query string, appended verbatim. Used to shoot the same steps with a
// render feature on and off — `--q ao=off` — so a change can be compared
// against itself rather than against a remembered frame.
const EXTRA = argOf('q', '');
const WANT = args.filter((a) => /^\d+$/.test(a)).map(Number);

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find((p) => existsSync(p));

const freePort = () => new Promise((res, rej) => {
  const s = createServer();
  s.on('error', rej);
  s.listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => res(port)); });
});

const PORT = await freePort();
// `npx.cmd vite preview` is a shim: it exits immediately and leaves the real
// server running detached, so `server.kill()` never stopped it. Seven orphaned
// preview servers and thirty-four headless Chromes accumulated across a single
// afternoon of iteration, and the next run then failed to bind. serve.mjs is
// one node process that this script actually owns.
const server = spawn(process.execPath, [path.join(ROOT, 'scripts/serve.mjs'), String(PORT)],
  { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
await new Promise((res, rej) => {
  const t = setTimeout(() => rej(new Error('static server did not start')), 30000);
  server.stdout.on('data', (d) => { if (String(d).includes('READY')) { clearTimeout(t); res(); } });
});

await mkdir(OUT, { recursive: true });
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
    '--hide-scrollbars', '--disable-lcd-text', '--window-size=1920,1080', '--force-device-scale-factor=1'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('console', (m) => { if (m.type() === 'error') errors.push(`console: ${m.text().slice(0, 200)}`); });

await page.goto(`http://127.0.0.1:${PORT}/?capture=1${SAFE ? '' : '&degrade=off'}${EXTRA ? `&${EXTRA}` : ''}`, { waitUntil: 'networkidle0', timeout: 60000 });
await page.waitForFunction(() => !document.querySelector('.boot__start')?.disabled, { timeout: 60000 });
if (SAFE) await page.keyboard.press('s');
await page.click('.boot__start');
await new Promise((r) => setTimeout(r, 1600));

const total = await page.evaluate(() => window.__STEPS__);
const want = new Set(WANT.length ? WANT : [...Array(total).keys()]);
const maxWanted = Math.max(...want);

for (let i = 0; i <= maxWanted; i += 1) {
  const hit = want.has(i);
  await new Promise((r) => setTimeout(r, hit ? SETTLE : 900));
  if (hit) {
    const info = await page.evaluate(() => ({
      n: document.querySelector('.rail__n')?.textContent ?? '??',
      on: document.querySelectorAll('.rail__beats i.on').length,
      cam: window.__CAM__,
    }));
    const tag = EXTRA ? `_${EXTRA.replace(/[^a-z0-9]+/gi, '-')}` : '';
    const name = `shot-${String(i).padStart(2, '0')}_scene-${info.n}_beat-${info.on || 1}${SAFE ? '_safe' : ''}${tag}.png`;
    await page.screenshot({ path: path.join(OUT, name), type: 'png' });
    console.log(`  ${name}  cam=${JSON.stringify(info.cam?.pos)} fov=${info.cam?.fov}`);
  }
  if (i < maxWanted) await page.keyboard.press('ArrowRight');
}
console.log(errors.length ? `\nPROBLEMS:\n${[...new Set(errors)].join('\n')}` : '\nNo console errors.');
await browser.close(); server.kill(); process.exit(0);
