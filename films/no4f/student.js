// "The student": an organic silhouette, almost a high-school girl in a winter uniform, wrong by 15–40 %:
// head a little small, neck far too long and bent, shoulders narrow and high, arms hanging past the knees, hair straight down over the face.
// Canvas2D, units in metres × S; origin = the ground between the feet (canvas y grows downward, so world y is negated)
// o = { seated: bool, tilt: head/neck tilt (rad), lean: torso lean (rad), color }
const lerp = (a, b, t) => a + (b - a) * t;
const P = (x, y) => ({ x, y });
const mixP = (a, b, t) => P(lerp(a.x, b.x, t), lerp(a.y, b.y, t));

function limb(x, pts, widths, S) {
  x.lineCap = 'round'; x.lineJoin = 'round';
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1], n = 10;
    for (let k = 0; k < n; k++) {
      const t0 = k / n, t1 = (k + 1) / n, p0 = mixP(a, b, t0), p1 = mixP(a, b, t1);
      x.lineWidth = lerp(widths[i], widths[i + 1], (t0 + t1) / 2) * S;
      x.beginPath(); x.moveTo(p0.x * S, -p0.y * S); x.lineTo(p1.x * S, -p1.y * S); x.stroke();
    }
  }
}

export function drawStudent(x, S, o = {}) {
  const tilt = o.tilt ?? .35, lean = o.lean ?? 0, seated = !!o.seated;
  x.save(); x.fillStyle = x.strokeStyle = o.color || '#000';
  const T = (px, py) => [px * S, -py * S];
  const hip = seated ? .62 : 1.0;           // seated: the desk hides everything under the hips
  if (!seated) {
    // Legs: thin, straight, a little too long; socks and flat school shoes
    for (const sd of [-1, 1]) {
      limb(x, [P(sd * .07, .74), P(sd * .068, .4), P(sd * .066, .07)], [.085, .065, .055], S);
      x.beginPath(); x.ellipse(sd * .072 * S, -.03 * S, .05 * S, .032 * S, 0, 0, 7); x.fill();
    }
    // Pleated skirt (knee length), a slight flare
    x.beginPath(); x.moveTo(...T(-.15, hip + .02)); x.lineTo(...T(-.205, .62)); x.quadraticCurveTo(...T(0, .6), ...T(.205, .62)); x.lineTo(...T(.15, hip + .02)); x.closePath(); x.fill();
  }
  // Torso (blazer): narrow, long; shoulders high and sloping
  x.save(); x.translate(0, -hip * S); x.rotate(lean);
  const B = (px, py) => [px * S, -py * S];
  const sh = .82;   // shoulder height above the hip (≈ 25 % too long)
  x.beginPath();
  x.moveTo(...B(-.15, 0));
  x.bezierCurveTo(...B(-.155, .3), ...B(-.175, .55), ...B(-.17, sh - .06));
  x.bezierCurveTo(...B(-.17, sh), ...B(-.14, sh + .04), ...B(-.03, sh + .06));
  x.lineTo(...B(.03, sh + .06));
  x.bezierCurveTo(...B(.14, sh + .04), ...B(.17, sh), ...B(.17, sh - .06));
  x.bezierCurveTo(...B(.175, .55), ...B(.155, .3), ...B(.15, 0));
  x.closePath(); x.fill();
  // Neck (far too long, bending to one side), head small, hair hanging straight down from the crown
  const nb = P(0, sh + .03), nm = P(Math.sin(tilt) * .07, sh + .2), nt = P(Math.sin(tilt) * .19, sh + .34);
  limb(x, [nb, nm, nt], [.07, .06, .055], S);
  const hc = P(nt.x + Math.sin(tilt) * .05, nt.y + .07);
  x.save(); x.translate(hc.x * S, -hc.y * S); x.rotate(tilt);
  x.beginPath(); x.ellipse(0, 0, .068 * S, .088 * S, 0, 0, 7); x.fill();
  x.restore();
  // Hair: a curtain from the crown straight down (gravity, not head-aligned), slightly uneven ends
  x.beginPath();
  const top = P(hc.x, hc.y + .09), L = .62;
  x.moveTo(...B(top.x - .06, top.y));
  x.quadraticCurveTo(...B(hc.x - .11, hc.y), ...B(hc.x - .1, hc.y - L * .6));
  for (let k = 0; k <= 8; k++) { const u = k / 8; x.lineTo(...B(hc.x - .1 + u * .2, hc.y - L + Math.sin(k * 2.3) * .025 - (k % 2) * .02)); }
  x.quadraticCurveTo(...B(hc.x + .11, hc.y), ...B(top.x + .06, top.y));
  x.closePath(); x.fill();
  // Arms: hanging, far too long (fingertips below the knees when standing)
  for (const sd of [-1, 1]) {
    const s0 = P(sd * .165, sh - .03), e = P(sd * .2, sh - .4), w = P(sd * .205, sh - .88), f = P(sd * .2, sh - 1.06);
    limb(x, [s0, e, w], [.075, .055, .042], S);
    limb(x, [w, mixP(w, f, .5), f], [.04, .03, .016], S);
  }
  x.restore();
  x.restore();
}
