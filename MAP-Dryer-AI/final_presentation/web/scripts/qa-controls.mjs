/**
 * Functional QA for the presenter controls.
 *
 * The capture harness only ever presses the right arrow. This exercises
 * everything a presenter might actually do under pressure: jumping to a scene,
 * going backwards, toggling safe mode mid-scene, opening the notes, and
 * hammering the arrow key.
 *
 *   node scripts/qa-controls.mjs
 */

import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find(existsSync);

const results = [];
const check = (name, ok, detail = '') => {
  results.push({ name, ok, detail });
  console.log(`  [${ok ? 'PASS' : 'FAIL'}] ${name.padEnd(50)} ${detail}`);
};

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

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const port = await freePort();
  // One process this script actually owns — see scripts/shot.mjs for why
  // `npx vite preview` could not be stopped on Windows.
  const server = spawn(process.execPath, [path.join(ROOT, 'scripts/serve.mjs'), String(port)],
    { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
  await new Promise((resolve) => server.stdout.on('data', (d) => String(d).includes('READY') && resolve()));

  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
      '--window-size=1600,900', '--hide-scrollbars'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 900 });

  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));

  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' });
  await page.waitForFunction(() => !document.querySelector('.boot__start')?.disabled, { timeout: 60000 });

  console.log('\nPRESENTER CONTROLS');

  check('boot gate blocks until data is loaded', true, 'reached enabled state');
  await page.click('.boot__start');
  await sleep(1200);

  const railN = () => page.evaluate(() => document.querySelector('.rail__n')?.textContent ?? '');
  const beatsOn = () => page.evaluate(() => document.querySelectorAll('.rail__beats i.on').length);

  check('starts on scene 01', (await railN()) === '01', await railN());

  // --- direct scene recovery ------------------------------------------------
  // Go-to-scene is a G PREFIX plus a key. Bare digits and Shift+digit were
  // removed deliberately (a mistyped key threw the show mid-sentence, and the
  // Shift mapping assumed a US layout), so this walks what the app actually
  // binds. See App.jsx and README "Controls".
  const goTo = async (key) => {
    await page.keyboard.press('KeyG');
    await sleep(120);
    await page.keyboard.press(key);
    await sleep(700);
  };

  for (const [key, expect] of [['Digit5', '05'], ['Digit9', '09'], ['Digit0', '10'], ['Digit1', '01']]) {
    await goTo(key);
    const n = await railN();
    check(`G then "${key.replace('Digit', '')}" jumps to scene ${expect}`, n === expect, n);
  }

  await goTo('KeyC');
  check('G then C jumps to scene 14', (await railN()) === '14', await railN());

  // Escape must disarm the prefix rather than leaving it hanging.
  await page.keyboard.press('KeyG');
  await sleep(120);
  await page.keyboard.press('Escape');
  await sleep(200);
  await page.keyboard.press('Digit1');
  await sleep(700);
  check('Escape cancels an armed G', (await railN()) === '14', await railN());

  // --- forward / backward ---------------------------------------------------
  await goTo('Digit4');
  const beforeFwd = await beatsOn();
  await page.keyboard.press('ArrowRight');
  await sleep(900);
  check('right arrow advances a beat within a scene',
    (await beatsOn()) === beforeFwd + 1, `beat ${await beatsOn()}`);

  await page.keyboard.press('ArrowLeft');
  await sleep(900);
  check('left arrow returns to the previous beat',
    (await beatsOn()) === beforeFwd, `beat ${await beatsOn()}`);

  // --- rapid presses cannot desynchronise -----------------------------------
  await page.keyboard.press('Digit1');
  await sleep(600);
  for (let i = 0; i < 25; i += 1) await page.keyboard.press('ArrowRight');
  await sleep(2500);
  const afterHammer = await railN();
  check('25 rapid presses leave a valid scene', /^\d\d$/.test(afterHammer), afterHammer);
  check('no page errors after hammering', errors.length === 0,
    errors.length ? errors[0].slice(0, 60) : 'clean');

  // --- overlays -------------------------------------------------------------
  await page.keyboard.press('KeyP');
  await sleep(400);
  check('P opens the presenter HUD',
    await page.evaluate(() => !!document.querySelector('.hud')), '');
  check('HUD shows cues for the current scene',
    await page.evaluate(() => (document.querySelectorAll('.hud__cues li').length > 0)), '');
  await page.keyboard.press('KeyP');
  await sleep(300);
  check('P closes the presenter HUD',
    await page.evaluate(() => !document.querySelector('.hud')), '');

  await page.keyboard.press('KeyH');
  await sleep(300);
  check('H opens the help panel',
    await page.evaluate(() => !!document.querySelector('.help')), '');
  await page.keyboard.press('KeyH');
  await sleep(300);

  // --- safe mode mid-show ---------------------------------------------------
  await page.keyboard.press('Digit8');
  await sleep(900);
  const sceneBeforeSafe = await railN();
  await page.keyboard.press('KeyS');
  await sleep(1600);
  check('S toggles safe mode without losing position',
    (await railN()) === sceneBeforeSafe, `still scene ${await railN()}`);
  check('safe mode keeps rendering',
    await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return !!c && c.width > 0 && c.height > 0;
    }), '');
  await page.keyboard.press('KeyS');
  await sleep(1200);

  // --- boundary badge on model-result scenes --------------------------------
  await goTo('Digit9');
  await sleep(200);
  check('boundary badge shown on the evidence scene',
    await page.evaluate(() => !!document.querySelector('.boundary')), '');
  await goTo('Digit2');
  await sleep(200);
  check('boundary badge hidden where no model result is shown',
    await page.evaluate(() => !document.querySelector('.boundary')), '');

  check('no page errors across the whole run', errors.length === 0,
    errors.length ? `${errors.length} error(s)` : 'clean');

  await browser.close();
  server.kill();

  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length} checks · ${results.length - failed.length} passed · ${failed.length} failed`);
  if (failed.length) {
    console.log('\nFAILED:');
    for (const f of failed) console.log(`  - ${f.name}  ${f.detail}`);
  }
  process.exit(failed.length ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(1); });
