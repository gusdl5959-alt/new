// Resumable chunked render for a long film on a machine without a GPU:
//   node films/no4f/tools/chunks.mjs <demo> [--fps 24] [--chunk 240] [--workers 3] [--from 0] [--to <frames>]
// Each chunk of frames becomes <demo>/out/chunks/c_<first frame>.mp4; finished chunks are skipped on a re-run, so a killed render resumes.
// Workers claim chunks with an atomic mkdir. Join with tools/join.sh.
import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process';
import { openDemo, closeServer } from '../../../core/render/page.mjs';
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const dir = args[0], FPS = +opt('--fps', 24), CH = +opt('--chunk', 240), WK = +opt('--workers', 3);
const outDir = path.resolve(dir, 'out', 'chunks'); fs.mkdirSync(outDir, { recursive: true });
const probe = await openDemo(dir); const DUR = await probe.page.evaluate(() => window.DUR); await probe.browser.close();
const TOTAL = Math.round(DUR * FPS), A = +opt('--from', 0), B = Math.min(TOTAL, +opt('--to', TOTAL));
const starts = []; for (let a = A - (A % CH); a < B; a += CH) starts.push(a);
const name = a => path.join(outDir, `c_${String(a).padStart(6, '0')}.mp4`);
const t0 = Date.now(); let done = 0;
async function worker(w) {
  let br = null;
  for (const a of starts) {
    if (fs.existsSync(name(a))) continue;
    try { fs.mkdirSync(name(a) + '.claim'); } catch { continue; }
    if (!br) br = await openDemo(dir);
    const b = Math.min(TOTAL, a + CH), tmp = name(a) + '.part.mp4';
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
    const closed = new Promise(r => ff.on('close', r));
    for (let f = a; f < b; f++) {
      await br.page.evaluate(t => window.render(t), f / FPS);
      const buf = await br.page.screenshot({ type: 'jpeg', quality: 94 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); const code = await closed;
    if (code !== 0) { console.error(`chunk ${a} failed`); fs.rmSync(name(a) + '.claim', { recursive: true, force: true }); process.exit(1); }
    fs.renameSync(tmp, name(a)); fs.rmSync(name(a) + '.claim', { recursive: true, force: true });
    done += b - a; const el = (Date.now() - t0) / 1000;
    console.log(`w${w} chunk ${a}-${b} done · ${done} frames in ${el.toFixed(0)}s (${(el / done).toFixed(2)} s/frame overall)`);
  }
  if (br) await br.browser.close();
}
await Promise.all([...Array(WK)].map((_, w) => worker(w)));
closeServer();
console.log('all chunks done');
