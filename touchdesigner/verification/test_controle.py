# Test des valeurs de contrôle de la partie 5 du prompt (160 × 8 LED, R = 180, w = 4)
import numpy as np
import reference as ref

REPO = "/Users/oslive/Documents/animation-cube-a-faire-dans-TD"
N, J, S, R = 160, 8, 10, 180
w = 4.0

ok = True
def check(nom, obtenu, attendu, tol=0.0):
    global ok
    if isinstance(attendu, (tuple, list, np.ndarray)):
        good = np.allclose(obtenu, attendu, atol=tol)
    else:
        good = abs(obtenu - attendu) <= tol if tol else obtenu == attendu
    print(f"{'OK ' if good else 'ÉCHEC'}  {nom} : {obtenu}  (attendu {attendu})")
    if not good: ok = False

# --- Poses ---
poses = ref.lire_poses(open(f"{REPO}/poses_cube_animatio.js").read())
check("nombre de poses", poses.shape, (300, 8))

# --- Positions ---
P = ref.positions_led(N, J, S, R)
check("LED (r=0, s=0, j=0, k=0)", P[0, 0, 0, 0], (-79.5, -3.5, 45.0), 1e-9)
check("LED (r=45, s=3, j=7, k=159)", P[45, 3, 7, 159], (-66.374, 43.897, 15.0), 5e-4)
check("LED (r=90, s=9, j=2, k=40)", P[90, 9, 2, 40], (-38.030, 10.780, -45.0), 5e-4)

# --- Échelle et pose 0 ---
L = ref.echelle_animation(poses, w, N, S)
check("L", L, 61.230, 5e-4)
centre, h, Rm, interp = ref.pose(poses, 0, L)
check("centre image 0", centre, (0.0, 0.0, 0.0), 1e-2)
check("h image 0", h, 16.905, 5e-4)

# --- LED allumées sur un tour ---
m_fixe = ref.allumees_cube_fixe(P, w, N, S)
check("cube fixe", int(m_fixe.sum()), 62848)

for i, attendu in [(0, 53888), (1, 54202), (100, 48062), (150, 49978), (299, 68814)]:
    centre, h, Rm, interp = ref.pose(poses, i, L)
    m = ref.allumees_animation(P, centre, h, Rm, w)
    label = f"image {i}" + (" (interpolée)" if interp else "")
    check(label, int(m.sum()), attendu)

# interpolées : image 1 oui, image 0 non
check("image 0 interpolée", ref.pose(poses, 0, L)[3], False)
check("image 1 interpolée", ref.pose(poses, 1, L)[3], True)

# --- Export .bin ---
centre, h, Rm, interp = ref.pose(poses, 0, L)
m0 = ref.allumees_animation(P, centre, h, Rm, w)
octets = ref.octets_bin(m0)
check("taille .bin", len(octets), 6912000)
check("octet de départ LED (r=45, s=3, j=7, k=159)", 3 * (((45 * S + 3) * J + 7) * N + 159), 1743357)

# --- 1 bit ---
bits = ref.octets_1bit(m0)
check("taille 1 bit", len(bits), 288000)

# --- Aller-retour atlas ---
atlas = ref.atlas_depuis_masque(m0)
check("forme atlas", atlas.shape, (J * R, S * N))
img = np.zeros((J * R, S * N, 4), np.float32)
img[..., 0] = atlas
m_retour = ref.masque_depuis_atlas(img, R, S, J, N)
check("aller-retour atlas", int((m_retour != m0).sum()), 0)

print()
print("TOUT EST BON" if ok else "DES ÉCARTS — à corriger avant de construire")
