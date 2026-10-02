# Animation d'un cube 3D pour un afficheur volumétrique à LED

Simulation en JavaScript ([p5.js](https://p5js.org)) d'un afficheur volumétrique à persistance rétinienne : 10 panneaux de 180 × 8 LED, posés à plat, en enfilade le long d'un axe et décalés de 18°, tournent ensemble. Chaque panneau affiche une tranche d'un volume 3D. Le programme joue une animation de 300 cubes 3D retrouvés dans les images du dossier `cube_animatio`.

**Toute l'explication du programme est dans [EXPLICATION.txt](EXPLICATION.txt).**

## Lancer

- Ouvrir `index.html` dans un navigateur (connexion internet nécessaire pour charger p5.js et dat.GUI), ou bien lancer `python3 -m http.server` dans ce dossier et ouvrir http://localhost:8000.
- Cliquer sur **Démarrer la simulation**.
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
| `cube_animatio/` | Les images `frame_00.png` … `frame_299.png` (à ajouter ; seulement utiles pour l'outil d'analyse) |
