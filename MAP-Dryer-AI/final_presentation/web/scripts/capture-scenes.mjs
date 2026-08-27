import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const args = new Set(process.argv.slice(2));
const safe = args.has('--safe');
const width = Number(process.env.CAPTURE_WIDTH || 1920);
const height = Number(process.env.CAPTURE_HEIGHT || 1080);
const baseUrl = process.env.PRESENTATION_URL || 'http://127.0.0.1:8765/';
const outputDir = process.env.CAPTURE_OUTPUT || path.resolve(scriptDir, '../../exports/screenshots');
const executablePath = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const sceneNumbers = process.env.CAPTURE_SCENES
  ? process.env.CAPTURE_SCENES.split(',').map((value) => Number(value.trim())).filter((value) => value >= 1 && value <= 15)
  : Array.from({ length: 15 }, (_, index) => index + 1);

await fs.mkdir(outputDir, { recursive: true });

const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  defaultViewport: { width, height, deviceScaleFactor: 1 },
  args: [
    '--no-first-run',
    '--no-default-browser-check',
    '--hide-scrollbars',
    '--font-render-hinting=none',
    '--enable-webgl',
    '--ignore-gpu-blocklist',
    ...(safe ? ['--disable-gpu'] : ['--use-angle=swiftshader'])
  ]
});

const page = await browser.newPage();
const errors = [];
page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
page.on('console', (message) => {
  if (message.type() === 'error') errors.push(`console: ${message.text()}`);
});

const results = [];
try {
  for (const scene of sceneNumbers) {
    const url = new URL(baseUrl);
    url.searchParams.set('shot', String(scene));
    url.searchParams.set('capture', '1');
    if (safe) url.searchParams.set('safe', '1');
    await page.goto(url.toString(), { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForFunction(() => window.__PRESENTATION_READY__ === true, { timeout: 45000 });
    await new Promise((resolve) => setTimeout(resolve, 260));
    const sceneState = await page.evaluate(() => ({
      id: document.body.dataset.scene,
      ready: document.documentElement.dataset.ready,
      fallbackHidden: document.querySelector('#fallback')?.hidden,
      stats: window.__director?.stats
    }));
    const filename = `scene-${String(scene).padStart(2, '0')}.png`;
    await page.screenshot({ path: path.join(outputDir, filename), type: 'png', captureBeyondViewport: false });
    results.push({ scene, filename, ...sceneState });
  }
} finally {
  await browser.close();
}

process.stdout.write(`${JSON.stringify({ safe, width, height, outputDir, errors, results }, null, 2)}\n`);
if (errors.length) process.exitCode = 2;
