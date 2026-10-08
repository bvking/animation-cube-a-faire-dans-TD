# ANIMATION_CUBE dans le projet TouchDesigner SAISON_9

Ajoute au projet SAISON_9 (`SAISON_9_ANIMATION_CUBE.toe` à la racine du dépôt,
issu de `SAISON_9_MOINS_DE_PY_ANNEAUX_SEULS_SANS_VARIATIONS.2`) une option
**animation-cube** : les 300 poses du cube en fil de fer de `cube_animatio`,
rejouées en boucle sur les panneaux, avec **un bouton dans la fenêtre
SORTIE_SPECTACLE** pour la lancer et la couper. Dans le `.toe` du dépôt
l'option est **déjà installée** ; l'installateur reste utile pour la mettre à
jour (il se réinstalle proprement par-dessus) ou pour équiper une autre
version du projet.

## Installer

1. Ouvrir le projet dans TouchDesigner (2025.32460, la version qui a enregistré
   le fichier).
2. Ouvrir le Textport : menu **Dialogs → Textport and DATs** (Alt+T).
3. Coller et exécuter :

   ```python
   exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/INSTALLER_ANIMATION_CUBE.py').read())
   ```

4. Lire la **MESURE** affichée dans le textport (échelle L ≈ 61.2296, demi-côté
   de l'image 0 ≈ 16.9055 cm, texels allumés, erreurs : aucune).
5. **Fichier → Enregistrer sous…** — ne pas écraser le `.toe` d'origine.

L'installation ne change **rien** au comportement tant que le bouton n'est pas
pressé : `Actif` est décoché et l'expression du switch retombe alors, au bit
près, sur celle d'origine. Le script est relançable (il se réinstalle
proprement par-dessus).

## Utiliser

- Dans **SORTIE_SPECTACLE**, panneau de commandes en bas, section
  **ANIMATION CUBE** : le bouton **LANCER LE CUBE / CUBE EN MARCHE** bascule
  l'option ; la ligne d'état montre l'image courante (et « interpolée » pour
  les 84 images calculées entre leurs voisines).
- Quand le cube est en marche, il part vers les **panneaux réels**
  (ports 9101-9110), le **simulateur** et le **rendu 3D** — les trois suivent
  `panel_mask_output`. Pour le rendu 3D, garder `TEXTURES_ROTATION.Mode` sur
  **Coupe** (voir COMMENT_31 du projet).
- Réglages sur `/project1/scale/ANIMATION_CUBE`, page **Cube** : Lecture,
  **Horloge de l'animation** (voir ci-dessous), Images par demi-tour (1),
  Images par seconde (30, mode temps), Image n°, Remettre, Cube fixe
  (vérification de la géométrie), Demi-épaisseur des arêtes (4 cm), Écart
  entre panneaux (10 cm), Couleur, Luminosité, Miroir vertical (calibration
  si le cube tourne à l'envers par rapport à la vidéo d'origine).
- **LANCER LE CUBE STATIQUE / CUBE STATIQUE EN MARCHE**, le bouton juste sous
  LANCER LE CUBE : une seule pose, immobile. C'est la rotation du cube de
  `analyse/capture_cube_statique.png`, retrouvée par `analyse/pose_capture.py`
  avec le même algorithme que les 300 poses ; le cube est centré dans le volume
  et agrandi au plus grand demi-côté qui tient entre les panneaux 0 et 9 et dans
  le rayon des lames (27,2 cm, soit 54 cm de côté). Même module, mêmes LED
  calculées lame par lame par le GLSL : les dix coupes en découlent. Pour le
  voir en volume : CUBE_3D (ci-dessous). Réglages page **Cube** : Cube
  statique, Pose du cube statique (−1 = la capture, 0 à 299 = figer une image
  de l'animation), Taille du cube statique (1 = le plus grand qui tient). Un
  seul maître à la fois : il coupe l'animation, l'anneau et Vasarely, et
  réciproquement. Contrôle hors TouchDesigner :
  `touchdesigner/verification/test_cube_statique.py` (27 080 LED allumées sur
  un demi-tour, 2 733 / 4 272 / 1 916 / 1 999 / 2 620 par panneau, symétrique).

### Ce que les pales impriment : CUBE_3D, le volume vu par l'œil

`INSTALLER_CUBE_3D.py` installe le module CUBE_3D, affiché par real_Move
(bouton **VOLUME BALAYÉ**, les flèches de vue agissent dessus) et par le
bandeau **RENDU 3D avec rémanence** de SORTIE_SPECTACLE dès qu'un cube a la
main. Il n'invente aucun balayage : à chaque image, l'image 160 × 80 réellement
envoyée aux panneaux (`panel_mask_output`, quel que soit le maître) est déposée
dans dix tranches de voxels de 1 cm aux angles réels des lames
(`MOTIFS_LED/angles_top`, consigne ou positions Teensy selon « MOTIFS SUR LES
ANGLES RÉELS »), tout le long de l'arc parcouru depuis l'image précédente ;
chaque dépôt est daté et pâlit comme dans l'œil (b = 1 − âge / Persistance,
0,2 s par défaut, extinction sous 3 %). Conséquence : à lames lentes on ne voit
que des morceaux de cube ; le cube n'apparaît entier que si chaque lame balaye
un demi-tour en moins d'une persistance (2,5 tours/s à 0,2 s), et l'écart entre
lames décide de la répartition des morceaux. Vérifié au texel près : chaque LED
allumée à l'angle courant a son voxel daté de l'image courante. Réglages page
**Volume** : sources (image, angles), Persistance, Pas de l'arc (2°), Seuil,
Écart, Miroir vertical (suit ANIMATION_CUBE), contours, Effacer. Tout est sur le
processeur graphique (atlas 320 × 801 en flottants 32 bits, rebouclé par un
Feedback TOP ; la clé non commerciale plafonne une texture à 1280 px, d'où deux
colonnes de cinq tranches).

### Cadence : ce qui coûte vraiment (mesuré le 6 octobre 2026)

Compter les images réellement cuites (un Execute DAT qui incrémente un
compteur à chaque image ; `absTime.frame` suit l'horloge murale et affiche
toujours 60). Avec l'éditeur de réseau ouvert sur `/project1/scale` (3 900
nœuds, 66 viseurs) : 17 images/s. Éditeur navigué dans un petit COMP, ou mode
Perform : 36 images/s. Sans effet mesurable : la synchronisation verticale des
six fenêtres, la résolution de `render1` (1280 × 720 → 640 × 360), la fermeture
de la fenêtre TIMELINES. Les opérateurs pèsent 22 ms de processeur et 16 ms de
carte graphique par image ; les plus lourds sont les textes de SORTIE_SPECTACLE
qui se recalculent à chaque image (`timeline/lecture` 2 ms, `timeline/avancement`
1 ms), `geo1` cuit trois fois par image (trois Render TOP), l'analyse audio
(ANALYSE_SOUFFLE_COEUR, 26 ms/s), le tableau de real_Move (0,8 ms). CUBE_3D
coûte 0,5 ms par image.

### Le curseur RÉMANENCE de real_Move

Sous le curseur VOLUME, dans la même bande : la persistance de l'œil de
CUBE_3D (0,02 à 1 s), liée à `CUBE_3D.Persistance`. Posé par
`INSTALLER_REAL_MOVE.py` (bloc « CURSEUR REMANENCE »).

### L'animation s'adapte à n'importe quelle vitesse de rotation

Une lame ne peint sa tranche qu'en passant dessus : il lui faut un demi-tour.
Par défaut (`Modehorloge = rotation`), l'image de l'animation n'avance donc
que d'**une image par demi-tour réellement balayé** — compté en déroulant
l'angle réel de la lame 0 (même source que les motifs, consigne ou Teensy).
Résultat, pour la lame 0 et toute lame au moins aussi rapide qu'elle (le cas
du projet sauvegardé, dérives positives) : chaque point n'est peint qu'avec
**une** pose par passage, et une tranche montre au plus **deux poses
consécutives** (la couture tourne avec les lames) — au lieu d'un mélange de
7 à 8 poses à 30 img/s — que la rotation soit lente, rapide, variable ou
inversée ; à l'arrêt des moteurs, l'animation s'arrête (rien n'est balayé).
Une lame **plus lente** que la lame 0 (ouverture d'éventail avec
`Ouvrirenretard`, dérive négative, moteur réel plus lent) peut montrer trois
poses ou plus le temps de la transition ; `PHASES_PANNEAUX.Figerecart` ou des
vitesses égales redonnent la garantie partout. À 2 tours/s, la boucle des 300
images dure 75 s ;
`Imagespardemitour` accélère ou ralentit ce couplage (au-delà de 1, le mélange
revient). Le mode `temps` (30 images/s, comme la simulation p5) reste là pour
prévisualiser ; basculer d'horloge en cours de lecture peut faire sauter
l'image courante.

## Comment ça marche

Même principe que le mode CHAMP 3D de `MOTIFS_LED` : le module produit l'image
**160 × 80** (dix bandes de 160 × 8, panneau 0 en bas), chaque texel connaît sa
position réelle en cm — l'angle de sa lame est lu dans
`MOTIFS_LED/angles_top` (en degrés, consigne ou positions Teensy selon le
réglage existant), la profondeur vient de son panneau (z = (4,5 − s) × 10 cm) —
et s'allume si cette position est à moins de 4 cm d'une des 12 arêtes du cube
de l'image courante (règle de `volumetric3D.js`). Le seul Python par image est
un petit Script CHOP qui lit **une** ligne de la table des poses ; tout le
volume est calculé dans le GLSL.

## Installer / désinstaller sans Textport

Glisser-déposer le fichier `.py` depuis le Finder dans le réseau
(`/project1/scale`) : TouchDesigner crée un Text DAT. **Clic droit sur le
nœud → Run Script.** C'est équivalent au Textport (les messages MESURE ne
sont alors simplement pas visibles). Le Text DAT peut être supprimé après.

- `INSTALLER_ANIMATION_CUBE.py` — installe le cube et le cube statique
  (ré-exécutable sans danger : il garde les boutons de l'anneau et de Vasarely
  et leur place dans le switch)
- `INSTALLER_ANNEAU_CONE.py` — installe l'anneau-cône (après le cube ; son
  bouton se place sous « CUBE EN MARCHE »)
- `INSTALLER_VASARELY.py` — installe l'effet Vasarely (après les deux autres ;
  son bouton se place sous « LANCER L'ANNEAU »)
- `INSTALLER_PERFORM_LEGER.py` — le mode Perform allégé : une seule petite
  fenêtre (le volume imprimé en 320 × 180, LANCER LE CUBE, LANCER LE CUBE
  STATIQUE, TOUT ÉTEINDRE, RETOUR ÉDITEUR), les autres fenêtres fermées le
  temps du mode ; TouchDesigner y cuit 59 images/s au lieu de 17, l'envoi
  aux ESP32 n'est plus bridé que par le ruban (26 trames/s). Entrée par le
  bouton PERFORM LÉGER de SORTIE_SPECTACLE, sortie par RETOUR ÉDITEUR ou Échap
  (les fenêtres se rouvrent, la touche Perform redonne SORTIE_SPECTACLE)
- `INSTALLER_REDETECTION_TEENSY.py` — la carte Teensy rebranchée après le
  démarrage est redétectée toute seule (patch du DAT MOTEURS_TEENSY/horloge et
  de la copie de l'installeur Teensy rangée dans le projet ; à reporter dans
  le dépôt panneaux-led-rotatifs)
- `INSTALLER_REAL_MOVE.py` — installe la fenêtre **real_Move** (le contrôle du
  mouvement réel) ; indépendante des trois animations, ré-exécutable
- `DESINSTALLER_ANIMATION_CUBE.py` / `DESINSTALLER_ANNEAU_CONE.py` /
  `DESINSTALLER_VASARELY.py` — retirent tout et restaurent les expressions
  d'origine (désinstaller dans l'ordre inverse d'installation : Vasarely,
  puis l'anneau, puis le cube)

Au Textport, `desinstaller()` (après avoir exécuté l'installateur dans la
session) fait la même chose. Enregistrer sous ensuite.

## Ce qui a été vérifié avant livraison

- Les formules portées (positions des LED, échelle, pose, distance aux arêtes,
  exports) reproduisent les **20 valeurs de contrôle** du prompt
  (les chiffres de la partie 6 de `PROMPT_CE_QUE_JE_VEUX_FAIRE.md`) — voir
  `touchdesigner/verification/test_controle.py` (python3 + numpy, exécutable hors
  TouchDesigner) : positions au 1/1000, L = 61.2296, h₀ = 16.9055, comptes de
  LED exacts (cube fixe 62 848 ; images 0/1/100/150/299), ordre des octets.
- Les conventions du projet ont été lues dans le `.toe` lui-même (via
  `toeexpand`) : switch `panel_mask_output` et son expression, format 160 × 80
  en bandes `vertbt`, angles en degrés par `angles_top`, chaîne du simulateur
  et du rendu 3D (`rubans_choix` entrée 2), palette et style des boutons de
  `PANNEAU_COMMANDES`.
- La table embarquée dans l'installateur redonne L et h₀ exacts en python pur.

## L'anneau-cône (deuxième animation)

`INSTALLER_ANNEAU_CONE.py` ajoute, sur le même principe que le cube, la
**paroi d'un cône de révolution** (axe z, base au fond sur la lame 9, sommet
devant sur la lame 0) dont la base et le sommet **grandissent et
rétrécissent** de ± Amplitude — en opposition de phase par défaut : le cône
bascule en respirant, jusqu'à s'inverser quand les rayons se croisent. La
respiration est calée sur la rotation (8 demi-tours par cycle par défaut,
mode temps en secours) et, un cône étant invariant par rotation, elle reste
juste à n'importe quelle vitesse des moteurs.

Un `.toe` **prêt à l'emploi** avec les deux animations est à la racine du
dépôt : `SAISON_9_ANIMATION_CUBE_ET_ANNEAU_CONE.toe` — l'anneau y a été
injecté directement dans le fichier (toeexpand → génération → toecollapse,
vérifiée par re-décompression octet à octet) ; l'installateur reste la voie
normale pour mettre à jour ou équiper une autre version du projet.

Son bouton **LANCER L'ANNEAU** apparaît **sous le bouton du cube**, dans la
section « ANIMATION CUBE », avec sa ligne d'état base/sommet. **Un
seul maître à la fois** : allumer l'anneau coupe le cube et inversement ; tout
décocher rend la main à la chaîne d'origine, au bit près. Réglages sur
`/project1/scale/ANNEAU_CONE` (page Anneau) : rayons de repos (60/20 cm),
Amplitude (25 cm), Opposition, période, épaisseur de paroi, couleur (bleu).

## L'effet Vasarely (troisième animation)

`INSTALLER_VASARELY.py` ajoute une **grille op-art bombée/creusée** dans
l'esprit de la série Vega de Vasarely : N × N cellules colorées (carrés,
cercles, damier ou quadrillage, deux rampes de couleurs le long de la
diagonale), déformées par une ou plusieurs calottes sphériques (1 au centre
déplaçable, 2×2, 3×3, ou 2×2 bosses/creux alternés), avec un ombrage plat par
cellule qui vend le relief. Le tableau est **figé dans le plan frontal** du
disque balayé (comme le mode TABLEAU) ; le rendu est **par pixel en sens
inverse** : chaque texel défait la déformation (asin pour une bosse, sin pour
un creux — formules inverses vérifiées à 5 × 10⁻¹⁶) pour retrouver sa cellule.
Le relief **respire** (relief × cos de la phase), calé sur les demi-tours
réellement balayés (8 par cycle par défaut). Un `.toe` prêt à l'emploi avec
les **trois** animations est à la racine : `SAISON_9_CUBE_ANNEAU_VASARELY.toe`.

Son bouton **LANCER VASARELY** apparaît **sous LANCER L'ANNEAU** ; chaque
bouton coupe les deux autres. Réglages sur `/project1/scale/VASARELY`, page
Vasarely : Relief (−90…90°, défaut 80), Rayon (0,84), Densité (20), Ombrage
(0,4), Motif, Disposition, Centre X/Y, Palette (vega / braise / nuit),
Animer, Demi-tours par cycle, Période, Luminosité.

## La fenêtre real_Move (contrôle du mouvement réel)

`INSTALLER_REAL_MOVE.py` construit la fenêtre **real_Move** : en haut les dix
panneaux aux positions **réelles** rapportées par la Teensy, en bas le tableau
des chiffres qui les commandent — angle, vitesse, accélération commandée et
accélération subie, couple, couple maximum, et l'écart moyen entre lames
voisines. Plus un interrupteur **MOTIFS SUR LES ANGLES RÉELS** lié à
`MOTIFS_LED.Anglesreels`, et un curseur de volume à droite.

Pourquoi des chiffres sous l'image : une image dit si le mouvement est beau,
elle ne dit pas s'il est **juste**. Le compteur de la Teensy compte les pas
qu'elle *émet*, pas ceux que l'axe *fait* — un décrochage n'apparaît nulle
part. Le tableau ne recalcule rien : il lit les canaux déjà publiés par
`MOTEURS_TEENSY` (`vitesses_lames`, `couples_lames`, `couples_pic`,
`accels_lames`), parce que dériver un angle **replié modulo 360** aliasait
jusqu'à inverser le signe de la vitesse.

Le rapport d'installation affiche la **place restante** dans la boîte des
chiffres :

```
  place          pire cas 142 car. x 15 lignes = 1147 x 265 px
                 boite 1184 x 280 px -- marge 37 en largeur, 15 en hauteur
```

Cette marge compte. Le texte est centré, donc une ligne ou une colonne ajoutée
en trop se fait rogner **en silence** — aucune erreur, aucun opérateur rouge,
juste une colonne qui manque. C'est arrivé deux fois : les deux lignes
d'accélération et la colonne « écart moyen » ont débordé une boîte restée à sa
taille d'origine. Si une marge passe sous zéro, remonter `bas.par.h` et
`txt.par.resolutionh`, ou baisser `txt.par.fontsizex` (1280 px reste le plafond
d'une clé non commerciale).

## Si le Textport se remplit d'erreurs `text1` / `shuffle1`

```
File "/project1/scale/text1", line 2, in <listcomp>
AttributeError: 'NoneType' object has no attribute 'eval'
```

Ce n'est **pas** l'animation-cube : `text1` est l'envoi périodique des dix
angles `rz0…rz9` vers les sorties OSC, déclenché 8 fois par seconde par
`lfo4` (CHOP Execute `chotext1…pexecDat`). Il plante quand la chaîne `rz` est
en erreur en amont — typiquement parce que `audiofilein1` pointe sur
`../Signs Full - Audio et Synthese_debut.mp3`, un chemin **relatif** : la
copie du `.toe` ouverte depuis ce dépôt ne retrouve plus le mp3 (il vit dans
`Ameliorer controle panneaux rotation TD/`). L'erreur existait déjà ; le
Textport ouvert la rend simplement visible.

Réparation (diagnostic + chemin absolu du mp3 + `text1` durci, réversible) :

```python
exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/REPARER_ERREUR_TEXT1.py').read())
```

Après durcissement, quand des canaux manquent, `text1` n'envoie **rien**
(surtout pas des zéros aux moteurs) et le signale une seule fois. L'original
est conservé dans `text1_origine` ; `retablir_text1()` et `retablir_audio()`
reviennent en arrière.

## Note

La vue « led » de SORTIE_SPECTACLE (en haut à droite) pointait sur
`MOTIFS_LED/out` ; l'installateur la fait pointer sur `panel_mask_output`,
c'est-à-dire sur **ce qui part vraiment** vers les panneaux, quel que soit le
maître (chaîne d'origine, motifs, variations ou cube). La désinstallation
remet l'ancienne vue.
