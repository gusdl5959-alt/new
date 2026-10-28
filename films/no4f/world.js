// Space: one school corridor (reused for every floor; plates, windows, light states and notices change per floor), the duty room at its south end,
// a stairwell at its north end. Custom lighting shader: every fluorescent fixture lives in one float data texture (flat light, no occlusion), plus 4 point "spots"
// Coordinates: metres; x east, z south (−z = north, along the corridor); y up
import * as THREE from 'three';
import * as TX from './tex.js';

export const H = 2.7;                 // ceiling height (corridor and duty room)
export const HS = 5.6;                // stairwell ceiling
export const LX = 2.4, LZ = 2.4;      // light grid spacing
const WT = 0.16;
const LN = 64, LOFF = 32;
export const CW = 1.4;                // corridor half width
export const ZN = -40, ZS = -46.5;    // corridor north end / stairwell north wall
export const ROOM = { x0: -1.4, x1: 2.6, z0: 0, z1: 4.4 };

// ———————————————————— Layout ————————————————————
export const WALLS = [];   // {a, c, s0, s1, h}
const wx = (z, x0, x1, h = H) => WALLS.push({ a: 'x', c: z, s0: Math.min(x0, x1), s1: Math.max(x0, x1), h });
const wz = (x, z0, z1, h = H) => WALLS.push({ a: 'z', c: x, s0: Math.min(z0, z1), s1: Math.max(z0, z1), h });
wz(-CW, 0, ZN); wz(CW, 0, ZN);                                   // corridor
wx(0, -CW, -.5); wx(0, .5, ROOM.x1);                              // south end wall with the duty-room doorway (x ∈ [-.5, .5])
wz(ROOM.x0, 0, ROOM.z1); wz(ROOM.x1, 0, ROOM.z1); wx(ROOM.z1, ROOM.x0, ROOM.x1);   // duty room
wz(-CW, ZN, ZS, HS); wz(CW, ZN, ZS, HS); wx(ZS, -CW, CW, HS);    // stairwell
wz(0, -41.0, -44.6, 3.15);                                        // wall between the two flights
export const DOORWAY = { x0: -.5, x1: .5, h: 2.1 };

// ———————————————————— Light grid ————————————————————
export const lightData = new Float32Array(LN * LN * 4);
export const lightTex = new THREE.DataTexture(lightData, LN, LN, THREE.RGBAFormat, THREE.FloatType);
lightTex.magFilter = lightTex.minFilter = THREE.NearestFilter;
export const LIGHTS = [];   // {i, j, x, z, col, room, n (corridor index 1..16 from the south)}
{
  // corridor: x = 0, z = -2.4 … -38.4
  for (let n = 1; n <= 16; n++) LIGHTS.push({ i: 0, j: -n, x: 0, z: -2.4 * n, n, room: false });
  // duty room: one fixture
  LIGHTS.push({ i: 0, j: 1, x: 0, z: 2.4, n: 0, room: true });
  const tint = [[1.0, 1.0, .9], [1.02, 1.03, .86], [.97, 1.02, .95], [1.0, 1.05, .9]];
  LIGHTS.forEach((L, k) => { L.col = tint[k % 4]; L.ph = (k * 37.3) % 100; });
}
// k(L) → brightness multiplier, written each frame
export function updateLights(kfn) {
  lightData.fill(0);
  for (const L of LIGHTS) {
    const k = kfn(L), o = ((L.j + LOFF) * LN + (L.i + LOFF)) * 4;
    lightData[o] = L.col[0] * k; lightData[o + 1] = L.col[1] * k; lightData[o + 2] = L.col[2] * k; lightData[o + 3] = 1;
  }
  lightTex.needsUpdate = true;
}

// ———————————————————— Shaders ————————————————————
export const U = {
  uLights: { value: lightTex }, uAmb: { value: 0.15 }, uI: { value: 2.1 },
  uSpotP: { value: [new THREE.Vector3(0, 2.5, -39.8), new THREE.Vector3(-2.0, 1.9, -4), new THREE.Vector3(.4, 4.2, -45.6), new THREE.Vector3(.9, 1.15, 3.9)] },
  uSpotC: { value: [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()] },
  uFogCol: { value: new THREE.Color(0.11, 0.135, 0.105) }, uFogD: { value: 0.03 }, uFogG: { value: 1 },
  uTime: { value: 0 },
};
const VS = `
varying vec3 vW; varying vec3 vN; varying vec2 vUv;
void main(){ vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; vN = normalize(mat3(modelMatrix) * normal); vUv = uv;
  gl_Position = projectionMatrix * viewMatrix * w; }`;
const f2 = v => v.toFixed(2);
const COMMON = `
uniform sampler2D uLights; uniform float uAmb, uI, uFogD, uFogG, uTime; uniform vec3 uFogCol; uniform vec3 uSpotP[4]; uniform vec3 uSpotC[4];
varying vec3 vW; varying vec3 vN; varying vec2 vUv;
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.-2.*f);
  return mix(mix(h21(i), h21(i+vec2(1,0)), f.x), mix(h21(i+vec2(0,1)), h21(i+vec2(1,1)), f.x), f.y); }
float fbm(vec2 p){ float a = .5, s = 0.; for (int k = 0; k < 5; k++){ s += a * vn(p); p = p * 2.03 + 17.1; a *= .5; } return s; }
void lightAt(vec3 P, vec3 N, vec3 V, float shin, out vec3 dif, out vec3 spc, out vec3 amb){
  dif = vec3(0); spc = vec3(0); amb = vec3(0);
  float gi = floor(P.x / ${f2(LX)} + .5), gj = floor(P.z / ${f2(LZ)} + .5);
  for (int di = -1; di <= 1; di++) for (int dj = -2; dj <= 2; dj++) {
    float i = gi + float(di), j = gj + float(dj);
    vec4 L = texture2D(uLights, (vec2(i, j) + ${LOFF}.5) / ${LN}.);
    if (L.a < .5) continue;
    vec3 lp = vec3(i * ${f2(LX)}, ${f2(H - 0.03)}, j * ${f2(LZ)});
    vec3 d = lp - P; float d2 = dot(d, d); vec3 l = d * inversesqrt(d2);
    float emit = .3 + .7 * max(l.y, 0.);
    float ndl = max(dot(N, l), 0.);
    dif += L.rgb * ndl * emit / (d2 + .3);
    if (shin > 0.) { vec3 hv = normalize(l + V); spc += L.rgb * pow(max(dot(N, hv), 0.), shin) * emit / (d2 + .3); }
    vec2 dh = d.xz; amb += L.rgb / (dot(dh, dh) + 3.);
  }
  dif *= uI; spc *= uI; amb *= uAmb;
  for (int k = 0; k < 4; k++) {
    vec3 C = uSpotC[k]; if (dot(C, C) < 1e-6) continue;
    vec3 d = uSpotP[k] - P; float d2 = dot(d, d); vec3 l = d * inversesqrt(d2);
    dif += C * (max(dot(N, l), 0.) * .9 + .03) / (d2 + .2);
    if (shin > 0.) { vec3 hv = normalize(l + V); spc += C * pow(max(dot(N, hv), 0.), shin) / (d2 + .2); }
    amb += C * .04 / (d2 + 1.);
  }
}
vec3 fog(vec3 c, vec3 P){ float d = length(P - cameraPosition); float f = 1. - exp(-d * uFogD); return mix(c, uFogCol * uFogG, f); }
vec3 fogA(vec3 c, vec3 P, vec3 a){ float d = length(P - cameraPosition); float f = 1. - exp(-d * uFogD);
  float k = clamp(dot(a, vec3(.333)) / (.2 * uAmb / .16), .1, 1.25); return mix(c, uFogCol * uFogG * k, f); }
`;
function mat(frag, extraU = {}, opts = {}) {
  return new THREE.ShaderMaterial({ uniforms: { ...U, ...extraU }, vertexShader: VS, fragmentShader: COMMON + frag, ...opts });
}

// Walls: institutional two-tone oil paint (green dado below 1.15 m, cream above), a dark stripe, scuffs, grime, a terrazzo skirting
const WALL_FS = `
void main(){
  vec3 N = normalize(vN); vec3 V = normalize(cameraPosition - vW);
  float u = abs(N.x) > .5 ? vW.z * sign(N.x) : -vW.x * sign(N.z);
  float y = vW.y; bool upper = y > 1.19; float shin = 0., spec = 0.;
  vec3 alb;
  if (y < .13) alb = vec3(.36, .35, .31) * (.85 + .3 * vn(vec2(u * 40., y * 40.)));                       // terrazzo skirting
  else if (y < 1.15) { alb = vec3(.30, .41, .30); shin = 26.; spec = .07; }                              // green gloss dado
  else if (y < 1.19) alb = vec3(.15, .21, .15);
  else alb = vec3(.72, .73, .62);                                                                        // cream
  float st = fbm(vec2(u * .7, y * 1.1) + 5.);
  alb *= mix(vec3(1.), vec3(.84, .8, .66), smoothstep(.55, .8, st) * .7);
  alb *= 1. - .25 * smoothstep(.5, .9, fbm(vec2(u * 6., y * 3.))) * step(y, .55) * step(.13, y);        // shoe scuffs
  alb *= mix(vec3(1.), vec3(.8, .78, .66), smoothstep(${f2(H - .45)}, ${f2(H)}, y) * .5 * step(y, ${f2(H + .01)}));   // grime under the ceiling
  float crack = smoothstep(.012, .0, abs(vn(vec2(u * 1.3, y * .6) + 3.) - .5)) * step(.82, h21(vec2(floor(u / 3.), 2.)));
  alb *= 1. - .35 * crack;
  vec3 d, s, a; lightAt(vW + N * .02, N, V, shin, d, s, a);
  vec3 c = alb * (d + a) + s * spec;
  gl_FragColor = vec4(fogA(c, vW, a), 1.);
}`;
// Polished terrazzo: reflections of the tubes as soft specular streaks, wax wear down the middle
const FLOOR_FS = `
uniform sampler2D map;
void main(){
  vec3 N = vec3(0, 1, 0); vec3 V = normalize(cameraPosition - vW);
  vec3 alb = texture2D(map, vW.xz / 1.2).rgb;
  alb *= .92 + .14 * vn(vW.xz * 1.1);
  float wear = smoothstep(.9, .2, abs(vW.x - .1)) * step(vW.z, .1);
  float dull = smoothstep(.55, .75, fbm(vW.xz * .6 + 3.));
  vec3 d, s, a; lightAt(vW, N, V, 70., d, s, a);
  vec3 c = alb * (d + a * .8) + s * (.18 * (1. - .6 * dull) - .08 * wear) * vec3(1., .98, .9);
  gl_FragColor = vec4(fogA(c, vW, a), 1.);
}`;
const CEIL_FS = `
uniform sampler2D map;
void main(){
  vec3 N = vec3(0, -1, 0); vec3 V = normalize(cameraPosition - vW);
  vec3 alb = texture2D(map, vW.xz / 1.2).rgb;
  vec2 tile = floor(vW.xz / .6); float hs = h21(tile);
  alb *= .94 + .08 * hs;
  if (hs > .92) { vec2 f = fract(vW.xz / .6) - .5; float r = length(f + (vec2(h21(tile + 3.), h21(tile + 5.)) - .5) * .4);
    alb *= mix(vec3(1.), vec3(.74, .62, .4), smoothstep(.3, .26, r) * (.5 + .5 * smoothstep(.15, .28, r)) * .8); }
  vec3 d, s, a; lightAt(vW - vec3(0, .05, 0), N, V, 0., d, s, a);
  vec3 c = alb * (d * .5 + a * 1.1);
  gl_FragColor = vec4(fogA(c, vW, a), 1.);
}`;
const FIX_FS = `
uniform sampler2D map; uniform float uEmit;
void main(){
  vec2 cell = vec2(floor(vW.x / ${f2(LX)} + .5), floor(vW.z / ${f2(LZ)} + .5));
  vec4 L = texture2D(uLights, (cell + ${LOFF}.5) / ${LN}.);
  vec3 tx = texture2D(map, vUv).rgb;
  float glow = smoothstep(.8, .97, dot(tx, vec3(.33)));
  vec3 c = mix(tx * .22 * (L.rgb * .4 + .04), tx * L.rgb * uEmit, glow);
  gl_FragColor = vec4(fog(c, vW), 1.);
}`;
const PAINT_FS = `
uniform sampler2D map; uniform vec3 color; uniform float useMap, shin, spec, emit;
void main(){
  vec3 N = normalize(vN); if (!gl_FrontFacing) N = -N; vec3 V = normalize(cameraPosition - vW);
  vec3 alb = color; if (useMap > .5) alb *= texture2D(map, vUv).rgb;
  vec3 d, s, a; lightAt(vW + N * .02, N, V, shin, d, s, a);
  vec3 c = alb * (d + a) + s * spec + alb * emit;
  gl_FragColor = vec4(fogA(c, vW, a), 1.);
}`;
const SIL_FS = `
uniform sampler2D map; uniform float rim;
void main(){
  vec4 tx = texture2D(map, vUv); if (tx.a < .5) discard;
  vec3 N = normalize(vN); vec3 V = normalize(cameraPosition - vW);
  vec3 d, s, a; lightAt(vW + N * .05, N, V, 0., d, s, a);
  vec3 c = vec3(.012, .011, .009) * (d + a) * (1. + rim);
  gl_FragColor = vec4(fogA(c, vW, a), 1.);
}`;
export function silhouetteMat(map) { const m = mat(SIL_FS, { map: { value: map }, rim: { value: 0 } }); m.side = THREE.DoubleSide; return m; }
export function paint(o = {}) {
  return mat(PAINT_FS, {
    map: { value: o.map || null }, color: { value: new THREE.Color(o.color ?? '#ffffff') }, useMap: { value: o.map ? 1 : 0 },
    shin: { value: o.shin ?? 0 }, spec: { value: o.spec ?? 0 }, emit: { value: o.emit ?? 0 },
  }, o.side ? { side: o.side } : {});
}

// ———————————————————— Geometry ————————————————————
function boxInto(pos, nor, uv, x0, y0, z0, x1, y1, z1) {
  const g = new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0); g.translate((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
  const ni = g.toNonIndexed();
  pos.push(...ni.attributes.position.array); nor.push(...ni.attributes.normal.array); uv.push(...ni.attributes.uv.array);
}
function merged(pos, nor, uv) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  return g;
}
const box = (m, x0, y0, z0, x1, y1, z1) => { const b = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0), m); b.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); return b; };
// A textured plane on a wall face. side: '+x' faces east, '-x' west, '+z' south, '-z' north
function onWall(m, w, h, x, y, z, side) {
  const p = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); p.position.set(x, y, z);
  p.rotation.y = { '+z': 0, '-z': Math.PI, '+x': Math.PI / 2, '-x': -Math.PI / 2 }[side]; return p;
}

export function buildWorld(scene) {
  const T = { floor: TX.terrazzo(), ceil: TX.ceiling(), fix: TX.fixture() };
  const wallMat = mat(WALL_FS);
  const P = [], N = [], UV = [];
  for (const w of WALLS) {
    if (w.a === 'x') boxInto(P, N, UV, w.s0, 0, w.c - WT / 2, w.s1, w.h, w.c + WT / 2);
    else boxInto(P, N, UV, w.c - WT / 2, 0, w.s0, w.c + WT / 2, w.h, w.s1);
  }
  boxInto(P, N, UV, DOORWAY.x0, DOORWAY.h, -WT / 2, DOORWAY.x1, H, WT / 2);     // lintel over the duty-room doorway
  boxInto(P, N, UV, -CW, H, ZN - WT / 2, CW, HS, ZN + WT / 2);                    // header between corridor and stairwell
  const walls = new THREE.Mesh(merged(P, N, UV), wallMat); scene.add(walls);
  // The doorway, bricked up on every floor except the first (same paint)
  const plug = box(wallMat, DOORWAY.x0, 0, -WT / 2, DOORWAY.x1, DOORWAY.h, WT / 2); scene.add(plug);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 70), mat(FLOOR_FS, { map: { value: T.floor } }));
  floor.rotation.x = -Math.PI / 2; floor.position.set(0, 0, -20); scene.add(floor);
  const ceilM = mat(CEIL_FS, { map: { value: T.ceil } });
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.x1 - ROOM.x0, ROOM.z1 - ZN), ceilM);
  ceil.rotation.x = Math.PI / 2; ceil.position.set((ROOM.x0 + ROOM.x1) / 2, H, (ROOM.z1 + ZN) / 2); scene.add(ceil);
  const ceil2 = new THREE.Mesh(new THREE.PlaneGeometry(2 * CW, ZN - ZS), ceilM);
  ceil2.rotation.x = Math.PI / 2; ceil2.position.set(0, HS, (ZN + ZS) / 2); scene.add(ceil2);
  // Fixtures: hung 4 cm below the ceiling, merged
  const tp = [], tn = [], tu = [];
  for (const L of LIGHTS) {
    const x0 = L.x - .11, x1 = L.x + .11, z0 = L.z - .6, z1 = L.z + .6, y = H - .04;
    tp.push(x0, y, z0, x1, y, z0, x1, y, z1, x0, y, z0, x1, y, z1, x0, y, z1);
    for (let k = 0; k < 6; k++) tn.push(0, -1, 0);
    tu.push(0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1);
  }
  const fixMat = mat(FIX_FS, { map: { value: T.fix }, uEmit: { value: 4.0 } });
  const fix = new THREE.Mesh(merged(tp, tn, tu), fixMat); scene.add(fix);
  const fixBodyM = paint({ color: '#a8a69d' });
  for (const L of LIGHTS) scene.add(box(fixBodyM, L.x - .12, H - .04, L.z - .62, L.x + .12, H, L.z + .62));
  // Stairs: flight 1 (x ∈ [0, CW]) rises north to the landing; flight 2 (x ∈ [-CW, 0]) rises south from the landing
  const stairM = paint({ color: '#8f8a78', shin: 30, spec: .05 }), noseM = paint({ color: '#3d3a33' });
  const R1 = 10, rise = .16, run = .36, zA = -41.0;
  for (let k = 0; k < R1; k++) {
    const z0 = zA - k * run, y1 = (k + 1) * rise;
    scene.add(box(stairM, 0.05, 0, z0 - run, CW - WT / 2, y1, z0));
    scene.add(box(noseM, 0.05, y1 - .03, z0 - .04, CW - WT / 2, y1 + .005, z0));
  }
  const zL = zA - R1 * run;   // −44.6: landing starts
  scene.add(box(stairM, -CW + WT / 2, 1.45, ZS + WT / 2, CW - WT / 2, R1 * rise, zL));
  for (let k = 0; k < R1; k++) {
    const z1 = zL + k * run, y1 = R1 * rise + (k + 1) * rise;
    scene.add(box(stairM, -CW + WT / 2, y1 - .3, z1, -0.05, y1, z1 + run));
    scene.add(box(noseM, -CW + WT / 2, y1 - .03, z1 + run - .04, -0.05, y1 + .005, z1 + run));
  }
  // Handrail on the dividing wall
  const railM = paint({ color: '#9fa29e', shin: 80, spec: .5 });
  const rail = new THREE.Mesh(new THREE.CylinderGeometry(.025, .025, Math.hypot(R1 * run, R1 * rise), 8), railM);
  rail.position.set(.1, .9 + R1 * rise / 2, zA - R1 * run / 2); rail.rotation.x = -Math.atan2(R1 * rise, R1 * run) + Math.PI / 2; rail.rotation.order = 'YXZ'; scene.add(rail);
  return { walls, plug, floor, ceil, fix, fixMat, T, wallMat };
}

// Props. Returns handles that change per floor
export const CLASS = [0, 1, 2, 3, 4];   // classroom k spans z ∈ [-8k, -8k-8] on the west side
export const doorZ = (k, back) => -8 * k - (back ? 6.5 : 1.5);
export const PLATES = {
  1: ['행정실', '교무실', '방송실', '보건실', '과학실'],
  2: ['2-5', '2-4', '2-3', '2-2', '2-1'],
  3: ['3-7', '3-6', '3-5', '3-4', '3-3'],
  4: ['4-4', '4-4', '4-3', '4-2', '4-1'],
  5: ['4-4', '4-4', '4-4', '4-4', '4-4'],
};
export function buildProps(scene) {
  const out = { doors: [], windows: [], plates: [], outside: [] };
  const plateT = {}; for (const f in PLATES) for (const s of PLATES[f]) plateT[s] ??= TX.plate(s, /-/.test(s) ? '' : '');
  out.plateT = plateT;
  const doorDark = TX.door(0, 1), doorLit = TX.door(1, 2);
  const winDark = TX.highWindow(0, false, 3), winLit = TX.highWindow(1, true, 4), winLitEmpty = TX.highWindow(1, false, 4);
  out.T = { doorDark, doorLit, winDark, winLit, winLitEmpty };
  const xw = -CW + WT / 2;   // west wall face
  const frameM = paint({ color: '#4a3524', shin: 20, spec: .04 });
  for (const k of CLASS) {
    for (const back of [false, true]) {
      const z = doorZ(k, back);
      // Black void behind the door (seen when it slides open)
      const vm = paint({ color: '#000000' });
      scene.add(onWall(vm, 1.0, 2.1, xw + .002, 1.05, z, '+x'));
      const m = paint({ map: doorDark, shin: 14, spec: .03 });
      const d = onWall(m, 1.0, 2.1, xw + .012, 1.05, z, '+x'); scene.add(d);
      out.doors.push({ k, back, mesh: d, mat: m, voidMat: vm, z });
      // Frame
      scene.add(box(frameM, xw, 0, z - .56, xw + .05, 2.16, z - .5), box(frameM, xw, 0, z + .5, xw + .05, 2.16, z + .56), box(frameM, xw, 2.1, z - .56, xw + .05, 2.16, z + .56));
    }
    const wm = paint({ map: winDark, shin: 120, spec: .45 });
    const w = onWall(wm, 3.6, .8, xw + .006, 1.95, -8 * k - 4, '+x'); scene.add(w);
    out.windows.push({ k, mesh: w, mat: wm });
    scene.add(box(frameM, xw, 1.5, -8 * k - 5.85, xw + .06, 1.55, -8 * k - 2.15));   // sill
    // Protruding plate above the front door: two faces back to back (south face read walking north, north face read walking south)
    const pm = paint({ map: plateT[PLATES[1][k]] }), pz = doorZ(k, false);
    const pS = onWall(pm, .42, .16, xw + .27, 2.42, pz + .006, '+z'), pN = onWall(pm, .42, .16, xw + .27, 2.42, pz - .006, '-z');
    scene.add(pS, pN, box(paint({ color: '#e8e6dc' }), xw + .05, 2.33, pz - .005, xw + .49, 2.51, pz + .005));
    out.plates.push({ k, mat: pm });
  }
  // Posters on the piers between classrooms (low), notice board frames
  const posters = [[-8, 'quiet', 21], [-24, 'motto', 22], [-32, 'study', 23]];
  out.posters = [];
  for (const [z, kind, seed] of posters) {
    const m = paint({ map: TX.poster(kind, seed) });
    const p = onWall(m, .36, .52, xw + .006, 1.45, z, '+x'); scene.add(p); out.posters.push(p);
  }
  // The 4th-floor notice (taped where the 1st floor has nothing): z = −16
  out.rules4 = onWall(paint({ map: TX.notice('rules4', { age: .85, seed: 9 }) }), .42, .594, xw + .004, 1.42, -16.0, '+x'); scene.add(out.rules4);
  const tapeM = paint({ color: '#d8cf98' }); out.tape4 = [];
  for (const [dz, dy, r] of [[-.19, .28, .5], [.19, .285, -.4], [-.195, -.27, -.5], [.2, -.275, .6]]) { const t = onWall(tapeM, .07, .022, xw + .006, 1.42 + dy, -16.0 + dz, '+x'); t.rotation.x = r; scene.add(t); out.tape4.push(t); }
  // PA speaker high on the pier at z = −16
  const spk = box(paint({ color: '#b8b7ad' }), xw, 2.3, -16.2, xw + .12, 2.5, -15.8); scene.add(spk);
  scene.add(onWall(paint({ map: TX.speakerTex() }), .38, .18, xw + .122, 2.4, -16.0, '+x'));
  // East wall: outside windows (one bay per 2.4 m), sills, a radiator under every other bay
  const xe = CW - WT / 2;
  const outT = [1, 2, 3, 4].map(s => TX.outsideWindow(s)), voidT = TX.outsideWindow(9, true);
  out.T.outT = outT; out.T.voidT = voidT;
  const sillM = paint({ color: '#cfcdc2', shin: 30, spec: .05 }), radM = paint({ color: '#b9b7aa', shin: 20, spec: .05 });
  for (let k = 0; k < 16; k++) {
    const z = -1.2 - 2.4 * k;
    const m = paint({ map: outT[k % 4], shin: 140, spec: .55, emit: .5 });
    const w = onWall(m, 2.0, 1.4, xe - .006, 1.65, z, '-x'); scene.add(w); out.outside.push({ mat: m, k });
    scene.add(box(sillM, xe - .14, .9, z - 1.02, xe, .95, z + 1.02));
    if (k % 2 === 0) scene.add(box(radM, xe - .2, .18, z - .55, xe - .08, .74, z + .55));
  }
  // Exit sign hanging at the corridor's north end (both faces)
  const exT = TX.exitSign(); const exM = paint({ map: exT, emit: 7 });
  scene.add(box(paint({ color: '#d9d8cc' }), -.27, 2.4, ZN + .05, .27, 2.62, ZN + .15));
  out.exitS = onWall(exM, .5, .2, 0, 2.51, ZN + .152, '+z'); scene.add(out.exitS);
  scene.add(box(paint({ color: '#888' }), -.01, 2.62, ZN + .09, .01, H, ZN + .11));
  out.exitM = exM;
  // Floor sign on the landing wall (the floor above): 1F→2F … ; only ever seen once
  out.floorSign = onWall(paint({ map: TX.floorSign('4층') }), 1.2, .9, .7, 2.5, ZS + WT / 2 + .004, '+z'); scene.add(out.floorSign);
  // Bulb fixture over the landing
  out.bulb = new THREE.Mesh(new THREE.SphereGeometry(.07, 12, 8), paint({ color: '#fff6dc', emit: 6 })); out.bulb.position.set(.4, 4.3, -45.6); scene.add(out.bulb);
  // —— Duty room ——
  const r = ROOM;
  out.rulesT = TX.notice('rules', { age: .6, seed: 5 });
  out.rules = onWall(paint({ map: out.rulesT }), .42, .594, r.x0 + WT / 2 + .004, 1.45, 2.7, '+x'); scene.add(out.rules);
  scene.add(onWall(paint({ map: TX.calendar() }), .32, .46, r.x1 - WT / 2 - .004, 1.62, 1.9, '-x'));
  const wood = paint({ color: '#6b4f33', shin: 30, spec: .06 }), steel = paint({ color: '#7c7f78', shin: 40, spec: .1 });
  scene.add(box(wood, -.7, .70, 3.55, 1.6, .745, 4.3));                                      // desk top
  scene.add(box(steel, -.66, 0, 3.6, -.6, .7, 4.25), box(steel, 1.5, 0, 3.6, 1.56, .7, 4.25), box(steel, .95, 0, 3.62, 1.55, .7, 4.25));
  scene.add(box(paint({ color: '#2b2b2b', shin: 40, spec: .1 }), -.4, .745, 3.95, -.12, .82, 4.2));   // telephone
  scene.add(box(paint({ color: '#3d4a6b', shin: 30, spec: .1 }), 1.25, .745, 3.95, 1.33, .98, 4.03));  // thermos
  // Chair
  const chairM = paint({ color: '#4f4b45' });
  scene.add(box(chairM, -1.05, .44, 2.95, -.6, .49, 3.4), box(chairM, -1.08, .49, 2.95, -1.03, .9, 3.4));   // pushed back against the west wall
  for (const [cx, cz] of [[-1.03, 2.97], [-.62, 2.97], [-1.03, 3.38], [-.62, 3.38]]) scene.add(box(steel, cx - .015, 0, cz - .015, cx + .015, .44, cz + .015));
  // Duty log on the desk (two states)
  out.ledgerT = [TX.ledger(false), TX.ledger(true)];
  out.ledgerM = paint({ map: out.ledgerT[0] });
  const lg = new THREE.Mesh(new THREE.PlaneGeometry(.6, .42), out.ledgerM); lg.rotation.set(-Math.PI / 2, 0, Math.PI); lg.position.set(.75, .748, 3.88); scene.add(lg);   // text faces someone north of the desk, looking south
  scene.add(box(paint({ color: '#5b2f2a' }), .43, .745, 3.66, 1.07, .747, 4.1));   // ledger cover under the pages
  // Desk lamp
  const lampM = paint({ color: '#2f3a33', shin: 40, spec: .2 });
  scene.add(box(lampM, 1.3, .745, 3.95, 1.45, .76, 4.1), box(lampM, 1.36, .76, 4.0, 1.39, 1.12, 4.03));
  out.lampHead = box(paint({ color: '#fff3d6', emit: 2.5 }), 1.0, 1.08, 3.9, 1.38, 1.14, 4.05); scene.add(out.lampHead);
  return out;
}
