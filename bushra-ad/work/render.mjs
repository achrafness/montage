// usage: node render.mjs stills out_dir t1 t2 ...
//        node render.mjs video out.mp4 fps duration workers
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';

const here = path.dirname(new URL(import.meta.url).pathname);
const url = 'file://' + path.join(here, 'ad.html');
const [mode, out, ...rest] = process.argv.slice(2);

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(url);
  await page.evaluate(() => window.ready);
  return page;
}

const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security'] });

if (mode === 'stills') {
  fs.mkdirSync(out, { recursive: true });
  const page = await openPage(browser);
  for (const ts of rest) {
    const t = parseFloat(ts);
    await page.evaluate(t => window.seek(t), t);
    await page.screenshot({ path: path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`) });
  }
} else {
  const fps = +rest[0], dur = +rest[1], workers = +rest[2] || 4;
  const total = Math.round(fps * dur);
  const per = Math.ceil(total / workers);
  const segs = [];
  await Promise.all(Array.from({ length: workers }, async (_, w) => {
    const a = w * per, b = Math.min(total, a + per);
    if (a >= b) return;
    const seg = `${out}.part${w}.mp4`; segs[w] = seg;
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '10', '-pix_fmt', 'yuv420p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
    const page = await openPage(browser);
    for (let f = a; f < b; f++) {
      await page.evaluate(t => window.seek(t), f / fps);
      const buf = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 60 === 0) console.log(`w${w} frame ${f}/${b}`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }));
  fs.writeFileSync(`${out}.list.txt`, segs.filter(Boolean).map(s => `file '${path.resolve(s)}'`).join('\n'));
  console.log('segments done');
}
await browser.close();
