#!/usr/bin/env python3
"""Catalogue source material and make contact sheets you can actually look at.

  contact_sheets.py clips FOLDER --work WORK --prefix C     # videos  -> WORK/clips_C.json, WORK/sheets/clips_C_NN.jpg
  contact_sheets.py images FOLDER --work WORK --prefix I    # stills  -> WORK/stills_I.json, WORK/sheets/stills_I_NN.jpg
  contact_sheets.py dense --work WORK C06 C07 N14 ...       # 8 frames per clip, to find the action peak / defects
  contact_sheets.py refs FOLDER --work WORK                 # reference openings: cut rhythm + frame sheets

Each clip gets a short key (C00, C01 ...). Use a different prefix per folder so keys never collide.
"""
import argparse, glob, json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools

VID = (".mp4", ".mov", ".webm", ".mkv", ".m4v")
IMG = (".jpg", ".jpeg", ".png", ".webp")


def font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def grab(ff, f, t, w, h, out):
    if not os.path.exists(out):
        subprocess.run([ff, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", f, "-frames:v", "1", "-vf", f"scale={w}:{h}", "-q:v", "4", out])
    return Image.open(out) if os.path.exists(out) else Image.new("RGB", (w, h))


def clips(a):
    ff = tools.ffmpeg()
    files = sorted(f for f in glob.glob(os.path.join(a.folder, "*")) if f.lower().endswith(VID))
    os.makedirs(os.path.join(a.work, "sheets"), exist_ok=True)
    os.makedirs(os.path.join(a.work, "thumbs"), exist_ok=True)
    W, H, N = 320, 180, 6
    meta, rows = [], []
    for i, f in enumerate(files):
        p = tools.probe(f)
        key = f"{a.prefix}{i:02d}"
        meta.append(dict(key=key, file=f, id=os.path.basename(f)[:-4][-28:], dur=p["dur"], w=p["w"], h=p["h"], cfps=p["fps"]))
        row = Image.new("RGB", (W * N, H + 26), (20, 20, 20))
        for k in range(N):
            t = 0.03 + k * (max(0.1, p["dur"] - 0.1) / (N - 1))
            row.paste(grab(ff, f, t, W, H, os.path.join(a.work, "thumbs", f"{key}_{k}.jpg")), (k * W, 26))
        ImageDraw.Draw(row).text((6, 2), f"{key}  {meta[-1]['id']}  {p['dur']:.2f}s {p['w']}x{p['h']} {p['fps']:.0f}fps", font=font(18), fill=(255, 230, 80))
        rows.append(row)
    json.dump(meta, open(os.path.join(a.work, f"clips_{a.prefix}.json"), "w"), ensure_ascii=False, indent=1)
    per = 7
    for s in range(0, len(rows), per):
        g = rows[s:s + per]
        sh = Image.new("RGB", (W * N, (H + 26) * len(g)))
        for r, im in enumerate(g):
            sh.paste(im, (0, r * (H + 26)))
        out = os.path.join(a.work, "sheets", f"clips_{a.prefix}_{s // per:02d}.jpg")
        sh.save(out, quality=84)
        print(out)
    print(len(files), "clips ->", os.path.join(a.work, f"clips_{a.prefix}.json"))


def images(a):
    files = sorted(f for f in glob.glob(os.path.join(a.folder, "*")) if f.lower().endswith(IMG))
    os.makedirs(os.path.join(a.work, "sheets"), exist_ok=True)
    W, H, cols, rws = 480, 300, 4, 3
    meta = []
    for s in range(0, len(files), cols * rws):
        sh = Image.new("RGB", (W * cols, (H + 28) * rws), (20, 20, 20))
        d = ImageDraw.Draw(sh)
        for k, f in enumerate(files[s:s + cols * rws]):
            im = Image.open(f).convert("RGB")
            key = f"{a.prefix}{s + k:02d}"
            meta.append(dict(key=key, file=f, w=im.width, h=im.height))
            t = im.copy(); t.thumbnail((W, H))
            x, y = (k % cols) * W, (k // cols) * (H + 28)
            sh.paste(t, (x + (W - t.width) // 2, y + 28 + (H - t.height) // 2))
            d.text((x + 4, y + 3), f"{key} {im.width}x{im.height} {os.path.basename(f)[:24]}", font=font(18), fill=(255, 230, 80))
        out = os.path.join(a.work, "sheets", f"stills_{a.prefix}_{s // (cols * rws):02d}.jpg")
        sh.save(out, quality=82)
        print(out)
    json.dump(meta, open(os.path.join(a.work, f"stills_{a.prefix}.json"), "w"), ensure_ascii=False, indent=1)
    print(len(files), "stills ->", os.path.join(a.work, f"stills_{a.prefix}.json"))


def dense(a):
    ff = tools.ffmpeg()
    meta = {}
    for p in glob.glob(os.path.join(a.work, "clips_*.json")):
        for m in json.load(open(p)):
            meta[m["key"]] = m
    os.makedirs(os.path.join(a.work, "thumbs"), exist_ok=True)
    W, H, N = 240, 135, 8
    sh = Image.new("RGB", (W * N, (H + 24) * len(a.keys)), (20, 20, 20))
    d = ImageDraw.Draw(sh)
    for r, k in enumerate(a.keys):
        m = meta[k]
        for i in range(N):
            t = 0.05 + i * (max(0.2, m["dur"] - 0.15) / (N - 1))
            sh.paste(grab(ff, m["file"], t, W, H, os.path.join(a.work, "thumbs", f"{k}_d{i}.jpg")), (i * W, r * (H + 24) + 24))
            d.text((i * W + 4, r * (H + 24) + 3), (f"{k} " if i == 0 else "") + f"{t:.1f}s", font=font(16), fill=(255, 230, 80))
    out = os.path.join(a.work, "sheets", "dense_" + "_".join(a.keys[:4]) + ".jpg")
    sh.save(out, quality=82)
    print(out)


def refs(a):
    ff = tools.ffmpeg()
    os.makedirs(os.path.join(a.work, "sheets"), exist_ok=True)
    for i, f in enumerate(sorted(x for x in glob.glob(os.path.join(a.folder, "*")) if x.lower().endswith(VID))):
        d = tools.probe(f)["dur"]
        r = subprocess.run([ff, "-hide_banner", "-i", f, "-vf", "scale=320:180,select='gt(scene,0.28)',showinfo", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        cc = [0.0]
        for c in [float(x) for x in re.findall(r"pts_time:([\d.]+)", r)]:
            if c - cc[-1] > 0.25:
                cc.append(c)
        lens = sorted(b - x for x, b in zip(cc, cc[1:] + [d]))
        print(f"R{i} {os.path.basename(f)[:44]}  dur={d:.1f}s shots={len(cc)} avg={d / len(cc):.2f}s median={lens[len(lens) // 2]:.2f}s")
        print("    shots per 10s:", [sum(1 for c in cc if x <= c < x + 10) for x in range(0, int(d), 10)])
        tmp = os.path.join(a.work, "thumbs", f"ref{i}")
        os.makedirs(tmp, exist_ok=True)
        subprocess.run([ff, "-v", "error", "-y", "-i", f, "-vf", "fps=1/1.5,scale=240:135", "-q:v", "4", os.path.join(tmp, "%03d.jpg")])
        fr = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
        cols = 8
        sh = Image.new("RGB", (240 * cols, 135 * ((len(fr) + cols - 1) // cols)))
        dr = ImageDraw.Draw(sh)
        for k, p in enumerate(fr):
            sh.paste(Image.open(p), ((k % cols) * 240, (k // cols) * 135))
            dr.text(((k % cols) * 240 + 3, (k // cols) * 135 + 2), f"{k * 1.5 + 0.75:.0f}s", font=font(14), fill=(255, 255, 0))
        out = os.path.join(a.work, "sheets", f"ref_{i}.jpg")
        sh.save(out, quality=80)
        print("   ", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("clips", "images"):
        s = sub.add_parser(name); s.add_argument("folder"); s.add_argument("--work", required=True); s.add_argument("--prefix", required=True)
    s = sub.add_parser("dense"); s.add_argument("--work", required=True); s.add_argument("keys", nargs="+")
    s = sub.add_parser("refs"); s.add_argument("folder"); s.add_argument("--work", required=True)
    a = ap.parse_args()
    dict(clips=clips, images=images, dense=dense, refs=refs)[a.cmd](a)
