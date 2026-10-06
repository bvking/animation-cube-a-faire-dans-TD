# Ce que je veux faire

Lis ce document en entier avant de proposer quoi que ce soit. Il décrit une machine réelle et un objectif précis. Les formules et les chiffres qu'il contient sont mesurés, pas estimés : tu peux les utiliser comme vérité.

Réponds-moi en français.

---

## 1. La machine

Dix panneaux de LED tournent ensemble autour d'un axe. Chacun est une barre droite qui passe par l'axe — une **barre diamétrale**, avec donc deux demi-bras opposés.

| Grandeur | Valeur |
|---|---|
| Panneaux | 10 |
| LED par panneau | 160 colonnes × 8 rangées |
| Pas entre deux LED | 1 cm, dans les deux sens |
| Longueur d'un panneau | 160 cm (il traverse tout le disque) |
| Écart de profondeur entre deux panneaux | 10 cm |
| Écart angulaire entre deux panneaux voisins | **18°** |
| Vitesse de rotation | 2 tours par seconde |
| Rafraîchissements par tour | 180, soit un pas de 2° |

Les dix panneaux sont empilés en profondeur le long de l'axe : le panneau 0 est devant, à +45 cm, le panneau 9 derrière, à −45 cm. En tournant, chacun balaye un disque à sa propre profondeur. Les dix disques empilés forment un **cylindre de voxels** de 160 cm de diamètre et 90 cm de profondeur.

---

## 2. Ce que je veux obtenir

**Un cube en trois dimensions qui apparaît dans l'air pendant que les panneaux tournent.**

Pas un cube dessiné sur un écran. Un cube qu'on peut contourner, dont chaque œil voit un angle différent, et qui a donc un vrai relief.

Je veux y arriver en deux temps, dans cet ordre :

1. **Un cube fixe, simple.** Centré, immobile, en fil de fer. Rien d'autre. Tant que celui-là n'apparaît pas, il est inutile d'aller plus loin.
2. **Un cube qui se meut.** Une séquence de 300 poses, jouée en boucle : le cube glisse, grossit, rétrécit et tourne sur lui-même.

---

## 3. Le principe — et l'erreur qu'on fait tous

**On ne dessine pas un cube. On allume des LED qui se trouvent physiquement sur le cube.**

À chaque instant, une LED donnée est quelque part dans l'espace. On l'allume si, **à cet instant**, elle est sur une arête du cube. On l'éteint sinon. En tournant, les panneaux promènent leurs LED dans tout le volume, et la succession de ces allumages trace le cube dans l'espace réel. L'œil additionne la lumière pendant environ un dixième de seconde et recompose la forme.

Ce qui en découle, et qu'il faut avoir en tête :

- **Les LED s'allument et s'éteignent en permanence.** Si rien ne clignote, c'est que le calcul est faux. Une simulation qui montre un cube figé entouré de panneaux qui tournent a raté l'essentiel.
- **Les points ne tournent pas avec les panneaux.** Les voxels allumés sont **fixes dans l'espace** ; seuls les panneaux tournent. Faire tourner les points avec les panneaux est l'erreur la plus facile à commettre, et elle change tout.
- **Une tranche ne ressemble pas à un cube.** Pour un cube en fil de fer, les tranches avant et arrière donnent un contour carré, et les huit tranches intermédiaires se réduisent à **quatre points** — les quatre arêtes parallèles à l'axe de rotation. Si tu regardes un seul panneau et que tu n'y vois que quatre points, c'est juste.
- **Le volume est feuilleté en dix plans.** C'est la signature visuelle de la machine. Un cube continu en profondeur serait visiblement faux.

---

## 4. Les formules exactes

**Repère** : origine au centre du volume, x vers la droite, y vers le bas, z vers le spectateur. Tout en centimètres.

**Position d'une LED.** La colonne *k* (de 0 à 159) et la rangée *j* (de 0 à 7) du panneau *s* (de 0 à 9), quand ce panneau est à l'angle θ :

```
d = k − 79,5                 position le long de la barre, en cm
o = j − 3,5                  décalage perpendiculaire de la rangée, en cm
θ = 18° × s + φ              φ = angle de rotation commun

x = d·cos θ − o·sin θ
y = d·sin θ + o·cos θ
z = (4,5 − s) × 10
```

**Chacune des huit rangées doit utiliser son propre `o`.** Sinon le dessin est dédoublé sur 8 cm.

**Faut-il allumer cette LED ?** On ramène le point dans le repère du cube, puis on mesure sa distance aux douze arêtes :

```
q = transposée(R) · (p − centre) / h       R = rotation du cube, h = demi-côté

X, Y, Z    = |q.x|, |q.y|, |q.z|
dx, dy, dz = X−1, Y−1, Z−1
ex, ey, ez = max(0, dx), max(0, dy), max(0, dz)

distance = √( min( ex²+dy²+dz² ,  dx²+ey²+dz² ,  dx²+dy²+ez² ) )

LED allumée  ⟺  distance × h ≤ demi-épaisseur
```

La demi-épaisseur vaut **4 cm** par défaut : les arêtes font donc 8 cm d'épaisseur. C'est volontairement gras — le cube ressemble à un assemblage de boudins lumineux, pas à un fil de fer.

Par symétrie, trois arêtes suffisent : celles qui partent du sommet (1, 1, 1).

**Pourquoi 18° et pas 36°.** Un panneau est une barre diamétrale : il occupe les directions θ **et** θ+180. À 18°, dix panneaux donnent dix directions distinctes réparties sur le demi-tour. À 36°, les panneaux 5 à 9 retombent exactement sur les panneaux 0 à 4 — cinq directions au lieu de dix, l'éventail est cassé.

**Un demi-tour suffit.** Un panneau centré se retrouve sur lui-même après 180°. Pour couvrir tout le volume il faut donc 90 pas de 2°, pas 180.

---

## 5. Si tu simules à l'écran

Pour montrer ce que l'œil perçoit, il faut dessiner **toutes les LED balayées sur un demi-tour** — 90 pas × 10 panneaux × 8 rangées × 160 colonnes = 1 152 000 positions testées — et donner à chacune une luminosité qui dépend de **son âge** :

```
angle_de_persistance = 360° × tours_par_seconde × persistance_en_secondes
age = (rotation_courante − φ_de_la_LED)  replié sur 180°
b   = 1 − age / angle_de_persistance
si b ≤ 0,03 : la LED est ÉTEINTE, ne la dessine pas
couleur = rouge × b
```

Le repli sur 180° et non 360° est ce qui fait que **les deux demi-bras d'un panneau comptent**.

**Attention au réglage de persistance**, c'est là que la simulation ment :

| persistance | angle de persistance | ce qu'on voit |
|---|---|---|
| 0,30 s | **216°**, plus qu'un demi-tour | plus rien ne s'éteint, le cube entier reste allumé en permanence |
| 0,20 s | 144° | un secteur reste éteint : on voit le balayage peindre le cube |
| 0,10 s | 72° | un quart du cube à la fois, proche de l'œil réel |

À 0,30 s on obtient une belle image, mais **on ne voit plus les LED s'allumer et s'éteindre** — et c'est précisément ce que je veux voir. Descends à 0,20 s ou moins.

**Pas de traînée d'écran.** La rémanence se calcule **par point**, à partir de son âge. Un flou de mouvement en deux dimensions donne des arcs baveux, dépend de la cadence d'affichage et s'efface dès qu'on bouge la caméra.

**Dessine aussi les contours des dix panneaux**, un rectangle de 160 × 8 cm à l'angle de chaque panneau et à sa profondeur. Sans eux, on ne sait ni où est l'axe, ni de quel côté on regarde : le nuage de points rouges flotte dans le noir et ne se lit pas. Mets le panneau 0 plus clair que les neuf autres — c'est le seul repère de l'avant de la machine.

---

## 6. Les chiffres qui disent que c'est juste

**Cube fixe**, centré, demi-côté 45 cm, demi-épaisseur 4 cm, décalage 18°, sur un demi-tour :

| Mesure | Valeur attendue |
|---|---|
| LED testées | 1 152 000 |
| LED allumées | **31 424** |
| proportion | 2,73 % |
| répartition | **12 896** sur le panneau 0, **704** sur chacun des huit panneaux intermédiaires, **12 896** sur le panneau 9 |

La répartition par panneau est le contrôle le plus utile : elle attrape les erreurs de repère et de profondeur que le total laisse passer.

Le demi-côté de 45 cm n'est pas arbitraire : c'est `min(79,5/√2 × 0,95 ; 4,5 × 10) = min(53,40 ; 45)`. C'est la **profondeur** qui borne, et les faces avant et arrière du cube tombent exactement sur le panneau 0 et le panneau 9.

**Cube animé**, mêmes réglages : entre **15 207** LED allumées (pose 166) et **34 874** (pose 295), moyenne 27 028. Neuf poses passent sous 20 000 — ce sont celles où le cube est à la fois petit et excentré, et c'est normal.

Si tu trouves 0,5 % ou 8 %, tu as une erreur d'épaisseur, d'échelle ou de repère — pas un problème d'affichage.

---

## 7. La séquence animée

Les 300 poses viennent d'une vidéo analysée image par image. Chaque pose donne le centre du cube, son demi-côté et sa rotation.

- **Une seule échelle pour toute la séquence** : 61,2296 cm par demi-largeur d'image. Ne la recalcule pas pose par pose — cela supprimerait la respiration du cube, qui est la moitié du mouvement perçu.
- **Aucune interpolation à la lecture** : on passe d'une pose à la suivante d'un coup. Toute l'interpolation a déjà été faite en amont (84 des 300 poses sont reconstruites entre leurs voisines).
- Le cube glisse **sur la diagonale**, son côté passe de 26,5 à 47,3 cm (facteur 1,79), et il ne s'approche ni ne s'éloigne jamais.
- La boucle **ne se referme pas** : de la pose 299 à la pose 0, la rotation saute de 42,8°. C'est fidèle, ne le corrige pas.
- Cadence nominale : 30 images par seconde, soit un cycle de 10 secondes.

---

## 8. Ce qu'il ne faut pas faire

- **Modéliser un cube en 3D et le faire tourner devant une caméra.** C'est le contresens central : il n'y a pas de projection, il y a des LED allumées à des positions réelles.
- **Faire tourner les points avec les panneaux.** Ils sont fixes.
- **Oublier le décalage `o` de chaque rangée**, ou le mettre identique pour les huit.
- **Prendre 36° au lieu de 18°.**
- **Utiliser un flou de mouvement d'écran** à la place de la rémanence calculée par point.
- **Laisser la persistance à 0,30 s** et conclure que ça marche parce que l'image est jolie : à cette valeur rien ne s'éteint jamais, donc on ne voit pas le balayage.
- **Calculer la luminosité sur le processeur central à chaque image.** Trente mille valeurs réécrites soixante fois par seconde suffisent à figer un logiciel temps réel. La position et l'angle φ de chaque LED ne dépendent pas du temps : mets-les en cache, et ne recalcule par image que la luminosité, de préférence dans un nuanceur.

---

## 9. Avant de commencer

Dis-moi en quelques lignes ce que tu as compris, en particulier :

1. ce qui tourne et ce qui ne tourne pas ;
2. pourquoi une tranche intermédiaire ne montre que quatre points ;
3. pourquoi 18° et pas 36° ;
4. comment tu comptes vérifier que tu obtiens bien 31 424 LED allumées.

Ensuite seulement, propose-moi un plan. Je te dirai quel logiciel viser et je te fournirai le fichier des 300 poses.
