# Retrouver la pose 3D d'un cube en fil de fer dans UNE image -- portage en
# Python de analyse/analyse_cube.js (le meme algorithme que celui qui a produit
# les 300 poses de poses_cube_animatio.js) : on cherche la rotation R et la
# position T d'un cube (cote 2, sommets en +-1) dont la projection en
# perspective (focale F pixels, image de travail S x S) recouvre au mieux les
# traits de l'image.
#
#   python3 pose_capture.py image.png [graine]
#
# Lecture des images par `sips` (macOS) : pas de PIL dans cet environnement.
import math, os, subprocess, sys, tempfile, zlib, struct
import numpy as np

S = 160          # image de travail (analyse_cube_animatio.html)
F = 165.0        # focale en pixels de l'image de travail
CAP = 20.0
M = 10

CUBE_V = np.array([[(1 if (i & 1) else -1), (1 if (i & 2) else -1), (1 if (i & 4) else -1)]
                   for i in range(8)], dtype=float)
CUBE_E = [(i, j) for i in range(8) for j in range(i + 1, 8) if (i ^ j) in (1, 2, 4)]


def lire_bmp(p):
    b = open(p, 'rb').read()
    off = int.from_bytes(b[10:14], 'little')
    w = int.from_bytes(b[18:22], 'little', signed=True)
    h = int.from_bytes(b[22:26], 'little', signed=True)
    bpp = int.from_bytes(b[28:30], 'little')
    bu = h > 0
    h = abs(h)
    n = bpp // 8
    stride = ((w * n + 3) // 4) * 4
    a = np.frombuffer(b, np.uint8, count=stride * h, offset=off).reshape(h, stride)[:, :w * n].reshape(h, w, n)
    g = a[..., :3].astype(np.float32).mean(axis=-1)
    return g[::-1] if bu else g


def charger_image_carree(chemin, S):
    """Comme drawImage(src, 0, 0, S, S) dans l'outil : l'image est ramenee a S x S.
    Une image non carree est d'abord completee en noir (pas etiree)."""
    d = tempfile.mkdtemp()
    out = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', chemin],
                         capture_output=True, text=True).stdout
    w = int(out.split('pixelWidth:')[1].split()[0])
    h = int(out.split('pixelHeight:')[1].split()[0])
    c = max(w, h)
    carre = os.path.join(d, 'carre.png')
    subprocess.run(['sips', '-p', str(c), str(c), '--padColor', '000000', chemin, '--out', carre],
                   capture_output=True, check=True)
    bmp = os.path.join(d, 'petit.bmp')
    subprocess.run(['sips', '-z', str(S), str(S), '-s', 'format', 'bmp', carre, '--out', bmp],
                   capture_output=True, check=True)
    return lire_bmp(bmp)


def distance_transform(mask):
    """Distance euclidienne de chaque pixel au trait le plus proche (exacte)."""
    S = mask.shape[0]
    INF = 1e9
    f = np.where(mask, 0.0, INF)
    idx = np.arange(S)
    D2 = ((idx[:, None] - idx[None, :]) ** 2).astype(float)
    g = (f[None, :, :] + D2[:, :, None]).min(axis=1)       # passe verticale
    h = (g[:, None, :] + D2[None, :, :]).min(axis=2)       # passe horizontale
    return np.sqrt(h)


def analyser(gris):
    S = gris.shape[0]
    mask = gris > 50
    pts = np.flatnonzero(mask.ravel())
    if pts.size < 20:
        return None
    xs = pts % S
    ys = pts // S
    step = max(1, pts.size // 300)
    sx = xs[::step] + 0.5
    sy = ys[::step] + 0.5
    return {'S': S, 'dt': distance_transform(mask), 'sx': sx.astype(float), 'sy': sy.astype(float),
            'cx': xs.mean() + 0.5, 'cy': ys.mean() + 0.5,
            'size': max(xs.max() - xs.min(), ys.max() - ys.min()) + 1}


def projeter(R, T, F, S):
    P = CUBE_V @ R.T + T            # (8, 3)
    if (P[:, 2] < 0.3).any():
        return None
    return np.stack([S / 2 + F * P[:, 0] / P[:, 2], S / 2 + F * P[:, 1] / P[:, 2]], axis=1)


def cout(im, R, T, F):
    S = im['S']
    P = projeter(R, T, F, S)
    if P is None:
        return 1e9
    dt = im['dt']
    # 1. les aretes doivent tomber sur des traits
    a = 0.0
    na = 0
    t = np.arange(M + 1) / M
    for i, j in CUBE_E:
        x = np.floor(P[i, 0] + (P[j, 0] - P[i, 0]) * t).astype(int)
        y = np.floor(P[i, 1] + (P[j, 1] - P[i, 1]) * t).astype(int)
        dehors = (x < 0) | (y < 0) | (x >= S) | (y >= S)
        xi = np.clip(x, 0, S - 1)
        yi = np.clip(y, 0, S - 1)
        v = np.minimum(CAP, dt[yi, xi])
        v[dehors] = CAP
        a += v.sum()
        na += M + 1
    # 2. tous les traits doivent etre expliques par une arete
    px, py = im['sx'], im['sy']
    best = np.full(px.shape, 1e18)
    for i, j in CUBE_E:
        ax, ay = P[i]
        bx, by = P[j] - P[i]
        L = bx * bx + by * by
        tt = ((px - ax) * bx + (py - ay) * by) / L if L > 0 else np.zeros_like(px)
        tt = np.clip(tt, 0, 1)
        dx = ax + bx * tt - px
        dy = ay + by * tt - py
        best = np.minimum(best, dx * dx + dy * dy)
    b = np.minimum(CAP, np.sqrt(best)).sum()
    return a / na + b / px.size


def rot_vec(w):
    th = float(np.linalg.norm(w))
    if th < 1e-12:
        return np.eye(3)
    x, y, z = w / th
    c, s = math.cos(th), math.sin(th)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def affiner(im, F, R0, T0, max_evals):
    """Nelder-Mead, le meme que refinePose() de l'outil (memes pas, meme arret)."""
    sc = T0[2]

    def vers_pose(x):
        return rot_vec(np.array(x[:3])) @ R0, np.array([T0[0] + x[3] * sc, T0[1] + x[4] * sc, T0[2] + x[5] * sc])

    def f(x):
        R, T = vers_pose(x)
        return cout(im, R, T, F)

    n = 6
    steps = [0.25, 0.25, 0.25, 0.05, 0.05, 0.08]
    simplex = [np.zeros(n)]
    for i in range(n):
        x = np.zeros(n)
        x[i] = steps[i]
        simplex.append(x)
    vals = [f(x) for x in simplex]
    evals = n + 1
    while evals < max_evals:
        order = sorted(range(n + 1), key=lambda i: vals[i])
        simplex = [simplex[i] for i in order]
        vals = [vals[i] for i in order]
        if vals[n] - vals[0] < 1e-4:
            break
        c = sum(simplex[:n]) / n
        pt = lambda t: c + t * (simplex[n] - c)
        xr = pt(-1); fr = f(xr); evals += 1
        if fr < vals[0]:
            xe = pt(-2); fe = f(xe); evals += 1
            if fe < fr:
                simplex[n], vals[n] = xe, fe
            else:
                simplex[n], vals[n] = xr, fr
        elif fr < vals[n - 1]:
            simplex[n], vals[n] = xr, fr
        else:
            xc = pt(-0.5) if fr < vals[n] else pt(0.5)
            fc = f(xc); evals += 1
            if fc < min(fr, vals[n]):
                simplex[n], vals[n] = xc, fc
            else:
                for i in range(1, n + 1):
                    simplex[i] = simplex[0] + 0.5 * (simplex[i] - simplex[0])
                    vals[i] = f(simplex[i]); evals += 1
    bi = int(np.argmin(vals))
    R, T = vers_pose(simplex[bi])
    return R, T, vals[bi]


def rotation_aleatoire(rnd):
    u1, u2, u3 = rnd(), rnd(), rnd()
    q = [math.sqrt(1 - u1) * math.sin(2 * math.pi * u2), math.sqrt(1 - u1) * math.cos(2 * math.pi * u2),
         math.sqrt(u1) * math.sin(2 * math.pi * u3), math.sqrt(u1) * math.cos(2 * math.pi * u3)]
    return rotation_depuis_quaternion(q)


def rotation_depuis_quaternion(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def quaternion_depuis_rotation(R):
    """(qx, qy, qz, qw) tel que rotation_depuis_quaternion redonne R."""
    m = R
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    return [x, y, z, w]


def generateur(graine):
    s = graine & 0xFFFFFFFF

    def rnd():
        nonlocal s
        s = (s * 1664525 + 1013904223) & 0xFFFFFFFF
        return s / 4294967296
    return rnd


def translation_initiale(im, F):
    tz = 3.0 * F / im['size']
    return np.array([(im['cx'] - im['S'] / 2) * tz / F, (im['cy'] - im['S'] / 2) * tz / F, tz])


def ajustement_global(im, F, rnd, n_essais):
    T = translation_initiale(im, F)
    cand = []
    for i in range(n_essais):
        R = np.eye(3) if i == 0 else rotation_aleatoire(rnd)
        cand.append((cout(im, R, T, F), i, R))
    cand.sort(key=lambda c: c[0])
    best = None
    for c, _, R in cand[:6]:
        R1, T1, c1 = affiner(im, F, R, T, 400)
        R2, T2, c2 = affiner(im, F, R1, T1, 300)
        if best is None or c2 < best[2]:
            best = (R2, T2, c2)
    return best


def ecrire_png(chemin, rgb):
    """rgb : (H, W, 3) uint8 -- PNG sans bibliotheque."""
    H, W, _ = rgb.shape
    raw = b''.join(b'\x00' + rgb[y].tobytes() for y in range(H))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    open(chemin, 'wb').write(png)


def tracer(gris, R, T, F, chemin, zoom=4):
    """L'image de travail agrandie, avec le cube ajuste trace en couleur par-dessus."""
    S = gris.shape[0]
    H = S * zoom
    base = np.repeat(np.repeat(gris, zoom, 0), zoom, 1)
    rgb = np.stack([base, base, base], axis=-1).astype(np.uint8)
    P = projeter(R, T, F, S) * zoom
    for i, j in CUBE_E:
        n = int(max(abs(P[j] - P[i])) * 2) + 2
        for t in np.linspace(0, 1, n):
            x = int(P[i, 0] + (P[j, 0] - P[i, 0]) * t)
            y = int(P[i, 1] + (P[j, 1] - P[i, 1]) * t)
            if 0 <= x < H and 0 <= y < H:
                rgb[y, x] = (255, 40, 40)
                if x + 1 < H:
                    rgb[y, x + 1] = (255, 40, 40)
    ecrire_png(chemin, rgb)


def pose_en_ligne(R, T, F, S):
    """La ligne [cx, cy, s, qx, qy, qz, qw] au format de poses_cube_animatio.js :
    centre et demi-cote apparent en demi-largeurs d'image."""
    half = S / 2
    cx = F * T[0] / T[2] / half
    cy = F * T[1] / T[2] / half
    s = F / T[2] / half
    return [cx, cy, s] + quaternion_depuis_rotation(R)


if __name__ == '__main__':
    chemin = sys.argv[1]
    graine = int(sys.argv[2]) if len(sys.argv) > 2 else 12345
    gris = charger_image_carree(chemin, S)
    im = analyser(gris)
    assert im is not None, 'pas assez de traits dans l image'
    R, T, c = ajustement_global(im, F, generateur(graine), 400)
    q = quaternion_depuis_rotation(R)
    assert np.allclose(rotation_depuis_quaternion(q), R, atol=1e-9)
    ligne = pose_en_ligne(R, T, F, S)
    print('cout (px) : %.3f' % c)
    print('T : %s' % np.round(T, 4).tolist())
    print('R :')
    print(np.round(R, 4))
    print('ligne poses : [%s]' % ', '.join('%.4f' % v for v in ligne))
    sortie = os.path.splitext(chemin)[0] + '_ajuste.png'
    if len(sys.argv) > 3:
        sortie = sys.argv[3]
    tracer(gris, R, T, F, sortie)
    print('trace : %s' % sortie)
