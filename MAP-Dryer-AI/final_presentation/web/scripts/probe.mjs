/** Quick diagnostic: walk to a step and report the actual camera pose. */
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const STEP = Number(process.argv[2] ?? 19);

async function freePort() {
  return new Promise((resolve, reject) => {
    const srv = createServer();
    srv.on('error', reject);
    srv.listen(0, '127.0.0.1', () => { const { port } = srv.address(); srv.close(() => resolve(port)); });
  });
}

const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);

const PORT = await freePort();
const server = spawn('npx.cmd', ['vite', 'preview', '--host', '127.0.0.1', '--port', String(PORT)],
  { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'], shell: true });
await new Promise((r) => server.stdout.on('data', (d) => String(d).includes('Local') && r()));

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--window-size=1600,900'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 900 });
page.on('pageerror', (e) => console.log('PAGEERROR', e.message));
await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' });
await page.waitForFunction(() => !document.querySelector('.boot__start')?.disabled);
await page.click('.boot__start');
await new Promise((r) => setTimeout(r, 1500));
for (let i = 0; i < STEP; i += 1) {
  await page.keyboard.press('ArrowRight');
  await new Promise((r) => setTimeout(r, 260));
}
await new Promise((r) => setTimeout(r, 6000));
for (const t of [0, 1500, 3000]) {
  if (t) await new Promise((r) => setTimeout(r, 1500));
  const c = await page.evaluate(() => window.__CAM__);
  console.log('t+' + t, JSON.stringify(c));
}
const out = await page.evaluate(() => ({
  cam: window.__CAM__ ?? null,
  rail: document.querySelector('.rail__n')?.textContent,
  on: document.querySelectorAll('.rail__beats i.on').length,
  hero: [...document.querySelectorAll('.hero__line')].map((e) => e.textContent),
}));
console.log(JSON.stringify(out, null, 2));
await browser.close();
server.kill();
process.exit(0);
