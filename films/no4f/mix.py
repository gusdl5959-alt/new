"""Mix: everything the camcorder microphone would have recorded → mix.wav (48 kHz stereo). No score.
Fluorescent hum (follows the light around the camera) / room tone per space / tape hiss / footsteps on terrazzo / breathing / cloth / AF + zoom motors /
the school PA chime (Westminster quarters, public domain) through a ceiling speaker / ballast pops / a chair, a sliding door, light steps in the lit classroom /
a step on the landing above / a rattling door / a low drone on the 4th floor / digital silences / tape tears / colour-bar tone / rewind / low-battery beeps.
All timings come from events.json (exported from the page's window.EV), the same source as the picture."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB') or os.path.abspath(os.path.join(HERE, '../..'))
sys.path.insert(0, LIB)
import numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d
from core.audio.sfx import SR, bp, lp, hp, limit
from core.audio.sampler import room as reverb

rng = np.random.default_rng(1103)
E = json.load(open(os.path.join(HERE, 'events.json'))); DUR = E['dur']; EV = E['ev']; N = int(DUR * SR)
ev = lambda ty: [e for e in EV if e['type'] == ty]
one = lambda ty: ev(ty)[0]
C = one('curves'); CDT = C['dt']
tt = np.arange(N, dtype=np.float64) / SR
def curve(name):
    v = np.asarray(C[name], np.float64); return np.interp(tt, np.arange(len(v)) * CDT, v)
LC, CZ, FEAR = curve('lc'), curve('z'), curve('fear')
def nz(n): return rng.standard_normal(n)
def sec(d): return int(round(d * SR))
def env_ar(n, a, r):
    x = np.ones(n); na = min(n, max(1, sec(a))); x[:na] = np.linspace(0, 1, na)
    nr = min(n, max(1, sec(r))); x[n - nr:] *= np.exp(-np.linspace(0, 5, nr)); return x
def fade(n, fi=.01, fo=.01):
    x = np.ones(n); a, b = min(n, sec(fi)), min(n, sec(fo)); x[:a] = np.linspace(0, 1, a); x[n - b:] *= np.linspace(1, 0, b); return x
def put(b, x, t, g=1., pan=0.):
    """mono or stereo x into bus b at time t (equal-power pan for mono)"""
    i = sec(t); j = min(len(b), i + len(x))
    if i >= len(b) or j <= max(i, 0): return
    if i < 0: x = x[-i:]; i = 0; j = min(len(b), len(x))
    x = x[:j - i]
    if x.ndim == 2: b[i:j] += (x * g).astype(np.float32)
    else:
        l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
        b[i:j, 0] += (x * g * l).astype(np.float32); b[i:j, 1] += (x * g * r).astype(np.float32)
def bus(): return np.zeros((N, 2), np.float32)
def hashjs(n): v = np.sin(n * 127.1 + 311.7) * 43758.5453; return v - np.floor(v)   # same as core/lib.js hash

REC0 = one('recOn')['t'] + .25; FREEZE = one('freeze')['t']; OFF = one('recOff')['t']; END = one('end')['t']
TEARS = ev('tear'); HUSH = ev('hush')
rec = ((tt >= REC0) & (tt < FREEZE)).astype(np.float32)
inRoom = (CZ > .05).astype(np.float64); inRoom = uniform_filter1d(inRoom, sec(.4))
inStair = (CZ < -40.2).astype(np.float64)

# ———————— Fluorescent hum: 60 Hz mains → 120 Hz + harmonics, ballast buzz, a faint whine; level follows the light around the camera ————————
wob = 1 + .004 * np.sin(2 * np.pi * .13 * tt) + .002 * np.sin(2 * np.pi * .71 * tt)
ph = 2 * np.pi * 120 * np.cumsum(wob) / SR
hum = sum(a * np.sin(k * ph + k * 1.3) for k, a in [(1, 1.), (2, .5), (3, .4), (4, .2), (5, .14), (7, .05)])
buzz = bp(np.sign(np.sin(ph)) * .3 + nz(N) * .05, 900, 3200, 2) * .5
whine = np.sin(2 * np.pi * 9150 * tt + .3 * np.sin(2 * np.pi * .2 * tt)) * .04
del ph
fl4 = ((tt >= TEARS[3]['t'] + .5) & (tt < TEARS[4]['t'] + .5)).astype(np.float64)   # on the 4th floor the hum sits lower (detuned by tape)
humlvl = np.clip(LC, 0, 1.2) ** 1.3 * (1 + .2 * inRoom) * (1 - .45 * inStair)
hum_bed = (hum * .1 * (1 - .2 * fl4) + buzz * .05 + whine * .25) * humlvl * rec
del hum, buzz, whine
# bad tubes buzzing now and then (picked where the picture has flickery tubes nearby)
for t0 in [130, 152, 160, 190, 199, 230, 262, 270, 282, 352, 361, 380, 395]:
    d = rng.uniform(.4, 1.3); n = sec(d)
    z = bp(nz(n), 1800, 4200, 2) * (rng.random(n // 480 + 1).repeat(480)[:n] > .5) * env_ar(n, .05, .2)
    a = sec(t0); hum_bed[a:a + n] += z * .014
amb = bus(); amb[:, 0] = hum_bed; amb[:, 1] = np.roll(hum_bed, 37)
del hum_bed
# Room tone: the duty room (close, small), the corridor (wide, faint air), the stairwell (hollow)
air = lp(nz(N), 500) * .006 * rec * (1 - inRoom) + bp(nz(N), 60, 300) * .004 * rec * inStair
amb[:, 0] += air.astype(np.float32); amb[:, 1] += np.roll(air, 211).astype(np.float32)
del air
# A wall clock ticking in the duty room (off screen)
ck = np.zeros(N)
for t in np.arange(REC0 + .3, DUR, 1.0):
    i = sec(t)
    if i + 400 < N: k = np.arange(400) / SR; ck[i:i + 400] += (np.sin(2 * np.pi * 3200 * k) + .5 * np.sin(2 * np.pi * 5100 * k)) * np.exp(-k / .003)
ck *= inRoom * rec * .016
put(amb, ck, 0, 1, .35)

# ———————— Tape hiss + the reel motor ————————
hiss = hp(nz(N), 3500, 2) * .0055
hiss_g = np.clip(rec + (tt < 11.0) * .9 + ((tt >= FREEZE) & (tt < OFF + .2)) * 1.2, 0, 1.2)
hs = bus(); hs[:, 0] = hiss * hiss_g; hs[:, 1] = np.roll(hiss, 91) * hiss_g
del hiss

# ———————— Foley ————————
fx, fxw = bus(), bus()   # dry / sent to the corridor reverb
def step(v, hard=1., soft=False):
    n = sec(.25); t = np.arange(n) / SR
    heel = lp(nz(n), 1800) * np.exp(-t / .012) * 1.2 + np.sin(2 * np.pi * rng.uniform(90, 120) * t) * np.exp(-t / .03) * .6
    click = hp(nz(n), 2500) * np.exp(-t / .004) * (.5 if not soft else .1)
    sq = bp(nz(n), 1800, 3600, 2) * np.exp(-np.maximum(t - .04, 0) / .02) * (t > .035) * rng.uniform(0, .5) * hard   # rubber sole squeak on polish
    return (heel + click + sq) * v
for e in ev('step'):
    x = step(e['v'] * rng.uniform(.85, 1.1)); room = e['t'] < 99.5 or e['t'] > 447.4
    put(fx, x, e['t'], .2, rng.uniform(-.12, .12)); put(fxw, x, e['t'], .05 if room else .14)
for e in ev('run'):
    x = step(1.6 * rng.uniform(.9, 1.1), 1.4); put(fx, x, e['t'], .26, rng.uniform(-.15, .15)); put(fxw, x, e['t'], .2)
for e in ev('rustle'):
    d = rng.uniform(.35, .6); n = sec(d)
    x = bp(nz(n), 1500, 6500, 2) * env_ar(n, d * .3, d * .5) * (.5 + .5 * np.abs(uniform_filter1d(nz(n), 300)) * 8)
    put(fx, x * e['v'], e['t'], .06, rng.uniform(-.3, .3))
def clack(n=.08):
    k = sec(n); t = np.arange(k) / SR
    return hp(nz(k), 1500) * np.exp(-t / .006) + np.sin(2 * np.pi * 180 * t) * np.exp(-t / .02) * .8
def motor(d, f0, f1):
    k = sec(d); t = np.arange(k) / SR; f = np.linspace(f0, f1, k); p = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(p) + .4 * np.sin(2 * p) + .2 * np.sin(3 * p)) * env_ar(k, .05, d * .6) * .3 + bp(nz(k), 800, 3000) * .05 * env_ar(k, .05, d * .6)
r0 = one('recOn')['t']; put(fx, clack(), r0, .3); put(fx, motor(.9, 90, 230), r0 + .05, .1)
# picking the camera up off the desk / setting it down on the desk (a wooden knock through the body)
def knock(v=1.):
    k = sec(.3); t = np.arange(k) / SR
    return (np.sin(2 * np.pi * 140 * t) * np.exp(-t / .04) + bp(nz(k), 300, 1500) * np.exp(-t / .02) * .8 + hp(nz(k), 2000) * np.exp(-t / .004) * .4) * v
put(fx, knock(.7), one('pickup')['t'] + .05, .3); put(fx, knock(1.2), one('setdown')['t'] - .02, .45)
for e in ev('zoom'):
    k = sec(e['d']); t = np.arange(k) / SR; p = 2 * np.pi * np.cumsum(1350 + 60 * np.sin(2 * np.pi * 11 * t)) / SR
    x = (np.sin(p) + .15 * np.sign(np.sin(p))) * fade(k, .06, .1) + bp(nz(k), 2000, 5000) * .15 * fade(k, .06, .1)
    put(fx, bp(x, 700, 5000), e['t'], .025)
for e in ev('af'):
    for j in range(rng.integers(3, 6)):
        k = sec(.012); c = hp(nz(k), 3000) * np.exp(-np.arange(k) / SR / .002); put(fx, c, e['t'] + j * rng.uniform(.04, .09), .06)
def ballast(g=1.):
    k = sec(.14); t = np.arange(k) / SR
    tink = (np.sin(2 * np.pi * 3150 * t) + .6 * np.sin(2 * np.pi * 4720 * t)) * np.exp(-t / .03)
    zz = bp(np.sign(np.sin(2 * np.pi * 120 * t)) + nz(k) * .3, 1500, 4000) * np.exp(-t / .04)
    return (tink * .15 + zz * .3) * g
for i, e in enumerate(ev('flick')):
    f = e['t'] + .03
    for t0, gg in [(f - .03, .5), (f + .1 + i * .02, .8)]: put(fx, ballast(gg), t0, .22); put(fxw, ballast(gg), t0, .1)
# The lit classroom: a chair scraping (through the wall), the back door sliding open, light steps passing very close
def scrape(d):
    k = sec(d); t = np.arange(k) / SR
    f = 22 + 14 * np.sin(np.pi * t / d) + nz(k).cumsum() * .0005
    pulses = (np.diff(np.floor(np.cumsum(f / SR)), prepend=0) > 0).astype(float)
    x = sum(bp(pulses, fc * .9, fc * 1.1, 2) for fc in (380, 900, 1700)) + bp(nz(k), 400, 2500) * .05
    return lp(x * fade(k, .05, .15), 1600)
x = scrape(.9); put(fx, x / (np.abs(x).max() + 1e-9), one('chair')['t'], .1, -.5); put(fxw, x / (np.abs(x).max() + 1e-9), one('chair')['t'], .1)
e = one('slide'); k = sec(e['d'] + .2); t = np.arange(k) / SR
rumble = lp(nz(k), 220) * 2.5 + bp((rng.random(k) > .9993).astype(float), 600, 2400) * 4
rumble *= np.sin(np.pi * np.clip(t / (e['d'] + .2), 0, 1)) ** .7
rumble += np.pad(knock(.6), (sec(e['d']), 0))[:k] * 1.2           # it hits the stop
put(fx, rumble, e['t'], .1, -.35); put(fxw, rumble, e['t'], .12)
e = one('lightsteps')
for j, t0 in enumerate(np.arange(e['t'], e['t'] + e['d'], .46)):
    pan = -.8 + 1.6 * (t0 - e['t']) / e['d']
    x = step(.55, .1, True); put(fx, x, t0, .16, pan); put(fxw, x, t0, .1)
e = one('off'); put(fx, clack(.06) * .9, e['t'] - .02, .25, -.4); put(fx, ballast(1.0), e['t'], .25, -.4); put(fxw, ballast(1.0), e['t'], .12)
# Stairwell: one step from the landing above, hollow and far
x = lp(step(1.0, .2), 900); put(fxw, x, one('above')['t'], .55); put(fx, x, one('above')['t'], .05)
# The door on the 4th floor rattling in its frame
e = one('rattle'); k = sec(e['d']); rat = np.zeros(k)
tk = 0.
while tk < e['d'] - .1:
    i = sec(tk); kn = knock(rng.uniform(.4, 1.0) * (1 - .6 * tk / e['d']))[:k - i]; rat[i:i + len(kn)] += kn
    tk += rng.uniform(.06, .14)
put(fx, bp(rat, 120, 3000), e['t'], .14, -.2); put(fxw, rat, e['t'], .18)
# Tubes dying one by one (4th floor), then everything restriking at once
for e in ev('die'):
    dist = abs(e['z'] - (-15.6)); g = 1 / (1 + dist * .08)
    pop = ballast(1.3) + np.pad(clack(.05), (0, sec(.09)))[:sec(.14)] * .6
    put(fx, pop, e['t'], .3 * g); put(fxw, pop, e['t'], .25 * g)
e = one('restrike'); k = sec(.6); t = np.arange(k) / SR
thunk = np.sin(2 * np.pi * 48 * t) * np.exp(-t / .12) + lp(nz(k), 500) * np.exp(-t / .05) * .6 + bp(np.sign(np.sin(2 * np.pi * 120 * t)), 1500, 4000) * np.exp(-t / .08) * .3
for j in range(7): put(fx, ballast(1.0), e['t'] + j * .012, .14, rng.uniform(-.6, .6))
put(fx, thunk, e['t'], .38); put(fxw, thunk, e['t'], .3)
# Ending: the corridor tubes going out, far → near (seen through the doorway)
for e in ev('out'):
    d = abs(e['z'] - 3.78); g = 1 / (1 + d * .09)
    put(fx, ballast(1.0), e['t'], .5 * g, .05); put(fxw, ballast(1.0), e['t'], .5 * g)
# Duty-room tube stuttering (the same hash as the picture) — a zap on every drop-out
e = one('roomflick'); prev = 1
for s in range(int(e['t'] * 18), int((e['t'] + e['d']) * 18)):
    t = s / 18; dense = (t - e['t']) / e['d']; cur = 0 if hashjs(s * 1.31) < .35 + .45 * dense else 1
    if cur != prev: put(fx, ballast(.9 if cur == 0 else .6), t, .28, .1)
    prev = cur
for e in ev('beep'):
    k = sec(.09); t = np.arange(k) / SR; put(fx, np.sin(2 * np.pi * 2730 * t) * fade(k, .004, .01) * .4, e['t'], .2)
put(fx, clack(.08), FREEZE + .02, .3); put(fx, motor(.5, 230, 40), FREEZE + .05, .12)
put(fx, clack(.1), OFF, .35)

# ———————— Breathing (close to the mic): rate and level follow fear; held at the silences; gone after the camera is set down ————————
br = bus()
def breath(tin, d_in, d_out, g):
    n1, n2 = sec(d_in), sec(d_out)
    a = bp(nz(n1), 900, 2800, 2) * np.sin(np.linspace(0, np.pi, n1)) ** 1.5
    b = bp(nz(n2), 400, 1900, 2) * np.sin(np.linspace(0, np.pi, n2)) ** 2 * .7
    put(br, a, tin, g); put(br, b, tin + d_in + .08, g)
STOP = one('breathStop')['t']; holds = [(h['t'] - .5, h['t'] + h['d'] + .2) for h in HUSH]
fear_at = lambda t: FEAR[min(N - 1, sec(t))]
t = REC0 + 6.5
while t < STOP:
    if any(a < t < b for a, b in holds):
        b = [b for a, b in holds if a < t < b][0]; t = b + .1; breath(t, .2, 1.6, .05); t += 2.2; continue   # one long exhale after a hold
    f = fear_at(t); per = 3.8 - 2.3 * f; g = .012 + .035 * f
    if not (one('setdown')['t'] - 2 < t < one('setdown')['t'] + 1): breath(t, per * .32, per * .4, g)
    t += per * rng.uniform(.92, 1.08)

# ———————— The PA chime: Westminster quarters on a tubular-bell tone, through a ceiling speaker, down a long corridor ————————
NOTE = {'G3': 55, 'C4': 60, 'D4': 62, 'E4': 64}
QUART = ['E4', 'C4', 'D4', 'G3', 'G3', 'D4', 'E4', 'C4']
def bell(midi, d=2.4):
    f0 = 440 * 2 ** ((midi - 69) / 12); k = sec(d); t = np.arange(k) / SR
    x = sum(a * np.sin(2 * np.pi * f0 * r * t + r) * np.exp(-t / (d * dec)) for r, a, dec in [(1, 1, .35), (2.0, .6, .25), (3.0, .35, .15), (4.2, .25, .1), (5.4, .15, .07), (6.8, .08, .05)])
    return x * fade(k, .003, .2)
def chime(notes, gap, det, slow=1.0):
    k = sec(len(notes) * gap * slow + 2.6); y = np.zeros(k)
    for j, n in enumerate(notes):
        b = bell(NOTE[n] + det); i = sec(j * gap * slow); y[i:i + len(b)] += b[:k - i]
    return y
def speaker(x, far=.5):
    y = bp(x, 320, 3600, 2); y = y + .5 * bp(y, 1000, 1600, 2)
    y = np.tanh(2.0 * y / (np.abs(y).max() + 1e-9)) / np.tanh(2.0)
    st = np.stack([y, y], 1)
    wet = reverb(np.pad(st, ((0, sec(3)), (0, 0))).astype(np.float32), size=.75, mix=1.0, damp=.55)
    return np.pad(st, ((0, sec(3)), (0, 0))) * (1 - .4 * far) + wet * (.25 + .5 * far)
pa = bus()
for e in ev('chime'):
    if e['k'] == 0: y = speaker(chime(QUART, .62, 0), .45); g = .5
    elif e['k'] == 1: y = speaker(chime(QUART[:4], .62, -.7, 1.12), .5); g = .45          # again, slower and flat
    else: y = speaker(chime(QUART[4:], .62, -3.2, 1.5), .85); g = .22                     # on the end card: a tape far gone
    y = y / (np.abs(y).max() + 1e-9); put(pa, y, e['t'], g)

# ———————— Drone: brown noise + beating low sines on the 4th floor; a thinner one on the 3rd ————————
dr_env = np.interp(tt, [0, 285, 299, 311, 318.8, 343.6, 345, 405, 433.8, 434.0, 436, 443, 447.4, 448], [0, 0, .25, .35, 0, 0, .35, .5, 1, 0, 0, .8, .8, 0])
w = np.cumsum(nz(N)); w = hp(w - uniform_filter1d(w, SR), 18)
lw = lp(w, 70); lw /= np.abs(lw).max() + 1e-9
drone = (lw * .6 + np.sin(2 * np.pi * 41 * tt) * .5 + np.sin(2 * np.pi * 43.3 * tt) * .4 + np.sin(2 * np.pi * 82.6 * tt) * .12) * dr_env
del w, lw
drn = bus(); drn[:, 0] = drone; drn[:, 1] = drone
del drone

# ———————— Colour bars and the rewind before the tape plays ————————
e = one('tone'); k = sec(e['d']); t = np.arange(k) / SR
put(fx, np.sin(2 * np.pi * 1000 * t * (1 + .002 * np.sin(2 * np.pi * .6 * t))) * fade(k, .02, .05) * .25, e['t'], 1.0)
e = one('rewind'); k = sec(e['d']); t = np.arange(k) / SR
garble = sum(np.sin(2 * np.pi * np.cumsum(f0 * (1 + .5 * np.sin(2 * np.pi * r * t))) / SR) for f0, r in [(1900, 3.1), (2600, 4.7), (3400, 2.3)])
garble = bp(garble * (rng.random(k // 240 + 1).repeat(240)[:k] > .3) + nz(k) * .4, 900, 6000) * .5 + motor(e['d'], 600, 700)[:k] * .8
put(fx, garble * fade(k, .05, .02), e['t'], .22)
put(fx, clack(.12), e['t'] + e['d'] - .02, .35)

# ———————— Reverbs ————————
print('reverb…', flush=True)
fxw = reverb(fxw, size=.62, mix=1.0, damp=.5)

# ———————— Assembly ————————
mix = amb * .4 + hs * 1.0 + fx * 1.0 + fxw * .8 + br * 1.0 + pa * 1.0 + drn * .1
del amb, hs, fx, fxw, br, pa, drn
# Tape tears: the whole mix chopped + a burst of noise
for e in TEARS:
    a, b = sec(e['t']), min(N, sec(e['t'] + e['d']))
    gate = np.repeat((rng.random((b - a) // 960 + 1) > .45).astype(np.float32), 960)[:b - a]
    gate = uniform_filter1d(gate, 48); mix[a:b] *= gate[:, None]
    burst = bp(nz(b - a), 300, 7000) * .12 * np.sin(np.linspace(0, np.pi, b - a)) ** .5 + bp(nz(b - a), 60, 400) * .08
    mix[a:b, 0] += burst.astype(np.float32); mix[a:b, 1] += np.roll(burst, 13).astype(np.float32)
# Freeze: the sound stretches and dies with the battery
a, b = sec(FREEZE), sec(OFF)
mix[a:b] *= np.linspace(1, 0, b - a, dtype=np.float32)[:, None] ** 2
# Digital silences (reverb tails included): the strongest sound in the film
for h in HUSH:
    a, b = sec(h['t']), sec(h['t'] + h['d']); mix[a - sec(.004):a] *= np.linspace(1, 0, sec(.004), dtype=np.float32)[:, None]; mix[a:b] = 0
# Before REC and after it stops: only what the tape itself plays (bars tone, rewind, hiss); end card: hiss fading, the last chime
mix[sec(OFF + .2):] *= np.interp(tt[sec(OFF + .2):], [OFF + .2, END + 2, DUR], [1, .6, 0]).astype(np.float32)[:, None]
for c in range(2): mix[:, c] = limit(mix[:, c].astype(np.float64), .92).astype(np.float32)
sf.write(os.path.join(HERE, 'mix.wav'), mix, SR, subtype='FLOAT')
def db(x): return 20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)
print('mix peak %.3f  rms %.1f dB' % (np.abs(mix).max(), db(mix)))
