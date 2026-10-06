# Animation d'un cube 3D pour un afficheur volumétrique à LED

Simulation en JavaScript ([p5.js](https://p5js.org)) d'un afficheur volumétrique à persistance rétinienne : 10 panneaux de 180 × 8 LED, posés à plat, en enfilade le long d'un axe et décalés de 18°, tournent ensemble. Chaque panneau affiche une tranche d'un volume 3D. Le programme joue une animation de 300 cubes 3D retrouvés dans les images du dossier `cube_animatio`.

**Toute l'explication du programme est dans [EXPLICATION.txt](EXPLICATION.txt).**

## Lancer

- Ouvrir `index.html` dans un navigateur (connexion internet nécessaire pour charger p5.js et dat.GUI), ou bien lancer `python3 -m http.server` dans ce dossier et ouvrir http://localhost:8000.
- La simulation démarre toute seule au chargement (et à chaque actualisation) ; le bouton **Arrêter la simulation** la met en pause.
- On peut aussi copier `index.html`, `style.css`, `volumetric3D.js` et `poses_cube_animatio.js` dans un sketch de [l'éditeur p5](https://editor.p5js.org).

## Fichiers

| Fichier | Rôle |
|---|---|
| `index.html` | Page web : charge p5.js 1.6.0, dat.GUI, les poses et le programme |
| `style.css` | Mise en page |
| `volumetric3D.js` | Le programme : géométrie des panneaux, LED à allumer, simulation, exports |
| `poses_cube_animatio.js` | Les 300 poses (position, taille, rotation) des cubes de l'animation |
| `analyse/analyse_cube_animatio.html` | Outil pour recalculer les poses à partir des images |
| `analyse/analyse_cube.js` | Code de l'analyse d'image utilisé par l'outil |
| `cube_animatio/` | Les images `frame_00.png` … `frame_299.png` (seulement utiles pour l'outil d'analyse) |
| `PROMPT_CE_QUE_JE_VEUX_FAIRE.md` | **Le seul prompt du dépôt** : ce que je veux faire, pour une IA qui ne connaît ni le projet ni le logiciel cible (160 × 8 LED, formules, chiffres de contrôle, pièges) |
| `touchdesigner/` | Option « animation-cube » pour le projet TouchDesigner SAISON_9 : installateur à exécuter dans le Textport, mode d'emploi ([touchdesigner/README.md](touchdesigner/README.md)) et vérifications. Ajoute un bouton dans la fenêtre SORTIE_SPECTACLE |
| `SAISON_9_CUBE_ANNEAU_VASARELY_CUBE.toe` | **Le projet prêt à l'emploi** (6 octobre 2026) : animation-cube, cube statique, anneau-cône respirant et grille Vasarely, chacun sur son bouton dans SORTIE_SPECTACLE (un seul maître à la fois) ; CUBE_3D imprime ce que les pales affichent réellement (real_Move, VOLUME BALAYÉ, curseur RÉMANENCE) ; motifs sur les angles rapportés par la Teensy. TouchDesigner en garde des incréments locaux `….N_CUBE.toe`, ignorés par git |
| `SAISON_9_CUBE_ANNEAU_VASARELY.toe` | Version précédente du même projet (cube animé, anneau, Vasarely ; CUBE_3D encore en balayage idéal) |
| `SAISON_9_ANIMATION_CUBE_ET_ANNEAU_CONE.toe` | Version précédente : cube + anneau seulement |
| `SAISON_9_ANIMATION_CUBE.toe` | Version précédente, cube seul (issu de SAISON_9_MOINS_DE_PY_ANNEAUX_SEULS_SANS_VARIATIONS.2) ; sert aussi de sauvegarde d'avant l'anneau |
