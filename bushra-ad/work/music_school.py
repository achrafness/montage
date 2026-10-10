"""Soundtrack for the Bushra whole-school film: 96 BPM, G major (I-vi-IV-V), 32.5 s.
Music and sound effects are written as one piece: every effect is pitched in key
and shares the same reverb, mixed softly under the music.
Writes out/mix.wav (full mix) and out/bed_for_voice.wav (ducked under the voice lines)."""
import json, sys
import numpy as np

SR = 48000
DUR = 32.5
BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int(SR * (DUR + 3.0))
rng = np.random.default_rng(23)
TRANSPOSE = 5  # written in D, sounds in G
OUT = 'out/school'

def hz(note):
    names = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    n, o = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (o + 1) - 69 + TRANSPOSE) / 12)

def fft_filter(x, lo=None, hi=None, slope=1.5):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if hi: g *= 1 / (1 + (f / hi) ** (2 * slope))
    if lo: g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (2 * slope))
    return np.fft.irfft(X * g, len(x))

L = np.zeros(N); R = np.zeros(N)
sendL = np.zeros(N); sendR = np.zeros(N)

def place(sig, t, gain=1.0, pan=0.0, send=0.25):
    i = int(t * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    gl = np.cos((pan + 1) * np.pi / 4); gr = np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gl; R[i:i + len(sig)] += sig * gr
    sendL[i:i + len(sig)] += sig * gl * send; sendR[i:i + len(sig)] += sig * gr * send

def env_adsr(n, a, d_tau, rel_at=None, rel=0.3):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d_tau)
    if rel_at is not None:
        e *= np.clip(1 - (t - rel_at) / rel, 0, 1)
    return e

# ---------------- instruments ----------------
def piano(f, dur=2.6, vel=1.0):
    n = int(SR * dur); t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 12000: break
        amp = (1 / k ** 1.7) * (0.6 + 0.4 * vel)
        dec = np.exp(-t * (0.9 + 0.75 * k) * (0.7 + 0.3 * (f / 300)))
        s += amp * dec * (np.sin(2 * np.pi * fk * t) + 0.5 * np.sin(2 * np.pi * fk * 1.0007 * t))
    s *= np.minimum(1, t / 0.004)
    ham = fft_filter(rng.standard_normal(n) * np.exp(-t / 0.006), hi=2500) * 0.05
    s = s + ham
    s *= np.clip((dur - t) / 0.25, 0, 1)
    return s * 0.22 * vel

def pad(freqs, dur, attack=0.9, release=1.0):
    n = int(SR * (dur + release)); t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for det in (-0.006, 0.0, 0.0055):
            ff = f * (1 + det)
            ph = rng.uniform(0, 2 * np.pi)
            for k in range(1, 9):
                s += np.sin(2 * np.pi * ff * k * t + ph * k) / k * (0.9 ** k)
    s = fft_filter(s, lo=90, hi=1400, slope=1.2)
    e = np.minimum(1, t / attack) * np.clip(1 - (t - dur) / release, 0, 1)
    e *= 1 + 0.06 * np.sin(2 * np.pi * 0.35 * t)
    return s * e * 0.012

def bass(f, dur=1.0):
    n = int(SR * dur); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
    e = np.minimum(1, t / 0.012) * np.exp(-t / 0.55) * np.clip((dur - t) / 0.08, 0, 1)
    return s * e * 0.13

def kick(vel=1.0):
    n = int(SR * 0.5); t = np.arange(n) / SR
    f = 48 + 70 * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.22) * np.minimum(1, t / 0.002)
    click = fft_filter(rng.standard_normal(n) * np.exp(-t / 0.003), hi=1800) * 0.06
    return (s + click) * 0.24 * vel

def brush(length=0.05, vel=1.0, lo=4000, hi=11000):
    n = int(SR * (length * 4)); t = np.arange(n) / SR
    s = fft_filter(rng.standard_normal(n), lo=lo, hi=hi) * np.exp(-t / length) * np.minimum(1, t / 0.004)
    return s * 0.05 * vel

def bell(f, dur=2.2, vel=1.0):
    n = int(SR * dur); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9)
         + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.45)
         + 0.18 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / 0.22)
         + 0.08 * np.sin(2 * np.pi * f * 4.2 * t) * np.exp(-t / 0.12))
    s *= np.minimum(1, t / 0.003)
    return s * 0.07 * vel

def pluck(f, dur=0.9, vel=1.0):  # soft marimba-like
    n = int(SR * dur); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.28)
         + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.05))
    s *= np.minimum(1, t / 0.004)
    return s * 0.09 * vel

def whoosh(dur=0.6, f0=300, f1=3000, peak=0.6, vel=1.0):
    """filtered-noise swell; the band follows f0->f1 (done in 16 short blocks)."""
    n = int(SR * dur); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); blocks = 16; bl = n // blocks + 1
    win = np.hanning(2 * bl)
    for b in range(blocks):
        c = b * bl
        a0 = max(0, c - bl // 2); a1 = min(n, c + bl + bl // 2)
        seg = noise[a0:a1]
        fc = f0 * (f1 / f0) ** (b / (blocks - 1))
        seg = fft_filter(seg, lo=fc * 0.5, hi=fc * 1.6, slope=1.0)
        w = np.hanning(len(seg))
        out[a0:a1] += seg * w * 0.66
    x = t / dur
    e = np.where(x < peak, (x / peak) ** 2, ((1 - x) / (1 - peak)) ** 1.5)
    return out * e * 0.11 * vel

def boom(vel=1.0):
    n = int(SR * 2.2); t = np.arange(n) / SR
    f = 42 + 30 * np.exp(-t / 0.12)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.8) * np.minimum(1, t / 0.006)
    return s * 0.30 * vel

def wash(dur=2.4, vel=1.0):
    n = int(SR * dur); t = np.arange(n) / SR
    s = fft_filter(rng.standard_normal(n), lo=2500, hi=9000, slope=1.0) * np.exp(-t / 0.7) * np.minimum(1, t / 0.02)
    return s * 0.03 * vel

# ---------------- score ----------------
CH = {
    'D':  (['D2'], ['D3', 'A3', 'C#4', 'E4', 'F#4'], ['F#4', 'A4', 'C#5', 'E5']),
    'Bm': (['B1'], ['B2', 'F#3', 'A3', 'D4', 'C#4'], ['D4', 'F#4', 'A4', 'C#5']),
    'G':  (['G1'], ['G2', 'D3', 'B3', 'F#4', 'A4'], ['B4', 'D5', 'F#5', 'A4']),
    'A':  (['A1'], ['A2', 'E3', 'D4', 'F#4', 'B4'], ['C#5', 'E5', 'A4', 'D5']),
}
PROG = ['D', 'Bm', 'G', 'A'] * 3 + ['D']

for b, name in enumerate(PROG):
    t0 = b * BAR
    root, voicing, arp = CH[name]
    last = b == len(PROG) - 1
    # pad
    place(pad([hz(n) for n in voicing[1:4]], BAR + (0.6 if not last else 0.0), attack=0.7 if b else 1.4, release=1.6 if not last else 2.8), t0, gain=1.0, send=0.35)
    # felt piano chord: soft, slightly rolled
    for i, n in enumerate(voicing):
        place(piano(hz(n), dur=BAR + 0.4 if not last else 3.2, vel=0.5 + 0.04 * i), t0 + 0.028 * i, gain=0.42, pan=-0.25 + 0.12 * i, send=0.3)
    # gentle piano motif on beats 2.5 and 4 (answering phrase)
    if b in (0, 1, 4, 5, 8, 9, 12):
        mel = {0: ['F#4', 'A4'], 1: ['D4', 'F#4'], 4: ['A4', 'D5'], 5: ['F#5', 'D5'], 8: ['D5', 'E5'], 9: ['F#5', 'A5'], 12: ['A5', 'D6']}[b]
        place(piano(hz(mel[0]), 1.6, 0.5), t0 + 1.5 * BEAT, gain=0.7, pan=0.2, send=0.4)
        place(piano(hz(mel[1]), 1.6, 0.45), t0 + 3.0 * BEAT, gain=0.65, pan=0.25, send=0.4)
    # groove from bar 2 (steps scene) until bar 11
    if 2 <= b <= 11:
        place(bass(hz(root[0]), 1.4), t0, gain=0.9, send=0.05)
        place(bass(hz(root[0]), 0.7), t0 + 2.5 * BEAT, gain=0.6, send=0.05)
        place(kick(0.9), t0, send=0.04)
        place(kick(0.6), t0 + 2 * BEAT, send=0.04)
        for e in range(8):
            sw = 0.04 * BEAT if e % 2 else 0.0
            v = 0.55 if e % 2 else 0.8
            place(brush(0.035, v), t0 + e * BEAT / 2 + sw, pan=0.3, send=0.15)
        place(brush(0.12, 0.9, lo=1800, hi=7000), t0 + 1 * BEAT, pan=-0.1, send=0.25)
        place(brush(0.12, 0.9, lo=1800, hi=7000), t0 + 3 * BEAT, pan=-0.1, send=0.25)
    # soft arpeggio texture during the footage (bars 6-9)
    if 6 <= b <= 9:
        for e in range(8):
            n = arp[e % 4]
            place(pluck(hz(n), 0.6, 0.45), t0 + e * BEAT / 2, gain=0.6, pan=(-0.4 if e % 2 else 0.4), send=0.45)

# ---------------- sound effects (in key, same room) ----------------
FX = []
def fx(t, sig, gain=1.0, pan=0.0, send=0.35):
    FX.append(round(t, 3)); place(sig, t, gain, pan, send)

fx(0.2, pluck(hz('A5'), 0.8, 0.5), 0.8, 0.2)                         # badge
for t, n in [(0.6, 'D6'), (1.2, 'F#6'), (2.0, 'A6')]:
    fx(t, bell(hz(n), 1.2, 0.35), 0.7, 0.3)                          # stars
fx(0.55, pad([hz('D4'), hz('A4'), hz('F#5')], 0.5, attack=0.15, release=1.2), 2.0, 0, 0.5)  # hero photo opens
fx(1.8, pluck(hz('B5'), 0.9, 0.7), 0.9, 0.35)                        # sticky note
fx(2.4, whoosh(0.9, 2500, 7000, 0.5, 0.3), 1.0, -0.3, 0.5)           # paper plane
fx(2.6, bell(hz('A5'), 1.8, 0.7), 0.9, 0.1)                          # "in one place"
fx(4.1, whoosh(0.45, 2800, 600, 0.8, 0.5), 1.0, 0)                   # photo collapses
fx(4.45, whoosh(0.6, 400, 2400, 0.6, 0.55), 1.0, 0.1)                # card grows into the panel
for (t, n) in zip([5.625, 6.25, 6.875], ['F#5', 'A5', 'D6']):
    fx(t, bell(hz(n), 1.4, 0.6), 0.85, 0.2)                          # promises
fx(8.85, whoosh(0.5, 3000, 900, 0.6, 0.35), 1.0, -0.1)               # rows swap to levels
for (t, n) in zip([9.95, 10.575, 11.2], ['D5', 'F#5', 'A5']):
    fx(t, pluck(hz(n), 0.9, 0.8), 0.9, -0.1)                         # dot climbs the levels
for i, n in enumerate(['D6', 'E6', 'F#6', 'A6']):
    fx(11.55 + i * 0.22, pluck(hz(n), 0.6, 0.35), 0.7, -0.3 + 0.2 * i)  # subjects + languages
fx(13.55, whoosh(0.7, 400, 2600, 0.6, 0.7), 1.0, 0.1)                # panel becomes the window
fx(14.0, pad([hz('D4'), hz('A4'), hz('F#5')], 0.5, attack=0.12, release=1.2), 2.0, 0, 0.5)  # footage blooms from the dot
for i, n in enumerate(['A5', 'D6', 'F#6']):
    fx(14.55 + i * 0.3, pluck(hz(n), 0.6, 0.45), 0.75, -0.3 + 0.3 * i)  # teacher avatars
for t in [14.3, 16.7, 18.85]:
    fx(t, pluck(hz('A6'), 0.5, 0.35), 0.7, -0.3)                     # chips
for t in [16.4, 18.6, 19.9]:
    fx(t, whoosh(0.5, 1200, 5000, 0.4, 0.45), 1.0, 0.2, 0.45)        # footage reveals
fx(21.1, whoosh(0.6, 3000, 600, 0.75, 0.55), 1.0, 0)                 # window becomes the in-person card
fx(21.45, whoosh(0.5, 1200, 5000, 0.45, 0.45), 1.0, 0.2, 0.45)
fx(21.75, pluck(hz('A5'), 0.8, 0.6), 0.8, -0.2)                      # online card
fx(22.4, bell(hz('D6'), 1.8, 0.8), 0.9); fx(22.4, bell(hz('A5'), 1.8, 0.5), 0.9)   # "or"
fx(22.7, pluck(hz('F#6'), 0.6, 0.4), 0.7, 0.3)
fx(23.15, pluck(hz('A6'), 0.5, 0.35), 0.7, -0.3)
for n in ['D6', 'A6', 'F#6']:
    fx(23.95, bell(hz(n), 2.2, 0.7), 0.85, 0)                        # free intro courses
fx(25.0, whoosh(0.66, 300, 4500, 0.95, 1.0), 1.0, 0, 0.3)
fx(25.625, boom(0.9), 1.0, 0, 0.15); fx(25.64, wash(2.6, 1.0), 1.0, 0, 0.6)
fx(26.0, whoosh(0.6, 3500, 600, 0.3, 0.5), 1.0, 0)
for i, n in enumerate(['D6', 'F#6', 'A6', 'D7']):
    fx(26.45 + i * 0.06, bell(hz(n), 1.8, 0.45), 0.8, -0.3 + 0.2 * i)
fx(26.75, whoosh(0.45, 800, 3000, 0.5, 0.35), 1.0, 0)
fx(27.35, bell(hz('A5'), 1.6, 0.6), 0.9, 0); fx(27.35, bell(hz('D6'), 1.6, 0.4), 0.9, 0)
fx(27.7, pluck(hz('F#6'), 0.6, 0.35), 0.7, 0.3); fx(27.9, pluck(hz('A6'), 0.6, 0.3), 0.7, -0.3)

# ---------------- room ----------------
def reverb(x, seconds=2.4, seed=1):
    r = np.random.default_rng(seed)
    n = int(SR * seconds); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / (seconds / 6.9)) * np.minimum(1, t / 0.012)
    ir = fft_filter(ir, lo=180, hi=5500)
    ir /= np.sqrt(np.sum(ir ** 2))
    m = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[: len(x)]
    return y

wetL = reverb(sendL, seed=1); wetR = reverb(sendR, seed=2)
mixL = L + 0.55 * wetL; mixR = R + 0.55 * wetR
# gentle glue: soft-knee saturation
def soft(x): return np.tanh(x * 1.2) / 1.2
mixL, mixR = soft(mixL), soft(mixR)

end = int(SR * DUR)
fade = np.clip((DUR - np.arange(end) / SR) / 0.6, 0, 1) ** 1.5
fade_in = np.clip(np.arange(end) / SR / 0.02, 0, 1)
mix = np.stack([mixL[:end], mixR[:end]], 1) * (fade * fade_in)[:, None]

# voice-ready bed: -6 dB under each voice line, 150 ms ramps
lines = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else []
g = np.ones(end)
for a, b in lines:
    i0, i1 = int((a - 0.15) * SR), int((b + 0.25) * SR)
    g[max(0, i0):min(end, i1)] = 0.5
k = int(0.15 * SR); ker = np.ones(k) / k
g = np.convolve(g, ker, mode='same')
bed = mix * g[:, None]

def write_wav(path, x):
    x = np.clip(x / max(1e-9, np.max(np.abs(x))) * 0.89, -1, 1)
    pcm = (x * 32767).astype('<i2')
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

write_wav(OUT + '_mix_raw.wav', mix)
write_wav(OUT + '_bed_raw.wav', bed)
print('fx events:', len(FX))
