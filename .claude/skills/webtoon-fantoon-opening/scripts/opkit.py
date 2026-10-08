"""opkit — beat-synced opening compositor.

A project file describes the edit as data (shots, overlays) and calls opkit.main().
See assets/project_template.py for the shape and references/opkit-api.md for every parameter.

Rendering is done frame by frame with Pillow and piped to ffmpeg, so any frame can be previewed
as a still (`sheet`, `frames`, `seq`) before the full render.
"""
import glob, json, math, os, random, subprocess, sys, wave
from collections import OrderedDict, Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools

# ---------------------------------------------------------------- state
W = H = FPS = TOTAL = 0
SC = 1.0
DUR = 0.0
WORK = OUT = NAME = ''
FF = None
CLIPS, STILLS, GRID, FONTS = {}, {}, {}, {}
SHOTS = []
PULSES, TYPO, LYRICS = [], [], []
TITLE = ENDCARD = None
GRID_TILES, ERASE_ORDER = [], []
ACCENT = (255, 64, 64)       # tint of negative flashes
FLASH_ALT = (150, 8, 12)     # colour of the second-stage flash when redflash=1
GRADES = {}
_GRAIN = []
WHITE = BLACK = FLASHC = ACCMUL = None


def make_lut(contrast=1.0, bright=1.0, gamma=1.0, gain=(1, 1, 1), lift=(0, 0, 0)):
    lut = []
    for c in range(3):
        for i in range(256):
            v = i / 255.0
            v = (v - 0.5) * contrast + 0.5
            v = max(0.0, min(1.0, v))
            v = v ** gamma
            v = v * bright * gain[c] + lift[c]
            lut.append(int(max(0, min(255, round(v * 255)))))
    return lut


# grade = (lut, saturation). Names follow song sections so a shot can simply say grade='chorus'.
MOODS = {
    # cold, desaturated lows; hot red-leaning highs
    'horror': {
        'intro': ((1.06, 0.86, 1.05, (0.94, 1.0, 1.07)), 0.70), 'chant': ((1.12, 0.66, 1.06, (0.93, 1.0, 1.08)), 0.55),
        'title': ((1.25, 0.88, 1.05, (0.97, 1.0, 1.04)), 0.35), 'cast': ((1.12, 1.0, 1.0, (1.01, 1.0, 0.99)), 1.05),
        'verse': ((1.07, 0.97, 1.0, (1.0, 1.0, 1.0)), 0.95), 'versed': ((1.13, 0.92, 1.03, (0.97, 1.0, 1.03)), 0.90),
        'pre': ((1.10, 0.88, 1.05, (0.94, 1.0, 1.06)), 0.82), 'chorus': ((1.16, 1.0, 1.0, (1.02, 1.0, 0.98)), 1.12),
        'break': ((1.15, 0.66, 1.10, (0.88, 1.02, 1.0)), 0.40), 'final': ((1.24, 0.98, 1.04, (1.10, 0.95, 0.92)), 1.15),
        'finald': ((1.28, 0.72, 1.12, (1.05, 0.92, 0.92)), 0.35), 'outro': ((1.2, 0.85, 1.05, (0.97, 1.0, 1.03)), 0.45),
    },
    # punchy, saturated: battle / sports / thriller
    'action': {
        'intro': ((1.10, 0.90, 1.03, (0.97, 1.0, 1.04)), 0.85), 'chant': ((1.12, 0.80, 1.04, (0.96, 1.0, 1.05)), 0.75),
        'title': ((1.25, 0.92, 1.03, (1.0, 1.0, 1.0)), 0.60), 'cast': ((1.14, 1.02, 1.0, (1.02, 1.0, 0.98)), 1.15),
        'verse': ((1.10, 1.0, 1.0, (1.0, 1.0, 1.0)), 1.08), 'versed': ((1.15, 0.95, 1.02, (0.98, 1.0, 1.03)), 1.0),
        'pre': ((1.14, 0.94, 1.03, (0.97, 1.0, 1.05)), 1.0), 'chorus': ((1.20, 1.03, 1.0, (1.04, 1.0, 0.96)), 1.25),
        'break': ((1.15, 0.78, 1.06, (0.94, 1.0, 1.06)), 0.60), 'final': ((1.26, 1.03, 1.02, (1.07, 0.99, 0.93)), 1.30),
        'finald': ((1.28, 0.80, 1.08, (1.04, 0.96, 0.94)), 0.60), 'outro': ((1.15, 0.92, 1.03, (1.0, 1.0, 1.0)), 0.80),
    },
    # soft contrast, warm highlights: romance / drama / slice of life
    'warm': {
        'intro': ((1.02, 0.95, 0.98, (1.03, 1.0, 0.96)), 0.90), 'chant': ((1.04, 0.88, 1.0, (1.02, 1.0, 0.97)), 0.80),
        'title': ((1.10, 0.98, 1.0, (1.02, 1.0, 0.97)), 0.85), 'cast': ((1.06, 1.03, 0.98, (1.03, 1.0, 0.96)), 1.08),
        'verse': ((1.04, 1.02, 0.98, (1.02, 1.0, 0.97)), 1.02), 'versed': ((1.06, 0.96, 1.0, (0.99, 1.0, 1.02)), 0.92),
        'pre': ((1.06, 1.0, 0.99, (1.02, 1.0, 0.98)), 1.0), 'chorus': ((1.10, 1.05, 0.97, (1.05, 1.0, 0.94)), 1.15),
        'break': ((1.05, 0.85, 1.03, (0.97, 1.0, 1.04)), 0.65), 'final': ((1.12, 1.06, 0.97, (1.06, 1.0, 0.93)), 1.20),
        'finald': ((1.10, 0.85, 1.04, (1.0, 0.98, 0.98)), 0.60), 'outro': ((1.06, 0.95, 1.0, (1.02, 1.0, 0.98)), 0.85),
    },
}


def set_mood(name):
    """rebuild the grade table. Individual grades can still be overridden: GRADES['x'] = (make_lut(...), sat)"""
    GRADES.clear()
    for k, (p, sat) in MOODS[name].items():
        GRADES[k] = (make_lut(*p), sat)
    GRADES['none'] = (make_lut(), 1.0)


def _font_path(role):
    p = FONTS.get(role)
    if p and os.path.exists(p):
        return p
    for cand in (FONTS.get('sub'), FONTS.get('title'), "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                 "/System/Library/Fonts/Supplemental/AppleMyungjo.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        if cand and os.path.exists(cand):
            return cand
    raise SystemExit(f"no font for role '{role}'. Run scripts/fonts.py or pass fonts={{...}} to init().")


def init(work, name, out=None, size=(1280, 720), fps=24, mood='horror', fonts=None, seed=44, accent=None, flash_alt=None):
    """work: folder holding song.wav, grid.json, clips_*.json, stills_*.json, fonts.json (made by the helper scripts).
    name: base name of the deliverables. out: where they go (default: parent of work)."""
    global W, H, SC, FPS, DUR, TOTAL, WORK, OUT, NAME, FF, GRID, ACCENT, FLASH_ALT, WHITE, BLACK, FLASHC, ACCMUL
    WORK = os.path.abspath(work)
    OUT = os.path.abspath(out) if out else os.path.dirname(WORK)
    NAME = name
    W, H = size
    SC = H / 1080.0
    FPS = fps
    FF = tools.ffmpeg()
    with wave.open(os.path.join(WORK, 'song.wav')) as w:
        DUR = w.getnframes() / w.getframerate()
    TOTAL = int(math.ceil(DUR * FPS))
    gp = os.path.join(WORK, 'grid.json')
    GRID = json.load(open(gp)) if os.path.exists(gp) else {}
    for p in sorted(glob.glob(os.path.join(WORK, 'clips*.json'))):
        for m in json.load(open(p)):
            if not m.get('cfps'):
                num, _, den = str(m.get('fps', '24/1')).partition('/')
                m['cfps'] = float(num) / float(den or 1)
            CLIPS[m['key']] = m
    for p in sorted(glob.glob(os.path.join(WORK, 'stills*.json'))) + sorted(glob.glob(os.path.join(WORK, 'imgs.json'))):
        for m in json.load(open(p)):
            STILLS[m['key']] = m['file']
    fp = os.path.join(WORK, 'fonts.json')
    if os.path.exists(fp):
        FONTS.update(json.load(open(fp)))
    FONTS.update(fonts or {})
    if accent:
        ACCENT = accent
    if flash_alt:
        FLASH_ALT = flash_alt
    set_mood(mood)
    random.seed(seed)
    np.random.seed(seed)
    _GRAIN.clear()
    for _ in range(6):
        g = np.clip(128 + np.random.randn(H // 2, W // 2) * 5.0, 0, 255).astype(np.uint8)
        gi = Image.fromarray(g).resize((W, H), Image.BILINEAR)
        _GRAIN.append(Image.merge('RGB', (gi, gi, gi)))
    WHITE = Image.new('RGB', (W, H), (255, 255, 255))
    BLACK = Image.new('RGB', (W, H), (0, 0, 0))
    FLASHC = Image.new('RGB', (W, H), FLASH_ALT)
    ACCMUL = Image.new('RGB', (W, H), ACCENT)


def add_still(key, path):
    STILLS[key] = path


def beat(sec, n):
    g = GRID[sec]
    return g['first'] + n * g['per']


def beats(sec):
    return lambda n: beat(sec, n)


def fr(t):
    return int(round(t * FPS))


# ---------------------------------------------------------------- sources
_cache = OrderedDict()
_fcache = {}
_still = {}
CACHE_CLIPS = 12


def load_clip(key):
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    m = CLIPS[key]
    raw = subprocess.run([FF, "-v", "error", "-i", m['file'], "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    arr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, m['h'], m['w'], 3)
    _cache[key] = arr
    while len(_cache) > CACHE_CLIPS:
        _cache.popitem(last=False)
    return arr


def clip_frame(key, t):
    arr = load_clip(key)
    idx = int(round(t * CLIPS[key]['cfps']))
    return Image.fromarray(arr[max(0, min(len(arr) - 1, idx))])


def still_frame(key, t):
    k = (key, round(t, 3))
    if k not in _fcache:
        _fcache[k] = clip_frame(key, t).copy()
    return _fcache[k]


def load_still(key):
    if key not in _still:
        im = Image.open(STILLS[key]).convert('RGB')
        if im.width > 2752:
            im = im.resize((2752, int(im.height * 2752 / im.width)), Image.LANCZOS)
        _still[key] = im
    return _still[key]


_vig = {}


def vignette(strength):
    k = round(strength, 2)
    if k not in _vig:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = ((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2
        v = np.clip(1.0 - k * (r2 ** 1.3) * 0.5, 0, 1)
        m = Image.fromarray((v * 255).astype(np.uint8))
        _vig[k] = Image.merge('RGB', (m, m, m))
    return _vig[k]


def neg_tint(im):
    g = ImageEnhance.Contrast(im.convert('L')).enhance(1.7)
    return ImageChops.multiply(ImageChops.invert(g).convert('RGB'), ACCMUL)


def hard_bw(im):
    return ImageEnhance.Contrast(im.convert('L')).enhance(2.2).convert('RGB')


def fit169(src, zoom=1.0, cx=0.5, cy=0.5, size=None, shake=(0, 0)):
    """crop a window with the output aspect (centre cx,cy; zoom>=1) from src and scale it to size"""
    size = size or (W, H)
    sw, shh = src.size
    ar = W / H
    if sw / shh > ar:
        bh = shh
        bw = shh * ar
    else:
        bw = sw
        bh = sw / ar
    w = bw / zoom
    h = bh / zoom
    l = cx * sw - w / 2 + shake[0] * bw / W
    t = cy * shh - h / 2 + shake[1] * bw / W
    l = max(0, min(sw - w, l))
    t = max(0, min(shh - h, t))
    return src.resize(size, Image.LANCZOS if zoom < 2.4 else Image.BICUBIC, box=(l, t, l + w, t + h))


# ---------------------------------------------------------------- edit description
def S(t, src, tin=0.0, speed=1.0, z=(1.04, 1.09), c=(0.5, 0.5), c1=None, ease='lin', grade='verse',
      flash=0, shake=0, chroma=0, punch=0.0, vig=0.55, kind=None, tr=None, **kw):
    """one shot, starting at song time t and lasting until the next shot starts"""
    if src == 'black' and kind is None:
        kind = 'black'
    d = dict(t=t, src=src, tin=tin, speed=speed, z=z, c=c, c1=c1 or c, ease=ease, grade=grade, flash=flash,
             shake=shake, chroma=chroma, punch=punch, vig=vig, kind=kind, tr=tr)
    d.update(kw)
    SHOTS.append(d)


def pulse(t0, t1, sec, amount):
    """beat-synced zoom pulse between t0 and t1, following grid section sec (amount 0.015 subtle … 0.05 hard)"""
    PULSES.append((t0, t1, sec, amount))


def typo(t0, t1, rows, side='L', end=None, style='chalk'):
    """word-by-word handwritten lines. rows = [[(word, time), ...], ...]; the first row is drawn larger."""
    TYPO.append(dict(t0=t0, t1=t1, rows=rows, side=side, end=end or t1 - 0.05, style=style))


def lyrics(lines):
    """[(start, end, text), ...] — only drawn in the 'lyric' variant"""
    LYRICS.extend(lines)


def title_card(t0, t1, parts, sub=None, credit=None, size=212):
    """parts = [(text, (r,g,b)), ...] drawn on one line; slams in at t0 and leaves at t1"""
    global TITLE
    TITLE = dict(t0=t0, t1=t1, parts=parts, sub=sub, credit=credit, size=size)


def end_card(t0, parts, sub=None, credit=None, size=212, fade=None, glitch=None):
    """closing title from t0. fade=(start, dur). glitch=(time, (clip_key, clip_time) or None) for a last scare."""
    global ENDCARD
    ENDCARD = dict(t0=t0, parts=parts, sub=sub, credit=credit, size=size, fade=fade, glitch=glitch)


def grid_tiles(keys, erase_order=None):
    """16 portraits for kind='grid_fill' / 'grid_erase'. key = still key or (clip_key, time)."""
    GRID_TILES[:] = keys
    ERASE_ORDER[:] = erase_order or [5, 10, 2, 15, 8, 3, 12, 6, 13, 1, 11, 4, 14, 9]


def _finalize():
    if SHOTS and 'f0' in SHOTS[0]:
        return
    SHOTS.sort(key=lambda s: s['t'])
    for i, s in enumerate(SHOTS):
        s['f0'] = fr(s['t'])
        s['f1'] = fr(SHOTS[i + 1]['t']) if i + 1 < len(SHOTS) else TOTAL + 24
    _prep_typo()


def beat_phase(t):
    for t0, t1, sec, a in PULSES:
        if t0 <= t < t1:
            g = GRID[sec]
            return ((t - g['first']) / g['per']) % 1.0, a
    return 0.0, 0.0


# ---------------------------------------------------------------- composite sources
_tiles = None


def _tile_images():
    global _tiles
    if _tiles is None:
        tw, th = W // 4, H // 4
        _tiles = []
        for k in GRID_TILES:
            src = still_frame(k[0], k[1]) if isinstance(k, (tuple, list)) else load_still(k)
            _tiles.append(fit169(src, size=(tw, th)))
    return _tiles


def grid_frame(sh, f):
    tl = _tile_images()
    tw, th = W // 4, H // 4
    im = Image.new('RGB', (W, H), (0, 0, 0))
    tau = (f - sh['f0']) / FPS
    dur = (sh['f1'] - sh['f0']) / FPS
    if sh['kind'] == 'grid_fill':
        step = sh.get('step') or (dur - 0.05) / len(tl)
        for i, t in enumerate(tl):
            age = tau - i * step
            if age < -1e-6:
                continue
            tt = t
            if age < 2 / FPS:
                tt = Image.blend(t, Image.new('RGB', t.size, (255, 255, 255)), 0.75 if age < 1 / FPS else 0.3)
            im.paste(tt, ((i % 4) * tw, (i // 4) * th))
    else:
        step = (dur - 0.25) / max(1, len(ERASE_ORDER))
        gone = {}
        for n, i in enumerate(ERASE_ORDER):
            age = tau - (0.12 + n * step)
            if age >= 0:
                gone[i] = age
        dead = tuple(int(c * 0.10) for c in ACCENT)
        for i, t in enumerate(tl):
            x, y = (i % 4) * tw, (i // 4) * th
            if i in gone:
                im.paste(ImageChops.invert(t) if gone[i] < 1.5 / FPS else Image.new('RGB', t.size, dead), (x, y))
            else:
                im.paste(t, (x, y))
    d = ImageDraw.Draw(im)
    for k in range(1, 4):
        d.rectangle([k * tw - 1, 0, k * tw + 1, H], fill=(0, 0, 0))
        d.rectangle([0, k * th - 1, W, k * th + 1], fill=(0, 0, 0))
    return im


def quad_frame(sh, f):
    """2x2 cast board: one moving portrait slams in every `step` seconds"""
    step = sh.get('step') or (sh['f1'] - sh['f0']) / FPS / 4.0
    tau = (f - sh['f0']) / FPS
    im = Image.new('RGB', (W, H), (0, 0, 0))
    hw, hh = W // 2, H // 2
    for i, (key, tin) in enumerate(sh['tiles']):
        age = tau - i * step
        if age < -1e-6:
            continue
        src = clip_frame(key, tin + tau) if key in CLIPS else load_still(key)
        t = fit169(src, zoom=1.0 + 0.16 * math.exp(-age * 16), size=(hw, hh))
        if age < 2 / FPS:
            t = Image.blend(t, Image.new('RGB', t.size, (255, 255, 255)), 0.8 if age < 1 / FPS else 0.35)
        im.paste(t, ((i % 2) * hw, (i // 2) * hh))
    d = ImageDraw.Draw(im)
    d.rectangle([hw - 2, 0, hw + 1, H], fill=(0, 0, 0))
    d.rectangle([0, hh - 2, W, hh + 1], fill=(0, 0, 0))
    return im


# ---------------------------------------------------------------- transitions
def dir_blur(im, s, vertical=False):
    if s <= 1:
        return im
    if vertical:
        return im.resize((W, max(1, H // s)), Image.BOX).resize((W, H), Image.BILINEAR)
    return im.resize((max(1, W // s), H), Image.BOX).resize((W, H), Image.BILINEAR)


def radial_blur(im, amt):
    out = im
    for k, a in ((1.0 + amt, 0.5), (1.0 + 2 * amt, 0.33)):
        w = W / k
        h = H / k
        zi = im.resize((W, H), Image.BILINEAR, box=((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2))
        out = Image.blend(out, zi, a)
    return out


WHIP_OUT = [(0.10, 10), (0.34, 26)]              # (offset fraction, blur) on the last 2 frames of the outgoing shot
WHIP_IN = [(0.34, 26), (0.13, 12), (0.035, 4)]   # first 3 frames of the incoming shot
ZOOM_OUT = [1.16, 1.45]
ZOOM_IN = [1.55, 1.22, 1.06]
SPARSE = ('quad', 'grid_fill', 'grid_erase')     # mostly-black composites: motion transitions INTO them read as a black blip


def tr_state(sh, nxt, f):
    n = f - sh['f0']
    rem = sh['f1'] - 1 - f
    if sh.get('tr') and n < 3 and sh['tr'] != 'black' and sh['kind'] not in SPARSE:
        return sh['tr'], n, True
    if nxt is not None and nxt.get('tr') and rem < 2:
        return nxt['tr'], 1 - rem, False
    return None, 0, False


def ease_fn(name, p):
    if name == 'in':
        return p ** 2.6
    if name == 'out':
        return 1 - (1 - p) ** 2.2
    if name == 'exp':
        return p ** 1.7
    return p


def src_time(sh, tau):
    rd, rm = sh.get('ramp', (0.0, 1.0))
    return sh['tin'] + sh['speed'] * (tau + (rm - 1.0) * min(tau, rd))


def base_frame(f):
    _finalize()
    sh = nxt = None
    for i, s in enumerate(SHOTS):
        if s['f0'] <= f < s['f1']:
            sh = s
            nxt = SHOTS[i + 1] if i + 1 < len(SHOTS) else None
            break
    if sh is None:
        return BLACK.copy(), None
    n = f - sh['f0']
    tau = n / FPS
    tt = f / FPS
    dur = (sh['f1'] - sh['f0']) / FPS
    p = n / max(1, (sh['f1'] - sh['f0'] - 1))
    kind = sh['kind']
    rnd = random.Random(f * 7919)
    if kind == 'black':
        return BLACK.copy(), sh
    if nxt is not None and nxt.get('tr') == 'black' and sh['f1'] - 1 - f < 2:
        return BLACK.copy(), sh
    trk, trs, trin = tr_state(sh, nxt, f)
    sub_on = bool(sh.get('sub')) and (sh['f1'] - f) <= sh['sub'][2]
    sh_z = sh['z']
    if kind in ('grid_fill', 'grid_erase'):
        src = grid_frame(sh, f)
        sh_z = (1.0, 1.04) if kind == 'grid_fill' else (1.04, 1.0)
    elif kind == 'quad':
        src = quad_frame(sh, f)
        sh_z = (1.0, 1.03)
    elif kind == 'strobe':
        fl = sh['frames']
        key, tsrc = fl[(n // 2) % len(fl)]
        src = still_frame(key, tsrc)
        sh_z = (1.08, 1.30)
    elif sub_on:
        src = still_frame(sh['sub'][0], sh['sub'][1] + (sh['f1'] - f) / 24.0)
    else:
        key = sh['src']
        src = clip_frame(key, src_time(sh, tau)) if key in CLIPS else load_still(key)
    pe = ease_fn(sh['ease'], p)
    if sh['ease'] == 'exp':
        z = sh_z[0] * (sh_z[1] / sh_z[0]) ** pe
    else:
        z = sh_z[0] + (sh_z[1] - sh_z[0]) * pe
    for (ts, fac) in sh.get('stepz', []):
        if tt >= ts - 1e-6:
            z *= fac * (1 + 0.10 * math.exp(-(tt - ts) * 14))
    if sh['punch']:
        z *= 1 + sh['punch'] * math.exp(-tau * 9.0)
    ph, pa = beat_phase(tt)
    if pa and not sh.get('nopulse'):
        z *= 1 + pa * math.exp(-ph * 4.5)
    cx = sh['c'][0] + (sh['c1'][0] - sh['c'][0]) * pe
    cy = sh['c'][1] + (sh['c1'][1] - sh['c'][1]) * pe
    if sh.get('snap') and tt >= sh['snap'][0]:
        st, sf, sc_, sd = (list(sh['snap']) + [0.40])[:4]
        q = min(1.0, (tt - st) / sd)
        q = 1 - (1 - q) ** 3
        z *= 1 + sf * q
        cx += (sc_[0] - cx) * q
        cy += (sc_[1] - cy) * q
    if trk == 'zoom':
        z *= ZOOM_IN[trs] if trin else ZOOM_OUT[trs]
    sx = sy = 0.0
    if sh['shake']:
        amp = sh['shake'] * SC * (0.25 + 0.75 * math.exp(-tau * 5.0))
        sx = rnd.uniform(-amp, amp)
        sy = rnd.uniform(-amp, amp)
    im = fit169(src, zoom=max(1.0, z), cx=cx, cy=cy, shake=(sx, sy))
    if src.width < W * 0.8 and kind not in SPARSE:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
    if sh.get('hblur'):
        im = dir_blur(im, sh['hblur'])
    # look
    if sub_on or (kind == 'strobe' and (n // 2) % 2 == 0):
        im = neg_tint(im)
    elif kind == 'hit':
        im = neg_tint(im) if sh.get('look', 'neg') == 'neg' else ImageEnhance.Brightness(hard_bw(im)).enhance(1.05)
    elif kind == 'strobe':
        im = hard_bw(im)
    else:
        lut, sat = GRADES[sh['grade']]
        if sh.get('desat'):
            d0, dd, dsat = sh['desat']
            q = max(0.0, min(1.0, (tt - d0) / dd))
            sat = sat * (1 - q) + dsat * q
        if abs(sat - 1.0) > 0.01:
            im = ImageEnhance.Color(im).enhance(sat)
        im = im.point(lut)
    # chroma split
    ch = sh['chroma'] * SC
    if sh.get('glitch_tail'):
        rem_t = dur - tau
        ch = (2 + 22 * (1 - rem_t / sh['glitch_tail'])) * SC if rem_t < sh['glitch_tail'] else 0
    elif ch:
        ch = ch * (0.35 + 0.65 * math.exp(-tau * 6.0))
    if trk == 'glitch':
        ch = max(ch, ((18, 10, 4)[trs] if trin else (8, 18)[trs]) * SC)
    c2 = int(round(ch))
    if c2:
        r, g, b = im.split()
        im = Image.merge('RGB', (ImageChops.offset(r, c2, 0), g, ImageChops.offset(b, -c2, 0)))
    tears = 0
    if sh.get('glitch_tail') and (dur - tau) < sh['glitch_tail'] and rnd.random() < 0.6:
        tears = 1
    if trk == 'glitch':
        tears = 2
    for _ in range(tears):
        y0 = rnd.randint(0, H - int(135 * SC))
        hh = rnd.randint(int(30 * SC), int(120 * SC))
        strip = im.crop((0, y0, W, y0 + hh))
        im.paste(ImageChops.offset(strip, rnd.randint(-int(105 * SC), int(105 * SC)), 0), (0, y0))
    # motion transitions
    if trk and trk.startswith('whip'):
        d = trk.split('_')[1]
        vert = d in ('u', 'd')
        sign = -1 if d in ('l', 'u') else 1
        off, bl = (WHIP_IN[trs] if trin else WHIP_OUT[trs])
        px = int(sign * off * (H if vert else W)) * (-1 if trin else 1)
        im = dir_blur(im, bl, vert)
        im = ImageChops.offset(im, 0, px) if vert else ImageChops.offset(im, px, 0)
    elif trk == 'zoom':
        im = radial_blur(im, (0.10, 0.06, 0.03)[trs] if trin else (0.05, 0.10)[trs])
    if sh['vig']:
        im = ImageChops.multiply(im, vignette(sh['vig']))
    if sh.get('flicker') and rnd.random() < 0.10:
        im = Image.blend(im, BLACK, rnd.uniform(0.25, 0.5))
    if sh.get('strobe') and (n // sh['strobe']) % 2 == 1:
        im = Image.blend(im, BLACK, 0.92)
    if sh.get('dimtail'):
        rem_t = dur - tau
        if rem_t < sh['dimtail']:
            im = Image.blend(im, BLACK, 0.75 * (1 - rem_t / sh['dimtail']))
    if sh['flash'] and n < sh['flash']:
        a = (1 - n / sh['flash']) ** 1.5 * (0.95 if sh['flash'] >= 4 else 0.6)
        im = Image.blend(im, FLASHC if (sh.get('redflash') and n >= 1) else WHITE, a)
    if kind == 'hit' and n == 0:
        im = Image.blend(im, WHITE, 0.45)
    if sh.get('fadein') and n < sh['fadein']:
        im = Image.blend(BLACK, im, (n / sh['fadein']) ** 1.5)
    if sh.get('fadeout'):
        rem = sh['f1'] - 1 - f
        if rem < sh['fadeout']:
            im = Image.blend(im, BLACK, 1 - rem / sh['fadeout'] * 0.7)
    if sh.get('fadeblack'):
        q = max(0.0, min(1.0, (tt - sh['fadeblack'][0]) / sh['fadeblack'][1]))
        if q > 0:
            im = Image.blend(im, BLACK, q)
    return im, sh


def finish(im, f):
    return ImageChops.add(im, _GRAIN[f % len(_GRAIN)], 1, -128)


# ---------------------------------------------------------------- text
def text_rgba(txt, font, fill, stroke=0, stroke_fill=(0, 0, 0, 255), pad=24):
    d0 = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    l, t, r, b = d0.textbbox((0, 0), txt, font=font, stroke_width=stroke)
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


_chalk_noise = None


def chalkify(im, amount=0.45):
    global _chalk_noise
    if _chalk_noise is None:
        rs = np.random.RandomState(7)
        n = rs.rand(900, 3200).astype(np.float32)
        n = Image.fromarray((n * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
        _chalk_noise = np.asarray(n).astype(np.float32) / 255.0
    a = np.asarray(im.split()[3]).astype(np.float32) / 255.0
    n = _chalk_noise[:a.shape[0], :a.shape[1]]
    n = np.clip((n - 0.5) * 3.2 + 0.5, 0, 1)
    out = im.copy()
    out.putalpha(Image.fromarray((np.clip(a * (1 - amount + amount * n), 0, 1) * 255).astype(np.uint8)))
    return out


def shadow_of(im, blur=10, alpha=0.8):
    a = im.split()[3].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(min(255, v * alpha * 1.6)))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sh.putalpha(a)
    return sh


# style -> (font role, number size, text size, colour, jitter)
TYPO_STYLES = {
    'chalk': ('hand', 200, 136, (246, 244, 234, 255), False),
    'blood': ('hand2', 250, 178, (240, 36, 40, 255), True),
}


def _prep_typo():
    for ln in TYPO:
        role, nsz, tsz, col, jit = TYPO_STYLES[ln['style']]
        fnum = ImageFont.truetype(_font_path(role), int(nsz * SC))
        ftxt = ImageFont.truetype(_font_path(role), int(tsz * SC))
        pad = int(24 * SC)
        x0 = int((130 if ln['side'] == 'L' else 1180) * SC)
        lead = int(150 * SC)
        ybase = int(930 * SC)
        items = []
        nrows = len(ln['rows'])
        for r, row in enumerate(ln['rows']):
            fnt = fnum if r == 0 else ftxt
            yb = ybase - (nrows - 1 - r) * lead - (int(36 * SC) if r == 0 else 0)
            x = x0
            space = int(fnt.getlength(' ') * 1.15)
            for wtxt, ts in row:
                wi = chalkify(text_rgba(wtxt, fnt, col, stroke=1, stroke_fill=col, pad=pad), 0.42)
                items.append(dict(im=wi, sh=shadow_of(wi, max(2, int(12 * SC)), 0.95), x=x - pad, y=yb - (wi.height - pad), ts=ts))
                x += int(fnt.getlength(wtxt)) + space
        for i, it in enumerate(items):
            nxt = items[i + 1]['ts'] if i + 1 < len(items) else ln['end']
            it['te'] = min(nxt, it['ts'] + 0.42)
        ln['items'] = items
        ln['jit'] = jit


def typo_overlay(im, f):
    t = f / FPS
    for ln in TYPO:
        if not (ln['t0'] <= t < ln['t1']):
            continue
        rnd = random.Random((f // 2) * 31 + 5)
        j = int(3 * SC)
        for it in ln['items']:
            if t < it['ts']:
                continue
            p = min(1.0, (t - it['ts'] + 1 / FPS) / max(0.08, it['te'] - it['ts']))
            wimg, simg = it['im'], it['sh']
            cw = max(1, int(wimg.width * p))
            jx = jy = 0
            if ln['jit']:
                jx, jy = rnd.randint(-j, j), rnd.randint(-j, j)
            box = (0, 0, cw, wimg.height)
            im.paste(simg.crop(box), (it['x'] + int(round(4.5 * SC)) + jx, it['y'] + int(6 * SC) + jy), simg.crop(box))
            im.paste(wimg.crop(box), (it['x'] + jx, it['y'] + jy), wimg.crop(box))
    return im


_title = {}


def title_lockup(card, scale=1.0):
    key = (id(card), round(scale, 3))
    if key in _title:
        return _title[key]
    S2 = 2
    DW, DH = 1920, 1080
    size = card['size']
    while True:
        f_big = ImageFont.truetype(_font_path('title'), int(size * S2))
        tot = sum(f_big.getlength(p[0]) for p in card['parts']) - 30 * S2 * sum(1 for p in card['parts'] if p[0] == ' ')
        if tot <= 1720 * S2 or size <= 60:
            break
        size -= 8
    cv = Image.new('RGBA', (DW * S2, DH * S2), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    x = (DW * S2 - tot) / 2
    y = (540 - int(size * 0.6227)) * S2
    for txt, col in card['parts']:
        if col:
            d.text((x, y), txt, font=f_big, fill=tuple(col) + (255,))
        x += f_big.getlength(txt) - (30 * S2 if txt == ' ' else 0)
    sub_y = y + int(size * 1.4529) * S2
    if card.get('sub'):
        fs = ImageFont.truetype(_font_path('small'), int(30 * S2))
        tw = fs.getlength(card['sub'])
        d.text(((DW * S2 - tw) / 2, sub_y), card['sub'], font=fs, fill=(205, 203, 196, 235))
        d.rectangle([(DW * S2 - tw) / 2, sub_y - 16 * S2, (DW * S2 + tw) / 2, sub_y - 16 * S2 + 3],
                    fill=(int(ACCENT[0] * 0.77), int(ACCENT[1] * 0.35), int(ACCENT[2] * 0.44), 255))
    if card.get('credit'):
        fc = ImageFont.truetype(_font_path('small'), int(32 * S2))
        tw = fc.getlength(card['credit'])
        d.text(((DW * S2 - tw) / 2, 960 * S2), card['credit'], font=fc, fill=(232, 230, 224, 240))
    im = cv.resize((W, H), Image.LANCZOS)
    if abs(scale - 1.0) > 1e-3:
        nw, nh = int(W * scale), int(H * scale)
        big = im.resize((nw, nh), Image.BICUBIC)
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        im.paste(big, ((W - nw) // 2, (H - nh) // 2))
    _title[key] = im
    return im


def rgb_split_rgba(ov, shf):
    r, g, b, a = ov.split()
    return Image.merge('RGBA', (ImageChops.offset(r, shf, 0), g, ImageChops.offset(b, -shf, 0),
                                ImageChops.lighter(ImageChops.offset(a, shf, 0), ImageChops.offset(a, -shf, 0))))


def title_overlay(im, f):
    t = f / FPS
    if TITLE and fr(TITLE['t0']) <= f < fr(TITLE['t1']):
        n = f - fr(TITLE['t0'])
        tau = n / FPS
        ov = title_lockup(TITLE, 1.0 + 0.16 * math.exp(-tau * 11) + 0.012 * tau)
        if n < 5:
            ov = rgb_split_rgba(ov, int(27 * SC * (1 - n / 5)))
        rem = fr(TITLE['t1']) - 1 - f
        if rem < 2:
            ov = rgb_split_rgba(ov, int((39, 18)[rem] * SC))
        plate = shadow_of(ov, blur=int(27 * SC), alpha=0.9)
        im.paste(plate, (0, 0), plate)
        im.paste(ov, (0, 0), ov)
    elif ENDCARD and t >= ENDCARD['t0']:
        n = f - fr(ENDCARD['t0'])
        tau = n / FPS
        ov = title_lockup(ENDCARD, 1.0 + 0.05 * math.exp(-tau * 9) + 0.006 * tau)
        a = (n + 1) / 4 if n < 3 else 1.0
        if ENDCARD.get('fade') and t > ENDCARD['fade'][0]:
            a = max(0.0, 1 - (t - ENDCARD['fade'][0]) / ENDCARD['fade'][1])
        if a < 1.0:
            ov = ov.copy()
            ov.putalpha(ov.split()[3].point(lambda v: int(v * a)))
        if ENDCARD.get('glitch'):
            g0 = fr(ENDCARD['glitch'][0])
            if 0 <= f - g0 < 5:
                gn = f - g0
                gsrc = ENDCARD['glitch'][1]
                if gn < 2 and gsrc:
                    ghost = fit169(still_frame(gsrc[0], gsrc[1]))
                    ghost = ImageEnhance.Contrast(ghost.convert('L')).enhance(1.5).convert('RGB')
                    im = Image.blend(im, ImageChops.multiply(ghost, ACCMUL), 0.42)
                ov = rgb_split_rgba(ov, int(30 * SC * (1 - gn / 5)))
        im.paste(ov, (0, 0), ov)
        if n < 4:
            im = Image.blend(im, WHITE, 0.35 * (1 - n / 4))
    return im


_lyr = {}


def lyric_overlay(im, f):
    t = f / FPS
    for a, b, txt in LYRICS:
        if a <= t < b:
            if txt not in _lyr:
                fnt = ImageFont.truetype(_font_path('sub'), int(50 * SC))
                _lyr[txt] = text_rgba(txt, fnt, (250, 248, 242, 255), stroke=max(2, int(round(4.5 * SC))),
                                      stroke_fill=(10, 8, 8, 235), pad=int(30 * SC))
            ov = _lyr[txt]
            al = min(1.0, (t - a) * FPS / 3 + 0.34, (b - t) * FPS / 3 + 0.34)
            if al < 1:
                ov = ov.copy()
                ov.putalpha(ov.split()[3].point(lambda v: int(v * al)))
            im.paste(ov, ((W - ov.width) // 2, int(972 * SC) - ov.height // 2), ov)
    return im


def render_all(f):
    base, sh = base_frame(f)
    clean = finish(base.copy(), f)
    m = title_overlay(typo_overlay(base, f), f)
    main_ = finish(m, f)
    return {'clean': clean, 'main': main_, 'lyric': lyric_overlay(main_.copy(), f)}


def render_frame(f, variant='main'):
    return render_all(f)[variant]


# ---------------------------------------------------------------- checks / drivers
COMPOSITE = ('hit', 'strobe', 'quad', 'grid_fill', 'grid_erase', 'black')


def check():
    """the two mistakes that are easy to make and ugly on screen: a clip reused as a full shot,
    and a shot that asks for footage past the end of its clip (it would freeze on the last frame)."""
    _finalize()
    ok = True
    use = Counter()
    for s in SHOTS:
        key = s['src']
        if s['kind'] in COMPOSITE:
            continue
        if key not in CLIPS and key not in STILLS:
            ok = False
            print(f"!! unknown source {key} at {s['t']:.2f}")
            continue
        if not s.get('dup_ok'):
            use[key] += 1
        if key in CLIPS:
            dur = (min(s['f1'], TOTAL) - s['f0'] - 1) / FPS
            a, b = src_time(s, 0), src_time(s, dur)
            lim = CLIPS[key]['dur'] - 1.0 / CLIPS[key]['cfps']
            if min(a, b) < -0.02 or max(a, b) > lim + 0.05:
                ok = False
                print(f"!! source range at {s['t']:.2f} {key}: {a:.2f}->{b:.2f}s but the clip is {lim:.2f}s long")
    for k, v in use.items():
        if v > 1:
            ok = False
            print(f"!! {k} is used as a full shot {v} times (pick another clip, or mark dup_ok=True if it is deliberate)")
    lens = [(min(s['f1'], TOTAL) - s['f0']) / FPS for s in SHOTS]
    print(f"shots {len(SHOTS)}  avg {sum(lens) / len(lens):.2f}s  unique clips {len([k for k in use if k in CLIPS])}/{len(CLIPS)}")
    unused = sorted(k for k in CLIPS if k not in use and not any(k == t[0] for s in SHOTS for t in s.get('tiles', [])))
    print("unused clips:", " ".join(unused) if unused else "-")
    return ok


def _label_font():
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, 14)
    return ImageFont.load_default()


def sheet(name='timeline', frames=None, variant='main', cols=6, tw=320):
    _finalize()
    th = int(tw * H / W)
    font = _label_font()
    if frames is None:
        frames = []
        for s in SHOTS:
            n = min(s['f1'], TOTAL) - s['f0']
            if n <= 10:
                frames.append((s['f0'] + n // 2, s))
            else:
                frames.append((s['f0'] + 3, s))
                frames.append((min(s['f1'], TOTAL) - 3, s))
    os.makedirs(os.path.join(WORK, 'sheets'), exist_ok=True)
    per = cols * 7
    for pg in range(0, len(frames), per):
        grp = frames[pg:pg + per]
        rows = (len(grp) + cols - 1) // cols
        shimg = Image.new('RGB', (cols * tw, rows * (th + 18)), (20, 20, 20))
        d = ImageDraw.Draw(shimg)
        for k, (f, s) in enumerate(grp):
            im = render_frame(f, variant).resize((tw, th), Image.BILINEAR)
            x, y = (k % cols) * tw, (k // cols) * (th + 18)
            shimg.paste(im, (x, y + 18))
            d.text((x + 3, y + 2), f"{f / FPS:6.2f}s f{f} {s['src'] if s else ''}", font=font, fill=(255, 230, 80))
        p = os.path.join(WORK, 'sheets', f"{name}_{pg // per:02d}.jpg")
        shimg.save(p, quality=80)
        print(p)


VARIANTS = (('main', ''), ('lyric', '_가사자막'), ('clean', '_텍스트없음'))


def render(t0=0.0, t1=None, tag='', variants=('main', 'lyric', 'clean'), crf=16):
    _finalize()
    f0 = fr(t0)
    f1 = TOTAL if t1 is None else fr(t1)
    procs = {}
    for v in variants:
        outp = os.path.join(WORK, f"render_{v}{tag}.mp4")
        procs[v] = subprocess.Popen(
            [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
             "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-colorspace", "bt709", "-color_primaries", "bt709",
             "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", outp], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        fr_all = render_all(f)
        for v in variants:
            procs[v].stdin.write(fr_all[v].tobytes())
        if (f - f0) % 240 == 0:
            print(f"frame {f}/{f1}", flush=True)
    for v in variants:
        procs[v].stdin.close()
        procs[v].wait()
    print('render done')


def out_path(suffix):
    return os.path.join(OUT, f"{NAME}_{H}p{suffix}.mp4")


def mux():
    for v, suffix in VARIANTS:
        src = os.path.join(WORK, f"render_{v}.mp4")
        if os.path.exists(src):
            subprocess.run([FF, "-v", "error", "-y", "-i", src, "-i", os.path.join(WORK, 'song.wav'), "-map", "0:v", "-map", "1:a",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", out_path(suffix)], check=True)
            print(out_path(suffix))


def qa():
    """checks on the real output file: stream facts, black frames, loudness, and frame sheets to look at"""
    main_ = out_path('')
    for v, suffix in VARIANTS:
        p = out_path(suffix)
        if os.path.exists(p):
            print(os.path.basename(p), tools.probe(p), f"{os.path.getsize(p) / 1e6:.0f}MB")
    r = subprocess.run([FF, "-v", "error", "-i", main_, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
    print("decode check (every frame + audio):", "clean" if not r else f"{len(r.splitlines())} error lines\n" + r[:600])
    small = sorted({s['src'] for s in SHOTS if s['src'] in CLIPS and CLIPS[s['src']]['h'] < H * 0.95})
    if small:
        print(f"sources smaller than the output ({len(small)} clips, resized up — say so, do not call them native {H}p):", " ".join(small))
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", main_, "-vf", "freezedetect=n=0.03:d=1.2", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    fz = [ln[ln.index('freeze_'):] for ln in r.splitlines() if 'freeze_start' in ln or 'freeze_duration' in ln]
    print("frozen picture >= 1.2s (title cards and deliberate holds are fine):", " | ".join(fz) if fz else "none")
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", main_, "-vf", "blackdetect=d=0.05:pix_th=0.06", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    print("black stretches (each one should be intentional):")
    for ln in r.splitlines():
        if 'blackdetect' in ln:
            print("  " + ln[ln.index('black_start'):])
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", main_, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    print("loudness:", " | ".join(l.strip() for l in r.splitlines() if l.strip().startswith(('I:', 'Peak:')))[-60:])
    tmp = os.path.join(WORK, 'qa')
    os.makedirs(tmp, exist_ok=True)
    for old in glob.glob(os.path.join(tmp, '*.jpg')):
        os.remove(old)
    src = out_path('_가사자막') if os.path.exists(out_path('_가사자막')) else main_
    subprocess.run([FF, "-v", "error", "-i", src, "-vf", "fps=3,scale=256:144", "-q:v", "5", os.path.join(tmp, "%04d.jpg")])
    fs = sorted(glob.glob(os.path.join(tmp, '*.jpg')))
    font = _label_font()
    cols = 10
    per = cols * 9
    for pg in range(0, len(fs), per):
        g = fs[pg:pg + per]
        sh = Image.new('RGB', (cols * 256, ((len(g) + cols - 1) // cols) * 144))
        d = ImageDraw.Draw(sh)
        for k, p in enumerate(g):
            sh.paste(Image.open(p), ((k % cols) * 256, (k // cols) * 144))
            d.text(((k % cols) * 256 + 3, (k // cols) * 144 + 2), f"{(pg + k) / 3 + 1 / 6:.2f}", font=font, fill=(255, 255, 0))
        outp = os.path.join(WORK, 'sheets', f"qa_{pg // per}.jpg")
        sh.save(outp, quality=78)
        print(outp)


def _ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt():
    """lyrics as a separate subtitle file (the main video carries no lyric text). Returns problems found."""
    lines = sorted(LYRICS)
    problems = []
    for i, (a, b, t) in enumerate(lines):
        if b <= a:
            problems.append(f"line {i + 1} ends before it starts ({a:.2f}->{b:.2f})")
        if i and a < lines[i - 1][1] - 1e-3:
            problems.append(f"line {i + 1} overlaps the previous one at {a:.2f}s")
        if b > DUR + 0.05:
            problems.append(f"line {i + 1} runs past the end of the song ({b:.2f}s > {DUR:.2f}s)")
    p = os.path.join(OUT, f"{NAME}.srt")
    if lines:
        open(p, 'w', encoding='utf-8').write(''.join(f"{i + 1}\n{_ts(a)} --> {_ts(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(lines)))
        print(p, f"({len(lines)} lines)")
    else:
        print("no lyrics registered — no SRT written")
    for pr in problems:
        print("!! SRT:", pr)
    return problems


def cutlist(sections=None):
    """writes a human-readable cut list next to the deliverables. sections = [(time, label), ...]"""
    _finalize()
    L = [f"# {NAME} — 컷 리스트", "", f"- {W}×{H} · {FPS}fps · {DUR:.2f}초 · {len(SHOTS)}컷", ""]
    secs = sorted(sections or [(0.0, '전체')])
    si = 0
    for i, s in enumerate(SHOTS):
        while si < len(secs) and s['t'] >= secs[si][0] - 0.02:
            L += ["", f"## {secs[si][1]}", "", "| # | 시작 | 길이 | 소스 | 전환 |", "|---|---|---|---|---|"]
            si += 1
        a = s['f0'] / FPS
        e = min(s['f1'], TOTAL) / FPS
        m = int(a // 60)
        key = s['src']
        src = CLIPS[key].get('id', key) if key in CLIPS else key
        if s['kind'] == 'quad':
            src = '2×2 보드 (' + ', '.join(CLIPS[k].get('id', k) if k in CLIPS else k for k, _ in s['tiles']) + ')'
        L.append(f"| {i + 1:02d} | {m}:{a - 60 * m:05.2f} | {e - a:.2f}s | {src} | {s.get('tr') or ''} |")
    L += ["", "## 사용 소스", "", "| 키 | 파일 | 사용 구간(초) | 원본 규격 |", "|---|---|---|---|"]
    seen = set()
    for s in SHOTS:
        keys = [(s['src'], s)] if s['src'] in CLIPS or s['src'] in STILLS else []
        keys += [(k, None) for k, _ in s.get('tiles', [])] + [(k, None) for k, _ in s.get('frames', [])]
        if s.get('sub'):
            keys.append((s['sub'][0], None))
        for key, full in keys:
            if key in CLIPS:
                m = CLIPS[key]
                if full is not None:
                    d = (min(full['f1'], TOTAL) - full['f0'] - 1) / FPS
                    a, b = sorted((src_time(full, 0), src_time(full, d)))
                    rng = f"{a:.2f}–{b:.2f}"
                else:
                    rng = "프레임 인용"
                row = (key, os.path.basename(m['file']), rng, f"{m['w']}×{m['h']} {m['cfps']:.0f}fps")
            elif key in STILLS:
                row = (key, os.path.basename(STILLS[key]), "스틸", "")
            else:
                continue
            if (row[0], row[2]) not in seen:
                seen.add((row[0], row[2]))
                L.append("| " + " | ".join(row) + " |")
    p = os.path.join(OUT, f"{NAME}_컷리스트.md")
    open(p, 'w').write('\n'.join(L) + '\n')
    print(p)


def main(sections=None):
    """command line of a project file:
       edl | sheet [variant] | frames NAME t ... | seq NAME t count | render [t0 t1 tag] | mux | srt | qa | cutlist | all"""
    _finalize()
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'edl'
    if cmd == 'edl':
        for s in SHOTS:
            print(f"{s['t']:7.2f} {s['f0']:5d}-{min(s['f1'], TOTAL):5d} {(min(s['f1'], TOTAL) - s['f0']) / FPS:5.2f}s "
                  f"{s['src']:8s} {s['kind'] or '':10s} {s.get('tr') or ''}")
        print('CHECK OK' if check() else 'CHECK FAILED — fix before rendering')
    elif cmd == 'sheet':
        sheet(variant=sys.argv[2] if len(sys.argv) > 2 else 'main')
    elif cmd == 'frames':
        sheet(name=sys.argv[2], frames=[(fr(float(x)), None) for x in sys.argv[3:]], cols=4, tw=480)
    elif cmd == 'seq':
        f0 = fr(float(sys.argv[3]))
        sheet(name=sys.argv[2], frames=[(f0 + i, None) for i in range(int(sys.argv[4]))], cols=6, tw=320)
    elif cmd == 'render':
        if len(sys.argv) >= 4:
            render(float(sys.argv[2]), float(sys.argv[3]), tag=sys.argv[4] if len(sys.argv) > 4 else '_part', variants=('main',), crf=20)
        else:
            render()
    elif cmd == 'mux':
        mux()
    elif cmd == 'qa':
        qa()
    elif cmd == 'cutlist':
        cutlist(sections)
    elif cmd == 'srt':
        srt()
    elif cmd == 'all':
        if not check():
            raise SystemExit('CHECK FAILED — fix before rendering')
        render()
        mux()
        srt()
        qa()
        cutlist(sections)
