"""Original, copyright-free background tracks for @smartwork.ai.in reels.
Everything is synthesized from scratch (drums, bass, chords, lead), so no licensing issues.

Usage: python3 tools/make_music.py   -> writes music/<mood>.wav (about 32 s each, loop-friendly)
"""
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "music")
rng = np.random.default_rng(7)

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

def env(n, a=0.005, d=0.1, s=0.6, r=0.1):
    t = np.arange(n) / SR
    e = np.ones(n) * s
    ai = int(a * SR); di = int(d * SR); ri = int(r * SR)
    e[:ai] = np.linspace(0, 1, ai, endpoint=False) if ai else e[:ai]
    if di: e[ai:ai + di] = np.linspace(1, s, len(e[ai:ai + di]))
    if ri: e[-ri:] *= np.linspace(1, 0, len(e[-ri:]))
    return e

def lowpass(x, cut):
    b, a = butter(2, cut / (SR / 2), "low"); return lfilter(b, a, x)

def highpass(x, cut):
    b, a = butter(2, cut / (SR / 2), "high"); return lfilter(b, a, x)

def saw(f, n):
    t = np.arange(n) / SR
    return 2 * ((t * f) % 1) - 1

def sq(f, n, duty=0.5):
    t = np.arange(n) / SR
    return np.where((t * f) % 1 < duty, 1.0, -1.0)

def sine(f, n):
    return np.sin(2 * np.pi * f * np.arange(n) / SR)

def kick(n=int(0.35 * SR)):
    t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)

def snare(n=int(0.22 * SR)):
    t = np.arange(n) / SR
    noise = highpass(rng.standard_normal(n), 1500) * np.exp(-t * 18)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    return 0.55 * noise + 0.4 * tone

def clap(n=int(0.2 * SR)):
    t = np.arange(n) / SR
    e = np.exp(-t * 22) * (1 + 0.6 * (np.sin(2 * np.pi * 90 * t) > 0))
    return highpass(rng.standard_normal(n), 900) * e * 0.6

def hat(n=int(0.06 * SR), open_=False):
    if open_: n = int(0.25 * SR)
    t = np.arange(n) / SR
    return highpass(rng.standard_normal(n), 7000) * np.exp(-t * (14 if open_ else 70)) * 0.35

def place(buf, sample, pos, gain=1.0):
    pos = int(pos)
    if pos >= len(buf): return
    end = min(len(buf), pos + len(sample))
    buf[pos:end] += sample[:end - pos] * gain

def chord_pad(notes, n, kind="saw", cut=1800):
    x = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0.08):
            f = midi(m + det)
            x += (saw(f, n) if kind == "saw" else sq(f, n, 0.3) if kind == "sq" else sine(f, n))
    x = lowpass(x / (len(notes) * 2), cut)
    return x * env(n, a=0.08, d=0.3, s=0.8, r=0.25)

def pluck(m, n, cut=3000, kind="sq"):
    f = midi(m)
    x = sq(f, n, 0.25) if kind == "sq" else saw(f, n) if kind == "saw" else sine(f, n)
    t = np.arange(n) / SR
    return lowpass(x, cut) * np.exp(-t * 7)

def bassnote(m, n, kind="saw", cut=500):
    f = midi(m)
    x = saw(f, n) * 0.6 + sine(f, n) * 0.6 if kind == "saw" else sine(f, n) + 0.3 * sine(2 * f, n)
    return lowpass(x, cut) * env(n, a=0.005, d=0.15, s=0.7, r=0.05)

def master(x, name):
    x = x - np.mean(x)
    x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.6)
    fade = int(1.5 * SR)
    x[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    x = x / np.max(np.abs(x)) * 0.89
    st = np.stack([x, np.roll(x, int(0.012 * SR)) * 0.97], axis=1)  # slight stereo width
    os.makedirs(OUT, exist_ok=True)
    wavfile.write(os.path.join(OUT, name + ".wav"), SR, (st * 32767).astype(np.int16))
    print("wrote", name)

def song(bpm, bars, prog, drums, pad_kind, pad_cut, bass_pat, lead=None, swing=0.0, bass_kind="saw", lead_kind="sq"):
    beat = 60 / bpm * SR
    n = int(beat * 4 * bars)
    mix = {"drums": np.zeros(n), "pad": np.zeros(n), "bass": np.zeros(n), "lead": np.zeros(n)}
    for b in range(bars):
        root, chord = prog[b % len(prog)]
        start = b * 4 * beat
        place(mix["pad"], chord_pad(chord, int(4 * beat), pad_kind, pad_cut), start)
        for step, (pos, semis, length) in enumerate(bass_pat):
            place(mix["bass"], bassnote(root + semis, int(length * beat), bass_kind), start + pos * beat)
        for i in range(16):
            sw = swing * beat / 4 if i % 2 else 0
            p = start + i * beat / 4 + sw
            d = drums[i]
            if "k" in d: place(mix["drums"], kick(), p, 1.0)
            if "s" in d: place(mix["drums"], snare(), p, 0.8)
            if "c" in d: place(mix["drums"], clap(), p, 0.7)
            if "h" in d: place(mix["drums"], hat(), p, 0.8)
            if "o" in d: place(mix["drums"], hat(open_=True), p, 0.6)
        if lead and b % 4 in lead.get("bars", (0, 1, 2, 3)):
            for pos, m, length in lead["notes"][b % len(lead["notes"])]:
                place(mix["lead"], pluck(m, int(length * beat), kind=lead_kind), start + pos * beat)
    w = {"drums": 0.9, "pad": 0.35, "bass": 0.6, "lead": 0.3}
    return sum(mix[k] * w[k] for k in mix)

# ---------------- moods ----------------
def upbeat():   # energetic tech / AI hack reels, 120 bpm, C major-ish
    prog = [(36, [60, 64, 67, 71]), (33, [57, 60, 64, 67]), (29, [53, 57, 60, 64]), (31, [55, 59, 62, 65])]
    drums = ["kh", "h", "oh", "h", "csh", "h", "oh", "h", "kh", "kh", "oh", "h", "csh", "h", "oh", "h"]
    bass = [(0, 0, .5), (.75, 0, .25), (1.5, 12, .25), (2, 0, .5), (3, 7, .5), (3.5, 10, .5)]
    lead = {"bars": (1, 3), "notes": [[(0, 76, .5), (.5, 79, .5), (1, 83, .5), (2, 81, .5), (3, 79, 1)]] * 4}
    return song(120, 16, prog, drums, "saw", 2200, bass, lead)

def chill():    # lo-fi, 84 bpm, swung, warm
    prog = [(38, [62, 65, 69, 72]), (43, [55, 59, 62, 65]), (36, [60, 64, 67, 71]), (33, [57, 60, 64, 67])]
    drums = ["k", "", "h", "", "s", "", "h", "k", "", "k", "h", "", "s", "", "h", ""]
    bass = [(0, 0, 1.5), (2.5, 7, .5), (3, 12, 1)]
    lead = {"bars": (2, 3), "notes": [[(0, 74, 1), (1.5, 72, .5), (2, 69, 1.5)]] * 4}
    return song(84, 12, prog, drums, "sine", 1200, bass, lead, swing=0.3, bass_kind="sine", lead_kind="sine")

def dramatic(): # before-vs-after reveals, 95 bpm, minor
    prog = [(33, [57, 60, 64]), (29, [53, 57, 60]), (36, [55, 60, 64]), (31, [55, 59, 62])]
    drums = ["k", "", "", "", "c", "", "", "k", "k", "", "", "", "c", "", "o", ""]
    bass = [(0, 0, 2), (2, 0, 1), (3, -2, 1)]
    lead = {"bars": (1, 2, 3), "notes": [[(0, 69, .75), (.75, 72, .75), (1.5, 76, 2.5)]] * 4}
    return song(95, 12, prog, drums, "saw", 1500, bass, lead, lead_kind="saw")

def funky():    # memes / office humour, 110 bpm, bouncy
    prog = [(40, [64, 67, 71, 74]), (45, [57, 60, 64, 67]), (38, [62, 66, 69, 72]), (43, [55, 59, 62, 66])]
    drums = ["kh", "h", "h", "kh", "ch", "h", "kh", "h", "h", "kh", "h", "h", "ch", "h", "h", "o"]
    bass = [(0, 0, .25), (.5, 12, .25), (.75, 0, .25), (1.5, 7, .25), (2, 0, .25), (2.75, 10, .25), (3.25, 12, .25), (3.5, 7, .5)]
    lead = {"bars": (0, 2), "notes": [[(.5, 76, .25), (1, 79, .25), (1.5, 76, .25), (2.5, 74, .5)]] * 4}
    return song(110, 14, prog, drums, "sq", 2500, bass, lead, swing=0.15)

if __name__ == "__main__":
    for name, fn in [("upbeat", upbeat), ("chill", chill), ("dramatic", dramatic), ("funky", funky)]:
        master(fn(), name)
