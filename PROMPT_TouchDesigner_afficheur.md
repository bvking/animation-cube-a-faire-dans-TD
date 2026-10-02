# Prompt — Afficheur volumétrique (10 panneaux de 160 × 8 LED) dans TouchDesigner

Tu es un développeur TouchDesigner expérimenté (Python, TOP, CHOP, SOP, DAT, GLSL, instancing). Tu es relié à TouchDesigner par MCP : tu peux créer des opérateurs, régler leurs paramètres et exécuter du Python dans le projet ouvert. Je travaille sur Mac (Apple Silicon). Réponds-moi en français.

## Objectif

Recréer dans TouchDesigner la simulation de mon afficheur volumétrique à persistance rétinienne (aujourd'hui en p5.js), puis préparer la sortie vers le vrai dispositif :

1. calculer, pour chaque position angulaire, la couleur de chaque LED des 10 panneaux ;
2. afficher en 3D les panneaux qui tournent et l'image 3D que l'œil perçoit ;
3. exporter et envoyer ces données au matériel.

Version de référence (p5.js, avec 180 LED par rangée) : https://github.com/bvking/animation-cube-a-faire-dans-TD
- `volumetric3D.js` : le programme ;
- `poses_cube_animatio.js` : l'animation (300 poses de cubes) ;
- `EXPLICATION.txt` : l'explication complète ;
- `cube_animatio/` : les images d'origine.

**La nouvelle version a 160 LED par rangée** ; tout le reste est identique. Ce document fait foi : ses formules et ses valeurs de contrôle sont déjà adaptées à 160 LED.

## 0. Avant de construire

- Liste les outils MCP dont tu disposes et vérifie la version de TouchDesigner (`app.version`, `app.build`).
- Demande-moi le chemin du dépôt sur mon Mac, pour lire `poses_cube_animatio.js`. Si TouchDesigner a accès à Internet, tu peux aussi le lire ici : https://raw.githubusercontent.com/bvking/animation-cube-a-faire-dans-TD/main/poses_cube_animatio.js
- Demande-moi le format de données qu'attend mon code ESP32 (voir la partie 6). Tu peux construire les parties 1 à 5 en attendant ma réponse.
- Présente-moi ton plan (réseau d'opérateurs) en quelques lignes avant de commencer.

## 1. Le dispositif

**Repère du volume** (celui de la référence, à garder pour tous les calculs) : x à droite, y vers le bas, z vers le spectateur, en cm, origine au centre. TouchDesigner a y vers le haut : change le signe de y seulement pour l'affichage 3D. Les données LED n'en dépendent pas. Dans l'affichage, les angles de rotation changent donc aussi de signe.

**Paramètres** (tous réglables) :

| Paramètre | Symbole | Défaut |
|---|---|---|
| Panneaux | S | 10 |
| LED par rangée (colonnes) | N | 160 |
| Rangées par panneau | J | 8 |
| Pas entre deux LED d'une rangée | — | 1 cm |
| Pas entre deux rangées | — | 1 cm |
| Écart entre deux panneaux (profondeur) | — | 10 cm |
| Rafraîchissements par tour | R | 180 (2° entre deux) |
| Vitesse de rotation | — | 2 tours/s |
| Demi-épaisseur des arêtes des cubes | w | 4 cm (de 1 à 10) |
| Images/s de l'animation | — | 30 |
| Persistance simulée de l'œil | — | 0,3 s |
| Taille d'affichage d'une LED | — | 1,5 cm |

**Indices** : panneau s = 0…S−1 (0 = devant), rangée j = 0…J−1, colonne k = 0…N−1, rafraîchissement r = 0…R−1.

**Géométrie**

- Chaque panneau est une bande de N × J LED (160 × 8 cm), posée à plat dans le plan de sa tranche (perpendiculaire à z) et centrée sur l'axe z. L'axe passe entre les colonnes 79 et 80 et entre les rangées 3 et 4 (indices comptés depuis 0).
- Les panneaux sont alignés en enfilade le long de z. Profondeur du panneau s : z_s = ((S−1)/2 − s) × écart, soit de +45 cm (panneau 0, devant) à −45 cm.
- Le panneau s est tourné de s × 180°/S (18°) par rapport au panneau 0 : les 20 demi-bandes sont réparties tous les 18°.
- Tous les panneaux tournent ensemble autour de z. Au rafraîchissement r, l'angle de rotation vaut φ_r = 2π·r/R.
- Position de la LED (r, s, j, k) :
  - ang = s·π/S + φ_r
  - d = (k − (N−1)/2) × pas LED (le long du panneau)
  - o = (j − (J−1)/2) × pas rangées (en travers du panneau)
  - x = d·cos(ang) − o·sin(ang) ; y = d·sin(ang) + o·cos(ang) ; z = z_s
- Chaque panneau affiche sa propre tranche du volume, celle qui est à z = z_s. Une LED est allumée si sa position tombe sur le contenu 3D.
- Après un demi-tour, un panneau retombe sur lui-même (rangée j ↔ J−1−j, colonne k ↔ N−1−k). Pour l'affichage, un demi-tour de rafraîchissements suffit donc quand R est pair.
- **Pas de capteur d'angle.** Les panneaux sont montés avec le bon décalage (18°) et tournent à vitesse constante. L'ESP32 affiche donc les rafraîchissements à cadence fixe : le rafraîchissement r à l'instant t0 + r / (R × tours/s), soit un toutes les 2,78 ms à 2 tours/s avec R = 180. N'ajoute ni capteur ni synchronisation par capteur.
- Prévois tout de même un paramètre de sens de rotation (+1/−1) et un décalage d'angle (réglage manuel de la position de départ). Les données sont rangées par angle, pas par temps.

## 2. Le contenu : des cubes rouges en fil de fer

Une LED est allumée (en rouge) si sa distance aux 12 arêtes d'un cube est inférieure ou égale à w.

**Distance aux arêtes** d'un point q exprimé dans le repère du cube (demi-côté ramené à 1) :
- a = |q| − 1 (composante par composante) ; e = max(a, 0)
- dist = √min(e.x² + a.y² + a.z², a.x² + e.y² + a.z², a.x² + a.y² + e.z²)

**Source « Cube fixe »** : un cube centré, non tourné, de demi-côté a = min((N−1)/2 × pas / √2 × 0,95 ; (S−1)/2 × écart), soit 45 cm. La LED en P est allumée si dist(P/a) × a ≤ w.

**Source « Animation cube_animatio »** (source par défaut) : 300 cubes retrouvés dans les images frame_00 à frame_299.
- `poses_cube_animatio.js` contient `const CUBE_POSES = [ … ]`, avec une ligne par image : [cx, cy, s, qx, qy, qz, qw, interpolée].
  - cx, cy : centre du cube dans l'image ; s : demi-côté apparent. Les trois sont en demi-largeurs d'image.
  - qx…qw : rotation du cube (quaternion).
  - interpolée = 1 si l'image manquait : sa pose a été calculée entre ses voisines.
- Lis ce fichier avec une expression régulière (voir l'annexe A) et range-le dans une Table DAT de 300 lignes.
- **Échelle** L (cm par demi-largeur d'image), calculée une fois pour toute la séquence pour que tous les cubes tiennent dans le volume :
  - L = minimum, sur les 300 lignes, de (zmax − w)/(s·√3) et de (demi-longueur − w)/(√(cx² + cy²) + s·√3) ;
  - zmax = (S−1)/2 × écart = 45 ; demi-longueur = (N−1)/2 × pas = 79,5 ;
  - résultat : L ≈ 61,23, soit des cubes de 26,5 à 47,3 cm de côté. L dépend de w, N, S et des pas : recalcule-le quand l'un d'eux change.
- **Pose de l'image i** :
  - centre = (L·cx, L·cy, 0) ; demi-côté h = L·s ;
  - rotation R = matrice du quaternion (formule standard, rangée en lignes r0 r1 r2 / r3 r4 r5 / r6 r7 r8), puis on change le signe de r2, r5, r6 et r7. La caméra des images regardait vers le fond alors que le volume a z vers le spectateur.
- La LED en P est allumée si dist(q) × h ≤ w, avec q = transposée(R) × (P − centre) / h.
- L'image affichée avance au rythme « Images/s » et boucle sur les 300. Affiche « (interpolée) » pour les images calculées.

Plus tard, seulement si je le demande, la source « Images chargées » de la référence :
- 10 images par volume, l'image s allant au panneau s ;
- l'image couvre le disque de rayon √(79,5² + 3,5²) ;
- un pixel plus sombre que 40/255 éteint la LED.

## 3. Architecture demandée dans TouchDesigner

Mets tout dans un Base COMP `/project1/volumetric`, avec une page de paramètres personnalisés reprenant le tableau de la partie 1. Les noms de paramètres personnalisés s'écrivent avec une majuscule puis des minuscules ou des chiffres (`Ledsperrow`, `Edgehalf`…). L'organisation ci-dessous est une suggestion : adapte-la si tu as mieux, mais explique pourquoi.

- **`reference`** (Text DAT utilisé comme module Python) : le code de l'annexe A, qui sert de vérité terrain pour les tests et les exports.
- **`poses`** (Table DAT) : les 300 poses.
- **Horloge** :
  - rotation : Constant CHOP (tours/s × sens) → Speed CHOP → angle = 2π × partie fractionnaire + décalage ;
  - image de l'animation : Speed CHOP (images/s), modulo 300 ;
  - pas de saut quand on change une vitesse ; boutons lecture/pause et choix de l'image n°.
- **`pose`** (Script CHOP) : pour l'image courante, les canaux cx, cy, cz, h, r0…r8 et interp. Pour le cube fixe : (0, 0, 0, a) et la matrice identité.
- **`atlas`** (GLSL TOP, code de l'annexe B) : la couleur de toutes les LED pour un tour complet.
  - Résolution personnalisée N·S × J·R (1600 × 1440), en 8 bits.
  - Le pixel (x, y), avec y compté depuis le bas, correspond à la colonne k = x mod N, au panneau s = x div N, à la rangée j = y mod J et au rafraîchissement r = y div J.
  - Ses uniforms sont reliés au CHOP `pose` et aux paramètres.
- **Simulation 3D** :
  - `positions` (GLSL TOP en RGBA 32 bits float) : même disposition que l'atlas, mais seulement le premier demi-tour (J·R/2 lignes). Ses canaux rgb contiennent la position de la LED pour l'affichage, soit (x, −y, z).
  - `couleurs` (GLSL TOP) : la couleur de l'atlas multipliée par une luminosité de persistance b = clamp(1 − âge / angle_persistance, 0, 1).
    - âge = (sens × (angle_rotation − φ_r)) mod π ;
    - angle_persistance = 2π × tours/s × persistance (s) ;
    - à l'arrêt, b = 1.
  - Une Geometry COMP instanciée depuis ces deux TOP, avec une instance par pixel (1600 × 720, environ 1,15 million). Chaque LED est un petit carré de « Taille LED » en mélange additif sur fond noir. Vérifie les noms exacts des paramètres d'instanciation dans ta version.
  - Les contours des 10 panneaux (160 × 8 cm) à l'angle courant, le panneau 0 plus clair que les autres.
  - Une caméra en vue de biais, avec une orbite à la souris si possible, et un Render TOP.
  - Une ligne d'information : source, image n° (interpolée ou non), pas angulaire, nombre de LED allumées, fps.
- **Sortie** : voir la partie 6.
- **`LISEZMOI`** (Text DAT) : comment fonctionne le réseau, en français simple.

**Performance** : vise 60 fps sur un Mac Apple Silicon. Aucune boucle Python sur les LED à chaque image : le Python ne sert qu'aux poses, aux tests et aux exports.

## 4. Étapes et vérifications

Avance étape par étape. Après chaque étape, vérifie qu'il n'y a pas d'erreur (`op('/project1/volumetric').errors(recurse=True)`), puis montre-moi le résultat (une capture du Render TOP ou de l'atlas, si ton outil MCP le permet).

1. Base COMP, paramètres, module `reference` et Table `poses` (300 lignes).
2. Valeurs de contrôle de la partie 5, calculées avec le module de référence.
3. Horloge et CHOP `pose`.
4. `atlas`. Compare-le à la référence : `numpyArray()`, puis `masque_depuis_atlas`. L'écart attendu est d'au plus 0,1 % des LED (arrondis de la carte graphique sur les LED pile à la limite w). S'il est plus grand, cherche l'erreur : orientation des lignes, disposition, signe de la rotation…
5. Simulation 3D.
6. Exports et sortie vers le matériel.
7. `LISEZMOI` et résumé pour moi.

## 5. Valeurs de contrôle

Pour 160 × 8 LED, R = 180, w = 4 cm, sur un tour complet :

- Positions :
  - LED (r = 0, s = 0, j = 0, k = 0) → (−79,5 ; −3,5 ; 45) ;
  - LED (r = 45, s = 3, j = 7, k = 159) → (−66,374 ; 43,897 ; 15) ;
  - LED (r = 90, s = 9, j = 2, k = 40) → (−38,030 ; 10,780 ; −45).
- Animation : L = 61,230. Pour l'image 0, centre (0 ; 0 ; 0) et h = 16,905.
- LED allumées sur un tour :

| Source | LED allumées |
|---|---|
| Cube fixe | 62 848 |
| Image 0 | 53 888 |
| Image 1 (interpolée) | 54 202 |
| Image 100 | 48 062 |
| Image 150 | 49 978 |
| Image 299 | 68 814 |

- Un volume (un tour complet) en .bin RGB fait 6 912 000 octets. La LED (r = 45, s = 3, j = 7, k = 159) commence à l'octet 1 743 357.

Le module de l'annexe A redonne exactement ces nombres. Le shader de l'annexe B, testé en WebGL, les redonne à 0,05 % près.

## 6. Sortie vers le matériel (ESP32)

**L'envoi des données à l'ESP32 et l'affichage sur les rubans de LED sont déjà maîtrisés de mon côté.** Ne conçois pas de protocole, ne choisis pas de matériel et ne me pose pas de questions sur les LED.

**Il n'y a pas de capteur d'angle** (voir la partie 1). Les panneaux sont espacés comme il faut et tournent à vitesse constante ; l'ESP32 affiche les rafraîchissements à cadence fixe.

Ton travail : produire les données au bon format et les brancher sur ma méthode d'envoi.

1. Demande-moi le format qu'attend mon code ESP32 :
   - ordre des LED et des octets ;
   - couleur (RGB) ou 1 bit par LED ;
   - transport (Wi-Fi/UDP, série…), adresse et port ;
   - ce qui est envoyé : un rafraîchissement à la fois, ou un tour complet à chaque image de l'animation.
2. Adapte la sortie de TouchDesigner à ce format, avec :
   - un paramètre pour activer ou couper l'envoi ;
   - l'adresse et le port (ou le port série) ;
   - un compteur d'octets par seconde.

Ce que tu peux construire tout de suite, avant ma réponse :

- **a. Export .bin d'un volume** (image courante ou plage d'images), au même format que la référence :
  - ordre : rafraîchissement → panneau → rangée → colonne → R, G, B ;
  - octet de départ = 3 × (((r·S + s)·J + j)·N + k) ;
  - 6 912 000 octets par volume.
- **b. Variante à 1 bit par LED** (cubes d'une seule couleur) : même ordre, 8 LED par octet, la première LED dans le bit de poids fort. Cela fait 288 000 octets par volume, soit 86,4 Mo pour les 300 images.
- **c. Export JSON des poses** (centre, demi-côté, rotation, w, géométrie des panneaux), comme `exportAnimationJSON` dans la référence.
- **d. Mode « test à l'arrêt »** : envoie un seul rafraîchissement, choisi par son numéro, pour vérifier l'ordre des LED sur les panneaux immobiles. Branche-le sur ma méthode d'envoi dès que je t'ai donné le format.

Chiffres utiles pour vérifier que le format tient le rythme :

| Quantité | Couleur RGB | 1 bit par LED |
|---|---|---|
| Un rafraîchissement (12 800 LED) | 38 400 octets | 1 600 octets |
| Un tour complet (180 rafraîchissements) | 6 912 000 octets | 288 000 octets |
| Envoi en direct de chaque rafraîchissement (360 par seconde) | ≈ 13,8 Mo/s | ≈ 576 Ko/s |

Si ma méthode actuelle ne peut pas tenir le débit nécessaire, dis-le-moi. Propose alors une autre façon de faire : envoyer un tour complet par image d'animation, ou tout précalculer pour que l'ESP32 rejoue.

## 7. Règles de travail

- Ne modifie et ne supprime rien en dehors de `/project1/volumetric` sans mon accord. N'écrase pas un fichier .toe existant : propose « Enregistrer sous ».
- Vérifie les noms de paramètres et d'opérateurs dans ta version de TouchDesigner (par introspection Python) au lieu de les deviner.
- Commente le Python et le GLSL en français.
- Si une formule de ce document te paraît fausse ou ambiguë, dis-le-moi au lieu de la changer sans rien dire.
- À la fin, donne-moi :
  - un résumé de ce qui est fait et de ce qui reste ;
  - la liste des opérateurs créés.

## Annexe A — Module de référence Python (numpy)

À mettre dans le Text DAT `reference`. Exemple d'usage dans TouchDesigner : `ref = op('reference').module`, puis `poses = ref.lire_poses(open(chemin).read())`.

```python
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

def pose(poses, i, L):
    cx, cy, s, x, y, z, w_, interp = poses[i]
    Rm = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w_), 2 * (x * z + y * w_)],
                   [2 * (x * y + z * w_), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w_)],
                   [2 * (x * z - y * w_), 2 * (y * z + x * w_), 1 - 2 * (x * x + y * y)]])
    Rm[0, 2] *= -1; Rm[1, 2] *= -1; Rm[2, 0] *= -1; Rm[2, 1] *= -1   # retournement de l'axe z
    return np.array([L * cx, L * cy, 0.0]), L * s, Rm, bool(interp)

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
```

## Annexe B — GLSL TOP « atlas »

Réglages du GLSL TOP :
- résolution personnalisée N·S × J·R (1600 × 1440) ;
- format 8 bits RGBA ;
- aucune entrée.

Uniforms à déclarer sur la page Vectors :

| Uniform | Valeur |
|---|---|
| `uDims` | (N, J, S, R) |
| `uPas` | (pas LED, pas rangées, écart, w) |
| `uCube` | (cx, cy, cz, h) |
| `uR0`, `uR1`, `uR2` | les trois lignes de la rotation R |
| `uCouleur` | (1, 0, 0, 1) |

Pour le cube fixe : `uCube` = (0, 0, 0, a) et R = matrice identité.

```glsl
// GLSL TOP « atlas » — couleur de chaque LED pour un tour complet
// Résolution : (N*S) x (J*R) = 1600 x 1440 par défaut. Format : 8 bits RGBA.
// Pixel (x, y), y compté depuis le bas : colonne k = x % N, panneau s = x / N,
//                                         rangée j = y % J, rafraîchissement r = y / J
uniform vec4 uDims;     // N, J, S, R
uniform vec4 uPas;      // pas LED, pas rangées, écart panneaux, demi-épaisseur w (cm)
uniform vec4 uCube;     // cx, cy, cz, h   (cube fixe : 0, 0, 0, a)
uniform vec3 uR0;       // rotation, ligne 1 : r0 r1 r2   (cube fixe : 1 0 0)
uniform vec3 uR1;       // rotation, ligne 2 : r3 r4 r5   (cube fixe : 0 1 0)
uniform vec3 uR2;       // rotation, ligne 3 : r6 r7 r8   (cube fixe : 0 0 1)
uniform vec4 uCouleur;  // couleur des LED allumées : 1 0 0 1

out vec4 fragColor;
const float PI = 3.14159265358979;

// Distance d'un point (repère du cube, demi-côté 1) aux 12 arêtes du cube
float distanceAretes(vec3 q) {
    vec3 a = abs(q) - 1.0;
    vec3 e = max(a, 0.0);
    return sqrt(min(min(e.x * e.x + a.y * a.y + a.z * a.z,
                        a.x * a.x + e.y * e.y + a.z * a.z),
                        a.x * a.x + a.y * a.y + e.z * e.z));
}

void main() {
    int N = int(uDims.x), J = int(uDims.y), S = int(uDims.z), R = int(uDims.w);
    ivec2 p = ivec2(gl_FragCoord.xy);
    int k = p.x % N, s = p.x / N, j = p.y % J, r = p.y / J;
    float ang = float(s) * PI / float(S) + 2.0 * PI * float(r) / float(R);
    float d = (float(k) - 0.5 * float(N - 1)) * uPas.x;
    float o = (float(j) - 0.5 * float(J - 1)) * uPas.y;
    vec3 P = vec3(d * cos(ang) - o * sin(ang),
                  d * sin(ang) + o * cos(ang),
                  (0.5 * float(S - 1) - float(s)) * uPas.z);
    vec3 D = P - uCube.xyz;
    vec3 q = (D.x * uR0 + D.y * uR1 + D.z * uR2) / uCube.w;   // transposée(R) × (P − centre) / h
    bool allumee = distanceAretes(q) * uCube.w <= uPas.w;
    fragColor = TDOutputSwizzle(allumee ? uCouleur : vec4(0.0, 0.0, 0.0, 1.0));
}
```
