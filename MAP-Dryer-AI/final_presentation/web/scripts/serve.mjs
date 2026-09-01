/**
 * A zero-dependency static server for the built presentation.
 *
 * The launcher used to shell out to `npx vite preview`. That failed in two
 * ways on the day: npx.cmd is a shim that exits immediately while the real
 * server keeps running detached, so the launcher could not hold or stop it; and
 * vite took longer to bind the port than the launcher's fixed wait, so the
 * browser opened onto ERR_CONNECTION_REFUSED.
 *
 * Node's own http module has neither problem, starts in milliseconds, and adds
 * nothing to the presentation's dependency surface.
 *
 *   node scripts/serve.mjs [port]
 */

import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');
const PORT = Number(process.argv[2] ?? 4173);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ico': 'image/x-icon',
  '.mp4': 'video/mp4',
};

if (!existsSync(path.join(ROOT, 'index.html'))) {
  console.error(`No build found at ${ROOT}\nRun:  npx vite build`);
  process.exit(1);
}

const server = createServer((req, res) => {
  let rel = decodeURIComponent((req.url ?? '/').split('?')[0]);
  if (rel.endsWith('/')) rel += 'index.html';

  // Never serve outside dist/, whatever the request says.
  const file = path.join(ROOT, path.normalize(rel).replace(/^(\.\.[/\\])+/, ''));
  if (!file.startsWith(ROOT)) {
    res.writeHead(403).end('Forbidden');
    return;
  }

  if (!existsSync(file) || !statSync(file).isFile()) {
    res.writeHead(404, { 'content-type': 'text/plain' }).end('Not found');
    return;
  }

  res.writeHead(200, {
    'content-type': TYPES[path.extname(file).toLowerCase()] ?? 'application/octet-stream',
    'cache-control': 'no-cache',
  });
  createReadStream(file).pipe(res);
});

server.listen(PORT, '127.0.0.1', () => {
  // The launcher waits for this exact line before opening the browser.
  console.log(`READY http://127.0.0.1:${PORT}/`);
});

server.on('error', (err) => {
  console.error(`Server failed: ${err.message}`);
  process.exit(1);
});

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => server.close(() => process.exit(0)));
}
