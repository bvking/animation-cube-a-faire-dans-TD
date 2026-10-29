# Vitesse de rotation : jusqu'à 5 tours/s

28 octobre 2026 (19 h 54 – 21 h 50) et 29 octobre (13 h 24 – 16 h). Demande de
Benjamin : « Analyse comment fonctionne le curseur de "VITESSE DE ROTATION" dans
l'onglet CHOREGRAPHIE dans le container MOTEURS_TEENSY. Fais en sorte que la
vitesse maximale soit 5 tours/s. Il se peut que la carte Teensy soit programmée
pour que les moteurs n'aillent pas aussi vite, alors il faudra changer le programme
de la Teensy […] normalOrder ».

Le journal détaillé, avec les chiffres et les numéros de ligne, est dans l'autre
dépôt : `Ameliorer controle panneaux rotation TD/commentaires/COMMENT_251_5_TOURS_S_DEPUIS_TD_LES_SEPT_BORNES_LA_LOI_TENUE_ET_F11.txt`
(GitHub : `bvking/panneaux-led-rotatifs`, branche `moins_de_script_Py`).

## En bref

- Le curseur **VITESSE DE ROTATION** va jusqu'à **±5,00 tour/s** (il s'arrêtait à ±2,30).
- Le **pilote** (le programme Python qui parle à la Teensy) accepte 5,00 : sept
  limites ont été levées **ensemble**. En lever une seule ne servait à rien, et
  pouvait même être dangereux (voir plus bas).
- **Sous 2,30, rien ne change** : la carte reçoit le même plafond qu'avant (7840),
  la même accélération, les mêmes gardes. Les bancs d'essai le vérifient.
- **Une porte** : le pilote ne dépasse 2,30 que si la carte annonce le nouveau
  firmware. Avec l'ancien, la rotation s'arrête à 2,30, et TD le dit : la ligne
  Chvmes commence par « PORTE 2,30 », et Chmot explique pourquoi.
- **Appliqué dans TD le 29 octobre à 16 h 21**, moteurs désarmés et lames
  arrêtées, sans rejouer l'installeur (tes réglages Margecouple 0,40 et Accelmax
  304 sont gardés). Projet enregistré sous
  `SAISON_9_CUBE_ANNEAU_VASARELY.11_CUBE_vitesse_5tr_sec.toe`.
- Le **programme de la Teensy** `..._normalOrder` est prêt (version finale du
  29 octobre). Il **n'est pas encore téléversé**. Depuis 14 h 13 aujourd'hui, la
  carte porte la version du 28, avec le moteur 2 sur les broches 10/9.
- **Rien n'a été mesuré au-dessus de 2,37 tour/s.** Le logiciel autorise 5 tour/s ;
  seul un essai dira si les moteurs suivent.

## Comment fonctionne le curseur

1. Le curseur est une **cible**. TouchDesigner l'envoie au pilote, qui tourne dans
   un processus à part (`pilote_processus.py`) et tient seul le port de la Teensy.
2. Le pilote n'y va pas d'un coup : il monte **par crans de 0,10 tour/s**. Il passe
   au cran suivant quand la carte suit le cran à 0,05 près depuis 1,5 s, ou au
   bout de 20 s. (Le libellé disait « 0,05 » : c'était la tolérance, pas le cran.
   C'est corrigé.)
3. Le pilote **réécrit le curseur** : une demi-seconde après ton geste, le curseur
   montre le cran en cours, pas la cible. La cible se lit dans la ligne « Chvmes ».
4. La vitesse commune suit le cran à une **accélération limitée par une loi de
   couple** : pleine jusqu'à 1,95, puis de plus en plus faible (64 pas/s² à 2,00,
   32 à 2,30), et tenue à 32 au-dessus.
5. Quarante fois par seconde, le pilote envoie à la Teensy les dix positions et un
   **plafond de vitesse par moteur** (ABC[20]). La Teensy suit, sans jamais
   dépasser ce plafond.

## Les sept limites, et ce qu'elles deviennent

| # | Limite | Avant | Après |
|---|---|---|---|
| 1 | le curseur (et les lignes « vitesse » des TIMELINES) | ±2,30 | ±5,00 |
| 2 | `Vitessemax`, ce que le pilote accepte de demander | 2,30 | 5,00 |
| 3 | le plafond envoyé à la carte (ABC[20]) | 7840 pas/s = 2,45 tour/s, toujours | **glisse** : 7840 tant que les lames tournent sous 2,30, puis la lame la plus rapide + 0,15 tour/s, jusqu'à 16480 (5,15) |
| 4 | GARDE 16, qui bornait ce plafond **en dur** | 7840 | 16480, et 7840 tant que la carte n'a pas annoncé le nouveau firmware |
| 5 | GARDE 3, le pas maximal entre deux trames | 200 pas = 2,50 tour/s | suit la rotation : 200 pas jusqu'à 2,30 comme avant, 416 au plus à 5,00 |
| 6 | la loi d'accélération au-dessus de 2,30 | tombait à 8 pas/s² : 26 min pour monter, 18 min pour s'arrêter | **tenue** à sa valeur de 2,30 (32 pas/s²) : 8 min pour monter de 0 à 5,00, ~6 min pour s'arrêter |
| 7 | la Teensy | `VMAX_HARD` 16000 = 5,00 pile, sans marge ; la boucle des pas sature vers 4,5 tour/s sur dix moteurs | `VMAX_HARD` 16480 ; **F11** : au-dessus de 2,45, les impulsions d'un même tour partent ensemble (dessous, exactement comme avant) |

**Pourquoi « ensemble » :** en simulation, relever le curseur sans relever GARDE 3
fait prendre de l'avance à la consigne interne. La carte reste à 2,50, puis, après
« vitesse 0 », elle **continue de tourner environ 140 s** avant de s'arrêter d'un coup.

**Pourquoi la loi est « tenue » :** c'est ta règle du 19 septembre : « en haut on
baisse l'accélération, on ne l'augmente jamais, et on la tient constante ».
Au-dessus de 2,30, le pilote ne demande jamais plus que ce qu'il demandait déjà à
2,30. Sous 2,30, rien ne change.

**Pourquoi le plafond glisse :** envoyé à 5,15 tour/s en permanence, il ne
retenait plus rien sous 2,30. Une lame à 1,00 aurait pu être rattrapée jusqu'à
3,7 tour/s, au lieu d'être arrêtée à 2,45. Il suit donc **ce que le pilote
commande** (et non ce que la carte fait : la relecture finale a montré que,
calculé sur la carte, il faisait cliquet et ne retenait plus rien). Il ne passe
jamais sous les lames : un preset ne le baisse plus en rotation, et si tu baisses
le curseur Plafondfigure en rotation, la rotation redescend à l'accélération
permise au lieu d'être coupée d'un coup.

## Ce qui change dans la Teensy (version finale du 29 octobre)

- **F12, le frein sans retour.** Quand les trames s'arrêtent en pleine vitesse
  (DÉSARMER, pilote mort, câble), la carte freinait, dépassait sa dernière cible
  d'une cinquantaine de tours à 5,00, puis **revenait** d'autant en sens inverse,
  jusqu'à 3,6 tour/s. Désormais elle freine jusqu'à l'arrêt **sans revenir**. Au
  banc : 3 pas en arrière au lieu de 53 tours. Elle freine toujours à 800 pas/s² :
  le dépassement d'une cinquantaine de tours reste.
- **F13.** Si personne ne lit le port, la carte n'attend plus jusqu'à 120 ms sans
  faire un pas : elle saute la ligne de compte rendu.
- **La carte dit ce qu'elle accepte** : `vmax_hard=16480` à la fin de sa ligne
  `<BOUCLE ...>`, chaque seconde. C'est la porte du pilote.
- Le moteur 2 reste sur les broches 10 (DIR) / 9 (STEP), comme tu l'as confirmé.

## Autres changements, pour que tout dise la même chose

- **Presets** : un preset ne baisse plus le plafond pendant que les lames tournent.
  Les onze presets enregistrés portent 6976 (2,18 tour/s). Quand le plafond baisse,
  la carte coupe **aussitôt** la vitesse des moteurs, sans rampe.
- **Sens négatif** : les crans « en accord » ne marchaient pas en marche arrière. La
  consigne sautait de 0 à −2,30 en 0,6 s sans attendre la carte. C'est corrigé :
  −2,20 à 60 s, comme +2,20.
- **Mesure** : les vitesses mesurées (real_Move, bandeau) restaient bloquées à
  2,999 au-dessus de 3 tour/s. Elles suivent maintenant le plafond. Le témoin
  « vitesse max » passe au ROUGE quand la carte colle à son plafond, et dit
  HORS MESURE au-dessus de 2,37.
- **Timelines** : vitesse jusqu'à 5,00, durée des montées au-dessus de 2,30 (150 s
  par tour/s), échelle de la ligne MESURE à 5,2.
- **Journal** : l'anomalie de vitesse commence au-dessus de 5,00. L'arrêt après FIN
  a plus de temps au-dessus de 2,30.
- **CUBE_3D** (ce dépôt, `touchdesigner/INSTALLER_CUBE_3D.py`) : avec « motifs sur
  les angles réels », à 5 tour/s la lame avance de 180° entre deux positions de la
  Teensy, et l'arc s'imprimait à l'envers. Le nuanceur retient maintenant le sens
  de chaque lame. En émulation : 2802 arcs sur 3000 à l'envers avant, 0 après.

## Ce que tu dois faire maintenant, dans l'ordre

0. **Fermer le moniteur série de l'IDE Arduino.** Il tient le port de la Teensy en
   même temps que le pilote (règle du dépôt : un seul programme à la fois).
1. **Recharger le croquis dans l'IDE avant toute sauvegarde.** L'éditeur de l'IDE
   garde peut-être le texte de 14 h 13 : l'enregistrer écraserait la version finale.
   Le plus sûr : fermer l'onglet et rouvrir le croquis.
2. **Téléverser la version finale**, lames libres, personne autour. Le croquis est
   `~/Documents/Arduino/hardware/WiFi_Kit_series/motor_positions_figures_MAX_or_TD_sens_inverse_normalOrder/`.
   Il faut d'abord libérer le port. **Fermer TD ne suffit pas** : le processus du
   pilote lui survit et garde le port. Dans TD : décocher `Fildedie` (le processus
   s'arrête), **puis** désactiver le serialDAT `MOTEURS_TEENSY/lien` (sinon TD
   reprend le port). Si TD est déjà fermé : `pgrep -f pilote_processus.py`, puis
   arrêter ce processus (il est désarmé).
   **Au redémarrage, les dix lames font un tour** (le tour de démarrage). Le repère
   du haut est ensuite à rétablir.
3. **Lire la bannière** : `<FIRMWARE ..._normalOrder -- 5 tours/s, F12 F13 -- 29 octobre 2026>`,
   `<VMAX_HARD 16480 ...>`, `<F12 FREIN SANS RETOUR ON ...>`, `<F13 ENVOIS SANS ATTENTE ON ...>`.
   Dans TD, tant que la carte n'a pas annoncé `vmax_hard=16480`, Chvmes commence
   par « PORTE 2,30 », Chmot dit pourquoi, et les crans s'arrêtent à 2,30. Après le
   téléversement, réactiver `lien`, recocher `Fildedie`, puis ARMER : « PORTE 2,30 »
   doit disparaître dans la seconde.
4. **Moteurs hors tension d'abord** : monter par paliers 2,5 / 3 / 4 / 5 en lisant la
   ligne `<BOUCLE it/s= moy_us= max_us= vmax_hard=>`. La boucle doit faire nettement
   plus de 16 480 tours par seconde à 5,00.
5. **Puis sous tension**, une lame montée, un palier par « go ». Fais un nombre
   entier de tours et vérifie à l'arrêt que la lame revient à son repère. Garde une
   coupure physique de l'alimentation des drivers à portée de main.

## Ce que ce changement ne garantit pas — à lire avant d'essayer

- **Un décrochage ne se voit pas** : la Teensy compte les pas qu'elle envoie, pas
  ceux que l'axe fait. La seule preuve est la lame qui revient à son repère.
- Le dépôt a mesuré un **« plafond pratique moteur ≈ 2,4 tour/s »**, et rien n'a
  été émis sans perte au-dessus de 2,37. À grande vitesse, le couple que le moteur
  peut donner s'effondre, et la traînée de l'air croît comme le carré de la vitesse.
- À 5 tour/s, une lame de 1,60 m va à **~90 km/h en bout** (42 km/h à 2,30). Elle
  stocke ~42 J, 4,7 fois plus qu'à 2,30, et tire ~79 N sur son moyeu ; ce qui est
  fixé en bout de lame subit ~80 g. **Personne dans le plan des lames.**
- **L'arrêt depuis 5,00 prend environ 6 minutes** (ARRÊT, FIN).
- **Ne jamais DÉSARMER en rotation rapide.** Plus aucune consigne ne part, et la
  Teensy freine seule, à 800 pas/s² : 25 fois l'accélération tenue. À 5,00, la lame
  dépasse sa cible d'une cinquantaine de tours, avec un décrochage probable. Avec
  F12 elle ne revient plus ; sans F12 (le firmware actuellement dans la carte),
  elle revient jusqu'à près de 3,6 tour/s. Même effet si une garde désarme ou si les
  trames s'arrêtent. **Pour s'arrêter : ARRÊT ou FIN.**
- **Ne pas relancer l'installeur, ni rouvrir TD, lames en rotation** : le processus
  du pilote est relancé aussitôt, sans trame de gel.
- **ARMER est refusé tant qu'une lame tourne** (Chmot : « ARMER REFUSÉ … ») : après
  un désarmement à 5,00, la carte freine seule ~21 s, et réarmer pendant ce
  freinage faisait repartir les lames en arrière.
- **La carte porte aujourd'hui la version du 28** (téléversée à 14 h 13) : F11 y
  agit à toutes les vitesses, même sous 2,45 (train d'impulsions jamais mesuré), et
  ni F12 ni F13. Avec TD, la porte la garde à 2,30. Téléverser la version finale
  remet sous 2,45 exactement les impulsions d'avant.
- **La marge au-dessus de 5,00 est petite** (0,15 tour/s, 3 %) : à 5,00, il ne
  reste presque rien pour les figures (hélices, rangs), et la rotation leur cède.
- **À décider par toi** : faut-il qu'un désarmement en rotation devienne un ARRÊT ?
  Faut-il que la carte date les trames à leur arrivée (à 5,00, elle court jusqu'à
  ~3 tours devant la consigne au banc) ? L'arrêt d'urgence ne freine pas en mode
  figure.
- **L'image** : les rubans LED font environ 26 images par seconde. À 5 tour/s,
  chaque image balaie 69° du tour (32° à 2,30) : le volume se peint par secteurs
  plus larges.

## Où sont les fichiers

| Quoi | Où |
|---|---|
| Le pilote et la page Chorégraphie | `Ameliorer controle panneaux rotation TD/choregraphie_reelle/INSTALLER_CONTAINER_TEENSY.py` (et `pilote_en_fil.py`) |
| Timelines / journal | `AgencementdesLumieres/INSTALLER_TIMELINES.py`, `choregraphie_reelle/INSTALLER_JOURNAL_EVENEMENTS.py` |
| Le firmware final | `~/Documents/Arduino/hardware/WiFi_Kit_series/motor_positions_figures_MAX_or_TD_sens_inverse_normalOrder/` ; copie dans `teensy/motor_positions_figures_MAX_or_TD_sens_inverse_normalOrder/` du dépôt panneaux |
| Ce que porte la carte depuis le 29 oct. 14 h 13 | `teensy/motor_positions_figures_MAX_or_TD_sens_inverse_normalOrder_flashe_29oct_14h13/` du dépôt panneaux |
| Le firmware du 28 oct. 17 h 46 | `teensy/motor_positions_figures_MAX_or_TD_sens_inverse/` du dépôt panneaux |
| CUBE_3D | `touchdesigner/INSTALLER_CUBE_3D.py` (ce dépôt) |
| Le projet TD | `SAISON_9_CUBE_ANNEAU_VASARELY.11_CUBE_vitesse_5tr_sec.toe` (ce dépôt) |

## Vérifié sans matériel

- 38 bancs d'essai du pilote, avant et après : les mêmes résultats, sauf les
  contrôles qui verrouillaient exprès 7840 et 2,30, mis à jour. GARDE 16 :
  50 contrôles, dont 14 sur le plafond glissant et la porte. Timelines : 182 ;
  journal : 52.
- La montée simulée, avec le vrai pilote et la carte simulée : 5,00 atteint en
  480 s, les dix moteurs à 0,02 près, le plafond montant de 7840 à 16480 avec les
  lames ; −5,00 pareil ; 2,30 en 75 s avec le plafond à 7840 tout du long, comme
  avant ; sans l'annonce de la carte, arrêt à 2,30.
- Le firmware final compile : 0 erreur, 0 avertissement. Au banc (simulation) :
  16 000 pas/s à 5,00 ; sous 2,45, le train d'impulsions est identique au bit à
  celui d'avant ; F12 supprime le retour ; F13 supprime l'arrêt de 121 ms.
- Une relecture indépendante en deux temps (le 28 au soir, puis le 29 sur la
  version finale), chaque constat vérifié par un second agent. La relecture finale
  a trouvé le défaut du « cliquet » ; corrigé, les scénarios du relecteur donnent
  des trames **identiques au bit** à l'ancien code sous 2,30 (console en essai haut,
  TD 0 → 2,30, figures à 1,00 / 1,85 / 2,20 / 2,30, rattrapage de 14,7 tours).
- Dans TD, sans moteur : curseur posé à 3,00 → ramené à 2,30 par la porte, et le
  message arrive dans Chmot ; aucune erreur dans TIMELINES, JOURNAL, CUBE_3D.
- Le juge du timecode : « en défaut » avant comme après le changement (TD dans
  l'éditeur à 10-16 images/s, Chrome au premier plan par moments) ; pas de
  dégradation : 9,7-11,6 images/s avant, 12,4-16,1 après.
