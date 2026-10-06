# Référence numpy (vérité terrain) — portage exact de volumetric3D.js
import re, math
import numpy as np

def lire_poses(texte):
    """Lit poses_cube_animatio.js → array (n, 8) : cx, cy, s, qx, qy, qz, qw, interpolee"""
    lignes = re.findall(r'^\s*\[([^\]]+)\]', texte, re.M)
    return np.array([[float(v) for v in l.split(',')] for l in lignes])

def positions_led(N=160, J=8, S=10, R=180, pas=1.0, pas_rangees=1.0, ecart=10.0):
    """Positions (cm) de toutes les LED pour un tour : array (R, S, J, N, 3).
    Repère du volume : x à droite, y vers le BAS, z vers le spectateur, origine au centre."""
    r = np.arange(R)[:, None, None, None]
    s = np.arange(S)[None, :, None, None]
    j = np.arange(J)[None, None, :, None]
    k = np.arange(N)[None, None, None, :]
    ang = s * math.pi / S + 2 * math.pi * r / R
    d = (k - (N - 1) / 2) * pas
    o = (j - (J - 1) / 2) * pas_rangees
    x = d * np.cos(ang) - o * np.sin(ang)
    y = d * np.sin(ang) + o * np.cos(ang)
    z = ((S - 1) / 2 - s) * ecart + 0 * x
    return np.stack(np.broadcast_arrays(x, y, z), axis=-1)

def echelle_animation(poses, w, N=160, S=10, pas=1.0, ecart=10.0):
    zmax = (S - 1) / 2 * ecart
    demi_longueur = (N - 1) / 2 * pas
    reach = poses[:, 2] * math.sqrt(3)
    L = np.minimum((zmax - w) / reach, (demi_longueur - w) / (np.hypot(poses[:, 0], poses[:, 1]) + reach))
    return max(0.0, float(L.min()))

def rotation_volume(x, y, z, w_):
    """Quaternion (repere de la camera) -> matrice de rotation dans le repere du volume :
    meme formule que volumetric3D.js, puis retournement de l'axe z."""
    Rm = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w_), 2 * (x * z + y * w_)],
                   [2 * (x * y + z * w_), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w_)],
                   [2 * (x * z - y * w_), 2 * (y * z + x * w_), 1 - 2 * (x * x + y * y)]])
    Rm[0, 2] *= -1; Rm[1, 2] *= -1; Rm[2, 0] *= -1; Rm[2, 1] *= -1   # retournement de l'axe z
    return Rm

def pose(poses, i, L):
    cx, cy, s, x, y, z, w_, interp = poses[i]
    Rm = rotation_volume(x, y, z, w_)
    return np.array([L * cx, L * cy, 0.0]), L * s, Rm, bool(interp)

SOMMETS_CUBE = np.array([[(1 if (i & 1) else -1), (1 if (i & 2) else -1), (1 if (i & 4) else -1)]
                         for i in range(8)], dtype=float)

def taille_max_statique(Rm, w, N=160, S=10, pas=1.0, ecart=10.0):
    """Le plus grand demi-cote h tel que les 8 sommets du cube tourne par Rm restent entre les
    panneaux 0 et 9 (|z| <= zmax) et que les aretes, epaisseur w comprise, restent dans le rayon
    des lames (hypot(x, y) <= demi_longueur - w). Chaque contrainte est lineaire en h.
    Cube non tourne : 45 cm, les faces avant et arriere sur les panneaux 0 et 9 (comme Cubefixe)."""
    zmax = (S - 1) / 2 * ecart
    rayon = (N - 1) / 2 * pas - w
    p = SOMMETS_CUBE @ Rm.T
    pz = np.abs(p[:, 2])
    pr = np.hypot(p[:, 0], p[:, 1])
    with np.errstate(divide='ignore'):
        hz = np.where(pz > 1e-12, zmax / np.where(pz > 1e-12, pz, 1.0), np.inf)
        hr = np.where(pr > 1e-12, rayon / np.where(pr > 1e-12, pr, 1.0), np.inf)
    return float(min(hz.min(), hr.min()))

def pose_statique(q, w, taille=1.0, N=160, S=10, pas=1.0, ecart=10.0):
    """Le CUBE STATIQUE : une seule pose, centree, de rotation q (quaternion du repere camera,
    comme une ligne de poses), agrandie a `taille` fois le plus grand demi-cote qui tient.
    Portage de la branche Cubestatique de CB_POSE (INSTALLER_ANIMATION_CUBE.py)."""
    Rm = rotation_volume(*q)
    h = taille_max_statique(Rm, w, N, S, pas, ecart) * min(1.0, max(0.05, float(taille)))
    return np.zeros(3), h, Rm

def distance_aretes(q):
    """Distance d'un point (repère du cube, demi-côté 1) aux 12 arêtes. q : (..., 3)"""
    a = np.abs(q) - 1.0
    e = np.maximum(a, 0.0)
    return np.sqrt(np.minimum(np.minimum(e[..., 0]**2 + a[..., 1]**2 + a[..., 2]**2,
                                         a[..., 0]**2 + e[..., 1]**2 + a[..., 2]**2),
                              a[..., 0]**2 + a[..., 1]**2 + e[..., 2]**2))

def allumees_animation(P, centre, h, Rm, w):
    q = ((P - centre) @ Rm) / h          # (p − centre) · R = transposée(R) × (p − centre)
    return distance_aretes(q) * h <= w

def allumees_cube_fixe(P, w, N=160, S=10, pas=1.0, ecart=10.0):
    a = min((N - 1) / 2 * pas / math.sqrt(2) * 0.95, (S - 1) / 2 * ecart)
    return distance_aretes(P / a) * a <= w

def octets_bin(masque, couleur=(255, 0, 0)):
    """masque (R, S, J, N) → octets dans l'ordre rafraîchissement → panneau → rangée → colonne → R, G, B"""
    out = np.zeros(masque.shape + (3,), np.uint8)
    out[masque] = couleur
    return out.tobytes()

def octets_1bit(masque):
    """1 bit par LED, même ordre que octets_bin ; 8 LED par octet, la première LED dans le bit de poids fort"""
    return np.packbits(masque.ravel()).tobytes()

def atlas_depuis_masque(masque):
    """(R, S, J, N) → image (J*R lignes, S*N colonnes) : ligne r*J + j, colonne s*N + k"""
    R, S, J, N = masque.shape
    return masque.transpose(0, 2, 1, 3).reshape(R * J, S * N)

def masque_depuis_atlas(img, R, S, J, N, seuil=0.5):
    """img = op('atlas').numpyArray() : (J*R, S*N, 4), valeurs 0..1.
    On suppose que la ligne 0 du tableau est la rangée 0 du rafraîchissement 0 :
    à vérifier contre la référence ; si c'est inversé, utiliser img[::-1]."""
    allumee = img[..., :3].max(axis=-1) > seuil
    return allumee.reshape(R, J, S, N).transpose(0, 2, 1, 3)
