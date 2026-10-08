#!/usr/bin/env python3
"""Find usable fonts on this machine and render a comparison sheet.

  fonts.py --work WORK --text "작품 제목" [--line "가사 한 줄"]

Writes WORK/sheets/fonts.jpg (look at it, pick by eye) and WORK/fonts.json with sensible defaults for the
roles opkit uses: title (heavy serif/display), hand (handwritten/chalk), hand2 (rougher handwriting),
sub (readable text). Edit fonts.json or pass fonts={...} to opkit.init() to override.
"""
import argparse, glob, json, os
from PIL import Image, ImageDraw, ImageFont

DIRS = ["~/Library/Fonts", "/Library/Fonts", "/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
        "/usr/share/fonts", "~/.fonts", "~/Documents/**/assets/fonts"]
PREF = dict(
    title=["NotoSerifKR-Black", "NanumMyeongjoExtraBold", "MaruBuri-Bold", "KoPubWorld Batang_Pro Bold", "AppleMyungjo", "AppleSDGothicNeo"],
    hand=["Dokdo-Regular", "OwnglyphParkDahyun", "NanumBrushScript-Regular", "Griun_Fromsol-Rg", "AppleSDGothicNeo"],
    hand2=["EastSeaDokdo-Regular", "NanumBrushScript-Regular", "Dokdo-Regular", "AppleSDGothicNeo"],
    sub=["KoPubWorld Batang_Pro Bold", "NotoSerifKR-Bold", "NanumMyeongjoBold", "AppleMyungjo", "AppleSDGothicNeo"],
    small=["KoPubWorld Dotum_Pro Medium", "NanumGothicBold", "AppleSDGothicNeo", "NotoSerifKR-Medium"],
)

ap = argparse.ArgumentParser()
ap.add_argument("--work", required=True)
ap.add_argument("--text", default="작품 제목")
ap.add_argument("--line", default="가사 한 줄이 여기에 들어갑니다")
a = ap.parse_args()

found = {}
for d in DIRS:
    for p in glob.glob(os.path.join(os.path.expanduser(d), "*"), recursive=True):
        if p.lower().endswith((".ttf", ".otf", ".ttc")):
            found.setdefault(os.path.splitext(os.path.basename(p))[0], p)


def supports(path, text):
    try:
        f = ImageFont.truetype(path, 40)
        box = f.getmask(text).getbbox()
        nd = f.getmask("￿").getbbox()
        return box is not None and (nd is None or f.getmask(text[0]).getbbox() != nd or True)
    except Exception:
        return False


roles = {}
for role, names in PREF.items():
    for n in names:
        if n in found and supports(found[n], a.text):
            roles[role] = found[n]
            break
json.dump(roles, open(os.path.join(a.work, "fonts.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(roles, ensure_ascii=False, indent=1))

cands = [p for n, p in sorted(found.items()) if any(k in n for k in
         ("Noto", "Nanum", "Maru", "KoPub", "Dokdo", "Gugi", "Song", "Yeon", "Black", "Ownglyph", "Aggro", "Paperlogy",
          "Gmarket", "Jalnan", "Chosun", "Distort", "LeeSeoyun", "Griun", "BMJUA", "SCDream", "Apple", "Freesentation"))][:40]
os.makedirs(os.path.join(a.work, "sheets"), exist_ok=True)
im = Image.new("RGB", (1920, len(cands) * 96 + 10), (12, 12, 14))
d = ImageDraw.Draw(im)
lab = ImageFont.load_default()
for i, p in enumerate(cands):
    try:
        ft = ImageFont.truetype(p, 70)
        d.text((20, i * 96 + 8), a.text, font=ft, fill=(240, 240, 235))
        d.text((820, i * 96 + 8), a.line, font=ft, fill=(240, 240, 235))
    except Exception:
        pass
    d.text((1700, i * 96 + 70), os.path.basename(p)[:34], font=lab, fill=(255, 220, 80))
out = os.path.join(a.work, "sheets", "fonts.jpg")
im.save(out, quality=88)
print(out)
