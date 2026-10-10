// usage: node render.mjs stills out_dir t1 t2 ...
//        node render.mjs video seg_dir fps duration workers
// Video mode renders 2-second chunks into seg_dir/NNNN.mp4 and skips chunks that already exist, so a stopped render resumes.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';

const here = path.dirname(new URL(import.meta.url).pathname);
const url = 'file://' + path.join(here, process.env.AD_HTML || 'ad.html');
const [mode, out, ...rest] = process.argv.slice(2);

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(url);
  await page.evaluate(() => window.ready);
  const cdp = await page.context().newCDPSession(page);
  return { page, cdp };
}

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });

if (mode === 'stills') {
  fs.mkdirSync(out, { recursive: true });
  const { page } = await openPage(browser);
  for (const ts of rest) {
    const t = parseFloat(ts);
    await page.evaluate(t => window.seek(t), t);
    await page.screenshot({ path: path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`) });
  }
} else {
  const fps = +rest[0], dur = +rest[1], workers = +rest[2] || 4;
  const total = Math.round(fps * dur), CH = fps * 2;
  fs.mkdirSync(out, { recursive: true });
  const queue = [];
  for (let c = 0; c * CH < total; c++) {
    if (!fs.existsSync(path.join(out, `${String(c).padStart(4, '0')}.mp4`))) queue.push(c);
  }
  console.log('chunks to render', queue.length);
  await Promise.all(Array.from({ length: workers }, async (_, w) => {
    const { page, cdp } = await openPage(browser);
    while (queue.length) {
      const c = queue.shift();
      const a = c * CH, b = Math.min(total, a + CH);
      const final = path.join(out, `${String(c).padStart(4, '0')}.mp4`), tmp = final + '.tmp.mp4';
      const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', '-color_range', 'tv', tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
      for (let f = a; f < b; f++) {
        await page.evaluate(t => window.seek(t), f / fps);
        const r = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 97, optimizeForSpeed: true });
        const buf = Buffer.from(r.data, 'base64');
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      }
      ff.stdin.end();
      await new Promise(r => ff.on('close', r));
      fs.renameSync(tmp, final);
      console.log(`w${w} chunk ${c} done`);
    }
  }));
  const segs = fs.readdirSync(out).filter(f => /^\d{4}\.mp4$/.test(f)).sort();
  fs.writeFileSync(path.join(out, 'list.txt'), segs.map(s => `file '${s}'`).join('\n'));
  console.log('all chunks done', segs.length);
}
await browser.close();
