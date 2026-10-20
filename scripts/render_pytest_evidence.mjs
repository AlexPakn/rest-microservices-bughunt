// Optional: screenshots of the local HTML pages produced by capture_pytest_evidence.py.
// Requires Node.js, Playwright and an installed Chrome or Edge browser.
import { createRequire } from 'node:module';
import { readFile, mkdir } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = path.join(root, 'docs', 'evidence', 'pytest');
const screenshots = path.join(root, 'docs', 'screenshots');
const manifest = JSON.parse(await readFile(path.join(source, 'manifest.json'), 'utf8'));
await mkdir(screenshots, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: process.env.PYTEST_BROWSER_CHANNEL || 'msedge' });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 240 }, deviceScaleFactor: 1 });
  for (const item of manifest) {
    await page.goto(pathToFileURL(path.join(source, item.page)).href);
    await page.screenshot({ path: path.join(screenshots, `pytest-${item.id}.png`), fullPage: true });
    console.log(`${item.id}: screenshot saved`);
  }
} finally {
  await browser.close();
}
