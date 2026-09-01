/**
 * Captures the two Power BI report pages, rendered by
 * tools/render_dashboard_preview.py from the LIVE PostgreSQL views, into the
 * textures the scene 10/11 dashboard plane uses.
 *
 * Nothing here styles or edits the report: it screenshots the deterministic
 * 1600x900 page at deviceScaleFactor 2, so the dashboard's own body text
 * survives being mapped onto a plane in a 1080-line projection.
 *
 *   1. run the replay so the views hold a fresh, meaningful state
 *   2. python tools/render_dashboard_preview.py
 *   3. node scripts/capture-dashboard.mjs
 */
import puppeteer from 'puppeteer-core';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const WEB = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ROOT = path.resolve(WEB, '..', '..');
const OUT = path.join(WEB, 'public', 'img');

const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);

const JOBS = [
  ['POWERBI DASHBOARD/preview/preview_page1_overview.html', 'powerbi_overview.png'],
  ['POWERBI DASHBOARD/preview/preview_page2_diagnostics.html', 'powerbi_diagnostics.png'],
];

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new', args: ['--hide-scrollbars'],
});

for (const [src, name] of JOBS) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1760, height: 1000, deviceScaleFactor: 2 });
  const url = pathToFileURL(path.join(ROOT, src)).href;
  await page.goto(url, { waitUntil: 'networkidle0' });
  // The page carries a default body margin; zero it so the clip is the
  // exact 1600x900 report canvas and the UV map below stays truthful.
  await page.evaluate(() => { document.body.style.margin = '0'; });
  const el = await page.$('.canvas');
  const box = await el.boundingBox();
  await page.screenshot({
    path: path.join(OUT, name),
    clip: { x: box.x, y: box.y, width: box.width, height: box.height },
  });
  console.log(`${name}  ${box.width}x${box.height} css -> ${box.width * 2}x${box.height * 2} px`);
  await page.close();
}

await browser.close();
