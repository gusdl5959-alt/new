// 4층은 없습니다 — a recovered camcorder tape (Liminal Found Footage)
// three.js scene (720×540, 4:3) → GTAO + depth of field (autofocus hunting) + bloom → VHS camcorder shader → 1920×1080 (pillarboxed)
import * as THREE from 'three';
import { makePost } from './post.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { clamp, seg, ss, lerp, hash, vnoise, env } from '/core/lib.js';
import { DUR, T, TEARS, floorAt, shotAt, POS, YAW, PITCH, CAMH, FOV, FOCUS, APER, HAND, FEAR, HOLD, clock, DATE, battery, lightK, studentAt, CAPS, outTimes } from './story.js';
import { buildWorld, buildProps, updateLights, U, LIGHTS, PLATES, doorZ } from './world.js';
import { makeLegs, makeStudent } from './figures.js';
import { VHS } from './vhs.js';
import { drawOSD } from './osd.js';

const Q = new URLSearchParams(location.search);
const NOSUB = Q.has('nosub');
for (const f of ["800 30px 'Nanum Gothic'", "700 30px 'Nanum Gothic'", "400 30px 'Nanum Gothic'", "800 30px 'Nanum Myeongjo'", "700 30px 'Nanum Gothic Coding'", "400 30px 'Nanum Pen Script'"]) await document.fonts.load(f, '가나다');

const W = 1920, H = 1080, SW = 640, SH = 480, RW = 960, RH = 540;   // 3D at 640×480; the VHS pass writes 960×540, scaled up by the page (tape resolution is lower than either)
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(RW, RH, false); renderer.domElement.style.width = W + 'px'; renderer.domElement.style.height = H + 'px';
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 0.85;
document.getElementById('stage').appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0, 0, 0);
const camera = new THREE.PerspectiveCamera(40, 4 / 3, .03, 120); camera.rotation.order = 'YXZ';
const post = makePost(renderer, scene, camera, SW, SH, { ssaa: 1, ao: true, aoRadius: .5, aoThickness: 1.2, aoScale: 1.6, aoAmt: .7 });
post.bloom.strength = .55; post.bloom.radius = .55; post.bloom.threshold = 1.05;
post.vig.uniforms.amt.value = 0; post.vig.uniforms.contrast.value = 0; post.vig.uniforms.sat.value = 1;
post.dof.maxCoc = 14;
const osdCv = document.createElement('canvas'); osdCv.width = SW; osdCv.height = SH;
const osdTex = new THREE.CanvasTexture(osdCv); osdTex.minFilter = osdTex.magFilter = THREE.LinearFilter; osdTex.generateMipmaps = false;
const vhs = new ShaderPass(VHS);
vhs.uniforms.tOSD.value = osdTex; vhs.uniforms.res.value = [RW, RH]; vhs.uniforms.src.value = [SW, SH];
post.composer.addPass(vhs);

const world = buildWorld(scene);
const props = buildProps(scene);
const legs = makeLegs(scene);
const student = makeStudent(scene); student.visible = false;
const ov = document.getElementById('ov'), ox = ov.getContext('2d');

// —— Gait: phase from distance walked within the current shot (one step per 0.7 m; running 1.05 m) ——
const DT = 1 / 240, NS = Math.ceil(DUR / DT) + 2, DIST = new Float32Array(NS);
for (let k = 1; k < NS; k++) {
  const t0 = (k - 1) * DT, t1 = k * DT;
  if (shotAt(t0) !== shotAt(t1)) { DIST[k] = DIST[k - 1]; continue; }
  const a = POS(t0), b = POS(t1); DIST[k] = DIST[k - 1] + Math.hypot(b[0] - a[0], b[1] - a[1]);
}
const distAt = t => { const f = clamp(t / DT, 0, NS - 1.001), i = Math.floor(f); return lerp(DIST[i], DIST[i + 1], f - i); };
const speedAt = t => (distAt(t + .15) - distAt(t - .15)) / .3;
const RUN = t => t >= T.run[0] + .9 && t < TEARS[4];
const stride = t => RUN(t) ? 1.05 : .7;

// —— Global light events: the three flickers on the 2nd floor ——
function gLight(t) {
  let g = 1;
  T.flick.forEach((f, i) => {
    if (t > f - .03 && t < f + .1 + i * .02) g = .03;
    else if (t >= f + .1 + i * .02 && t < f + .2) g = Math.min(g, .55 + .45 * seg(t, f + .1, f + .2));
  });
  return g;
}
const studentLitRoom = t => floorAt(t) === 3 && t < T.roomOff;
function kOf(L, t) {
  const fl = floorAt(t);
  if (L.room && (fl !== 1 || (t >= TEARS[0] && t < TEARS[4]))) return 0;   // the duty room only exists on the 1st floor
  return lightK(L.n, t, fl, hash) * gLight(t);
}
// Local light level around the camera (for auto exposure / AGC lag)
function localLight(t) {
  const [, z] = POS(t); let s = 0, w = 0;
  for (const L of LIGHTS) { const d = Math.abs(L.z - z), wt = 1 / (1 + d * d * .08); s += kOf(L, t) * wt; w += wt; }
  return s / w;
}
function darkMem(t) { let s = 0, w = 0; for (let k = 0; k < 30; k++) { const d = k * .04, e = Math.exp(-d / .45); s += (1 - localLight(t - d)) * e; w += e; } return s / w; }

// —— Handheld camera ——
const nz = (t, f, s) => vnoise(t * f + s * 17.3) - .5;
function camPose(t) {
  const [x, z] = POS(t); let yaw = YAW(t), pitch = PITCH(t), roll = 0;
  const hand = HAND(t), sp = speedAt(t), amp = clamp(sp / 1.0) * hand, run = RUN(t) ? 1 : 0, ph = distAt(t) / stride(t) * Math.PI, fear = FEAR(t);
  const hold = HOLD(t) * hand;
  let y = 1.56 + CAMH(t);
  y += (.03 + .03 * run) * amp * (Math.abs(Math.sin(ph)) - .6);
  const sway = (.018 + .03 * run) * amp * Math.sin(ph);
  const br = Math.sin(t * Math.PI * 2 * (.27 + .25 * fear));
  pitch += (nz(t, 1.1, 1) * .016 + nz(t, 3.7, 2) * .005 * (1 + 2 * fear) + nz(t, 9.5, 3) * .0024 * fear + br * .006 + run * .03 * Math.sin(ph * 2)) * hold;
  yaw += (nz(t, .9, 4) * .018 + nz(t, 3.3, 5) * .005 * (1 + 2 * fear) + (.011 + .02 * run) * amp * Math.sin(ph)) * hold;
  roll = (nz(t, .6, 6) * .035 + (.014 + .03 * run) * amp * Math.sin(ph) + nz(t, 7, 7) * .003 * fear) * hold + .012 * hand;
  y += br * .006 * hold;
  const down = clamp(-pitch - .4, 0, 1);
  const rx = Math.cos(yaw), rz = -Math.sin(yaw);
  const fx = -Math.sin(yaw), fz = -Math.cos(yaw), reach = down * .22;
  return { x: x + rx * sway * hold + fx * reach, y: y - down * .16, z: z + rz * sway * hold + fz * reach, yaw, pitch, roll, amp, ph, bx: x, bz: z };
}

// —— Korean bitmap text (camcorder title generator / end card): glyphs rasterised small, thresholded, drawn as square dots with a black outline ——
const pixCache = new Map();
function pixGlyphs(str, size) {
  const key = str + '|' + size; if (pixCache.has(key)) return pixCache.get(key);
  const c = document.createElement('canvas'), x = c.getContext('2d');
  x.font = `700 ${size}px 'Nanum Gothic Coding'`; const w = Math.ceil(x.measureText(str).width) + 4, h = size + 6;
  c.width = w; c.height = h; x.font = `700 ${size}px 'Nanum Gothic Coding'`; x.fillStyle = '#fff'; x.textBaseline = 'top'; x.fillText(str, 2, 2);
  const d = x.getImageData(0, 0, w, h).data, on = [];
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) if (d[(j * w + i) * 4 + 3] > 110) on.push([i, j]);
  const r = { w, h, on }; pixCache.set(key, r); return r;
}
function pixText(x, str, cx, cy, size, s, col = '#fbfbf2', n = 999) {
  const g = pixGlyphs([...str].slice(0, n).join(''), size), full = pixGlyphs(str, size);
  const x0 = Math.round(cx - full.w * s / 2), y0 = Math.round(cy - full.h * s / 2);
  x.fillStyle = 'rgba(0,0,0,.85)'; const o = Math.max(1, s * .5);
  for (const [i, j] of g.on) for (const [dx, dy] of [[-o, 0], [o, 0], [0, -o], [0, o]]) x.fillRect(x0 + i * s + dx, y0 + j * s + dy, s, s);
  x.fillStyle = col; for (const [i, j] of g.on) x.fillRect(x0 + i * s, y0 + j * s, s, s);
}

// —— Colour bars (drawn into the tape-space canvas so they go through the VHS pass) ——
function bars(c) {
  const x = c.getContext('2d'), w = c.width, h = c.height;
  const top = ['#bfbfbf', '#bfbf00', '#00bfbf', '#00bf00', '#bf00bf', '#bf0000', '#0000bf'];
  top.forEach((col, i) => { x.fillStyle = col; x.fillRect(Math.round(i * w / 7), 0, Math.ceil(w / 7), h * .67); });
  const mid = ['#0000bf', '#131313', '#bf00bf', '#131313', '#00bfbf', '#131313', '#bfbfbf'];
  mid.forEach((col, i) => { x.fillStyle = col; x.fillRect(Math.round(i * w / 7), h * .67, Math.ceil(w / 7), h * .08); });
  const bot = [['#00214c', 1.25], ['#ffffff', 1.25], ['#32006a', 1.25], ['#131313', 1.25], ['#090909', .33], ['#131313', .33], ['#1d1d1d', .34], ['#131313', 1]];
  let px = 0; for (const [col, f] of bot) { x.fillStyle = col; x.fillRect(Math.round(px), h * .75, Math.ceil(f * w / 7) + 1, h * .25); px += f * w / 7; }
}

// —— Per-floor set dressing ——
function dress(t, fl) {
  const pl = PLATES[fl] || PLATES[1];
  props.plates.forEach(p => { p.mat.uniforms.map.value = props.plateT[pl[p.k]]; });
  const voidOut = fl >= 4;
  props.outside.forEach(o => { o.mat.uniforms.map.value = voidOut ? props.T.voidT : props.T.outT[o.k % 4]; o.mat.uniforms.emit.value = voidOut ? 0 : .5; });
  world.plug.visible = fl !== 1;
  props.rules4.visible = fl >= 4; props.tape4.forEach(m => { m.visible = fl >= 4; });
  props.ledgerM.uniforms.map.value = props.ledgerT[t >= TEARS[4] ? 1 : 0];
  props.floorSign.visible = t >= TEARS[2] && t < TEARS[3];
  // Classroom k = 0 on the 3rd floor: lit, someone seated; empty after the camera looks at the floor; dark after roomOff
  const lit = studentLitRoom(t);
  props.windows.forEach(w => {
    const on = lit && w.k === 0;
    w.mat.uniforms.map.value = on ? (t < T.lookDown[0] + 1.6 ? props.T.winLit : props.T.winLitEmpty) : props.T.winDark;
    w.mat.uniforms.emit.value = on ? .42 : 0; w.mat.uniforms.spec.value = on ? .05 : .45;
  });
  props.doors.forEach(d => {
    const on = lit && d.k === 0;
    d.mat.uniforms.map.value = on ? props.T.doorLit : props.T.doorDark; d.mat.uniforms.emit.value = on ? .35 : 0;
    d.voidMat.uniforms.color.value.setRGB(on ? 1 : 0, on ? .97 : 0, on ? .86 : 0); d.voidMat.uniforms.emit.value = on ? .5 : 0;
    let off = 0;
    if (fl === 1 && d.k === 2 && !d.back) off = .12;                                                  // broadcasting room, ajar
    if (fl === 3 && d.k === 0 && d.back) off = .82 * ss(seg(t, T.doorOpen[0], T.doorOpen[1]));        // slides open while the camera looks down
    if (fl === 4 && d.k === 3 && d.back && t > T.rattle[0] && t < T.rattle[1]) off = .03 * Math.abs(Math.sin((t - T.rattle[0]) * 23)) * (1 - seg(t, T.rattle[1] - .6, T.rattle[1]));
    d.mesh.position.z = d.z - off;
  });
  // Spots: 0 green exit glow, 1 the lit classroom, 2 the landing bulb, 3 the desk lamp
  const g = gLight(t);
  U.uSpotC.value[0].set(.05, .85, .3).multiplyScalar((fl === 4 ? .9 : .32) * g);
  U.uSpotC.value[1].set(1, .95, .8).multiplyScalar(lit ? .9 : 0);
  U.uSpotC.value[2].set(1, .88, .68).multiplyScalar(1.6);
  const deskOn = fl === 1 && (t < TEARS[0] || t >= TEARS[4]) && t < T.freeze + .01;
  U.uSpotC.value[3].set(1, .82, .56).multiplyScalar(deskOn ? .22 : 0);
  props.lampHead.material.uniforms.emit.value = deskOn ? 2.5 : 0;
  props.exitM.uniforms.emit.value = 7 * g;
}

// —— Picture ——
function picTime(t) {
  if (t < T.rewind[1]) return 440 - t * 28;   // rewinding over the 4th floor
  if (t >= T.bars[0] && t < T.bars[1]) return T.rollIn + .01;
  return Math.min(t, T.freeze);
}
function render(t) {
  const tv = picTime(t), fl = floorAt(tv);
  const cp = camPose(tv);
  camera.position.set(cp.x, cp.y, cp.z); camera.rotation.set(cp.pitch, cp.yaw, cp.roll);
  const hf = FOV(tv) * Math.PI / 180; camera.fov = 2 * Math.atan(Math.tan(hf / 2) / (4 / 3)) * 180 / Math.PI; camera.updateProjectionMatrix();
  camera.updateMatrixWorld();
  legs.visible = HAND(tv) > .5;
  legs.pose({ x: cp.bx, z: cp.bz, yaw: YAW(tv), phase: cp.ph, amp: cp.amp, stance: .02 });
  dress(tv, fl);
  // The student
  const st = studentAt(tv);
  student.visible = !!st;
  if (st) { student.position.set(st.x, 0, st.z); student.scale.setScalar(st.s ?? 1); student.pose(st.tilt); student.rotation.y = Math.atan2(cp.x - st.x, cp.z - st.z); }
  // Lights
  updateLights(L => kOf(L, tv));
  const g = gLight(tv);
  U.uFogG.value = .35 + .65 * g;
  scene.background.copy(U.uFogCol.value).multiplyScalar(U.uFogG.value * .12);
  post.dof.focus = FOCUS(tv); post.dof.aper = APER(tv);
  // VHS
  const u = vhs.uniforms, dm = darkMem(tv);
  const f = Math.floor(t * 30); u.frame.value = f;
  const awb = ss(seg(t, T.rollIn, T.rollIn + 1.8));
  u.tint.value = [lerp(.8, 1.0, awb) * (1 + .02 * Math.sin(t * .23)), lerp(.93, 1.02, awb), lerp(1.4, .93, awb) * (1 + .04 * Math.sin(t * .31))];
  u.expo.value = (1 + .5 * dm) * (0.97 + .03 * Math.sin(t * .47));
  const zoomed = seg(FOV(tv), 52, 20);
  u.gain.value = .034 + .09 * dm + .02 * zoomed + .012 * FEAR(tv);
  let track = 0, roll = 0;
  if (t < T.rewind[1]) { track = .75 + .25 * hash(Math.floor(t * 9)); roll = (hash(Math.floor(t * 6)) - .5) * .15; }
  if (t >= T.rollIn && t < T.rollIn + .5) { const k = 1 - seg(t, T.rollIn, T.rollIn + .5); track = k; roll = k * k * .4; }
  for (const b of TEARS) {
    track = Math.max(track, env(t, b - .5, b + .6, .1, .3));
    if (t > b - .5 && t < b + .6) roll = (hash(Math.floor(t * 30) * .7) - .5) * .12 * (1 - seg(t, b + .4, b + .6));
  }
  if (t > T.freeze) track = Math.max(track, .15 + .1 * hash(Math.floor(t * 30)));
  if (t > T.off) track = Math.max(track, seg(t, T.off, T.off + .15));
  u.track.value = track; u.roll.value = roll;
  u.jitter.value = t > T.freeze ? .8 : .3;
  const inBars = t >= T.bars[0] && t < T.bars[1];
  u.off.value = (t >= T.rewind[1] && t < T.bars[0]) || t >= T.off + .2 ? 1 : 0;
  // OSD (and bars, which live in the same tape-space canvas)
  const rec = t >= T.rollIn && t < T.freeze;
  drawOSD(osdCv, {
    hide: t < T.rollIn || t >= T.off, t, rec,
    clock: t < T.freeze ? clock(t) : null, date: DATE, bat: battery(t), batBlink: battery(t) <= 1,
  });
  if (inBars) bars(osdCv);
  if (t >= T.title[0] && t < T.title[1]) {   // title generator, character by character
    const x = osdCv.getContext('2d'), n = Math.floor((t - T.title[0]) * 9);
    pixText(x, '야간 순찰 기록', SW / 2, SH * .4, 15, 3, '#fbfbf2', n);
    if (n > 7) pixText(x, '1998. 11. 3.', SW / 2, SH * .4 + 62, 15, 2, '#fbfbf2', n - 7);
  }
  osdTex.needsUpdate = true;
  U.uTime.value = t;
  if (t < T.endCard[0] + .7) post.composer.render();
  else { renderer.setRenderTarget(null); renderer.setClearColor(0x000000, 1); renderer.clear(); }
  // Overlay: captions, end card
  ox.clearRect(0, 0, W, H);
  if (t >= T.endCard[0]) endCard(t);
  if (!NOSUB) drawCaps(ox, t);
}
function endCard(t) {
  const a = ss(seg(t, T.endCard[0], T.endCard[0] + .6));
  ox.globalAlpha = a; ox.fillStyle = '#000'; ox.fillRect(0, 0, W, H);
  const b = ss(seg(t, T.endCard[0] + 1.2, T.endCard[0] + 2.4));
  ox.globalAlpha = b; pixText(ox, '4층은 없습니다', W / 2, 470, 16, 9, '#ecece4');
  const c = ss(seg(t, T.endCard[0] + 3.4, T.endCard[0] + 4.6));
  ox.globalAlpha = c; pixText(ox, '1998. 11. 3. 본관 야간 순찰 기록', W / 2, 640, 15, 3, '#9d9a8c');
  ox.globalAlpha = 1;
}
// Closed captions: CEA-608 look, white on a black box per row, inside the 4:3 frame
function drawCaps(x, t) {
  const c = CAPS.find(c => t >= c.t0 && t < c.t1); if (!c) return;
  const fs = 40, rh = 56, cx = 960, y = 1080 - 214;
  x.font = `700 ${fs}px 'Nanum Gothic Coding'`; x.textBaseline = 'middle';
  const w = x.measureText(c.text).width + fs * 1.2, x0 = Math.round(cx - w / 2);
  x.fillStyle = '#000'; x.fillRect(x0, y - rh / 2, w, rh);
  x.fillStyle = '#f2f2f2'; x.fillText(c.text, x0 + fs * .6, y + 2);
}
window.TEXTS = t => {
  const out = [];
  if (t >= T.title[0] + 1 && t < T.title[1]) out.push({ id: 'title', text: '야간 순찰 기록 1998. 11. 3.', x0: 600, y0: 300, x1: 1320, y1: 560 });
  if (t >= T.endCard[0] + 2.4) out.push({ id: 'end', text: '4층은 없습니다', x0: 500, y0: 380, x1: 1420, y1: 560 });
  return out;
};

// —— Events (sound effects / captions) → events.json ——
const EV = [];
EV.push({ t: 0, type: 'rewind', d: T.rewind[1] }, { t: T.bars[0], type: 'tone', d: T.bars[1] - T.bars[0] - .2 });
EV.push({ t: T.rollIn - .25, type: 'recOn' }, { t: T.pickup[0], type: 'pickup' }, { t: T.setDown[1], type: 'setdown' });
{ // footsteps from the gait phase, never while the camera lies on the desk
  let last = 0, shot = null;
  for (let t = T.rollIn; t < T.freeze; t += 1 / 120) {
    const s = shotAt(t); if (s !== shot) { shot = s; last = Math.floor(distAt(t) / stride(t)); continue; }
    const n = Math.floor(distAt(t) / stride(t));
    if (n > last) { last = n; if (HAND(t) > .5) EV.push({ t, type: RUN(t) ? 'run' : 'step', v: clamp(speedAt(t) / 1.0, .35, 1.2), fl: floorAt(t) }); }
  }
}
for (const b of TEARS) EV.push({ t: b - .5, type: 'tear', d: 1.1 });
T.flick.forEach(f => EV.push({ t: f - .03, type: 'flick' }));
EV.push({ t: T.chime1, type: 'chime', k: 0 }, { t: T.chime2, type: 'chime', k: 1 }, { t: T.endCard[0] + 6.2, type: 'chime', k: 2 });
EV.push({ t: T.chair, type: 'chair' }, { t: T.doorOpen[0], type: 'slide', d: T.doorOpen[1] - T.doorOpen[0] }, { t: T.steps3[0], type: 'lightsteps', d: T.steps3[1] - T.steps3[0] });
EV.push({ t: T.roomOff, type: 'off' }, { t: T.stepAbove, type: 'above' }, { t: T.rattle[0], type: 'rattle', d: T.rattle[1] - T.rattle[0] });
for (const [n, dt] of [[9, 0], [8, 2.6], [7, 5.0], [5, 9.3], [4, 11.3], [3, 13.0]]) EV.push({ t: T.dieStart + dt, type: 'die', z: -2.4 * n });
EV.push({ t: T.hushStair[0], type: 'hush', d: T.hushStair[1] - T.hushStair[0] }, { t: T.hush4[0], type: 'hush', d: T.hush4[1] - T.hush4[0] }, { t: T.restrike, type: 'restrike' });
EV.push({ t: T.hushEnd[0], type: 'hush', d: T.hushEnd[1] - T.hushEnd[0] });
for (const o of outTimes()) EV.push({ t: o.t, type: 'out', n: o.n, z: -2.4 * o.n });
EV.push({ t: T.roomFlick[0], type: 'roomflick', d: T.freeze - T.roomFlick[0] }, { t: T.freeze, type: 'freeze' }, { t: T.off, type: 'recOff' }, { t: T.endCard[0], type: 'end' });
EV.push({ t: T.breathStop, type: 'breathStop' });
for (let k = 0; k < 6; k++) EV.push({ t: 582 + k * .62, type: 'beep' });
for (const a of [11.2, 18.4, 21.2, 81.4, 125.3, 143.1, 206.8, 207.7, 291.4, 292.4, 299.4, 307.7, 319.0, 320.1, 368.2, 368.8, 411.1, 412.2, 455.2, 474.3, 493.1]) EV.push({ t: a, type: 'af' });
for (const [a, b] of [[208, 210], [218.5, 219.5], [291, 292.6], [298.8, 299.3], [324, 334], [409, 411], [418, 419], [436, 437.5], [471.5, 475]]) EV.push({ t: a, type: 'zoom', d: b - a });
for (const [t, v] of [[18.8, .7], [20.0, .6], [78.5, .6], [80.2, .7], [94.5, .7], [124.6, .5], [141.5, .5], [206.0, 1.0], [219.4, .7], [238.5, .7], [291.0, .5], [299.4, .8],
  [307.6, .9], [312.0, .8], [367.6, .7], [405.6, .7], [433.2, .8], [443.2, 1.0], [452.0, .7], [486.2, .8], [489.0, .6]]) EV.push({ t, type: 'rustle', v });
CAPS.forEach(c => EV.push({ t: c.t0, type: 'cap', t1: c.t1, text: c.text }));
{ // curves for the mixer, sampled every 50 ms in tape time: light level around the camera (the hum follows it), camera z (room / corridor / stairwell), fear (breathing)
  const dt = .05, n = Math.round(DUR / dt), lc = [], zz = [], fe = [];
  for (let i = 0; i <= n; i++) { const t = picTime(i * dt); lc.push(+localLight(t).toFixed(3)); zz.push(+POS(t)[1].toFixed(2)); fe.push(+FEAR(t).toFixed(3)); }
  EV.push({ t: 0, type: 'curves', dt, lc, z: zz, fear: fe });
}
EV.sort((a, b) => a.t - b.t);

window.DUR = DUR; window.EV = EV; window.render = render; window.CAPS = CAPS;
window.dbg = { camera, scene, post, vhs, U, student, props, camPose, world };
render(T.rollIn + 1);
window.READY = true;
