# Prompt — Faire apparaître un cube 3D sur les panneaux de LED en rotation

Tu es un développeur TouchDesigner expérimenté (Python, TOP, CHOP, SOP, DAT, GLSL, instancing), relié à TouchDesigner par MCP : tu peux lire le réseau, créer des opérateurs, régler des paramètres et exécuter du Python dans le projet ouvert. Je travaille sur Mac. Réponds-moi en français.

Ce document remplace toute supposition sur le dispositif. Ses formules et ses valeurs de contrôle ont été **mesurées** dans le projet, pas estimées.

---

## L'objectif, en deux temps

**Premier temps — un cube simple qui apparaît.** Un cube en fil de fer, fixe, centré, doit se former dans l'air pendant que les dix panneaux tournent. Rien d'autre : pas d'animation, pas de couleur, pas d'effet. **La porte entre les deux temps, trois conditions à remplir :** (1) les neuf écarts entre lames voisines valent −18,00° dans le tableau de `real_Move` ; (2) `CUBE_3D` annonce 31 424 LED allumées, réparties 12 896 / 704 × 8 / 12 896 ; (3) un cube à douze arêtes est identifiable sur `CUBE_3D/out`. La vue sur le dispositif réel est l'**objectif final du projet**, pas la condition de passage au second temps — voir « Les limites connues du dispositif réel » pour ce qu'elle demande en matériel.

**Second temps — un cube qui se meut.** Une fois le cube fixe observé et seulement à ce moment-là, le faire **bouger sur l'ensemble des panneaux** : les 300 poses de `poses_cube_animatio.js`, jouées en boucle, exactement comme le fait `volumetric3D.js`. Le cube glisse sur la diagonale, respire (son côté passe de 26,5 à 47,3 cm, facteur 1,79) et tourne sur lui-même.

Ne commence pas le second temps tant que le premier n'est pas acquis. Un cube animé qu'on ne voit pas ne dit rien sur ce qui ne va pas.

---

## Dans cet ordre

1. Ouvre `SAISON_9_CUBE_ANNEAU_VASARELY.toe` à la racine du dépôt (TouchDesigner **2025.32460**).
2. Vérifie que `panel_mask_output` a son index à **3** : c'est la valeur qui dit que le cube sort vraiment. 4 = l'anneau-cône, 5 = la grille Vasarely — ces deux-là **coupent le cube** sans rien signaler.
3. Pose les réglages du premier temps (tableau plus bas), puis **relis les écarts mesurés** dans `real_Move`, pas les paramètres.
4. Regarde `/project1/scale/CUBE_3D/out`.
5. Ne passe au second temps qu'une fois la porte franchie — ses trois conditions sont énoncées plus haut.

Pour rejouer un installeur, au Textport (Alt+T) :

```python
exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/INSTALLER_CUBE_3D.py').read())
```

ou glisse le `.py` dans `/project1/scale`, puis clic droit sur le nœud → **Run Script**.

**Vocabulaire — trois « écarts » à ne pas confondre :**

| Mot | Grandeur | Paramètres | Valeur |
|---|---|---|---|
| écart **angulaire** | entre deux lames voisines | `PHASES_PANNEAUX.Ecartpanneaux`, `CUBE_3D.Ecarthelice` | 18° |
| écart de **profondeur** | entre deux panneaux | `Ecartcm`, sur `ANIMATION_CUBE` **et** sur `CUBE_3D` | 10 cm |
| demi-**épaisseur** | grosseur des arêtes du cube | `Epaisseur`, sur les deux modules | 4 cm |

Les deux derniers existent en double, un par module, et **rien ne les tient d'accord** : c'est à toi de le faire.

## Le dispositif

Dix panneaux de **160 × 8 LED** au pas de 1 cm, posés à plat dans le plan de leur tranche, centrés sur l'axe Z, tournant **ensemble** autour de cet axe.

| Grandeur | Valeur | Formule |
|---|---|---|
| Panneaux | 10 | — |
| Colonnes par panneau | 160 | position de la colonne *k* : `d = k − 79,5` cm |
| Rangées par panneau | 8 | décalage de la rangée *j* : `o = j − 3,5` cm |
| Profondeur du panneau *s* | +45 … −45 cm | `z = (4,5 − s) × 10` cm — panneau 0 devant |
| Écart angulaire entre deux lames voisines | **18°** | `180° / 10` |
| Vitesse de rotation | 2 tours/s | — |
| Rafraîchissements par tour | 180 | un pas de 2° |
| Demi-épaisseur des arêtes | 4 cm | arête de 8 cm |

**Position d'une LED à l'angle θ de sa lame** :

```
x = d·cos θ − o·sin θ
y = d·sin θ + o·cos θ
z = (4,5 − s) × 10
```

Chacune des huit rangées doit utiliser **son propre** `o`. Sans cela le dessin est dédoublé sur 8 cm.

**Repère** : x à droite, y vers le bas, z vers le spectateur, en centimètres, origine au centre. TouchDesigner a y vers le haut : ne change le signe de y que pour l'affichage 3D, jamais pour les données LED.

---

## Pourquoi un cube apparaît

On ne dessine pas un cube : **on allume les LED qui se trouvent physiquement dessus**. En tournant, chaque panneau balaye un disque à sa profondeur ; les dix disques empilés forment un cylindre de voxels. À chaque instant on n'allume que les LED qui sont, à cet instant, sur les arêtes du cube. L'œil additionne la lumière pendant environ 1/20 à 1/10 de seconde, et ce sont ces points qui tracent le cube **dans l'espace réel**.

Ce n'est pas une projection : on peut tourner autour, chaque œil voit un angle différent, il y a un vrai relief.

**Un cube coupé en tranches ne ressemble pas à un cube.** Pour un cube en fil de fer, les tranches avant et arrière donnent un contour carré, et les tranches intermédiaires se réduisent à **quatre points** — les quatre arêtes parallèles à l'axe de rotation (les arêtes de profondeur, en x = ±45, y = ±45). Si tu regardes une seule tranche et que tu n'y vois que quatre points, c'est juste.

**La règle d'allumage**, celle de `volumetric3D.js:296-303` et `:352` :

```
q = transposée(R) · (p − centre) / h          R = rotation du cube, h = demi-côté
X, Y, Z = |q.x|, |q.y|, |q.z|
dx, dy, dz = X−1, Y−1, Z−1
ex, ey, ez = max(0, dx), max(0, dy), max(0, dz)
distance = √( min( ex²+dy²+dz² ,  dx²+ey²+dz² ,  dx²+dy²+ez² ) )
LED allumée  ⟺  distance × h ≤ demi-épaisseur
```

Par symétrie, trois arêtes suffisent : celles qui partent du sommet (1, 1, 1).

---

## Ce qui existe déjà — ne le reconstruis pas

Trois modules sont installés et **vérifiés**. Lis-les avant d'écrire une ligne.

**Le `.toe` livré contient trois animations qui s'excluent mutuellement** : animation-cube, anneau-cône et grille Vasarely, chacune sur son bouton dans `SORTIE_SPECTACLE`. Un seul maître à la fois : allumer l'anneau coupe le cube et inversement. Si l'anneau ou Vasarely est maître, le cube ne sortira jamais aux panneaux et **rien ne te le signalera**.

| Module | Ce qu'il fait | État |
|---|---|---|
| `/project1/scale/ANIMATION_CUBE` | l'image 160 × 80 d'**un instant** : ce qui part aux panneaux réels (ports 9101-9110) | portage du JavaScript **vérifié au texel près** |
| `/project1/scale/CUBE_3D` | le **volume balayé complet** d'un demi-tour, dessiné en 3D : ce que l'œil verrait | 31 424 LED = la valeur de contrôle du simulateur |
| `/project1/scale/real_Move` | les dix lames aux angles réels + le tableau de chiffres + sept flèches de point de vue | — |

Leurs installeurs, rejouables, sont dans `touchdesigner/` : `INSTALLER_ANIMATION_CUBE.py`, `INSTALLER_CUBE_3D.py`, `INSTALLER_REAL_MOVE.py`. Ils se réinstallent proprement par-dessus — mais une réinstallation **ajoute** les paramètres que le module vivant n'a pas encore, et peut donc changer la cadence de l'animation sous le lecteur (voir `Modehorloge` au second temps). Installe dans l'ordre cube → anneau → Vasarely.

**Un avertissement sur la vitesse du simulateur** : `volumetric3D.js:516` bride la lecture, l'image suivante n'arrive qu'après `max(1000/fps, 2 × durée du dernier calcul)`. Avec environ 1,3 million de LED testées par image en JavaScript, le sketch joue bien en dessous de 30 images/s et son cycle observé dépasse largement 10 s. Dans TouchDesigner on veut les **10 s nominales**, pas le comportement bridé du sketch : « exactement comme le fait `volumetric3D.js` » porte sur la règle, pas sur la vitesse réelle du navigateur.

**La différence entre les deux premiers est capitale.** `ANIMATION_CUBE` calcule un instant : dix segments. C'est correct pour piloter le matériel, et c'est structurellement incapable de ressembler à un cube à l'écran. `CUBE_3D` parcourt les 90 pas de rafraîchissement d'un demi-tour et les dessine **ensemble**, chaque point à sa luminosité — c'est l'équivalent de `processVolume()` du simulateur, et c'est là qu'un cube se voit.

---

## Premier temps — le cube fixe

### Les réglages à poser

| Opérateur | Paramètre | Valeur | Pourquoi |
|---|---|---|---|
| `/project1/scale/PHASES_PANNEAUX` | `Arrangement` | `identique` | « réparti » ajoute son propre pas de 36° **par-dessus** `Ecartpanneaux` |
| `PHASES_PANNEAUX` | `Ecartpanneaux` | **18** | une **cible**, pas une valeur appliquée : voir le piège n° 8 |
| `PHASES_PANNEAUX` | `Figerecart` | **coché** | sans quoi la dérive des dix moteurs défait l'écart en quelques secondes |
| `PHASES_PANNEAUX` | `Vitessevisuelle` | 2 | tours/s |
| `ANIMATION_CUBE` | `Cubefixe` | **coché** | pose forcée, centrée, rotation identité |
| `ANIMATION_CUBE` | `Epaisseur` | 4 | la valeur du simulateur |
| `CUBE_3D` | `Ecarthelice` | **18** | même valeur absolue que `Ecartpanneaux` (voir la note sur le signe plus bas) |
| `CUBE_3D` | `Epaisseur` | 4 | **son propre** paramètre, à tenir égal à celui d'`ANIMATION_CUBE` |
| `CUBE_3D` | `Ecartcm` | 10 | profondeur entre panneaux ; c'est lui qui fixe h = 45 cm |
| `CUBE_3D` | `Rafraichissements` | 180 | fixe les 90 pas du demi-tour, donc les 1 152 000 LED testées |
| `CUBE_3D` | `Remanenceanimee` | **décoché** | ne change pas le compte de 31 424, seulement la luminosité ; coche-le quelques secondes pour voir le secteur clair tourner, pas pendant le reste du travail (piège n° 3) |
| `ANIMATION_CUBE` | `Actif` | **coché** | **le seul interrupteur qui envoie le cube aux panneaux** ; décoché par défaut après installation, c'est lui qui fait passer `panel_mask_output` sur l'entrée 3. Le bouton LANCER LE CUBE de `SORTIE_SPECTACLE` fait la même chose |
| `ANIMATION_CUBE` | `Miroiry` | décoché | « Miroir vertical (calibration) » : le bouton à essayer si le cube tourne à l'envers par rapport à la vidéo d'origine |

Le cube fixe fait **45 cm de demi-côté**, soit 90 cm d'arête : `h = min(79,5/√2 × 0,95 ; 4,5 × Ecartcm) = min(53,40 ; 4,5 × 10) = min(53,40 ; 45) = 45`. C'est la **profondeur** qui borne, et ses faces avant et arrière tombent exactement sur le panneau 0 et le panneau 9. Le simulateur trouve la même valeur par le même raisonnement (`volumetric3D.js:356-361`). Il ne peut pas être plus grand sans sortir du volume.

### Ce qu'il faut regarder

- `/project1/scale/CUBE_3D/out` — le volume balayé complet. **C'est là qu'on voit le cube.**
- `/project1/scale/ANIMATION_CUBE/out_led` — l'image 160 × 80 qui part aux panneaux. On y voit des points épars : c'est normal, c'est un instant.
- `/project1/scale/real_Move` — les dix lames en rotation et le tableau de contrôle. La colonne **écart moyen** y dit si les lames tiennent leurs 18°.

### Les valeurs de contrôle

Avec le cube fixe, demi-épaisseur 4 cm, décalage 18° :

| Mesure | Valeur attendue |
|---|---|
| LED testées sur un demi-tour | 90 × 10 × 8 × 160 = **1 152 000** |
| LED allumées | **31 424** |
| proportion | 2,73 % |
| répartition par panneau | **12 896** (panneau 0) / **704** sur chacun des huit intermédiaires / **12 896** (panneau 9) |

**31 424 est le demi-tour, soit exactement la moitié des 62 848 du tour entier** publiés partout ailleurs dans le dépôt : `PROMPT_TouchDesigner_afficheur.md` partie 5, `touchdesigner/README.md`, et `touchdesigner/verification/test_controle.py:38`, qui vérifie en dur `cube fixe = 62 848`. Les deux moitiés sont identiques par symétrie. Qui lance le script de vérification du dépôt obtient 62 848 : ce n'est pas une contradiction.

**Où lire le 31 424** : nulle part à l'écran. Le nombre sort du rapport textport de l'installeur (`INSTALLER_CUBE_3D.py:446`) et vit dans un `comp.store`. Pour le relire sans rejouer l'installeur :
```python
op('/project1/scale/CUBE_3D').fetch('nb_allumees')
```

**31 424 est aussi le chiffre du simulateur** avec ses 180 colonnes. Que les deux coïncident s'explique : le coin du cube est à √(45²+45²) = 63,6 cm de l'axe, plus 4 cm d'épaisseur ; la lame de 79,5 cm comme celle de 89,5 cm englobent le cube entier.

Si tu trouves 0,5 % ou 8 %, tu as une erreur d'épaisseur, d'échelle ou de repère — pas un problème d'affichage.

### Vérifier autrement qu'à l'œil

Réimplémente la règle d'allumage en numpy, **depuis ce document et depuis `volumetric3D.js`**, pas depuis le shader, et compare texel par texel avec la sortie de TouchDesigner. Compare contre `ANIMATION_CUBE/out_led` (12 800 texels, dix bandes de 160 × 8), à pose et angle figés. Le désaccord attendu est d'**au plus 0,1 %**, soit une douzaine de texels, tous sur des LED pile à la limite `w` : le masque est calculé en GLSL, et le shader arrondit là où numpy tranche. Au-delà, cherche l'orientation des lignes, la disposition, le signe de la rotation ou le repère. Ce contrôle valide `ANIMATION_CUBE`, pas `CUBE_3D` : pour `CUBE_3D`, le compte de 31 424 est insensible à un miroir ou à une rotation de 90°, donc vérifie aussi la répartition par panneau (12 896 / 704 × 8 / 12 896).

---

## Second temps — le cube qui se meut

Décoche `ANIMATION_CUBE.Cubefixe`. Les 300 poses se jouent, et `CUBE_3D` suit sans autre réglage : il lit `ANIMATION_CUBE/pose`. Attention : seule la **pose** est partagée (centre, demi-côté, rotation). `CUBE_3D` a ses propres `Epaisseur`, `Ecartcm` et `Rafraichissements`, indépendants de ceux d'`ANIMATION_CUBE` : il faut les tenir égaux à la main, sinon les deux modules montrent deux cubes d'épaisseur ou de profondeur différentes sans qu'aucune erreur n'apparaisse.

### Les règles du mouvement, et leur source

| Règle | Valeur | Source |
|---|---|---|
| Nombre de poses | 300, lues dans l'ordre du fichier | `poses_cube_animatio.js` |
| Cadence | 30 images/s → cycle de 10,000 s, **mais seulement en mode `temps`** : mets `ANIMATION_CUBE.Modehorloge` sur `temps` et `Imagespersec` à 30. Le défaut est `rotation` (une image par demi-tour réellement balayé, `Imagespardemitour` = 1), qui étale la boucle sur 75 s à 2 tours/s — juste pour le dispositif réel, ce n'est pas la cadence du simulateur | `volumetric3D.js:45` ; `INSTALLER_ANIMATION_CUBE.py:767-776` |
| Interpolation à la lecture | **aucune** — l'image est un indice entier, le cube saute d'une pose à l'autre | `:341`, `:516-519` |
| Interpolation **en amont** | **84 des 300 poses** sont déjà reconstruites entre leurs voisines à l'analyse d'images (position et taille linéairement, rotation par slerp). Le drapeau est la 8e colonne de chaque pose, et l'interface affiche « (interpolée) ». Ce n'est pas un défaut de ton portage : c'est ce qui explique les paliers visibles dans cx/cy | `:292`, `:344` ; `EXPLICATION.txt:44-46` |
| Échelle, pour toute la séquence | L = **61,2296 cm** par demi-largeur d'image | `:272-280` |
| Centre du cube | (L·cx, L·cy, **0**) — il ne s'approche ni ne s'éloigne jamais | `:292` |
| Demi-côté | h = L·s, de 13,2 à 23,7 cm | `:292` |
| Trajectoire | la **diagonale** : cx et cy corrélés à 0,9999 | mesure sur les 300 poses |
| Respiration | côté de 26,5 à 47,3 cm, facteur 1,79 | mesure |
| Quaternion | [qx, qy, qz, qw], **w en dernier** | `:285-288` |
| Retournement de l'axe z | inverser le signe de R[2], R[5], R[6], R[7] | `:289-291` |
| La boucle ne se referme pas | de l'image 299 à la 0, le cube saute de 42,8° de rotation **apparente** — la plus petite rotation équivalente modulo les 24 rotations du cube ; la rotation brute du quaternion, elle, saute de 176,1°. À comparer au pas médian image→image de 0,87° (maximum 5,06°, entre 249 et 250) | mesure |

L'échelle L est calculée **une fois** pour toute la séquence, comme le minimum sur les 300 poses de `min((45−w)/(s√3), (79,5−w)/(hypot(cx,cy)+s√3))` — le simulateur écrit ici `halfLength()`, soit 89,5 cm pour ses 180 colonnes (`volumetric3D.js:277`). La substitution 89,5 → 79,5 est volontaire et ne change **rien** : L vaut 61,229594 dans les deux cas, parce que c'est le terme de **profondeur** qui borne, à la pose 217 (s = 0,3866, le plus gros cube de la séquence), le terme radial restant lâche sur les 300 poses. Ne la recalcule pas image par image : cela supprimerait la respiration, qui est la moitié du mouvement perçu.

### Ce qui doit rester identique au simulateur

- **Rouge pur sur noir pur.** rgb(255,0,0) sur rgb(0,0,0). Aucun orange, aucun rose, aucun gris de fond (`:337`, `:503`).
- **Le volume est feuilleté en dix plans.** C'est la signature visuelle numéro un. Un cube continu en profondeur serait immédiatement faux.
- **Les points ne tournent pas.** Seuls les dix contours de panneaux tournent ; les voxels sont **fixes** dans l'espace et ne font que varier de luminosité (`:384`, `:575` contre `:539-549`). Faire tourner les points avec les panneaux est l'erreur la plus facile à commettre et elle change tout.
- **La rémanence est analytique, pas un Feedback.** `b = 1 − âge / 216°`, l'âge étant `(rotation − φ) modulo 180°`. Comme 216° > 180°, **rien ne s'éteint jamais** — mais c'est conditionnel : le simulateur abandonne un voxel dès que `b ≤ 0,03`, et cela n'arrive jamais tant que l'angle de persistance (360° × tours/s × persistance) dépasse le demi-tour. À 0,3 s et 2 tours/s il vaut 216° et b ≥ 0,167 ; baisse la persistance et des points commencent à s'éteindre. Le volume entier reste visible avec un secteur clair qui tourne. Un Feedback TOP donnerait des arcs baveux et une traînée dépendante du framerate.
- **La traînée du simulateur est quantifiée** sur 16 niveaux par composante (multiples de 17), ce qui donne 13 paliers de rouge aux réglages persistance 0,3 s / 2 tours/s. C'est une **optimisation de dessin p5** — elle sert à regrouper les points de même couleur pour les tracer d'un coup, le commentaire de `volumetric3D.js` le dit — pas une intention visuelle. Reproduis-la si tu veux une comparaison pixel à pixel avec le simulateur ; ignore-la sinon, un dégradé lisse est plus fidèle à la physique.
- **Arêtes grasses.** 8 cm pour un cube de 26 à 47 cm : l'arête fait 17 à 30 % du côté. Le cube ressemble à un assemblage de boudins lumineux, pas à un fil de fer.
- **Densité de 2,3 % en moyenne** des LED testées (1,3 % à 3,0 % selon la pose) sur ce rig de 160 colonnes. Le « environ 2 % » qu'on lit ailleurs est la densité sur la lame de 180 colonnes du simulateur (2,1 %), où le dénominateur est 1 296 000 au lieu de 1 152 000.

---

## Les pièges, tous payés une fois

**1. L'écart est de 18°, pas 36.** Une lame est une barre **diamétrale** : elle occupe les directions θ **et** θ+180. À 18°, dix lames donnent dix directions distinctes réparties sur le demi-tour. À 36°, les lames 5 à 9 retombent exactement sur les lames 0 à 4 : **cinq** directions distinctes au lieu de dix à chaque instant. Ce que 18° change est la répartition dans le **temps** — moins de scintillement, meilleur équilibrage mécanique, plus grande fraction du cube allumée à un instant donné. Ce que 18° ne change **pas** : l'ensemble balayé ni le compte de LED. Sur un demi-tour complet, 18° et 36° allument tous deux exactement 31 424 LED, car chaque lame balaye les mêmes 90 angles quel que soit son décalage. Deux textes affirment le contraire et se trompent tous les deux : le commentaire ligne 164 de `PHASES_PANNEAUX/angles_phases_callbacks`, et l'aide du paramètre `Ecarthelice` dans `touchdesigner/INSTALLER_CUBE_3D.py:289-295`, qui écrit encore « la moitie du volume n'est plus balayee ». Le second est un fichier du dépôt : corrige-le.

Mesure faite : sur un demi-tour **complet**, 18° et 36° allument exactement le même nombre de LED, car chaque lame balaye les mêmes 90 angles quel que soit son décalage. L'hélice change la répartition dans le **temps** — le scintillement, l'équilibrage mécanique, la fraction du cube allumée à un instant donné — pas l'ensemble balayé.

**2. Un `geometryCOMP` tout neuf n'est pas vide.** TouchDesigner 2025 y dépose un `torusPOP` nommé `torus1`, rendu par défaut, d'un rayon de 1 unité. On voit un gros tore à la place de son nuage de points, et sa taille ne réagit à **aucun** réglage de la géométrie instanciée — ce qui envoie chercher le défaut partout sauf là où il est. Un inventaire qui filtre sur `isSOP` ne le voit pas : **un POP n'est pas un SOP**. Éteins son drapeau de rendu, ne le détruis pas.

**3. Ne lis pas l'horloge dans un Script CHOP sans le vouloir.** Lire `absTime` le rend dépendant du temps : TouchDesigner le recuit à **chaque image**, sur le fil principal. Quinze millisecondes de numpy par image, plus trente mille instances à dessiner, et l'éditeur cesse de répondre — c'est arrivé, il a fallu forcer la fermeture. `CUBE_3D` a pour cela un réglage **« Faire tourner la rémanence » (`Remanenceanimee`), décoché par défaut** : la phase devient un simple paramètre et le CHOP ne cuit que lorsque la pose change.

**Vérifie de quel côté du correctif est ton fichier avant de travailler.** Si le paramètre « Faire tourner la rémanence » est **absent** de la page Volume de `CUBE_3D`, le `.toe` est antérieur au correctif : son Script CHOP lit encore l'horloge et bloquera l'éditeur. Dans ce cas, relance `INSTALLER_CUBE_3D.py` tout de suite. Et sache que `Remanenceanimee` ne supprime que la dépendance à l'**horloge** : le cache est indexé sur la pose, donc dès que `Cubefixe` est décoché au second temps la pose change à chaque image, le cache manque à chaque image, et les quinze millisecondes de numpy plus les trente mille instances reviennent. Le second temps n'est pas gratuit.

**4. `comp.store()` est enregistré dans le `.toe`.** Y ranger des tableaux numpy a fait passer le projet de 1,0 à **9,2 Mo** pour des valeurs recalculables en quinze millisecondes. Les caches doivent vivre dans un dictionnaire de module.

**5. Un `renderTOP` ne se mesure pas dans le script qui le modifie.** Il est calculé par le GPU au fil des images ; un `cook(force=True)` dans le même appel rend l'image **précédente**. Mesure entre deux appels, jamais dedans.

**6. `COMMENT_48_REMANENCE_RENDU` est périmé.** Il dit « l'installation, c'est `null4` ». `null4` est aujourd'hui alimenté par `mesures_sous_lames` : le réseau a été recâblé. La vue avec rémanence d'écran est `transform1`, alimenté par `TRAINEES_LUMIERE/out_trainees`. Attention au propriétaire du réglage : `transform1` est un `transformTOP` et n'a **aucun** paramètre de persistance — c'est `/project1/scale/TRAINEES_LUMIERE`, un `baseCOMP`, qui porte `Persistance`. Elle doit valoir **0,97** ; relevée à **0,238**, bien sous le seuil de 0,90 où la traînée meurt, elle donnait 0,84 % de pixels allumés au lieu des 11,2 % de référence. Remise à 0,97 : 8,10 %.

**7. `project.save()` sur un nom en `.1` auto-incrémente.** TouchDesigner déplace l'ancien fichier dans `Backup/`, écrit `.toe` **et** `.N.toe`. Vérifie les md5 après chaque sauvegarde.

**8. `Ecartpanneaux` n'est qu'une consigne.** Le module ne l'applique pas tel quel : il range un `ecart_courant` dans son stockage et l'y amène progressivement, sous contrainte d'accélération, parce que les vrais moteurs ne peuvent pas sauter d'un écart à l'autre. Après l'avoir réglé, **attends et relis les écarts mesurés** dans `real_Move` au lieu de croire le paramètre : on peut lire 25,05° en chemin vers 18°. Et `Arrangement = reparti` ajoute son propre pas de 36° **par-dessus** cette valeur — d'où 54,1° mesurés pour `Ecartpanneaux = 18`. C'est pourquoi le tableau impose `identique`.

**9. `Vitesseplafond` écrête `Vitessevisuelle`.** Relevé dans le projet : `Vitessevisuelle` = 2,0 alors que `Vitesseplafond` = 1,71. Si la vitesse observée ne correspond pas à la consigne, regarde ce plafond avant de chercher ailleurs.

**10. `Figerecart` n'est pas optionnel.** Les dix moteurs ne tournent pas exactement à la même vitesse ; sans lui, aucun écart ne tient plus de quelques secondes et l'hélice se referme toute seule.

---

## Comment savoir que c'est gagné

**Premier temps.** Les neuf écarts entre lames voisines valent −18,00° dans le tableau de `real_Move`. `CUBE_3D` annonce 31 424 LED allumées. Et sur `/project1/scale/CUBE_3D/out`, on voit un cube en fil de fer rouge, en perspective, avec ses douze arêtes — pas un tore, pas une tache, pas deux carrés isolés.

**Second temps.** Le cube glisse sur la diagonale, grossit et rétrécit d'un facteur 1,79 sur un cycle de dix secondes, et tourne sur lui-même. Le compte de LED allumées reste entre **15 000 et 35 000** selon la pose : minimum 15 207 à l'image 166, maximum 34 874 à l'image 295, moyenne 27 028 — soit 1,3 % à 3,0 % des 1 152 000 LED testées. Neuf poses (162 à 170) passent sous 20 000 : ce sont celles où le cube est à la fois petit et excentré, et c'est juste. Trois repères vérifiables un par un sur un demi-tour : image 0 → 26 944, image 100 → 24 031, image 299 → 34 407. La boucle saute visiblement en rotation au passage de l'image 299 à l'image 0 : c'est fidèle, ne le corrige pas.

L'objectif final du projet reste que **le cube se voie sur le dispositif**, en regardant les panneaux tourner. Ce n'est pas la condition de passage entre les deux temps (voir la porte définie au début), parce qu'il y faut du matériel que les « limites connues » détaillent : sorties en parallèle ou LED plus rapides.

---

## Annexe — Les limites connues du dispositif réel

À garder en tête : elles expliquent ce qu'on verra, et ce qu'on ne verra pas.

- **Scintillement.** Le décalage ne fait pas rallumer un point plus souvent. À 2 tours/s, un point donné n'est allumé que **4 fois par seconde** (2 demi-bras × 2 tours). L'image ne paraît stable qu'à partir d'environ 25 Hz : le cube sera visible mais scintillant, comme balayé.
- **Débit.** Chaque image doit partir en 2,78 ms. Avec des WS2812 (≈ 30 µs par LED), une ligne de données ne rafraîchit qu'environ 90 LED dans ce temps, alors qu'un panneau en compte 1 280. Il faut des sorties en parallèle, ou des LED plus rapides (APA102, HUB75).
- **Pas de capteur d'angle.** Si la vitesse réelle diffère de 1 % de celle prévue, le cube semblera tourner tout seul d'environ 7°/s. Un capteur à effet Hall et un aimant — une impulsion par tour — suffisent à remettre le compteur à zéro à chaque tour.
- **Précision anisotrope.** 1 cm le long du panneau, mais jusqu'à 3 cm dans le sens de la rotation au bord : à 2° par image, une LED au bord (79,5 cm de l'axe) trace un arc de 2,8 cm. Pour 1 cm partout il faudrait une image tous les 0,72°, soit environ 500 par tour. (Les chiffres de 3,1 cm, 0,64° et 562 par tour qu'on lit dans `EXPLICATION.txt` valent pour la lame de **180** colonnes du simulateur, dont la demi-longueur est 89,5 cm — pas pour ce rig.)

---

## Avant de commencer

1. Ouvre `SAISON_9_CUBE_ANNEAU_VASARELY.toe` à la racine du dépôt — c'est « le projet prêt à l'emploi » désigné par le README. (`SAISON_9_CUBE_ANNEAU_VASARELY.3.toe` a le même md5, c'est le doublon d'auto-incrément du piège n° 7 ; les autres `.toe` sont des versions antérieures.) Version de TouchDesigner : **2025.32460**.
2. Liste les outils MCP dont tu disposes, et vérifie `app.version`. Pour rejouer un installeur, depuis le Textport :
   ```python
   exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/INSTALLER_CUBE_3D.py').read())
   ```
   L'ordre d'installation est **cube → anneau → Vasarely** (désinstallation en ordre inverse) : `INSTALLER_CUBE_3D.py` lève une exception si `ANIMATION_CUBE/pose` est absent, donc `INSTALLER_ANIMATION_CUBE.py` d'abord.
3. À l'ouverture, le Textport se remplit d'erreurs `text1` / `shuffle1` : elles **préexistent** et ne viennent pas de toi — `audiofilein1` pointe sur un mp3 par chemin relatif introuvable ici. Le correctif est `touchdesigner/REPARER_ERREUR_TEXT1.py`.
2. Lis `touchdesigner/INSTALLER_CUBE_3D.py` et `touchdesigner/INSTALLER_ANIMATION_CUBE.py` **en entier**. Ils sont très commentés, et les commentaires disent le *pourquoi* de chaque choix.
3. Relève l'état du rig : écarts entre lames, vitesse mesurée, `Cubefixe`, `Epaisseur`, et l'index de `panel_mask_output` — il vaut 3 quand le cube sort vraiment.
4. Dis-moi ce que tu comptes faire en quelques lignes avant de modifier quoi que ce soit.

Un rapport d'installation qui annonce « aucune erreur » ne prouve ni que le cube bouge, ni qu'on le voit. Seuls les chiffres mesurés le disent.
