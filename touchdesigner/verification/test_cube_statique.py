# Test du CUBE STATIQUE : la pose retrouvee dans la capture, sa taille maximale
# dans le volume, et ses LED allumees sur un demi-tour (160 x 8 LED, R = 180,
# w = 4). A lancer hors TouchDesigner : python3 test_cube_statique.py
import os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reference as ref

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
N, J, S, R = 160, 8, 10, 180
w = 4.0

# La pose de la capture (analyse/capture_cube_statique.png), retrouvee par
# analyse/pose_capture.py -- le meme algorithme que les 300 poses. C'est la
# constante POSE_STATIQUE de touchdesigner/INSTALLER_ANIMATION_CUBE.py.
Q_CAPTURE = (0.0303, -0.5728, 0.6839, 0.4509)

ok = True
def check(nom, obtenu, attendu, tol=0.0):
    global ok
    if isinstance(attendu, (tuple, list, np.ndarray)):
        good = np.allclose(obtenu, attendu, atol=tol)
    else:
        good = abs(obtenu - attendu) <= tol if tol else obtenu == attendu
    print(f"{'OK ' if good else 'ÉCHEC'}  {nom} : {obtenu}  (attendu {attendu})")
    if not good: ok = False

# --- 1. La pose statique : centree, rotation de la capture, retournement de z comme les 300 poses
centre, h, Rm = ref.pose_statique(Q_CAPTURE, w, 1.0, N, S)
check("centre", centre, (0.0, 0.0, 0.0), 1e-12)
check("R orthonormale", float(np.abs(Rm @ Rm.T - np.eye(3)).max()), 0.0, 2e-4)
check("det R = +1", float(np.linalg.det(Rm)), 1.0, 2e-4)
# meme retournement de z que ref.pose : on compare a une ligne de poses construite a la main
ligne = np.array([[0.0, 0.0, 1.0, *Q_CAPTURE, 0]])
_, _, R_anim, _ = ref.pose(ligne, 0, 1.0)
check("meme rotation que la chaine des 300 poses", Rm, R_anim, 1e-12)

# --- 2. La taille maximale qui tient dans le volume
check("cube non tourne : h max = 45 (faces sur les panneaux 0 et 9)",
      ref.taille_max_statique(np.eye(3), w, N, S), 45.0, 1e-9)
sommets = h * (ref.SOMMETS_CUBE @ Rm.T)                 # (8, 3) en cm
zmax, rayon = 4.5 * 10.0, (N - 1) / 2 - w
check("sommets entre les panneaux 0 et 9", float(np.abs(sommets[:, 2]).max()) <= zmax + 1e-9, True)
check("aretes (epaisseur comprise) dans le rayon des lames",
      float(np.hypot(sommets[:, 0], sommets[:, 1]).max()) <= rayon + 1e-9, True)
serre = (abs(np.abs(sommets[:, 2]).max() - zmax) < 1e-6
         or abs(np.hypot(sommets[:, 0], sommets[:, 1]).max() - rayon) < 1e-6)
check("la taille est bien la plus grande possible (une contrainte touchee)", serre, True)
check("demi-cote de la capture (cm)", h, 27.172, 0.001)
_, h_moitie, _ = ref.pose_statique(Q_CAPTURE, w, 0.5, N, S)
check("Taille 0.5 = moitie", h_moitie, h / 2, 1e-12)

# --- 3. LED allumees sur un demi-tour (controle a comparer avec TouchDesigner)
P = ref.positions_led(N, J, S, R)[: R // 2]
m = ref.allumees_animation(P, centre, h, Rm, w)
par_panneau = [int(m[:, s].sum()) for s in range(S)]
print("      LED allumees par panneau :", par_panneau)
check("LED allumees sur le demi-tour", int(m.sum()), 27080)

# --- 4. L'analyse de la capture redonne la constante (meme algorithme que les 300 poses)
out = subprocess.run([sys.executable, os.path.join(REPO, 'analyse', 'pose_capture.py'),
                      os.path.join(REPO, 'analyse', 'capture_cube_statique.png'), '12345',
                      '/tmp/capture_cube_statique_ajuste.png'],
                     capture_output=True, text=True)
cout = float(out.stdout.split('cout (px) :')[1].split()[0])
ligne_txt = out.stdout.split('ligne poses : [')[1].split(']')[0]
q_fit = [float(v) for v in ligne_txt.split(',')][3:7]
check("ecart cube ajuste / traits de la capture (px) < 3", cout < 3.0, True)
check("quaternion retrouve", q_fit, Q_CAPTURE, 2e-3)

print()
print("TOUT EST BON" if ok else "DES ÉCARTS — à corriger avant de construire")
