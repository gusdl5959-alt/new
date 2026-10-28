// Procedural textures (Canvas2D) for a 1998 Korean school building at night: terrazzo floor, gypsum ceiling, bare fluorescent fixtures,
// sliding classroom doors, high corridor windows (dark / lit with someone inside), outside windows, class plates, notices, duty log, exit sign
// All deterministic (mulberry seed), no external images
import * as THREE from 'three';
import { mulberry } from '/core/lib.js';

const cv = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
function tex(c, { srgb = true, repeat = true, aniso = 8 } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = aniso; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  return t;
}
function grain(x, w, h, n, a, R, cols) {
  for (let i = 0; i < n; i++) {
    x.fillStyle = cols[Math.floor(R() * cols.length)]; x.globalAlpha = a * (0.3 + R() * 0.7);
    const s = 1 + R() * 2; x.fillRect(R() * w, R() * h, s, s);
  }
  x.globalAlpha = 1;
}
export const F = {
  myeongjo: (w, px) => `${w} ${px}px 'Nanum Myeongjo'`, gothic: (w, px) => `${w} ${px}px 'Nanum Gothic'`, coding: (w, px) => `${w} ${px}px 'Nanum Gothic Coding'`, pen: (w, px) => `${w} ${px}px 'Nanum Pen Script'`,
};

// Terrazzo (인조석 물갈기) floor: 1.2 m square, brass divider strips on the edges, polished and waxed
export function terrazzo() {
  const S = 512, c = cv(S, S), x = c.getContext('2d'), R = mulberry(23);
  x.fillStyle = '#9d9784'; x.fillRect(0, 0, S, S);
  grain(x, S, S, 70000, 0.35, R, ['#7f7a69', '#b8b39f', '#6c6858', '#c9c4b0', '#8d8a7c']);
  for (let i = 0; i < 2600; i++) {   // marble chips
    const s = 1.5 + R() * 4; x.fillStyle = ['#d8d3c2', '#55534a', '#a7a08a', '#e6e1d2', '#3f3d37'][Math.floor(R() * 5)];
    x.globalAlpha = .55 + R() * .4; x.beginPath(); x.ellipse(R() * S, R() * S, s, s * (.5 + R() * .5), R() * 3, 0, 7); x.fill();
  }
  x.globalAlpha = 1;
  x.fillStyle = '#8a7444'; x.fillRect(0, 0, S, 3); x.fillRect(0, 0, 3, S);   // brass strip
  x.fillStyle = 'rgba(40,30,10,.35)'; x.fillRect(0, 3, S, 1); x.fillRect(3, 0, 1, S);
  return tex(c);
}

// Gypsum-board ceiling (석고 텍스) 0.6 m tiles, the texture spans 1.2 × 1.2 m
export function ceiling() {
  const S = 512, c = cv(S, S), x = c.getContext('2d'), R = mulberry(31);
  x.fillStyle = '#d8d6c8'; x.fillRect(0, 0, S, S);
  for (let i = 0; i < 7000; i++) { x.fillStyle = `rgba(100,96,80,${0.15 + R() * 0.3})`; const w = 1 + R() * 2.2; x.fillRect(R() * S, R() * S, w, 1 + R()); }
  grain(x, S, S, 16000, 0.08, R, ['#a8a593', '#efede0']);
  x.fillStyle = 'rgba(70,66,52,.55)';
  for (const p of [0, S / 2]) { x.fillRect(p, 0, 2, S); x.fillRect(0, p, S, 2); }
  return tex(c);
}

// Bare twin-tube fluorescent fixture, 0.22 × 1.2 m (texture 64 × 320); bright = the tubes
export function fixture() {
  const W = 64, H = 320, c = cv(W, H), x = c.getContext('2d');
  x.fillStyle = '#bdbab0'; x.fillRect(0, 0, W, H);
  x.fillStyle = '#8f8c82'; x.fillRect(0, 0, W, 6); x.fillRect(0, H - 6, W, 6);
  for (const cx of [18, 46]) {
    const g = x.createLinearGradient(cx - 9, 0, cx + 9, 0);
    g.addColorStop(0, '#d9d7cf'); g.addColorStop(.35, '#ffffff'); g.addColorStop(.65, '#ffffff'); g.addColorStop(1, '#d9d7cf');
    x.fillStyle = g; x.fillRect(cx - 9, 14, 18, H - 28);
    x.fillStyle = '#6a675f'; x.fillRect(cx - 9, 8, 18, 8); x.fillRect(cx - 9, H - 16, 18, 8);   // end caps
  }
  return tex(c, { repeat: false });
}

// Text helpers (Korean wraps per character)
function wrapKo(x, text, maxW) {
  const lines = []; let cur = '';
  for (const ch of text) { const t = cur + ch; if (x.measureText(t).width > maxW && cur) { const sp = cur.lastIndexOf(' '); if (sp > 0) { lines.push(cur.slice(0, sp)); cur = cur.slice(sp + 1) + ch; } else { lines.push(cur); cur = ch; } } else cur = t; }
  if (cur) lines.push(cur); return lines;
}
function paper(x, W, H, R, age) {
  x.fillStyle = age > .5 ? '#ebe5cc' : '#f1eedf'; x.fillRect(0, 0, W, H);
  const eg = x.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.78);
  eg.addColorStop(0, 'rgba(0,0,0,0)'); eg.addColorStop(1, `rgba(150,120,50,${0.16 + age * 0.22})`);
  x.fillStyle = eg; x.fillRect(0, 0, W, H);
  grain(x, W, H, 30000, 0.06, R, ['#8c7c55', '#fff9e6']);
}
function specks(x, W, H, R) {
  for (let i = 0; i < 90; i++) { x.fillStyle = `rgba(30,30,30,${R() * 0.25})`; x.fillRect(R() * W, R() * H, 1 + R() * 3, 1 + R() * 2); }
}

// The rules — duty room (A3 portrait 0.42 × 0.594 m → 1050 × 1485 px)
export const RULES = [
  '순찰은 1층부터 3층까지, 반드시 계단으로 이동합니다.',
  '자정 이후 교내 방송이 나오면 응답하지 마십시오. 이 건물에 방송 담당자는 없습니다.',
  '3층 복도 끝 교실에 불이 켜져 있으면 끄지 말고 지나가십시오.',
  '학생을 만나면 바닥만 보십시오. 이름을 묻지 마십시오.',
  '본관은 3층 건물입니다. 계단이 4층으로 이어진다면 뒤돌아 내려오십시오.',
  '순찰을 마치면 당직 일지에 서명하십시오.',
];
// The same sheet found on the floor that does not exist: revised, and wrong
export const RULES4 = [
  '순찰은 4층부터 시작합니다.',
  '교내 방송이 나오면 대답하십시오.',
  '불이 켜진 교실에는 학생이 있습니다. 출석을 부르십시오.',
  '학생을 만나면 이름을 물어보십시오.',
  '본관은 4층 건물입니다.',
  '서명은 이미 끝났습니다. 돌아가지 마십시오.',
];
export function notice(kind = 'rules', { age = 0.6, seed = 5 } = {}) {
  const W = 1050, H = 1485, c = cv(W, H), x = c.getContext('2d'), R = mulberry(seed), M = 84;
  paper(x, W, H, R, age);
  const ink = '#1c1a16'; x.fillStyle = ink; x.textBaseline = 'alphabetic';
  x.font = F.gothic(800, 30); x.fillText('○○고등학교 행정실', M, 118);
  const form = kind === 'rules' ? '서식 당-03 (개정 7)' : '서식 당-03 (개정 8)';
  x.fillText(form, W - M - x.measureText(form).width, 118);
  x.fillRect(M, 138, W - 2 * M, 5);
  x.font = F.myeongjo(800, 92);
  x.fillText('야간 순찰 수칙', M, 262);
  x.font = F.gothic(400, 34); x.fillStyle = '#3a362d';
  x.fillText(kind === 'rules' ? '당직 근무자는 순찰 전에 반드시 읽으십시오.' : '당직 근무자는 이 수칙을 따르십시오.', M, 326);
  x.fillStyle = ink; x.fillRect(M, 356, W - 2 * M, 2);
  const list = kind === 'rules' ? RULES : RULES4;
  let y = kind === 'rules' ? 436 : 470; const fs = kind === 'rules' ? 38 : 46, lh = kind === 'rules' ? 52 : 62, gap = kind === 'rules' ? 24 : 30;
  list.forEach((r, i) => {
    x.font = F.gothic(800, fs); x.fillText(`${i + 1}.`, M, y);
    x.font = F.gothic(700, fs);
    for (const ln of wrapKo(x, r, W - 2 * M - 74)) { x.fillText(ln, M + 74, y); y += lh; }
    y += gap;
  });
  x.fillRect(M, H - 168, W - 2 * M, 2);
  x.font = F.gothic(400, 32); x.fillStyle = '#3a362d';
  x.fillText('협조해 주셔서 감사합니다.', M, H - 112);
  x.fillText('행정실장', M, H - 70);
  if (kind === 'rules4') {   // the same stamp, smeared; one line in pen added under the closing
    x.save(); x.translate(W - 250, H - 110); x.rotate(-.2); x.strokeStyle = 'rgba(150,40,30,.55)'; x.lineWidth = 7; x.beginPath(); x.arc(0, 0, 70, 0, 7); x.stroke();
    x.font = F.myeongjo(800, 40); x.fillStyle = 'rgba(150,40,30,.55)'; x.textAlign = 'center'; x.fillText('행정', 0, -4); x.fillText('실장', 0, 40); x.restore();
  } else {
    x.save(); x.translate(W - 250, H - 110); x.rotate(.1); x.strokeStyle = 'rgba(170,40,30,.7)'; x.lineWidth = 7; x.beginPath(); x.arc(0, 0, 70, 0, 7); x.stroke();
    x.font = F.myeongjo(800, 40); x.fillStyle = 'rgba(170,40,30,.7)'; x.textAlign = 'center'; x.fillText('행정', 0, -4); x.fillText('실장', 0, 40); x.restore();
  }
  specks(x, W, H, R);
  x.fillStyle = 'rgba(0,0,0,.05)'; x.fillRect(0, H * 0.5, W, 3); x.fillStyle = 'rgba(255,255,255,.25)'; x.fillRect(0, H * 0.5 + 3, W, 2);
  return tex(c, { repeat: false, aniso: 16 });
}

// Duty log (당직 일지): an open ledger, two pages, 0.6 × 0.42 m → 1200 × 840 px
// signed = false: tonight's row is still blank; true: tonight's row and tomorrow's row are already signed in the same hand
export const LOG = [
  ['10.26', '박형철'], ['10.27', '이상훈'], ['10.28', '최민석'], ['10.29', '정대영'], ['10.30', '윤재호'], ['10.31', '한승우'], ['11.01', '오경수'], ['11.02', '서동진'],
];
export function ledger(signed = false) {
  const W = 1200, H = 840, c = cv(W, H), x = c.getContext('2d'), R = mulberry(signed ? 71 : 70);
  x.fillStyle = '#e7e0c6'; x.fillRect(0, 0, W, H);
  grain(x, W, H, 26000, .06, R, ['#8c7c55', '#fff9e6']);
  const sh = x.createLinearGradient(W / 2 - 60, 0, W / 2 + 60, 0); sh.addColorStop(0, 'rgba(0,0,0,0)'); sh.addColorStop(.5, 'rgba(60,45,20,.35)'); sh.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = sh; x.fillRect(W / 2 - 60, 0, 120, H);
  // Left page: title block
  x.fillStyle = '#2a2a33'; x.font = F.myeongjo(800, 54); x.fillText('당 직 일 지', 120, 150);
  x.font = F.gothic(700, 26); x.fillStyle = '#3d3b45'; x.fillText('1998학년도 2학기 · 본관', 122, 200);
  x.fillRect(110, 226, 420, 3);
  x.font = F.gothic(400, 24);
  ['· 순찰 후 반드시 본인이 서명할 것', '· 대리 서명 금지', '· 이상 사항은 비고란에 기재'].forEach((s, i) => x.fillText(s, 122, 280 + i * 42));
  x.font = F.pen(400, 44); x.fillStyle = 'rgba(40,40,90,.75)'; x.fillText('11/3 신임 김정우 선생 첫 당직', 130, 520);
  // Right page: the table
  const X0 = 650, Y0 = 70, cols = [0, 110, 260, 420, 500], RH = 66;
  x.strokeStyle = '#6b6a78'; x.lineWidth = 2; x.fillStyle = '#2a2a33'; x.font = F.gothic(800, 26);
  ['날짜', '당직자', '서명', '비고'].forEach((h, i) => x.fillText(h, X0 + cols[i] + 14, Y0 + 44));
  const rows = [...LOG, ['11.03', signed ? '김정우' : ''], ['11.04', signed ? '김정우' : '']];
  for (let r = 0; r <= rows.length + 1; r++) { x.beginPath(); x.moveTo(X0, Y0 + r * RH); x.lineTo(X0 + 500, Y0 + r * RH); x.stroke(); }
  for (const cx of cols) { x.beginPath(); x.moveTo(X0 + cx, Y0); x.lineTo(X0 + cx, Y0 + (rows.length + 1) * RH); x.stroke(); }
  rows.forEach(([d, n], i) => {
    const y = Y0 + (i + 1) * RH + 46;
    x.font = F.gothic(700, 26); x.fillStyle = '#2a2a33'; x.fillText(d, X0 + 16, y);
    if (!n) return;
    const late = i >= LOG.length;
    x.font = F.pen(400, 46); x.fillStyle = late ? 'rgba(25,25,30,.92)' : `rgba(30,35,${80 + (i * 37) % 60},.85)`;
    x.save(); x.translate(X0 + cols[1] + 14, y); x.rotate((R() - .5) * .05); x.fillText(n, 0, 0); x.restore();
    // Signature: a scrawl (the last two are identical, stroke for stroke)
    const S = mulberry(late ? 999 : 300 + i * 13);
    x.save(); x.translate(X0 + cols[2] + 18, y - 12); x.strokeStyle = x.fillStyle; x.lineWidth = 3; x.beginPath(); x.moveTo(0, 0);
    let px = 0; for (let k = 0; k < 7; k++) { px += 12 + S() * 10; x.quadraticCurveTo(px - 6, -18 + S() * 34, px, (S() - .5) * 12); }
    x.stroke(); x.restore();
  });
  // Pencilled remark on the 10.31 row
  x.font = F.pen(400, 34); x.fillStyle = 'rgba(70,70,70,.7)'; x.fillText('계단 이상', X0 + cols[3] + 2, Y0 + 6 * RH + 46);
  return tex(c, { repeat: false, aniso: 16 });
}

// Protruding class plate (반 표찰), 0.42 × 0.16 m (420 × 160 px); text such as '2-3', '방송실'
export function plate(label, sub = '') {
  const W = 420, H = 160, c = cv(W, H), x = c.getContext('2d');
  x.fillStyle = '#f0eee4'; x.fillRect(0, 0, W, H);
  x.strokeStyle = '#3f5a44'; x.lineWidth = 12; x.strokeRect(6, 6, W - 12, H - 12);
  x.fillStyle = '#1f2a22'; x.textAlign = 'center'; x.textBaseline = 'middle';
  const big = /^[0-9]-[0-9]$/.test(label);
  x.font = (big ? F.gothic(800, 104) : F.gothic(800, 74)); x.fillText(label, W / 2, H / 2 + (sub ? -10 : 4));
  if (sub) { x.font = F.gothic(700, 26); x.fillText(sub, W / 2, H - 28); }
  return tex(c, { repeat: false });
}

// Wooden sliding door (미닫이), 1.0 × 2.1 m (300 × 630 px); small glass window in the upper half (dark glass; glow sets the lit variant)
export function door(glow = 0, seed = 1) {
  const W = 300, H = 630, c = cv(W, H), x = c.getContext('2d'), R = mulberry(seed);
  x.fillStyle = '#7a5a3a'; x.fillRect(0, 0, W, H);
  for (let i = 0; i < 70; i++) { x.strokeStyle = `rgba(${50 + R() * 30},${32 + R() * 20},15,${.15 + R() * .2})`; x.lineWidth = 1 + R() * 2; const xx = R() * W; x.beginPath(); x.moveTo(xx, 0); x.bezierCurveTo(xx + (R() - .5) * 20, H * .3, xx + (R() - .5) * 20, H * .7, xx + (R() - .5) * 10, H); x.stroke(); }
  x.strokeStyle = 'rgba(30,20,10,.6)'; x.lineWidth = 6; x.strokeRect(14, 14, W - 28, H - 28);
  // Window
  const wx = 60, wy = 70, ww = W - 120, wh = 200;
  x.fillStyle = '#5b5f5c'; x.fillRect(wx - 8, wy - 8, ww + 16, wh + 16);
  const g = x.createLinearGradient(0, wy, 0, wy + wh);
  if (glow) { g.addColorStop(0, '#fffbe8'); g.addColorStop(1, '#f2ead0'); } else { g.addColorStop(0, '#1d211f'); g.addColorStop(1, '#0d0f0e'); }
  x.fillStyle = g; x.fillRect(wx, wy, ww, wh);
  if (!glow) { x.fillStyle = 'rgba(200,210,200,.08)'; x.beginPath(); x.moveTo(wx, wy + wh); x.lineTo(wx + 50, wy); x.lineTo(wx + 80, wy); x.lineTo(wx + 30, wy + wh); x.fill(); }
  // Handle recess, kick scuffs
  x.fillStyle = '#3d2b1a'; x.fillRect(W - 50, H * .52, 18, 70);
  for (let i = 0; i < 40; i++) { x.fillStyle = `rgba(30,25,20,${R() * .25})`; x.fillRect(R() * W, H - 90 + R() * 70, 4 + R() * 30, 2 + R() * 4); }
  return tex(c, { repeat: false });
}

// High corridor window strip into a classroom: 3.6 × 0.8 m (1080 × 240 px), four panes.
// lit = 0: dark glass (faint shapes of desks); lit = 1: room lit, rows of desks, someone seated (seat = true)
import { drawStudent } from './student.js';
export function highWindow(lit = 0, seat = false, seed = 3) {
  const W = 1080, H = 240, c = cv(W, H), x = c.getContext('2d'), R = mulberry(seed);
  // Inside: back wall + desk tops
  if (lit) {
    const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#fffdf2'); g.addColorStop(1, '#efe6c8'); x.fillStyle = g; x.fillRect(0, 0, W, H);
    x.fillStyle = '#5d6b55'; x.fillRect(0, H * .78, W, H * .22);   // blackboard band at the far wall bottom (seen through)
    x.fillStyle = 'rgba(120,100,70,.55)'; for (let k = 0; k < 9; k++) x.fillRect(30 + k * 120, H * .72, 70, 10);   // desk tops
    if (seat) { x.save(); x.translate(W * .6, H + 150); drawStudent(x, 200, { seated: true, color: '#14110e', tilt: .45 }); x.restore(); }
  } else {
    x.fillStyle = '#0b0d0c'; x.fillRect(0, 0, W, H);
    x.fillStyle = 'rgba(80,90,85,.18)'; for (let k = 0; k < 9; k++) x.fillRect(30 + k * 120, H * .72, 70, 8);
    x.fillStyle = 'rgba(200,210,205,.06)'; for (let k = 0; k < 4; k++) { x.beginPath(); x.moveTo(k * 270 + 20, H); x.lineTo(k * 270 + 90, 0); x.lineTo(k * 270 + 130, 0); x.lineTo(k * 270 + 60, H); x.fill(); }
  }
  // Aluminium frames
  x.fillStyle = '#8b8d86'; x.fillRect(0, 0, W, 10); x.fillRect(0, H - 10, W, 10);
  for (let k = 0; k <= 4; k++) x.fillRect(Math.min(W - 12, k * 270 - 6 + (k === 0 ? 6 : 0)), 0, 12, H);
  return tex(c, { repeat: false });
}

// Outside window bay (east wall): 2.0 × 1.4 m (600 × 420 px): two sliding panes, the town at night; void = nothing out there
export function outsideWindow(seed = 1, voidOut = false) {
  const W = 600, H = 420, c = cv(W, H), x = c.getContext('2d'), R = mulberry(seed);
  const g = x.createLinearGradient(0, 0, 0, H);
  if (voidOut) { x.fillStyle = '#000'; x.fillRect(0, 0, W, H); }
  else {
    g.addColorStop(0, '#0b1018'); g.addColorStop(.62, '#121722'); g.addColorStop(1, '#07090c'); x.fillStyle = g; x.fillRect(0, 0, W, H);
    // Apartment blocks on the horizon with a few lit windows
    for (let b = 0; b < 4; b++) {
      const bx = R() * W - 60, bw = 90 + R() * 120, top = H * (.42 + R() * .14);
      x.fillStyle = '#05070a'; x.fillRect(bx, top, bw, H - top);
      for (let k = 0; k < 14; k++) if (R() < .45) { x.fillStyle = R() < .7 ? 'rgba(255,214,150,.75)' : 'rgba(190,220,255,.6)'; x.fillRect(bx + 6 + Math.floor(R() * (bw / 14)) * 14, top + 8 + Math.floor(R() * 10) * 12, 7, 5); }
    }
    x.fillStyle = '#030405'; x.fillRect(0, H * .8, W, H * .2);   // playground wall
    const sl = x.createRadialGradient(W * .3, H * .7, 2, W * .3, H * .7, 60); sl.addColorStop(0, 'rgba(255,190,110,.55)'); sl.addColorStop(1, 'rgba(255,190,110,0)'); x.fillStyle = sl; x.fillRect(0, 0, W, H);
  }
  // Frames: outer + middle mullion where the panes overlap
  x.fillStyle = '#7f817b'; x.fillRect(0, 0, W, 14); x.fillRect(0, H - 14, W, 14); x.fillRect(0, 0, 14, H); x.fillRect(W - 14, 0, 14, H);
  x.fillRect(W / 2 - 10, 0, 20, H); x.fillStyle = '#5d5f5a'; x.fillRect(W / 2 + 6, 0, 4, H);
  x.fillRect(0, H * .5 - 4, W, 8);
  return tex(c, { repeat: false });
}

// School notice-board posters (A2-ish 0.42 × 0.6 m)
export function poster(kind, seed = 9) {
  const W = 630, H = 900, c = cv(W, H), x = c.getContext('2d'), R = mulberry(seed);
  paper(x, W, H, R, .7);
  x.textAlign = 'center'; x.fillStyle = '#20302a';
  if (kind === 'quiet') {
    x.fillStyle = '#2e5a3e'; x.fillRect(40, 60, W - 80, 150); x.fillStyle = '#f4f1e0'; x.font = F.gothic(800, 76); x.fillText('복도에서는', W / 2, 160);
    x.fillStyle = '#20302a'; x.font = F.gothic(800, 92); x.fillText('조용히', W / 2, 330); x.fillText('걸읍시다', W / 2, 450);
    x.font = F.gothic(700, 34); x.fillText('— 선도부 —', W / 2, 800);
  } else if (kind === 'motto') {
    x.font = F.myeongjo(800, 64); x.fillText('교 훈', W / 2, 150);
    x.font = F.myeongjo(800, 104); ['성 실', '근 면', '정 직'].forEach((s, i) => x.fillText(s, W / 2, 330 + i * 170));
  } else if (kind === 'study') {
    x.font = F.gothic(800, 60); x.fillText('야간 자율학습', W / 2, 130);
    x.font = F.gothic(700, 36); x.textAlign = 'left';
    [['1교시', '18:40 ~ 19:30'], ['2교시', '19:40 ~ 20:30'], ['3교시', '20:40 ~ 21:30'], ['4교시', '21:40 ~ 22:30'], ['', ''], ['※ 22:40 이후', '교내 잔류 금지']].forEach(([a, b], i) => { x.fillText(a, 80, 260 + i * 80); x.fillText(b, 300, 260 + i * 80); });
  }
  specks(x, W, H, R);
  return tex(c, { repeat: false });
}

// Green emergency exit sign (비상구), the only saturated colour: running figure + door + text
export function exitSign() {
  const W = 512, H = 200, c = cv(W, H), x = c.getContext('2d');
  x.fillStyle = '#16c25a'; x.fillRect(0, 0, W, H);
  x.fillStyle = '#f2fff4'; x.fillRect(26, 30, 90, 140);                 // door
  x.fillStyle = '#16c25a';                                               // running figure (cut into the door edge)
  x.beginPath(); x.arc(150, 58, 17, 0, 7); x.fill();
  x.lineCap = 'round'; x.strokeStyle = '#f2fff4'; x.lineWidth = 0;
  x.fillStyle = '#f2fff4'; x.beginPath(); x.arc(156, 56, 15, 0, 7); x.fill();
  x.strokeStyle = '#f2fff4'; x.lineWidth = 16;
  x.beginPath(); x.moveTo(150, 82); x.lineTo(138, 128); x.lineTo(110, 162); x.moveTo(138, 128); x.lineTo(168, 140); x.lineTo(176, 170);
  x.moveTo(146, 92); x.lineTo(120, 104); x.moveTo(146, 92); x.lineTo(180, 104); x.stroke();
  x.font = F.gothic(800, 92); x.textAlign = 'left'; x.textBaseline = 'middle'; x.fillText('비상구', 214, 104);
  return tex(c, { repeat: false });
}

// Floor number painted on the stair landing wall: 1.2 × 0.9 m
export function floorSign(label = '4층') {
  const W = 480, H = 360, c = cv(W, H), x = c.getContext('2d'), R = mulberry(4);
  x.fillStyle = '#c9cdb4'; x.fillRect(0, 0, W, H);
  grain(x, W, H, 9000, .1, R, ['#9a9e86', '#e6e9d4']);
  x.fillStyle = '#2b4a38'; x.font = F.gothic(800, 200); x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(label, W / 2 + 40, H / 2 - 10);
  x.beginPath(); x.moveTo(30, 130); x.lineTo(62, 80); x.lineTo(94, 130); x.closePath(); x.fill(); x.fillRect(52, 128, 20, 96);
  return tex(c, { repeat: false });
}

// Wall calendar in the duty room (November 1998)
export function calendar() {
  const W = 360, H = 520, c = cv(W, H), x = c.getContext('2d'), R = mulberry(8);
  x.fillStyle = '#f4f1e6'; x.fillRect(0, 0, W, H);
  x.fillStyle = '#3c6e8f'; x.fillRect(0, 0, W, 180); x.fillStyle = '#f4f1e6'; x.font = F.gothic(800, 40); x.fillText('1998', 24, 60); x.font = F.gothic(800, 96); x.fillText('11', 24, 160);
  x.fillStyle = '#222'; x.font = F.gothic(700, 24);
  for (let d = 1; d <= 30; d++) { const k = d - 1; const col = k % 7, row = Math.floor(k / 7); x.fillStyle = col === 0 ? '#b33' : '#222'; x.fillText(String(d), 18 + col * 48, 230 + row * 56); }
  x.strokeStyle = 'rgba(170,30,30,.8)'; x.lineWidth = 3; x.beginPath(); x.arc(18 + 2 * 48 + 10, 230 - 8, 22, 0, 7); x.stroke();   // 3rd circled
  grain(x, W, H, 4000, .05, R, ['#8c7c55']);
  return tex(c, { repeat: false });
}

// PA speaker box (grey with a grille)
export function speakerTex() {
  const W = 200, H = 140, c = cv(W, H), x = c.getContext('2d');
  x.fillStyle = '#b8b7ad'; x.fillRect(0, 0, W, H);
  x.fillStyle = '#4a4a46'; for (let j = 16; j < H - 14; j += 9) for (let i = 18; i < W - 16; i += 9) { x.beginPath(); x.arc(i, j, 2.4, 0, 7); x.fill(); }
  return tex(c, { repeat: false });
}
