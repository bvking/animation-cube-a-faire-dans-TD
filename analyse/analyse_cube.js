// ---------- Analyse des images : retrouver la pose 3D d'un cube en fil de fer ----------
// Principe : on cherche la rotation R et la position T d'un cube (côté 2, sommets en ±1)
// dont la projection en perspective (focale F, en pixels de l'image de travail)
// recouvre au mieux les traits de l'image.

const CUBE_V = [];
for (let i = 0; i < 8; i++) CUBE_V.push([(i & 1) ? 1 : -1, (i & 2) ? 1 : -1, (i & 4) ? 1 : -1]);
const CUBE_E = [];
for (let i = 0; i < 8; i++) for (let j = i + 1; j < 8; j++) { const d = i ^ j; if (d === 1 || d === 2 || d === 4) CUBE_E.push([i, j]); }

// Les 24 rotations qui laissent le cube identique (matrices de permutation signées, déterminant +1)
const CUBE_SYM = (() => {
  const perms = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]];
  const out = [];
  for (const p of perms) for (let s = 0; s < 8; s++) {
    const m = new Array(9).fill(0);
    for (let r = 0; r < 3; r++) m[r * 3 + p[r]] = (s >> r) & 1 ? -1 : 1;
    const det = m[0] * (m[4] * m[8] - m[5] * m[7]) - m[1] * (m[3] * m[8] - m[5] * m[6]) + m[2] * (m[3] * m[7] - m[4] * m[6]);
    if (det > 0) out.push(m);
  }
  return out;
})();

function matMul(a, b) {
  const o = new Array(9);
  for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++)
    o[r * 3 + c] = a[r * 3] * b[c] + a[r * 3 + 1] * b[3 + c] + a[r * 3 + 2] * b[6 + c];
  return o;
}
function matT(a) { return [a[0], a[3], a[6], a[1], a[4], a[7], a[2], a[5], a[8]]; }

// Rotation d'angle |w| autour de l'axe w (formule de Rodrigues)
function rotVec(wx, wy, wz) {
  const th = Math.hypot(wx, wy, wz);
  if (th < 1e-12) return [1, 0, 0, 0, 1, 0, 0, 0, 1];
  const x = wx / th, y = wy / th, z = wz / th, c = Math.cos(th), s = Math.sin(th), C = 1 - c;
  return [c + x * x * C, x * y * C - z * s, x * z * C + y * s,
          y * x * C + z * s, c + y * y * C, y * z * C - x * s,
          z * x * C - y * s, z * y * C + x * s, c + z * z * C];
}

// Angle (radians) entre deux rotations
function rotAngle(a, b) {
  const m = matMul(matT(a), b);
  return Math.acos(Math.max(-1, Math.min(1, (m[0] + m[4] + m[8] - 1) / 2)));
}

// Parmi les 24 rotations équivalentes de R (même cube), celle qui est la plus proche de ref
function closestEquivalent(R, ref) {
  let best = R, bestA = Infinity;
  for (const S of CUBE_SYM) {
    const Rs = matMul(R, S);
    const a = rotAngle(ref, Rs);
    if (a < bestA) { bestA = a; best = Rs; }
  }
  return best;
}

// Rotation aléatoire uniforme (quaternion)
function randomRotation(rnd) {
  const u1 = rnd(), u2 = rnd(), u3 = rnd();
  const q = [Math.sqrt(1 - u1) * Math.sin(2 * Math.PI * u2), Math.sqrt(1 - u1) * Math.cos(2 * Math.PI * u2),
             Math.sqrt(u1) * Math.sin(2 * Math.PI * u3), Math.sqrt(u1) * Math.cos(2 * Math.PI * u3)];
  const [x, y, z, w] = q;
  return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
          2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
          2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)];
}

// Petit générateur pseudo-aléatoire reproductible
function makeRandom(seed) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

// Transformée de distance exacte (Felzenszwalb) : distance de chaque pixel au trait le plus proche
function edt1d(f, n, d, v, z) {
  let k = 0; v[0] = 0; z[0] = -Infinity; z[1] = Infinity;
  for (let q = 1; q < n; q++) {
    let s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]);
    while (s <= z[k]) { k--; s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]); }
    k++; v[k] = q; z[k] = s; z[k + 1] = Infinity;
  }
  k = 0;
  for (let q = 0; q < n; q++) { while (z[k + 1] < q) k++; d[q] = (q - v[k]) * (q - v[k]) + f[v[k]]; }
}
function distanceTransform(mask, W, H) {
  const g = new Float64Array(W * H);
  for (let i = 0; i < W * H; i++) g[i] = mask[i] ? 0 : 1e10;
  const n = Math.max(W, H);
  const f = new Float64Array(n), d = new Float64Array(n), v = new Int32Array(n), z = new Float64Array(n + 1);
  for (let x = 0; x < W; x++) {
    for (let y = 0; y < H; y++) f[y] = g[y * W + x];
    edt1d(f, H, d, v, z);
    for (let y = 0; y < H; y++) g[y * W + x] = d[y];
  }
  const out = new Float32Array(W * H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) f[x] = g[y * W + x];
    edt1d(f, W, d, v, z);
    for (let x = 0; x < W; x++) out[y * W + x] = Math.sqrt(d[x]);
  }
  return out;
}

// Prépare une image : traits (pixels clairs), carte de distances, échantillon de points des traits
function analyzeCubeImage(src, S) {
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const g = c.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#000';
  g.fillRect(0, 0, S, S);
  g.drawImage(src, 0, 0, S, S);
  const px = g.getImageData(0, 0, S, S).data;
  const mask = new Uint8Array(S * S);
  const pts = [];
  for (let i = 0; i < S * S; i++) {
    if ((px[4 * i] + px[4 * i + 1] + px[4 * i + 2]) / 3 > 50) { mask[i] = 1; pts.push(i); }
  }
  if (pts.length < 20) return null;
  let mx = 0, my = 0, minx = S, maxx = 0, miny = S, maxy = 0;
  for (const i of pts) {
    const x = i % S, y = (i / S) | 0;
    mx += x; my += y;
    if (x < minx) minx = x; if (x > maxx) maxx = x; if (y < miny) miny = y; if (y > maxy) maxy = y;
  }
  const step = Math.max(1, Math.floor(pts.length / 300));
  const sx = [], sy = [];
  for (let k = 0; k < pts.length; k += step) { sx.push(pts[k] % S + 0.5); sy.push(((pts[k] / S) | 0) + 0.5); }
  return {
    S: S, dt: distanceTransform(mask, S, S), sx: Float32Array.from(sx), sy: Float32Array.from(sy),
    cx: mx / pts.length + 0.5, cy: my / pts.length + 0.5, size: Math.max(maxx - minx, maxy - miny) + 1
  };
}

// Écart entre le cube projeté et les traits de l'image (en pixels) : plus c'est petit, mieux c'est
function poseCost(im, R, T, F) {
  const S = im.S, half = S / 2, P = new Float64Array(16);
  for (let i = 0; i < 8; i++) {
    const v = CUBE_V[i];
    const X = R[0] * v[0] + R[1] * v[1] + R[2] * v[2] + T[0];
    const Y = R[3] * v[0] + R[4] * v[1] + R[5] * v[2] + T[1];
    const Z = R[6] * v[0] + R[7] * v[1] + R[8] * v[2] + T[2];
    if (Z < 0.3) return 1e9;
    P[2 * i] = half + F * X / Z;
    P[2 * i + 1] = half + F * Y / Z;
  }
  // 1. les arêtes du cube doivent tomber sur des traits
  let a = 0, na = 0;
  const M = 10, CAP = 20;
  for (const [i, j] of CUBE_E) {
    for (let m = 0; m <= M; m++) {
      const t = m / M;
      const x = Math.floor(P[2 * i] + (P[2 * j] - P[2 * i]) * t);
      const y = Math.floor(P[2 * i + 1] + (P[2 * j + 1] - P[2 * i + 1]) * t);
      a += (x < 0 || y < 0 || x >= S || y >= S) ? CAP : Math.min(CAP, im.dt[y * S + x]);
      na++;
    }
  }
  // 2. tous les traits doivent être expliqués par une arête
  let b = 0;
  const n = im.sx.length;
  for (let k = 0; k < n; k++) {
    const px = im.sx[k], py = im.sy[k];
    let best = 1e18;
    for (const [i, j] of CUBE_E) {
      const ax = P[2 * i], ay = P[2 * i + 1], bx = P[2 * j] - ax, by = P[2 * j + 1] - ay;
      const L = bx * bx + by * by;
      let t = L > 0 ? ((px - ax) * bx + (py - ay) * by) / L : 0;
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      const dx = ax + bx * t - px, dy = ay + by * t - py;
      const d2 = dx * dx + dy * dy;
      if (d2 < best) best = d2;
    }
    b += Math.min(CAP, Math.sqrt(best));
  }
  return a / na + b / n;
}

// Optimisation locale (Nelder-Mead) autour d'une pose de départ
function refinePose(im, F, R0, T0, maxEvals) {
  const sc = T0[2];
  const toPose = x => ({ R: matMul(rotVec(x[0], x[1], x[2]), R0), T: [T0[0] + x[3] * sc, T0[1] + x[4] * sc, T0[2] + x[5] * sc] });
  const f = x => { const p = toPose(x); return poseCost(im, p.R, p.T, F); };
  const n = 6, steps = [0.25, 0.25, 0.25, 0.05, 0.05, 0.08];
  let simplex = [new Array(n).fill(0)];
  for (let i = 0; i < n; i++) { const x = new Array(n).fill(0); x[i] = steps[i]; simplex.push(x); }
  let vals = simplex.map(f);
  let evals = n + 1;
  while (evals < maxEvals) {
    const order = vals.map((v, i) => i).sort((p, q) => vals[p] - vals[q]);
    simplex = order.map(i => simplex[i]); vals = order.map(i => vals[i]);
    if (vals[n] - vals[0] < 1e-4) break;
    const c = new Array(n).fill(0);
    for (let i = 0; i < n; i++) for (let k = 0; k < n; k++) c[k] += simplex[i][k] / n;
    const pt = (t) => c.map((ck, k) => ck + t * (simplex[n][k] - ck));
    const xr = pt(-1), fr = f(xr); evals++;
    if (fr < vals[0]) {
      const xe = pt(-2), fe = f(xe); evals++;
      if (fe < fr) { simplex[n] = xe; vals[n] = fe; } else { simplex[n] = xr; vals[n] = fr; }
    } else if (fr < vals[n - 1]) {
      simplex[n] = xr; vals[n] = fr;
    } else {
      const xc = fr < vals[n] ? pt(-0.5) : pt(0.5), fc = f(xc); evals++;
      if (fc < Math.min(fr, vals[n])) { simplex[n] = xc; vals[n] = fc; }
      else {
        for (let i = 1; i <= n; i++) { simplex[i] = simplex[i].map((v, k) => simplex[0][k] + 0.5 * (v - simplex[0][k])); vals[i] = f(simplex[i]); evals++; }
      }
    }
  }
  let bi = 0;
  for (let i = 1; i <= n; i++) if (vals[i] < vals[bi]) bi = i;
  const p = toPose(simplex[bi]);
  return { R: p.R, T: p.T, cost: vals[bi] };
}

// Position de départ déduite de la tache des traits (centre et taille)
function guessTranslation(im, F) {
  const tz = 3.0 * F / im.size;
  return [(im.cx - im.S / 2) * tz / F, (im.cy - im.S / 2) * tz / F, tz];
}

// Recherche globale (première image, ou si le suivi échoue)
function globalFit(im, F, rnd, nSamples) {
  const T = guessTranslation(im, F);
  const cand = [];
  for (let i = 0; i < nSamples; i++) {
    const R = i === 0 ? [1, 0, 0, 0, 1, 0, 0, 0, 1] : randomRotation(rnd);
    cand.push({ R: R, cost: poseCost(im, R, T, F) });
  }
  cand.sort((p, q) => p.cost - q.cost);
  let best = null;
  for (const c of cand.slice(0, 6)) {
    let r = refinePose(im, F, c.R, T, 400);
    r = refinePose(im, F, r.R, r.T, 300);
    if (!best || r.cost < best.cost) best = r;
  }
  return best;
}

// Suivi : on part de la pose de l'image précédente (et de quelques variantes)
const FLIP = [1, 0, 0, 0, 1, 0, 0, 0, -1];
function trackFit(im, F, prev, gap, rnd) {
  const T = [prev.T[0], prev.T[1], prev.T[2]];
  const g = guessTranslation(im, F);
  T[0] = (im.cx - im.S / 2) * T[2] / F;
  T[1] = (im.cy - im.S / 2) * T[2] / F;
  const starts = [prev.R, matMul(FLIP, matMul(prev.R, FLIP))];
  const amp = Math.min(1.2, 0.25 * gap + 0.2);
  for (let i = 0; i < 6; i++) {
    starts.push(matMul(rotVec((rnd() - 0.5) * 2 * amp, (rnd() - 0.5) * 2 * amp, (rnd() - 0.5) * 2 * amp), prev.R));
  }
  let best = null;
  for (const R of starts) {
    for (const T0 of [T, [g[0], g[1], g[2]]]) {
      const r = refinePose(im, F, R, T0, 300);
      if (!best || r.cost < best.cost) best = r;
    }
  }
  best = refinePose(im, F, best.R, best.T, 300);
  return best;
}
