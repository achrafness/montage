#!/usr/bin/env python3
"""Rebuild the Bushra's School Instagram Reels from source media.

    python3 build.py setup                  # npm install (fonts + playwright) in work/
    python3 build.py prep                   # logo, grain, footage frames, teacher crops -> work/assets/
    python3 build.py stills language 4.5 14.2 26.4   # check frames -> work/stills/<ad>/
    python3 build.py all language           # music + render + mux -> bushra-ad.mp4
    python3 build.py all teachers           # -> teachers/bushra-teachers.mp4
    python3 build.py all school             # -> school/bushra-school.mp4 (the whole-school film)
    python3 build.py render teachers --fresh   # throw away cached 2 s chunks first

Steps can also be run one by one: music, render, mux.
Needs: python3 with numpy + Pillow, node 18+, ffmpeg, Chromium for Playwright.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # bushra-ad/
WORK = ROOT / 'work'
SRC = WORK / 'src'
ASSETS = WORK / 'assets'
OUT = WORK / 'out'

FPS, DURATION, WORKERS = 60, 32.5, 4
POSTER_T = 31.0                                  # settled end-card frame, baked in as frame 0

# Voice-over windows (seconds). Both ads share this timing; the music bed dips under them.
LINES = [[0.35, 2.45], [2.6, 4.6], [5.15, 6.95], [7.1, 8.9], [9.2, 11.4], [11.55, 13.7], [14.2, 16.45],
         [16.6, 18.6], [18.75, 21.0], [21.5, 23.6], [23.75, 25.75], [26.6, 28.5], [28.65, 31.8]]

ADS = {
    'language': dict(html='ad.html', music='music.py', raw='out/mix_raw.wav', bed_raw='out/bed_raw.wav',
                     seg='out/seg', final=ROOT / 'bushra-ad.mp4', poster=ROOT / 'bushra-ad.jpg',
                     bed=ROOT / 'bed_for_voice.wav'),
    'teachers': dict(html='teachers.html', music='music_teachers.py', raw='out/teach_mix_raw.wav',
                     bed_raw='out/teach_bed_raw.wav', seg='out/tseg', final=ROOT / 'teachers' / 'bushra-teachers.mp4',
                     poster=ROOT / 'teachers' / 'bushra-teachers.jpg', bed=ROOT / 'teachers' / 'bed_for_voice.wav'),
    'school': dict(html='school.html', music='music_school.py', raw='out/school_mix_raw.wav',
                   bed_raw='out/school_bed_raw.wav', seg='out/sseg', final=ROOT / 'school' / 'bushra-school.mp4',
                   poster=ROOT / 'school' / 'bushra-school.jpg', bed=ROOT / 'school' / 'bed_for_voice.wav'),
}

# Footage clips used by the language ad: name -> (source, start s, length s)
CLIPS = {'c1': ('v0206.mp4', 1.0, 2.2), 'c2': ('v0209.mp4', 0.0, 2.5), 'c3': ('v0211.mp4', 0.0, 1.9),
         'c4': ('v0208.mp4', 1.3, 1.75), 'c5': ('v0210.mp4', 0.0, 2.2)}
FOOT_VF = ('crop=360:548:0:46,scale=800:1218:flags=lanczos,unsharp=5:5:0.6,eq=contrast=1.06:saturation=1.08:gamma=0.98,'
           'colorbalance=rs=0.03:bs=-0.03:rm=0.02:bm=-0.02,fps=30')

# Teacher portraits, in strip order: source, crop x, y, width (height = width*4/3), extra sharpening.
# Labcoat and hat crops are tight on purpose: they cut out children and a photographer's watermark.
TEACHERS = [('t_arabic', 250, 80, 740, False), ('t_blazer', 160, 0, 720, False), ('t_math', 40, 0, 540, False),
            ('t_glasses', 0, 0, 580, False), ('t_polo', 0, 40, 753, False), ('t_labcoat', 24, 6, 180, True),
            ('t_hat', 96, 70, 270, True)]

# Round avatars for the whole-school film: face centre x, y and crop size, as fractions of each portrait.
AVATARS = [(0.48, 0.16, 0.42), (0.52, 0.17, 0.40), (0.58, 0.37, 0.52), (0.46, 0.14, 0.36),
           (0.48, 0.28, 0.50), (0.51, 0.22, 0.46), (0.42, 0.54, 0.40)]


def run(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def setup():
    run(['npm', 'install', '--no-audit', '--no-fund'], cwd=WORK)


def prep():
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter
    ASSETS.mkdir(exist_ok=True)
    # logo: dark ink on white -> alpha; crest and wordmark split by their row gap
    a = np.asarray(Image.open(SRC / 'logo.jpg').convert('L')).astype(float) / 255
    alpha = np.clip((0.92 - a) / 0.75, 0, 1)
    for color, suf in [((30, 16, 72), 'indigo'), ((251, 246, 234), 'cream')]:
        for (y0, y1), name in [((88, 906), 'crest'), ((930, 1145), 'wordmark')]:
            al = alpha[y0:y1]
            cols = np.where((al > 0.05).any(0))[0]
            al = al[:, cols.min() - 6:cols.max() + 7]
            rgba = np.zeros(al.shape + (4,), np.uint8)
            rgba[..., :3] = color
            rgba[..., 3] = (al * 255).astype(np.uint8)
            Image.fromarray(rgba).save(ASSETS / f'{name}_{suf}.png')
    # static paper grain (an SVG noise filter is far too slow to render per frame)
    n = np.random.default_rng(3).normal(0, 1, (960, 540))
    Image.fromarray(np.clip(128 + n * 40, 0, 255).astype(np.uint8), 'L').resize((1080, 1920), Image.NEAREST).save(ASSETS / 'grain.png')
    # footage frames
    for name, (src, ss, d) in CLIPS.items():
        dst = ASSETS / 'foot' / name
        shutil.rmtree(dst, ignore_errors=True)
        dst.mkdir(parents=True)
        run(['ffmpeg', '-v', 'error', '-y', '-ss', ss, '-t', d, '-i', SRC / src, '-vf', FOOT_VF, '-q:v', 3, dst / '%03d.jpg'])
    # teacher portraits, 840x1120 (2x the on-screen card)
    (ASSETS / 'teach').mkdir(exist_ok=True)
    for i, (n_, x, y, w, sharpen) in enumerate(TEACHERS):
        im = Image.open(SRC / f'{n_}.jpg').convert('RGB')
        h = min(round(w * 4 / 3), im.size[1] - y)
        w = round(h * 3 / 4)
        c = im.crop((x, y, x + w, y + h)).resize((840, 1120), Image.LANCZOS)
        if sharpen:
            c = c.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
        c = ImageEnhance.Contrast(c).enhance(1.04)
        if not sharpen:
            c = ImageEnhance.Color(c).enhance(1.05)
        c.save(ASSETS / 'teach' / f'p{i}.jpg', quality=92)
    (ASSETS / 'avatar').mkdir(exist_ok=True)
    for i, (fx, fy, sz) in enumerate(AVATARS):
        im = Image.open(ASSETS / 'teach' / f'p{i}.jpg')
        W, H = im.size
        d = min(sz * 1.45 * W, W)
        x0 = max(0, min(W - d, fx * W - d / 2))
        y0 = max(0, min(H - d, fy * H - d / 2))
        im.crop((int(x0), int(y0), int(x0 + d), int(y0 + d))).resize((240, 240), Image.LANCZOS).save(ASSETS / 'avatar' / f'a{i}.jpg', quality=92)
    # the website's hero photo (public/assets/hero-desk.png in achrafness/Bushra-s-School)
    (ASSETS / 'site').mkdir(exist_ok=True)
    Image.open(SRC / 'site_hero_desk.png').convert('RGB').resize((1080, 1080), Image.LANCZOS).save(ASSETS / 'site' / 'hero.jpg', quality=92)
    print('assets ready in', ASSETS)


def loudnorm(src, dst, target):
    probe = subprocess.run(['ffmpeg', '-hide_banner', '-i', src, '-af', f'loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json',
                            '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = json.loads(probe[probe.rindex('{'):probe.rindex('}') + 1])
    af = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', af, '-ar', 48000, dst])


def music(ad):
    cfg = ADS[ad]
    OUT.mkdir(exist_ok=True)
    lines = OUT / f'{ad}_lines.json'
    lines.write_text(json.dumps(LINES))
    if ad == 'teachers':  # the card-pop times come from the page's camera, so the plucks land on them
        pops = subprocess.run(['node', 'pops.mjs'], cwd=WORK, capture_output=True, text=True, check=True).stdout.strip()
        (OUT / 'teach_pops.json').write_text(pops)
    run([sys.executable, '-I', WORK / cfg['music'], lines], cwd=WORK)
    loudnorm(WORK / cfg['raw'], OUT / f'{ad}_mix.wav', -14)       # finished ad
    cfg['bed'].parent.mkdir(parents=True, exist_ok=True)
    loudnorm(WORK / cfg['bed_raw'], cfg['bed'], -20)             # bed that leaves room for a voice
    print('music ready:', OUT / f'{ad}_mix.wav', cfg['bed'])


def render(ad, fresh=False):
    cfg = ADS[ad]
    seg = WORK / cfg['seg']
    if fresh:
        shutil.rmtree(seg, ignore_errors=True)
    run(['node', 'render.mjs', 'video', seg, FPS, DURATION, WORKERS], cwd=WORK, env={**os.environ, 'AD_HTML': cfg['html']})


def stills(ad, times):
    out = WORK / 'stills' / ad
    run(['node', 'render.mjs', 'stills', out, *times], cwd=WORK, env={**os.environ, 'AD_HTML': ADS[ad]['html']})
    print('stills in', out)


def mux(ad):
    cfg = ADS[ad]
    seg = WORK / cfg['seg']
    pdir = OUT / f'{ad}_poster'
    stills_env = {**os.environ, 'AD_HTML': cfg['html']}
    run(['node', 'render.mjs', 'stills', pdir, POSTER_T], cwd=WORK, env=stills_env)
    poster = next(pdir.glob('*.png'))
    video = OUT / f'{ad}_video.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', 0, '-i', seg / 'list.txt', '-c', 'copy', video])
    cfg['final'].parent.mkdir(parents=True, exist_ok=True)
    run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', poster, '-i', OUT / f'{ad}_mix.wav',
         '-filter_complex', "[0:v][1:v]overlay=0:0:enable='eq(n\\,0)',format=yuv420p[v]",
         '-map', '[v]', '-map', '2:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', 16, '-profile:v', 'high', '-level', '4.2',
         '-c:a', 'aac', '-b:a', '256k', '-ar', 48000, '-movflags', '+faststart', '-t', DURATION, cfg['final']])
    run(['ffmpeg', '-v', 'error', '-y', '-i', poster, '-q:v', 2, cfg['poster']])
    print('done:', cfg['final'])


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    if cmd == 'setup':
        return setup()
    if cmd == 'prep':
        return prep()
    if not rest or rest[0] not in ADS:
        sys.exit(f'name an ad: {", ".join(ADS)}')
    ad = rest[0]
    if cmd == 'music':
        music(ad)
    elif cmd == 'render':
        render(ad, '--fresh' in rest)
    elif cmd == 'mux':
        mux(ad)
    elif cmd == 'stills':
        stills(ad, rest[1:] or ['2', '10', '18', '24', '30'])
    elif cmd == 'all':
        music(ad)
        render(ad, '--fresh' in rest)
        mux(ad)
    else:
        sys.exit(f'unknown command {cmd}')


if __name__ == '__main__':
    main(sys.argv[1:])
