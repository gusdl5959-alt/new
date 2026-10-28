// Timeline: the single source of truth. Shots (one continuous tape, cut only by tape tears), camera keys, floors, lights, the student, captions, sound cues
// Coordinates: metres; x east, z south (−z = north); yaw 0 = facing north, +π/2 = west, π = south, −π/2 = east
import { track, monotone } from '/core/lib.js';

const PI = Math.PI;
export const DUR = 600;

// —— Key moments (seconds) ——
export const T = {
  rewind: [0, 3.6],           // cold open: the tape rewinding over the end of the 4th floor
  bars: [3.6, 11.0],          // colour bars + 1 kHz
  rollIn: 11.0,               // REC picture rolls in: the camera lying on the duty-room desk
  title: [12.2, 16.6],        // camcorder title generator
  pickup: [17.0, 18.8],
  readA: [22.0, 43.0], readB: [44.5, 58.5], readC: [60.0, 78.0],   // the rules, three framings
  ledger1: [81.5, 94.0],      // the duty log: tonight's row is blank
  doorAjar: [124.5, 133.0],   // the broadcasting room door, open a crack
  tears: [176.5, 251.9, 318.8, 343.6, 447.4],
  chime1: 205.2, chime2: 210.6,
  flick: [214.0, 214.45, 214.95],
  zoomWin: [291.0, 292.6],
  chair: 297.0,               // a chair scrapes inside the lit classroom
  lookDown: [299.3, 307.6],
  doorOpen: [300.6, 302.2],   // its back door slides open while the camera looks at the floor
  steps3: [303.0, 306.2],     // light steps pass by
  roomOff: 311.0,             // the classroom lights go out
  hushStair: [336.0, 338.0],
  stepAbove: 338.6,
  read4A: [369.5, 387.5], read4B: [388.5, 405.0],
  rattle: [405.5, 408.0],
  zoomFig: [409.0, 411.0],
  dieStart: 420.0,            // 4th floor: lights die from the north toward the camera
  hush4: [434.0, 436.0],
  restrike: 436.0,
  tilt: [439.5, 442.5],
  run: [443.2, 447.4],
  ledger2: [455.5, 486.0],
  setDown: [486.0, 492.6],
  breathStop: 506.0,
  outStart: 510.0, outStep: 4.5,   // ending: corridor lights out one by one, n = 16 … 2 (the one outside the door stays)
  appear: 575.6,              // during a room-light dropout the student is standing in the doorway, backlit by that last tube
  hushEnd: [576.0, 577.6],
  roomFlick: [575.0, 585.6],
  freeze: 586.0, off: 588.2,
  endCard: [588.4, 600],
};
export const TEARS = T.tears;
// Which floor the tape shows (1 = ground floor with the duty room; 5 = 4th floor after the restrike)
export function floorAt(t) {
  if (t < T.rewind[1]) return 4;
  if (t < TEARS[0]) return 1;
  if (t < TEARS[1]) return 2;
  if (t < TEARS[3]) return 3;
  if (t < TEARS[4]) return t >= T.restrike ? 5 : 4;
  return 1;
}

// —— Camera shots ——
// pos [x, z] / yaw / pitch / camh (height offset from 1.56 m) / fov (horizontal °) / focus (m) / aper (DOF strength)
const S = [];
S.push({  // C: duty room → rules → log → 1st floor (one take)
  t0: 0, t1: TEARS[0],
  pos: [[11, [.15, 3.78]], [17, [.15, 3.78]], [18.8, [.2, 3.3]], [20.5, [-.55, 2.75]], [21.5, [-.75, 2.7]], [78, [-.75, 2.7]], [80, [.2, 3.2]], [81.5, [.75, 3.66]],
    [94, [.75, 3.66]], [95.5, [.4, 3.0]], [97.5, [.05, 1.2]], [99.5, [0, 0]], [101, [.05, -1.2]], [122, [.15, -14.6]], [124.5, [.35, -16.4]], [133, [.35, -16.4]],
    [135, [.25, -18.2]], [141, [.3, -22.2]], [146, [.45, -25.4]], [160, [.2, -33.6]], [171, [.15, -38.6]], [176.5, [.2, -40.0]]],
  yaw: [[11, 0], [17, 0], [18.8, .4], [20.5, PI / 2], [78, PI / 2], [80, PI], [94, PI], [95.5, 1.4], [96.8, .1], [99.5, 0], [122, 0], [124.5, .5], [125.5, .99],
    [132, .97], [134, .1], [141, 0], [142.5, -.95], [145, -.9], [146.5, -.05], [176.5, 0]],
  pitch: [[11, -.04], [17, -.04], [18.8, -.02], [20.5, 0], [78, 0], [79.5, -.3], [81, -1.52], [94, -1.52], [95.3, -.1], [99.5, -.06], [124.5, -.06], [125.5, -.12],
    [132, -.1], [134, -.05], [142.5, -.08], [145, -.12], [146.5, -.05], [176.5, -.05]],
  camh: [[11, -.66], [17, -.66], [18.8, -.05], [20.5, 0], [21.5, .02], [43, .02], [44.5, -.24], [58.5, -.24], [60, -.26], [78, -.26], [79.5, -.1], [81, -.17],
    [94, -.17], [95.5, 0], [176.5, 0]],
  fov: [[11, 52], [19, 52], [20.5, 48], [58.5, 48], [61, 34], [78, 34], [79.5, 52], [81, 60], [94, 60], [95.5, 52], [176.5, 52]],
  focus: [[11, .4], [11.6, 6], [12, 2.6], [12.3, 3.4], [17, 3.4], [18.5, 1.0], [20.5, .9], [21.2, .4], [21.6, .62], [21.9, .57], [58.6, .57], [59.4, .3], [60.2, .62], [60.6, .57], [78, .57], [79.5, 1.0], [81, .4],
    [81.5, .55], [81.8, .48], [94, .48], [95.5, 3], [124.5, 3], [125.4, 1.4], [125.9, 2.2], [126.2, 2.0], [132, 2.0], [134, 6], [142.5, 3], [143.2, 1.2],
    [143.6, 1.6], [145, 1.6], [146.5, 6], [176.5, 6]],
  aper: [[11, 3], [20.5, 2], [58.5, 2], [61, 4], [78, 4], [79.5, 3], [176.5, 3]],
  hand: [[11, 0], [17, 0], [18.6, 1], [176.5, 1]],
});
S.push({  // D: 2nd floor, walking south; the chime
  t0: TEARS[0], t1: TEARS[1],
  pos: [[176.5, [.1, -34.0]], [205, [.2, -12.6]], [205.6, [.2, -12.2]], [219, [.2, -12.2]], [221, [.2, -11.0]], [236, [.15, -1.6]], [238, [.1, -1.0]], [251.9, [.1, -1.0]]],
  yaw: [[176.5, PI], [205.6, PI], [206.0, PI - .05], [207.0, .36], [219, .37], [219.5, .5], [221, PI], [238, PI], [239.5, 2.0], [241, .05], [251.9, 0]],
  pitch: [[176.5, -.05], [205.6, -.05], [207, .2], [219, .19], [221, -.05], [241, -.03], [251.9, -.03]],
  camh: [[176.5, 0]],
  fov: [[176.5, 52], [208, 52], [210, 40], [218.5, 40], [219.5, 52], [251.9, 52]],
  focus: [[176.5, 6], [206.5, 6], [206.9, .8], [207.4, 6], [207.8, 3.6], [208.1, 4.1], [219, 4.1], [221, 6], [241, 3], [241.6, 12], [242, 9], [251.9, 9]],
  aper: [[176.5, 3], [208, 3], [210, 6], [218.5, 6], [219.5, 3]],
  hand: [[176.5, 1]],
});
S.push({  // E: 3rd floor, walking south to the lit classroom (3-7); standing right in front of its window
  t0: TEARS[1], t1: TEARS[2],
  pos: [[251.9, [.15, -34.0]], [289, [.7, -6.4]], [291, [1.0, -4.2]], [312, [1.0, -4.2]], [318.8, [.9, -7.6]]],
  yaw: [[251.9, PI], [288.4, PI], [291, PI / 2 + .05], [307.6, PI / 2 + .05], [309.2, PI / 2 - .5], [318.8, PI / 2 - .2]],
  pitch: [[251.9, -.05], [288.4, -.04], [291, .14], [299.3, .14], [300.2, -1.25], [306.5, -1.22], [307.6, .1], [312, .08], [318.8, .05]],
  camh: [[251.9, 0]],
  fov: [[251.9, 52], [291, 52], [292.6, 40], [298.8, 40], [299.3, 52], [307.6, 52], [318.8, 52]],
  focus: [[251.9, 8], [290, 6], [291.5, 1], [292.2, 4], [292.6, 2.0], [292.9, 2.45], [298.8, 2.45], [299.4, 1.5], [300.2, .9], [306.5, .9], [307.6, 3],
    [308.4, 2.2], [309.4, 2.9], [318.8, 3.6]],
  aper: [[251.9, 3], [291, 3], [292.6, 6], [298.8, 6], [299.3, 3]],
  hand: [[251.9, 1]],
});
S.push({  // F: the stairwell: the landing wall says "4"
  t0: TEARS[2], t1: TEARS[3],
  pos: [[318.8, [.7, -40.3]], [343.6, [.7, -40.62]]],
  yaw: [[318.8, 0]],
  pitch: [[318.8, .1], [320, .16], [343.6, .16]],
  camh: [[318.8, 0]],
  fov: [[318.8, 52], [324, 52], [334, 30], [343.6, 28]],
  focus: [[318.8, .5], [319.6, 9], [320.2, 5.2], [320.5, 6.3], [343.6, 6.3]],
  aper: [[318.8, 3], [324, 3], [334, 8]],
  hand: [[318.8, 1]],
});
S.push({  // G: the 4th floor. 345.5–366.5 repeats the 1st-floor walk (101–122) key for key
  t0: TEARS[3], t1: TEARS[4],
  pos: [[343.6, [.04, -.3]], [345.5, [.05, -1.2]], [366.5, [.15, -14.6]], [368.5, [-.77, -16.0]], [405.5, [-.77, -16.0]], [406.5, [-.4, -15.6]], [421, [-.3, -15.6]],
    [433, [0, -7.5]], [443.2, [0, -7.5]], [444.2, [.05, -6.9]], [447.4, [.1, -1.6]]],
  yaw: [[343.6, 0], [366.5, 0], [367.5, .8], [368.5, PI / 2], [405.5, PI / 2], [406.5, 0], [443.2, 0], [444.2, PI], [447.4, PI]],
  pitch: [[343.6, -.06], [366.5, -.06], [368.5, 0], [405.5, 0], [406.5, -.03], [433, -.03], [436, -.02], [443.2, -.02], [444.2, -.15], [447.4, -.2]],
  camh: [[343.6, 0], [368.5, 0], [369.5, -.03], [387.5, -.03], [388.5, -.26], [405, -.26], [406.5, 0], [447.4, 0]],
  fov: [[343.6, 52], [367.5, 52], [368.5, 48], [405.5, 48], [406.5, 52], [409, 52], [411, 20], [418, 20], [419, 52], [436, 52], [437.5, 38], [443, 38], [443.5, 52]],
  focus: [[343.6, 6], [366.5, 6], [368, 1.5], [368.6, .5], [368.9, .6], [369.2, .55], [405, .55], [406.5, 6], [411, 3], [411.8, 34], [412.3, 16], [412.8, 24],
    [413.1, 22.8], [417.5, 22.8], [419, 8], [436, 8], [437, 10], [443, 10], [444, 4]],
  aper: [[343.6, 3], [368.5, 2], [405, 2], [406.5, 3], [409, 3], [411, 14], [418, 14], [419, 3], [436, 3], [437.5, 7], [443, 7], [443.5, 3]],
  hand: [[343.6, 1]],
});
S.push({  // H: back in the duty room; the log; the camera is set down where it started
  t0: TEARS[4], t1: DUR + 1,
  pos: [[447.4, [.35, 1.9]], [452, [.4, 2.3]], [455.5, [.75, 3.66]], [471.5, [.75, 3.66]], [475, [.6, 3.5]], [486, [.6, 3.5]], [489.5, [.3, 3.5]], [492.5, [.15, 3.78]], [DUR, [.15, 3.78]]],
  yaw: [[447.4, PI], [486, PI], [488, 1.6], [490.5, .15], [492.5, 0], [DUR, 0]],
  pitch: [[447.4, -.12], [452, -.15], [454.5, -1.0], [455.5, -1.52], [486, -1.52], [487.5, -.4], [490, -.1], [492.5, -.04], [DUR, -.04]],
  camh: [[447.4, 0], [452, 0], [455.5, -.17], [486, -.17], [489, -.3], [492.5, -.66], [DUR, -.66]],
  fov: [[447.4, 52], [454.5, 52], [455.5, 60], [471.5, 60], [475, 36], [486, 36], [487.5, 52], [DUR, 52]],
  focus: [[447.4, 2], [454.5, 1], [455.3, .3], [455.8, .55], [456.1, .48], [471.5, .48], [474, .9], [474.8, .35], [475.3, .5], [486, .5], [489, 2], [492.4, .5],
    [493.2, 6], [493.6, 2.6], [494, 3.4], [DUR, 3.4]],
  aper: [[447.4, 3], [455.5, 2.5], [471.5, 2.5], [475, 6], [486, 6], [487.5, 3], [DUR, 3]],
  hand: [[447.4, 1], [491.4, 1], [493, 0], [DUR, 0]],
});
for (const s of S) for (const k of ['pos', 'yaw', 'pitch', 'camh', 'fov', 'focus', 'aper', 'hand']) s[k] = k === 'pos' ? track(s[k]) : monotone(s[k]);
export const shotAt = t => S.find(s => t >= s.t0 && t < s.t1) || S[S.length - 1];
export const SHOTS = S;
export const POS = t => shotAt(t).pos(t), YAW = t => shotAt(t).yaw(t), PITCH = t => shotAt(t).pitch(t), CAMH = t => shotAt(t).camh(t);
export const FOV = t => shotAt(t).fov(t), FOCUS = t => shotAt(t).focus(t), APER = t => shotAt(t).aper(t), HAND = t => shotAt(t).hand(t);

// Fear (0 calm … 1 trembling): drives tremor and breathing
export const FEAR = monotone([[0, .1], [100, .12], [125, .3], [133, .2], [200, .2], [205.5, .55], [214, .7], [222, .4], [252, .35], [291, .5], [299, .75], [307.6, .9],
  [318.8, .6], [336, .7], [343.6, .5], [370, .45], [406, .6], [413, .85], [420, .8], [433, 1], [436, .95], [443, 1], [447.4, .9], [460, .55], [486, .7], [493, .5], [DUR, .5]]);
// Held breath: all handheld motion frozen
export const HOLDS = [[T.hushStair[0] - .3, T.hushStair[1] + .2], [T.hush4[0] - .4, T.hush4[1] + .25]];   // (the camera lies on the desk at the end: no hold needed)
export const HOLD = t => HOLDS.some(([a, b]) => t > a && t < b) ? 0 : 1;

// —— OSD: clock and battery are evidence ——
const CLK = [[0, 23 * 60 + 52], [TEARS[0], 24 * 60 + 31], [TEARS[1], 25 * 60 + 47], [TEARS[2], 26 * 60 + 13], [TEARS[3], 28 * 60 + 4], [TEARS[4], 29 * 60 + 58]];
export function clock(t) {
  if (t < T.rewind[1]) t = 345 + (T.rewind[1] - t) * 20;
  let k = 0; for (let i = 0; i < CLK.length; i++) if (t >= CLK[i][0]) k = i;
  const base = k === 0 ? T.rollIn : CLK[k][0];
  let m = Math.floor(CLK[k][1] + Math.max(0, t - base) / 60) % 1440;
  const pm = m >= 12 * 60, h = Math.floor(m / 60) % 12 || 12, mm = String(m % 60).padStart(2, '0');
  return `${pm ? 'PM' : 'AM'} ${String(h).padStart(2, ' ')}:${mm}`;
}
export const DATE = 'NOV. 3.1998';
export const battery = t => t < TEARS[1] ? 3 : t < TEARS[3] ? 2 : t < T.roomFlick[0] + 2 ? 1 : 0;

// —— Lights ——
// returns brightness multiplier for corridor fixture n (1..16, from the south) or the duty-room fixture (n = 0)
const DEAD = { 1: [], 2: [13], 3: [15, 16], 4: [10, 11, 12, 13, 14, 15], 5: [] };
const DIM = { 4: { 16: .45 } };   // 4th floor: one weak tube left at the far end, behind the student
const FLICKERY = { 1: [11], 2: [5], 3: [13], 4: [8, 16], 5: [] };
export function lightK(n, t, fl, hash) {
  if (n === 0) {   // duty room
    if (t >= T.roomFlick[0] && t < T.freeze) { const s = Math.floor(t * 18), h = hash(s * 1.31); const dense = (t - T.roomFlick[0]) / (T.freeze - T.roomFlick[0]); return h < .35 + .45 * dense ? .04 : 1; }
    return 1;
  }
  let k = (DEAD[fl] || []).includes(n) ? 0 : (DIM[fl] || {})[n] ?? 1;
  if ((FLICKERY[fl] || []).includes(n)) { const s = Math.floor(t * 24 + n * 7), h1 = hash(s * 1.7 + n), h2 = hash(Math.floor(t * 1.1 + n * 3)); k *= h2 < .3 ? (h1 < .5 ? .1 : .85) : 1; }
  if (fl === 4 && t >= T.dieStart && t < T.restrike) {   // dying from the north: n = 9, 8, 7, 5, 4, 3
    const order = [[9, 0], [8, 2.6], [7, 5.0], [5, 9.3], [4, 11.3], [3, 13.0]];
    for (const [m, dt] of order) if (n === m && t >= T.dieStart + dt) k = 0;
    if (n === 8 && t > T.dieStart + 1.4 && t < T.dieStart + 2.6) k *= hash(Math.floor(t * 20)) < .5 ? .1 : 1;   // stutter before it goes
  }
  if (fl === 1 && t >= TEARS[4]) {   // ending: corridor lights go out one by one, farthest first
    const out = n => T.outStart + (16 - n) * T.outStep;
    if (n >= 2 && t >= out(n)) k = 0;
    else if (n >= 2 && t > out(n) - .7) k *= hash(Math.floor(t * 22) + n) < .45 ? .08 : 1;   // a stutter before each goes
  }
  return k;
}
export const outTimes = () => Array.from({ length: 15 }, (_, i) => ({ n: 16 - i, t: T.outStart + i * T.outStep }));

// —— The student ——
// { x, z, tilt, show } or null
export function studentAt(t) {
  if (t >= T.zoomFig[0] - 4 && t < T.restrike) return { x: .02, z: -37.6, tilt: .3, s: 1.1 };   // in front of the exit sign: a hole in the green
  if (t >= T.restrike && t < TEARS[4]) return { x: .1, z: -17.5, tilt: .3 + .5 * Math.min(1, Math.max(0, (t - T.tilt[0]) / (T.tilt[1] - T.tilt[0]))) ** 2 };
  if (t >= T.outStart && t < T.freeze + 3) {
    const i = Math.floor((t - T.outStart) / T.outStep), n = Math.max(2, 16 - i);
    if (t >= T.appear) return { x: .06, z: -.5, tilt: .55 + .25 * Math.min(1, Math.max(0, (t - T.appear - 4) / 5)) };
    return { x: .12, z: -2.4 * n - .4, tilt: .55 };
  }
  return null;
}

// —— Captions (SDH; nothing is spoken on this tape) ——
export const CAPS = [
  [.3, 3.4, '[테이프 되감는 소리]'],
  [4.0, 10.6, '[기준 신호음]'],
  [17.0, 19.2, '[캠코더를 집어 드는 소리]'],
  [176.0, 177.8, '[테이프 잡음]'],
  [205.3, 208.4, '[교내 방송 차임]'],
  [210.7, 213.6, '[차임이 한 번 더 울린다]'],
  [214.0, 216.6, '[형광등 깜빡임]'],
  [251.4, 253.2, '[테이프 잡음]'],
  [297.0, 299.2, '[의자 끄는 소리]'],
  [300.6, 303.0, '[교실 문 여는 소리]'],
  [303.0, 306.4, '[가벼운 발소리]'],
  [311.0, 313.6, '[교실 불이 꺼진다]'],
  [318.3, 320.0, '[테이프 잡음]'],
  [336.0, 338.0, '[정적]'],
  [338.6, 341.4, '[위층에서 발소리]'],
  [343.1, 344.9, '[테이프 잡음]'],
  [405.5, 408.4, '[교실 문이 덜컹거린다]'],
  [420.0, 424.0, '[형광등이 하나씩 꺼진다]'],
  [428.0, 432.6, '[숨소리가 가빠진다]'],
  [434.0, 436.0, '[정적]'],
  [436.0, 439.2, '[형광등이 한꺼번에 켜진다]'],
  [444.0, 446.8, '[뛰는 발소리]'],
  [446.9, 448.6, '[테이프 잡음]'],
  [448.6, 451.8, '[거친 숨소리]'],
  [492.0, 494.4, '[캠코더를 내려놓는 소리]'],
  [506.0, 509.0, '[숨소리가 멎는다]'],
  [510.0, 513.6, '[멀리서 형광등이 꺼진다]'],
  [555.0, 558.6, '[소리가 가까워진다]'],
  [576.0, 577.6, '[정적]'],
  [582.0, 585.0, '[배터리 경고음]'],
  [594.6, 598.6, '[교내 방송 차임]'],
].map(([t0, t1, text]) => ({ t0, t1, text }));
