#!/usr/bin/env python3
"""Song analysis for beat-synced editing.

  analyze_song.py scan SONG --work WORK
      decodes the song into WORK/song.wav, prints a per-second energy map, tempo candidates and
      the strongest hits / silences, so you can mark the section boundaries.
  analyze_song.py grid --work WORK --sections A:15.5-45.2 B:45.0-57.2 ...
      fits a beat grid (bpm + first beat) inside each section and writes WORK/grid.json.
      Fit sections separately: generated songs drift, so one global grid slides off the beat.
  analyze_song.py hits --work WORK T0 T1
      prints 10 ms loudness around a moment to find the exact frame of a hit.
"""
import argparse, json, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools

SR = 22050


def load(work):
    x = np.fromfile(os.path.join(work, "song.pcm"), dtype=np.int16).astype(np.float32) / 32768
    return x


def flux_of(x, n=1024, h=128):
    win = np.hanning(n)
    nf = 1 + (len(x) - n) // h
    idx = np.arange(n)[None, :] + h * np.arange(nf)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * win, axis=1)).astype(np.float32)
    t = (np.arange(nf) * h + n / 2) / SR
    logS = np.log1p(20 * S)
    flux = np.r_[0, np.maximum(0, np.diff(logS, axis=0)).sum(1)]
    return t, np.convolve(flux, np.hanning(9), "same"), S


def scan(args):
    os.makedirs(args.work, exist_ok=True)
    ff = tools.ffmpeg()
    subprocess.run([ff, "-v", "error", "-y", "-i", args.song, "-ar", "48000", "-ac", "2", os.path.join(args.work, "song.wav")], check=True)
    subprocess.run([ff, "-v", "error", "-y", "-i", args.song, "-ac", "1", "-ar", str(SR), "-f", "s16le", os.path.join(args.work, "song.pcm")], check=True)
    subprocess.run([ff, "-v", "error", "-y", "-i", args.song, "-ac", "1", "-ar", "16000", os.path.join(args.work, "song16k.wav")], check=True)
    x = load(args.work)
    dur = len(x) / SR
    t, flux, S = flux_of(x)
    fr = np.fft.rfftfreq(1024, 1 / SR)
    rms = np.sqrt((S ** 2).mean(1)); rms /= rms.max()
    low = S[:, fr < 150].sum(1); low /= max(low.max(), 1e-9)
    print(f"duration {dur:.3f}s")
    print("sec  loud  bass   (bar = loudness; sudden changes mark section boundaries)")
    sec = []
    for s in range(int(dur) + 1):
        m = (t >= s) & (t < s + 1)
        if m.any():
            sec.append(float(rms[m].mean()))
            print(f"{s:3d}  {rms[m].mean():.2f}  {low[m].mean():.2f}  " + "#" * int(rms[m].mean() * 60))
    # tempo candidates
    f = flux - flux.mean()
    fps = SR / 128
    ac = np.correlate(f[::2], f[::2], "full")[len(f[::2]) - 1:]
    best = []
    for bpm in np.arange(60, 200, 0.5):
        lag = 60 / bpm * fps / 2
        best.append((sum(np.interp(lag * k, np.arange(len(ac)), ac) for k in (1, 2, 4, 8)), bpm))
    best.sort(reverse=True)
    print("tempo candidates (bpm):", [round(float(b), 1) for _, b in best[:6]], "(double/half of each other are the same pulse)")
    # boundaries
    sec = np.array(sec)
    d = np.abs(np.diff(sec))
    idx = [int(i) + 1 for i in np.argsort(-d)[:12]]
    print("largest loudness jumps at seconds:", sorted(idx))
    json.dump(dict(duration=dur, per_second=[round(v, 3) for v in sec.tolist()], tempo=[float(b) for _, b in best[:6]]),
              open(os.path.join(args.work, "analysis.json"), "w"))


def grid(args):
    x = load(args.work)
    t, sm, _ = flux_of(x)
    lo, hi = args.bpm
    G = {}
    for spec in args.sections:
        name, rng = spec.split(":")
        a, b = [float(v) for v in rng.split("-")]
        best = (0, 0, 0)
        for bpm in np.arange(lo, hi, 0.02):
            per = 60 / bpm
            for ph in np.arange(0, per, 0.004):
                s = np.interp(np.arange(a + ph, b, per), t, sm).mean()
                if s > best[0]:
                    best = (s, bpm, a + ph)
        _, bpm, first = best
        per = 60 / bpm
        G[name] = dict(bpm=float(bpm), first=float(first), per=float(per))
        n = int((b - first) / per) + 1
        print(f"{name}: bpm={bpm:.2f} first={first:.3f} beats={n}  " + " ".join(f"{first + k * per:.2f}" for k in range(min(n, 12))) + " ...")
    p = os.path.join(args.work, "grid.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(G)
    json.dump(old, open(p, "w"), indent=1)
    print("wrote", p)


def hits(args):
    x = load(args.work)
    out = []
    for tt in np.arange(args.t0, args.t1, 0.01):
        s = x[int(tt * SR):int((tt + 0.01) * SR)]
        out.append(f"{tt:.2f}:{np.sqrt((s ** 2).mean()):.2f}")
    print(" ".join(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("scan"); a.add_argument("song"); a.add_argument("--work", required=True)
    a = sub.add_parser("grid"); a.add_argument("--work", required=True); a.add_argument("--sections", nargs="+", required=True)
    a.add_argument("--bpm", nargs=2, type=float, default=[60, 200], help="search range; narrow it around the scan result")
    a = sub.add_parser("hits"); a.add_argument("--work", required=True); a.add_argument("t0", type=float); a.add_argument("t1", type=float)
    args = ap.parse_args()
    dict(scan=scan, grid=grid, hits=hits)[args.cmd](args)
