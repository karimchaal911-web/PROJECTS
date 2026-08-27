import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const baseUrl = process.env.PRESENTATION_URL || 'http://127.0.0.1:8765/';
const executablePath = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const screenshotPath = path.resolve(scriptDir, '../../exports/screenshots/safe-mode-1366x768.png');

const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  defaultViewport: { width: 1366, height: 768, deviceScaleFactor: 1 },
  args: ['--no-first-run', '--hide-scrollbars', '--enable-webgl', '--ignore-gpu-blocklist', '--disable-gpu']
});

const errors = [];
const page = await browser.newPage();
page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
page.on('console', (message) => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });

const makeUrl = (query) => {
  const url = new URL(baseUrl);
  for (const [key, value] of Object.entries(query)) url.searchParams.set(key, String(value));
  return url.toString();
};

await page.goto(makeUrl({ scene: 1, auto: 1, pace: 0.35, safe: 1 }), { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForFunction(() => window.__PRESENTATION_READY__ === true, { timeout: 45000 });
const bootState = await page.evaluate(() => ({
  scene: document.body.dataset.scene,
  fallbackHidden: document.querySelector('#fallback').hidden,
  canvas: { width: document.querySelector('canvas').width, height: document.querySelector('canvas').height },
  stats: window.__director.stats,
  state: window.__director.getState()
}));

await page.waitForFunction(() => window.__director.getState().sceneIndex >= 1, { timeout: 12000 });
await page.evaluate(() => window.__director.pause());
const pauseA = await page.evaluate(() => window.__director.getState());
await new Promise((resolve) => setTimeout(resolve, 900));
const pauseB = await page.evaluate(() => window.__director.getState());
await page.evaluate(() => window.__director.play());
await new Promise((resolve) => setTimeout(resolve, 350));
const resumed = await page.evaluate(() => window.__director.getState());

await page.goto(makeUrl({ shot: 15, capture: 1, safe: 1 }), { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForFunction(() => window.__PRESENTATION_READY__ === true, { timeout: 45000 });
await fs.mkdir(path.dirname(screenshotPath), { recursive: true });
await page.screenshot({ path: screenshotPath, type: 'png', captureBeyondViewport: false });

await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
await page.goto(makeUrl({ scene: 4, auto: 0, safe: 1 }), { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForFunction(() => window.__PRESENTATION_READY__ === true, { timeout: 45000 });
const reducedState = await page.evaluate(() => ({
  reducedClass: document.body.classList.contains('reduced-motion'),
  state: window.__director.getState(),
  scene: document.body.dataset.scene
}));

await browser.close();

const pausedStable = pauseA.sceneIndex === pauseB.sceneIndex && Math.abs(pauseA.holdProgress - pauseB.holdProgress) < 0.01;
const report = {
  bootState,
  autoplayAdvanced: pauseA.sceneIndex >= 1,
  pausedStable,
  resumed: resumed.autoplay === true,
  reducedState,
  screenshotPath,
  errors
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (!bootState.fallbackHidden || !report.autoplayAdvanced || !pausedStable || !report.resumed || !reducedState.reducedClass || errors.length) process.exitCode = 2;
