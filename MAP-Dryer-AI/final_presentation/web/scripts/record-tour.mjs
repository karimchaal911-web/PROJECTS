import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const baseUrl = process.env.PRESENTATION_URL || 'http://127.0.0.1:8765/';
const executablePath = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const frameRate = Number(process.env.RECORD_FPS || 15);
const pace = Number(process.env.RECORD_PACE || 0.52);
const safe = process.env.RECORD_SAFE !== '0';
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
const frameDir = process.env.RECORD_FRAME_DIR || path.resolve(scriptDir, `../../tmp/cinematic_frames_${stamp}`);

await fs.mkdir(frameDir, { recursive: true });

const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 },
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

const url = new URL(baseUrl);
url.searchParams.set('scene', '1');
url.searchParams.set('auto', '0');
url.searchParams.set('film', '1');
url.searchParams.set('pace', String(pace));
if (safe) url.searchParams.set('safe', '1');

await page.goto(url.toString(), { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForFunction(() => window.__PRESENTATION_READY__ === true, { timeout: 45000 });

const client = await page.createCDPSession();
let latestFrame = null;
let receivedFrames = 0;
client.on('Page.screencastFrame', (payload) => {
  latestFrame = Buffer.from(payload.data, 'base64');
  receivedFrames += 1;
  void client.send('Page.screencastFrameAck', { sessionId: payload.sessionId });
});

await client.send('Page.startScreencast', {
  format: 'jpeg',
  quality: 84,
  maxWidth: 1920,
  maxHeight: 1080,
  everyNthFrame: 1
});

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
const startTime = Date.now();
const interval = 1000 / frameRate;
let nextTick = startTime;
let frameNumber = 0;
let directorState = null;

while (!latestFrame) await delay(20);
await page.evaluate(() => window.__director.play());

try {
  while (Date.now() - startTime < 150000) {
    frameNumber += 1;
    const filename = `frame-${String(frameNumber).padStart(6, '0')}.jpg`;
    await fs.writeFile(path.join(frameDir, filename), latestFrame);

    if (frameNumber % frameRate === 0) {
      directorState = await page.evaluate(() => window.__director.getState());
      if (directorState.completed) break;
    }

    nextTick += interval;
    await delay(Math.max(0, nextTick - Date.now()));
  }
} finally {
  await client.send('Page.stopScreencast').catch(() => undefined);
  await browser.close();
}

const durationSeconds = (Date.now() - startTime) / 1000;
process.stdout.write(`${JSON.stringify({ frameDir, frameRate, pace, safe, frameNumber, receivedFrames, durationSeconds, directorState, errors }, null, 2)}\n`);
if (!directorState?.completed || errors.length) process.exitCode = 2;
