import puppeteer from 'puppeteer';
import { mkdir } from 'fs/promises';
import { join } from 'path';

const ASSETS = join(import.meta.dirname, 'assets');
await mkdir(ASSETS, { recursive: true });

const BASE = 'http://47.108.218.39:8082';

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--window-size=1920,1080'],
  defaultViewport: { width: 1920, height: 1080 },
});

async function shot(url, filename, opts = {}) {
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
  if (opts.delay) await new Promise(r => setTimeout(r, opts.delay));
  if (opts.scroll) await page.evaluate(() => window.scrollTo(0, 300));
  await page.screenshot({ path: join(ASSETS, filename), fullPage: false });
  console.log(`  saved ${filename}`);
  await page.close();
}

async function loginAndShot(path, filename, opts = {}) {
  const page = await browser.newPage();
  await page.goto(`${BASE}/home_recommended/code.html`, { waitUntil: 'networkidle2', timeout: 30000 });

  // Login via localStorage + API
  const resp = await page.evaluate(async () => {
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'admin', password: 'admin123456' }),
    });
    return r.json();
  });

  if (resp.code === 200) {
    await page.evaluate((data) => {
      localStorage.setItem('token', data.token);
      localStorage.setItem('userInfo', JSON.stringify(data));
    }, resp.data);
  }

  await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle2', timeout: 30000 });
  if (opts.delay) await new Promise(r => setTimeout(r, opts.delay));
  await page.screenshot({ path: join(ASSETS, filename), fullPage: false });
  console.log(`  saved ${filename} (logged in)`);
  await page.close();
}

console.log('Capturing screenshots...');

// 1. Homepage (no login needed for public view)
await shot(`${BASE}/home_recommended/code.html`, 'homepage.png', { delay: 2000 });

// 2-6. Logged-in pages
await loginAndShot('/home_recommended/code.html', 'homepage-loggedin.png', { delay: 2000 });
await loginAndShot('/create_post/code.html', 'create-post.png', { delay: 1500 });
await loginAndShot('/growth_center/code.html', 'growth-center.png', { delay: 1500 });
await loginAndShot('/rewards_mall/code.html', 'rewards-mall.png', { delay: 1500 });
await loginAndShot('/admin_overview/code.html', 'admin-dashboard.png', { delay: 2000 });

await browser.close();
console.log('Done! All screenshots saved to assets/');
