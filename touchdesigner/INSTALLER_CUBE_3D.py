# ============================================================================
# INSTALLER_CUBE_3D -- le cube COMPLET, en volume, comme le montre le simulateur p5
#
# A executer le projet SAISON_9 ouvert, APRES INSTALLER_ANIMATION_CUBE :
#   exec(open('.../touchdesigner/INSTALLER_CUBE_3D.py').read())
# REJOUABLE : relancer met a jour au lieu de creer un doublon.
#
# ----------------------------------------------------------------------------
# POURQUOI CE MODULE EXISTE, ALORS QU'ANIMATION_CUBE CALCULE DEJA LE CUBE
#
# ANIMATION_CUBE calcule UN INSTANT : les 12 800 LED des dix lames a l'angle
# qu'elles ont maintenant. C'est exactement ce qu'il faut pour PILOTER les
# panneaux -- une image, un instant, 160 x 80 pixels qui partent aux ports
# 9101-9110. Sa fidelite a volumetric3D.js est verifiee au texel pres.
#
# Mais a l'ECRAN cet instant ne ressemble a rien : dix segments. Le cube
# n'existe que dans l'oeil, qui integre un demi-tour. Le rendu 3D du projet
# tentait de le rattraper avec une trainee d'ECRAN (TRAINEES_LUMIERE) : un
# flou de mouvement en deux dimensions, qui bave, qui brule quand on
# s'approche, et qui s'efface des qu'on bouge la camera.
#
# Le simulateur p5, lui, ne fait rien de tel. processVolume() parcourt les
# QUATRE-VINGT-DIX pas de rafraichissement d'un demi-tour, garde toutes les
# LED allumees avec l'angle phi auquel elles l'etaient, et les dessine
# ENSEMBLE a leur position reelle dans l'espace. Chaque point porte sa propre
# luminosite, b = 1 - age / angle_de_persistance. Rien ne bouge a l'ecran :
# les points sont FIXES, seule leur luminosite varie. C'est pour ca que son
# cube est net, stable, et qu'on peut tourner autour.
#
# Ce module fait la meme chose dans TouchDesigner.
#
# ----------------------------------------------------------------------------
# LES REGLES REPRISES DE volumetric3D.js, ET LEUR SOURCE
#
#   90 pas de 2 degres          :53 et :370-373  un DEMI-tour suffit, une lame
#                                                centree se retrouve sur
#                                                elle-meme a 180 degres
#   decalage 18 degres par lame :86-88           panelOffset(s) = s * PI / 10.
#                                                PAS 36 : une lame est une barre
#                                                DIAMETRALE, elle occupe les
#                                                directions t ET t+180. A 36 les
#                                                lames 5 a 9 retombent sur 0 a 4
#                                                -- cinq directions au lieu de
#                                                dix, l'eventail est casse.
#   z = (4.5 - s) * ecart       :91-93           lame 0 devant, cote spectateur
#   d = (k - 79.5) cm           :96-103          ici 160 colonnes et non 180 :
#                                                c'est la chaine LED du projet
#   o = (j - 3.5) cm            :96-103          CHAQUE rangee a son decalage,
#                                                sinon le dessin est dedouble
#                                                sur 8 cm
#   x = d cos t - o sin t       :377-382
#   allumee si distance aux
#   12 aretes * h <= epaisseur  :296-303 et :352
#   b = 1 - age / persistAngle  :55 et :556-564  age = (rotation - phi) mod 180
#   persistAngle = 360 * t/s
#                      * persist                 216 degres par defaut. 216 > 180
#                                                donc b reste >= 0,167 : RIEN NE
#                                                S'ETEINT, le volume entier est
#                                                visible en permanence avec un
#                                                secteur clair qui tourne.
#   13 paliers de rouge         :566-577         round(c * b / 17) * 17. Un
#                                                degrade lisse se verrait tout
#                                                de suite comme different.
#   rouge pur sur noir pur      :337 et :503
#
# LE CUBE N'EST PAS RECALCULE ICI. La pose -- centre, demi-cote, rotation --
# est lue dans ANIMATION_CUBE/pose, le meme Script CHOP qui alimente le GLSL
# des panneaux. Les deux montrent donc le MEME cube, par construction : il n'y
# a pas deux implementations qui pourraient diverger.
# ============================================================================

RACINE = '/project1/scale'
CM_PAR_UNITE = 160.0   # la lame fait 160 cm et le SOP du rig 1,000 unite

CODE_VOXELS = r'''# Les LED allumees d'un DEMI-TOUR, a leur position reelle dans l'espace.
#
# Sortie : un echantillon par LED allumee, canaux tx ty tz (en UNITES de scene)
# et r g b (la luminosite deja quantifiee en 13 paliers).
#
# ----------------------------------------------------------------------------
# COMMENT ON EVITE DE CALCULER UN MILLION DE DISTANCES PAR IMAGE
#
# Il y a 90 pas x 10 lames x 8 rangees x 160 colonnes = 1 152 000 LED a tester.
# La version naive calcule pour chacune sa position (x, y) dans le volume, puis
# la ramene dans le repere du cube : treize multiplications par LED.
#
# ON REPLIE LA ROTATION DE LA LAME DANS LA MATRICE DU CUBE. La position d'une
# LED est p = Rz(theta) (d, o, 0) + (0, 0, z), et le test porte sur
# q = transposee(R) (p - centre) / h. En developpant :
#
#     q_x h = d (r0 cos + r3 sin) + o (r3 cos - r0 sin)
#             + (r6 (z - cz) - r0 cx - r3 cy)
#
# Les deux coefficients ne dependent que de (pas, lame) -- 900 valeurs -- et le
# terme constant que de la lame. Il reste DEUX multiplications par composante
# au lieu de treize au total, et surtout on ne materialise JAMAIS x et y pour
# le million de LED : on ne les calcule que pour les 30 000 retenues, a la fin.
#
# TROIS CACHES, parce que les trois couts sont tres differents :
#   la GRILLE (cosinus, sinus, d, o, z) ne depend que du rig et de l'helice ;
#   le MASQUE ne depend que de la POSE du cube ;
#   la LUMINOSITE depend du temps, mais ne porte que sur les LED retenues.
#
# REJET RAPIDE AVANT LE TEST COMPLET : dans le repere du cube reduit, un point
# ne peut etre allume que si |q| <= racine(3) + epaisseur/h -- la demi-diagonale
# plus l'epaisseur. Cinq operations qui en epargnent quinze sur 97 % des LED.

import numpy

NP, NJ, NC = 10, 8, 160       # lames, rangees, colonnes

#  LES CACHES VIVENT DANS LE MODULE, PAS DANS LE STORAGE DU COMP.
#  comp.store() est ENREGISTRE dans le .toe : y ranger dix-huit megaoctets de
#  tableaux numpy a fait passer le projet de 1,0 a 9,2 Mo, pour des valeurs
#  entierement recalculables en quinze millisecondes. Un dictionnaire de module
#  est remis a zero au chargement et ne pese rien sur le fichier.
_CACHE = {}


def _grille(comp, pas, ecart, helice):
    #  phi va de 0 a 180 degres : un DEMI-tour. Une lame centree se retrouve
    #  sur elle-meme apres 180 degres, le reste serait du travail en double.
    cle = (int(pas), round(ecart, 6), round(helice, 6))
    if _CACHE.get('grille_cle') == cle:
        return _CACHE['grille_val']
    demi = pas // 2 if pas % 2 == 0 else pas
    phi = numpy.arange(demi, dtype=numpy.float32) * (360.0 / pas)
    lame = numpy.arange(NP, dtype=numpy.float32)
    th = numpy.radians(phi[:, None] + helice * lame[None, :])
    val = (phi,
           numpy.cos(th).astype(numpy.float32),
           numpy.sin(th).astype(numpy.float32),
           (numpy.arange(NC, dtype=numpy.float32) - (NC - 1) / 2.0),
           (numpy.arange(NJ, dtype=numpy.float32) - (NJ - 1) / 2.0),
           ((4.5 - lame) * ecart).astype(numpy.float32))
    _CACHE['grille_cle'] = cle
    _CACHE['grille_val'] = val
    return val


def _masque(comp, gr, pose, w):
    #  La cle inclut l'identite de la grille : changer l'helice ou l'ecart
    #  deplace toutes les LED, le masque precedent ne vaut plus rien.
    cle = (tuple(round(v, 6) for v in pose), round(w, 6), id(gr))
    if _CACHE.get('masque_cle') == cle:
        return _CACHE['masque_val']
    phi, co, si, d, o, z = gr
    cx, cy, cz, h = pose[0], pose[1], pose[2], pose[3]
    R = pose[4:13]
    q = []
    for i in range(3):
        a, b, c = R[i], R[i + 3], R[i + 6]
        A = (a * co + b * si)[:, :, None, None]
        B = (b * co - a * si)[:, :, None, None]
        C = (c * (z - cz) - a * cx - b * cy)[None, :, None, None]
        q.append((A * d[None, None, None, :] + B * o[None, None, :, None] + C) / h)
    qx, qy, qz = q
    #  rejet rapide dans le repere reduit : au-dela de la demi-diagonale plus
    #  l'epaisseur, la LED est forcement eteinte.
    portee = (3.0 ** 0.5) + w / h
    ix = numpy.flatnonzero((qx * qx + qy * qy + qz * qz) <= portee * portee)
    if ix.size == 0:
        garde = ix
    else:
        ax = numpy.abs(qx.ravel()[ix]) - 1.0
        ay = numpy.abs(qy.ravel()[ix]) - 1.0
        az = numpy.abs(qz.ravel()[ix]) - 1.0
        ex, ey, ez = (numpy.maximum(ax, 0.0), numpy.maximum(ay, 0.0),
                      numpy.maximum(az, 0.0))
        d2 = numpy.minimum(numpy.minimum(ex * ex + ay * ay + az * az,
                                         ax * ax + ey * ey + az * az),
                           ax * ax + ay * ay + ez * ez)
        garde = ix[d2 <= (w / h) * (w / h)]
    #  LES POSITIONS AVEC LE MASQUE. Elles ne dependent que de la pose, pas du
    #  temps : les recalculer a chaque image reviendrait a refaire, soixante
    #  fois par seconde, un travail dont le resultat ne bouge pas. Seule la
    #  LUMINOSITE change d'une image a l'autre.
    k = garde % NC
    j = (garde // NC) % NJ
    lame = (garde // (NC * NJ)) % NP
    pas = garde // (NC * NJ * NP)
    dk, oj = d[k], o[j]
    c_, s_ = co[pas, lame], si[pas, lame]
    val = (dk * c_ - oj * s_, dk * s_ + oj * c_, z[lame], phi[pas])
    _CACHE['masque_cle'] = cle
    _CACHE['masque_val'] = (garde, val)
    return garde, val


def onCook(scriptOp):
    scriptOp.clear()
    comp = parent()
    src = comp.par.Posesrc.eval()
    if src is None:
        return
    pose = [float(src[n]) for n in ('cx', 'cy', 'cz', 'h',
                                    'r0', 'r1', 'r2', 'r3', 'r4',
                                    'r5', 'r6', 'r7', 'r8')]
    if pose[3] <= 0.0:
        return
    gr = _grille(comp, int(comp.par.Rafraichissements),
                 float(comp.par.Ecartcm), float(comp.par.Ecarthelice))
    phi, co, si, d, o, z = gr
    garde, (X, Y, Z, PHI) = _masque(comp, gr, pose, float(comp.par.Epaisseur))
    n = int(garde.size)
    comp.store('nb_allumees', n)
    if n == 0:
        return

    #  LA LUMINOSITE, exactement comme volumetric3D.js:556-577.
    #  age = (rotation - phi) replie sur 180 degres : l'angle parcouru depuis le
    #  dernier passage d'un demi-bras. Le repli sur 180 et non 360 est ce qui
    #  fait que les DEUX demi-bras d'une lame comptent.
    #  LE TEMPS NE RENTRE ICI QUE SI ON LE DEMANDE. Lire absTime rend le Script
    #  CHOP DEPENDANT DU TEMPS : TouchDesigner le recuit alors a CHAQUE image,
    #  sur le fil principal, pour quinze millisecondes de numpy -- plus trente
    #  mille instances a dessiner. Le fil sature et l'editeur ne repond plus ;
    #  c'est arrive, et il a fallu redemarrer TouchDesigner.
    #  Decoche (le defaut) : la phase est un simple parametre, le CHOP ne cuit
    #  que lorsque la POSE change. Un cube fixe ne coute alors plus rien.
    #  Coche : la remanence tourne pour de bon, au prix d'une cuisson par image.
    tours = float(comp.par.Toursparseconde)
    if comp.par.Remanenceanimee:
        rot = (absTime.seconds * tours * 360.0) % 360.0
    else:
        rot = float(comp.par.Phaseremanence) % 360.0
    pa = max(1e-6, 360.0 * tours * float(comp.par.Persistance))
    b = numpy.clip(1.0 - numpy.mod(rot - PHI, 180.0) / pa, 0.0, 1.0)
    #  13 paliers : round(c b / 17) * 17 sur 0..255. Un degrade lisse se verrait
    #  tout de suite comme different de l'original.
    rouge = (numpy.round(255.0 * b / 17.0) * (17.0 / 255.0)).astype(numpy.float32)

    #  QUATRE CANAUX, PAS SIX. Le vert et le bleu valaient zero pour les trente
    #  mille LED, a chaque image : deux tableaux ecrits pour rien. Le ROUGE est
    #  declare une fois pour toutes dans le materiau (1, 0, 0) et la luminosite
    #  multiplie les trois composantes -- rouge x (b, b, b) = (b, 0, 0).
    #  On fixe numSamples AVANT d'ajouter les canaux : sinon chaque canal est
    #  cree a un echantillon puis redimensionne.
    e = numpy.float32(1.0 / float(comp.par.Cmparunite))
    scriptOp.numSamples = n
    for nom, val in (('tx', X * e), ('ty', Y * e), ('tz', Z * e), ('r', rouge)):
        scriptOp.appendChan(nom).vals = val.astype(numpy.float32)
    scriptOp.rate = me.time.rate
    return
'''

scale = op(RACINE)
anim = scale.op('ANIMATION_CUBE')
if anim is None or anim.op('pose') is None:
    raise RuntimeError("ANIMATION_CUBE/pose absent : lancer d'abord "
                       "INSTALLER_ANIMATION_CUBE.")

cv = scale.op('CUBE_3D')
if cv is None:
    cv = scale.create(baseCOMP, 'CUBE_3D')
    cv.nodeX, cv.nodeY = anim.nodeX, anim.nodeY - 260
cv.comment = ("Le cube COMPLET : les 90 pas de rafraichissement d'un demi-tour "
              "dessines ensemble, chaque point a sa luminosite. L'equivalent de "
              "processVolume() du simulateur p5. ANIMATION_CUBE, lui, ne calcule "
              "qu'un INSTANT -- c'est lui qui pilote les panneaux.")


def enfant(parent_, nom, type_op, x, y):
    o = parent_.op(nom)
    if o is None:
        o = parent_.create(type_op, nom)
        if o.name != nom and parent_.op(nom) is None:
            o.name = nom
        o.nodeX, o.nodeY = x, y
    return o


# --- les reglages, tous repris du simulateur -------------------------------
pg = None
for p in cv.customPages:
    if p.name == 'Volume':
        pg = p
if pg is None:
    pg = cv.appendCustomPage('Volume')
deja = [q.name for q in pg.pars]

REGLAGES = (
    ('Posesrc', 'op', 'Pose du cube (CHOP)', None, None, None,
     "D'ou vient la pose : ANIMATION_CUBE/pose. Le cube n'est pas recalcule "
     "ici -- les deux modules montrent le meme, par construction."),
    ('Rafraichissements', 'int', 'Rafraichissements par tour', 180, 20, 720,
     "180 dans le simulateur, soit un pas de 2 degres. On n'en calcule que la "
     "MOITIE : une lame centree se retrouve sur elle-meme a 180 degres."),
    ('Ecarthelice', 'float', 'Ecart entre lames (deg)', 18.0, 0.0, 36.0,
     "L'angle qui separe deux lames voisines. 18 = 180/10, la valeur de "
     "volumetric3D.js:86-88 : une lame est une barre DIAMETRALE, elle occupe "
     "les directions t ET t+180, donc dix lames a 18 degres donnent dix "
     "directions distinctes reparties sur le demi-tour. A 36 les lames 5 a 9 "
     "retombent exactement sur les lames 0 a 4 : cinq directions au lieu de "
     "dix, l'eventail est casse et la moitie du volume n'est plus balayee."),
    ('Epaisseur', 'float', 'Demi-epaisseur aretes (cm)', 4.0, 1.0, 10.0,
     "4 cm dans le simulateur, donc des aretes de 8 cm. C'est 2,9 fois plus "
     "epais que le trait des images d'origine : un choix, pas une mesure."),
    ('Ecartcm', 'float', 'Ecart entre panneaux (cm)', 10.0, 1.0, 30.0,
     "La profondeur de la lame s vaut (4,5 - s) fois cet ecart."),
    ('Toursparseconde', 'float', 'Tours par seconde', 2.0, 0.5, 20.0,
     "Ne fait pas tourner les points -- ils sont FIXES. Ne sert qu'a dater "
     "leur luminosite."),
    ('Persistance', 'float', 'Persistance de l oeil (s)', 0.3, 0.02, 1.0,
     "0,3 s dans le simulateur. A 2 tours/s cela fait 216 degres de "
     "persistance, donc PLUS qu'un demi-tour : rien ne s'eteint jamais, le "
     "volume entier reste visible avec un secteur clair qui tourne. Descendre "
     "a 0,1 s ne laisserait qu'un secteur de 70 degres -- un balayage."),
    ('Remanenceanimee', 'toggle', 'Faire tourner la remanence', 0, 0, 1,
     "Decoche, le Script CHOP ne cuit que quand la pose change : un cube fixe "
     "ne coute plus rien par image. Coche, il lit l'horloge et se recalcule a "
     "CHAQUE image -- quinze millisecondes de numpy sur le fil principal, plus "
     "trente mille instances a dessiner. A n'allumer que pour voir tourner le "
     "secteur clair, et pas en meme temps que le reste du spectacle."),
    ('Phaseremanence', 'float', 'Phase de la remanence (deg)', 0.0, 0.0, 360.0,
     "La position du secteur clair quand la remanence ne tourne pas. Sans "
     "effet si « Faire tourner la remanence » est coche."),
    ('Tailleled', 'float', 'Taille d une LED (cm)', 1.5, 0.5, 5.0,
     "Diametre de la bille dessinee a l'endroit de chaque LED."),
    ('Cmparunite', 'float', 'Centimetres par unite de scene', CM_PAR_UNITE,
     80.0, 320.0,
     "Le rig du projet mesure 1,000 unite pour une lame de 160 cm. Les "
     "positions sont calculees en CENTIMETRES puis divisees par ce nombre."),
)
for nom, genre, label, defaut, mini, maxi, aide in REGLAGES:
    if nom in deja:
        continue
    if genre == 'op':
        q = pg.appendOP(nom, label=label)[0]
    elif genre == 'toggle':
        q = pg.appendToggle(nom, label=label)[0]
        q.default = bool(defaut)
        q.val = bool(defaut)
    elif genre == 'int':
        q = pg.appendInt(nom, label=label)[0]
        q.default = defaut
        q.val = defaut
        q.normMin, q.normMax = mini, maxi
    else:
        q = pg.appendFloat(nom, label=label)[0]
        q.default = defaut
        q.val = defaut
        q.normMin, q.normMax = mini, maxi
    q.help = aide
if not cv.par.Posesrc.eval():
    cv.par.Posesrc = anim.op('pose')

# --- le nuage de LED allumees ----------------------------------------------
cb = enfant(cv, 'voxels_callbacks', textDAT, -400, 0)
cb.text = CODE_VOXELS
vox = enfant(cv, 'voxels', scriptCHOP, -150, 0)
vox.par.callbacks = cb
vox.comment = ("Un echantillon par LED allumee du demi-tour : tx ty tz en "
               "unites de scene, r g b deja quantifies en 13 paliers.")

# --- la bille dessinee a l'endroit de chaque LED ----------------------------
#  Elle vit DANS la geometrie. Un selectSOP qui serait allee la chercher
#  dehors marche pour les mesures mais pas pour le rendu : on mesure alors un
#  rayon et on en voit un autre.
mat = enfant(cv, 'constant1', constantMAT, -150, -340)
#  ROUGE PUR sur NOIR PUR (volumetric3D.js:337 et :503). La luminosite arrive
#  par la couleur d'instance, qui MULTIPLIE celle-ci.
mat.par.colorr, mat.par.colorg, mat.par.colorb = 1.0, 0.0, 0.0

#  LE PIEGE QUI M'A COUTE UNE HEURE. Un geometryCOMP tout neuf n'est PAS
#  vide : TouchDesigner 2025 y depose un torusPOP nomme torus1, rendu par
#  defaut, d'un rayon de 1 unite. On voit donc un gros tore rouge a la place
#  du nuage, et -- le pire -- sa taille ne reagit a AUCUN reglage de la
#  sphere, ce qui envoie chercher le defaut partout sauf la ou il est.
#  Un inventaire qui filtre sur isSOP ne le voit pas : un POP n'est pas un SOP.
#  On ne le DETRUIT pas (c'est l'enfant par defaut du COMP), on eteint son
#  drapeau de rendu.
geo = enfant(cv, 'geo_voxels', geometryCOMP, 100, 0)
for _d in geo.children:
    if getattr(_d, 'render', False) and _d.name not in ('bille',):
        _d.render = False
geo.par.instancing = True
geo.par.instanceop = vox
geo.par.instancetx, geo.par.instancety, geo.par.instancetz = 'tx', 'ty', 'tz'
geo.par.instancecolorop = vox
#  le meme canal sur les trois composantes : il ne porte qu'une luminosite
geo.par.instancer, geo.par.instanceg, geo.par.instanceb = 'r', 'r', 'r'
geo.par.instancecolormode = 'multiply'
geo.par.material = mat
for n in ('tx', 'ty', 'tz'):
    getattr(geo.par, n).val = 0.0

bille = enfant(geo, 'bille', sphereSOP, 0, 0)
bille.par.type = 'poly'                 # une vraie maille, pas une primitive
bille.par.rows, bille.par.cols = 3, 4   # 8 triangles : il y en a des dizaines
#  de milliers, et chacune ne couvre que deux pixels a l'ecran.
for _n in ('radx', 'rady', 'radz'):
    getattr(bille.par, _n).expr = ("parent(2).par.Tailleled / "
                                   "parent(2).par.Cmparunite / 2")
bille.render = True
bille.comment = "Une LED. Instanciee autant de fois qu'il y en a d'allumees."


# --- la vue : la camera du simulateur, au cadrage du simulateur -------------
#  volumetric3D.js:530-531 pose la vue de base a rotateX(-0.35) puis
#  rotateY(0.6) radians, soit -20,05 et +34,38 degres. On la reproduit en
#  coordonnees spheriques autour du centre, lookat au centre : l'orientation
#  suit toute seule et la vue ne peut pas se perdre.
#  :532 cadre le disque a 84 % de la plus petite dimension de la fenetre.
#  La silhouette du rig vue sous cet angle fait 1,1193 unite de haut : disque
#  de rayon 0,5 plus la profondeur, projetes sur l'axe vertical de l'ecran.
import math

AZIMUT, ELEVATION, OCCUPATION = 34.38, 20.05, 0.84
SILHOUETTE = 1.1193

cible = enfant(cv, 'cible', nullCOMP, 100, -340)
cible.par.tx = cible.par.ty = cible.par.tz = 0.0
cam = enfant(cv, 'cam', cameraCOMP, 100, -200)
cam.par.lookat = cible
cam.par.fov = 45.0
_d = SILHOUETTE / (OCCUPATION * 2.0 * math.tan(math.radians(cam.par.fov.eval() / 2.0)))
_a, _e = math.radians(AZIMUT), math.radians(ELEVATION)
cam.par.tx = _d * math.cos(_e) * math.sin(_a)
cam.par.ty = _d * math.sin(_e)
cam.par.tz = _d * math.cos(_e) * math.cos(_a)
cam.comment = ("La vue de base du simulateur p5 : azimut 34,38, elevation "
               "20,05, et le rig a 84 %% de la hauteur. Camera PROPRE au "
               "module -- cam1 sert trois autres rendus.")

rendu = enfant(cv, 'rendu', renderTOP, 320, 0)
rendu.par.camera = cam
rendu.par.geometry = geo
#  fond NOIR PUR repeint a chaque image, aucune accumulation (:503). Toute la
#  rememanence est deja dans la couleur de chaque point : un Feedback TOP
#  rajouterait des arcs baveux et une trainee qui depend du framerate.
rendu.par.bgcolorr = rendu.par.bgcolorg = rendu.par.bgcolorb = 0.0
rendu.par.bgcolora = 1.0
sortie = enfant(cv, 'out', nullTOP, 480, 0)
if not sortie.inputs:
    sortie.inputConnectors[0].connect(rendu)
sortie.viewer = True

print('=' * 66)
print('CUBE_3D installe')
print('=' * 66)
vox.cook(force=True)
n = cv.fetch('nb_allumees', 0)
pas = int(cv.par.Rafraichissements)
testees = (pas // 2) * 10 * 8 * 160
print('  LED allumees sur le demi-tour : %d' % n)
print('  LED testees                   : %d  (%d pas x 10 lames x 8 rangees x 160 colonnes)'
      % (testees, pas // 2))
print('  soit %.2f %% -- le simulateur mesure environ 2 %% a l image 0'
      % (100.0 * n / max(1, testees)))
print('  echantillons du CHOP          : %d' % vox.numSamples)
print('  canaux                        : %s' % [c.name for c in vox.chans()])
mauvais = [(x.path, x.errors()) for x in cv.findChildren() if x.errors()]
print('  vue                           : azimut %.2f, elevation %.2f, distance %.3f' % (AZIMUT, ELEVATION, _d))
print('  a regarder                    : %s' % sortie.path)
print('  erreurs                       : %s' % (mauvais if mauvais else 'aucune'))
