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

### L'animation s'adapte à n'importe quelle vitesse de rotation

Une lame ne peint sa tranche qu'en passant dessus : il lui faut un demi-tour.
Par défaut (`Modehorloge = rotation`), l'image de l'animation n'avance donc
que d'**une image par demi-tour réellement balayé** — compté en déroulant
l'angle réel de la lame 0 (même source que les motifs, consigne ou Teensy).
Résultat : chaque tranche est toujours peinte d'une **seule** pose cohérente,
que la rotation soit lente, rapide, variable ou inversée ; à l'arrêt des
moteurs, l'animation s'arrête (rien n'est balayé). À 2 tours/s, la boucle des
300 images dure 75 s ; `Imagespardemitour` accélère ou ralentit ce couplage
(au-delà de 1, le mélange de poses revient). Le mode `temps` (30 images/s,
comme la simulation p5) reste disponible pour prévisualiser.

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

- `INSTALLER_ANIMATION_CUBE.py` — installe (ré-exécutable sans danger)
- `DESINSTALLER_ANIMATION_CUBE.py` — retire tout et restaure les expressions
  d'origine (depuis `ANIMATION_CUBE/sauvegarde`)

Au Textport, `desinstaller()` (après avoir exécuté l'installateur dans la
session) fait la même chose. Enregistrer sous ensuite.

## Ce qui a été vérifié avant livraison

- Les formules portées (positions des LED, échelle, pose, distance aux arêtes,
  exports) reproduisent les **20 valeurs de contrôle** du prompt
  (`PROMPT_TouchDesigner_afficheur.md`, partie 5) — voir
  `touchdesigner/verification/test_controle.py` (python3 + numpy, exécutable hors
  TouchDesigner) : positions au 1/1000, L = 61.2296, h₀ = 16.9055, comptes de
  LED exacts (cube fixe 62 848 ; images 0/1/100/150/299), ordre des octets.
- Les conventions du projet ont été lues dans le `.toe` lui-même (via
  `toeexpand`) : switch `panel_mask_output` et son expression, format 160 × 80
  en bandes `vertbt`, angles en degrés par `angles_top`, chaîne du simulateur
  et du rendu 3D (`rubans_choix` entrée 2), palette et style des boutons de
  `PANNEAU_COMMANDES`.
- La table embarquée dans l'installateur redonne L et h₀ exacts en python pur.

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
