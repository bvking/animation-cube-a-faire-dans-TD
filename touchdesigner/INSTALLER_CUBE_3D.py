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
    #  LA LUMINOSITE N'EST PLUS CALCULEE ICI. Elle depend du TEMPS, donc la
    #  calculer sur le processeur central obligeait ce Script CHOP a recuire a
    #  chaque image : quinze millisecondes de numpy sur trente mille LED, sur
    #  le fil principal. TouchDesigner a fini par ne plus repondre du tout.
    #  On ne sort donc que ce qui ne bouge pas avec le temps -- la position et
    #  l'angle PHI auquel la LED a ete balayee -- et c'est le nuanceur qui fait
    #  le reste, gratuitement, a chaque pixel.
    #  Consequence directe : les LED peuvent enfin s'allumer et s'eteindre.
    e = numpy.float32(1.0 / float(comp.par.Cmparunite))
    scriptOp.numSamples = n
    for nom, val in (('tx', X * e), ('ty', Y * e), ('tz', Z * e), ('phi', PHI)):
        scriptOp.appendChan(nom).vals = numpy.asarray(val, dtype=numpy.float32)
    #  PAS me.time.rate ICI : lire me.time rend le Script CHOP dependant du
    #  temps, donc recuit a chaque image -- ce qu'on cherche precisement a
    #  eviter puisque rien de ce qu'il sort ne depend du temps.
    scriptOp.rate = project.cookRate
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
     "dix A CHAQUE INSTANT, l'eventail est casse. MESURE : sur un demi-tour "
     "COMPLET les deux allument le meme nombre de LED -- 31 424 a 0, 18 et "
     "36 degres -- car chaque lame balaye les memes 90 angles quel que soit "
     "son decalage. L'helice change la repartition dans le TEMPS : le "
     "scintillement, l'equilibrage, la part du cube allumee a un instant. "
     "Garde un MULTIPLE DU PAS (2 degres a 180 rafraichissements) : sinon "
     "la valeur de controle de 31 424 ne tient plus."),
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
    ('Anglessrc', 'op', 'Angles des lames (CHOP)', None, None, None,
     "D'ou viennent les angles des dix contours de panneaux. Vide : on tourne "
     "a l'horloge interne, comme le simulateur. Renseigne "
     "(MOTIFS_LED/angles_choix) : les contours suivent les VRAIES lames, ce "
     "qui est le seul choix coherent dans la fenetre real_Move."),
    ('Traitcadres', 'float', 'Epaisseur du trait (cm)', 1.0, 0.2, 5.0,
     "Largeur des quatre barres qui dessinent le contour d'une lame. Le "
     "simulateur trace 1 px ; ici c'est de la geometrie, donc une vraie "
     "epaisseur en centimetres."),
    ('Eclatcadres', 'float', 'Eclat des contours', 1.0, 0.0, 4.0,
     "Multiplie le gris des contours. 1 = les valeurs du simulateur, 120 pour "
     "la lame 0 et 60 pour les neuf autres. Monter si les contours se perdent "
     "a cote du rouge des LED."),
    ('Paliers', 'float', 'Paliers de luminosite', 15.0, 1.0, 64.0,
     "Nombre de marches dans le degrade de la trainee. 15 reproduit les 16 "
     "niveaux par composante du simulateur (multiples de 17 sur 0..255). "
     "Mettre 1 pour un degrade lisse."),
    ('Remanenceanimee', 'toggle', 'Faire tourner la remanence', 1, 0, 1,
     "Coche (le defaut) : les LED s'allument au passage de la lame et "
     "s'eteignent ensuite -- c'est le balayage qui PEINT le cube, et sans lui "
     "on ne voit qu'un cube fige entoure de cadres qui tournent. Le calcul se "
     "fait au pixel, il ne coute rien. Decoche fige la trainee a la phase "
     "ci-dessous, ce qui sert a examiner une position precise."),
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
if not cv.par.Anglessrc.eval():
    _a = scale.op('MOTIFS_LED/angles_choix') or scale.op('MOTIFS_LED/angles')
    if _a is not None:
        cv.par.Anglessrc = _a

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


#  LA REMANENCE, SUR LE PROCESSEUR GRAPHIQUE
#  Chaque LED porte l'angle PHI auquel la lame est passee dessus. Le nuanceur
#  compare cet angle a la rotation courante et en deduit la luminosite :
#      age = (rotation - phi) replie sur 180 degres
#      b   = 1 - age / angle_de_persistance
#  C'est exactement volumetric3D.js:556-564. Le repli sur 180 et non 360 est ce
#  qui fait que les DEUX demi-bras d'une lame comptent.
#  CE CALCUL EST GRATUIT ICI. Fait en Python il obligeait a reecrire trente
#  mille valeurs par image sur le fil principal ; fait au pixel, il ne coute
#  rien et les LED s'allument et s'eteignent pour de bon.
#  Si b tombe sous 0,03 la LED est jetee (discard), comme dans le simulateur :
#  c'est ce qui la fait vraiment S'ETEINDRE au lieu de palir indefiniment.
CODE_SOMMET = '''// Chaque instance porte son angle de balayage.
out Vertex {
	flat float phi;
} oVert;

void main() {
	vec4 worldSpacePos = TDDeform(P);
	gl_Position = TDWorldToProj(worldSpacePos);
	oVert.phi = TDInstanceCustomAttrib0().x;
}
'''

CODE_PIXEL = '''// La remanence de volumetric3D.js:556-577, au pixel.
uniform vec4 uRegle;     // x : rotation courante (deg) ; y : angle de persistance (deg)
                         // z : nombre de paliers ; w : seuil d'extinction
uniform vec4 uCouleur;

in Vertex {
	flat float phi;
} iVert;

out vec4 fragColor;

void main() {
	float age = mod(uRegle.x - iVert.phi, 180.0);
	float b = 1.0 - age / max(1e-6, uRegle.y);
	if (b <= uRegle.w) discard;          // la LED est ETEINTE, pas juste sombre
	b = clamp(b, 0.0, 1.0);
	// paliers, comme les multiples de 17 sur 0..255 du simulateur
	if (uRegle.z > 1.0) b = floor(b * uRegle.z + 0.5) / uRegle.z;
	fragColor = TDOutputSwizzle(vec4(uCouleur.rgb * b, 1.0));
}
'''

dat_s = enfant(cv, 'remanence_sommet', textDAT, -400, -560)
dat_s.text = CODE_SOMMET
dat_p = enfant(cv, 'remanence_pixel', textDAT, -400, -640)
dat_p.text = CODE_PIXEL
mat_led = enfant(cv, 'remanence', glslMAT, -150, -600)
mat_led.par.vdat = dat_s     # un glslMAT dit vdat et pdat, pas vertexdat
mat_led.par.pdat = dat_p
mat_led.par.vec0name = 'uRegle'
#  LA ROTATION EST UNE EXPRESSION SUR UN SEUL FLOTTANT. C'est tout l'ecart avec
#  l'ancienne version : un nombre reevalue par image au lieu de trente mille.
mat_led.par.vec0valuex.expr = ("(absTime.seconds * parent().par.Toursparseconde "
                               "* 360.0) % 360.0 if parent().par.Remanenceanimee "
                               "else parent().par.Phaseremanence")
mat_led.par.vec0valuey.expr = "360.0 * parent().par.Toursparseconde * parent().par.Persistance"
mat_led.par.vec0valuez.expr = "parent().par.Paliers"
mat_led.par.vec0valuew = 0.03
mat_led.par.vec1name = 'uCouleur'
mat_led.par.vec1valuex, mat_led.par.vec1valuey, mat_led.par.vec1valuez = 1.0, 0.0, 0.0
mat_led.par.vec1valuew = 1.0
mat_led.comment = ("La remanence au pixel : chaque LED s'allume au passage de "
                   "la lame et s'eteint ensuite. Fait ici, le calcul est "
                   "gratuit ; fait en Python, il figeait l'editeur.")

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
#  PHI VOYAGE COMME ATTRIBUT PERSONNALISE D'INSTANCE : le nuanceur le lit par
#  TDInstanceCustomAttrib0(). La couleur d'instance ne sert plus a rien, c'est
#  le nuanceur qui la fabrique.
geo.par.instance0customop = vox
geo.par.instance0customx = 'phi'
geo.par.material = mat_led
for n in ('tx', 'ty', 'tz'):
    getattr(geo.par, n).val = 0.0

#  UNE BOITE, PAS UNE SPHERE. Une sphereSOP, meme reglee au minimum, sort 80
#  primitives : multipliees par trente mille LED cela faisait 2,5 MILLIONS de
#  triangles par image, et le rendu coutait 222 ms. Une boite en fait 12, soit
#  377 000 au total -- sept fois moins. A deux pixels d'ecran, la difference de
#  forme ne se voit pas ; celle de cout, oui.
bille = enfant(geo, 'bille', boxSOP, 0, 0)
for _n in ('sizex', 'sizey', 'sizez'):
    getattr(bille.par, _n).expr = ("parent(2).par.Tailleled / "
                                   "parent(2).par.Cmparunite")
bille.render = True
bille.comment = "Une LED. Instanciee autant de fois qu'il y en a d'allumees."


# --- les contours des dix panneaux -----------------------------------------
#  SANS EUX L'IMAGE N'EST PAS LISIBLE. Un nuage de points rouges flottant dans
#  le noir ne dit pas ou est le dispositif : on ne sait ni ou est l'axe, ni
#  dans quel sens on regarde, ni a quelle profondeur sont les tranches. Le
#  simulateur dessine les dix bandes, et c'est ce qui fait lire l'image comme
#  « un cube au milieu de dix lames » plutot que comme une tache.
#
#  Le rectangle fait 2 x (halfLength + pas/2) sur 2 x (halfWidth + pas/2), soit
#  160 x 8 cm, et ses quatre coins a l'angle a sont, d'apres le programme :
#     (-L c + W sn, -L sn - W c)   (L c + W sn,  L sn - W c)
#     ( L c - W sn,  L sn + W c)   (-L c - W sn, -L sn + W c)
#  ce qui est exactement le rectangle [-L, L] x [-W, W] TOURNE de a autour de
#  z. On le dessine donc une fois a l'angle zero et on l'instancie dix fois,
#  chacune a son angle et a sa profondeur : dix instances ne coutent rien,
#  alors que reconstruire la geometrie a chaque image en couterait.
#
#  GRIS 120 POUR LE PANNEAU 0, GRIS 60 POUR LES NEUF AUTRES. C'est le SEUL
#  repere visuel de l'avant du rig : sans lui on ne sait plus de quel cote on
#  regarde le volume.
CODE_CADRES = '''# Les dix contours de panneaux : angle, profondeur, couleur.
#
# Dix echantillons seulement : ce Script CHOP peut cuire a chaque image sans
# que cela se voie, contrairement a celui des voxels.
#
# L'ANGLE VIENT DES LAMES REELLES quand on les a sous la main. real_Move est la
# fenetre du mouvement REEL : montrer des contours a un angle invente pendant
# que les chiffres en dessous en affichent un autre serait un contresens.
# A defaut, on retombe sur l'horloge interne, a Tours par seconde.

import numpy


def onCook(scriptOp):
    scriptOp.clear()
    comp = parent()
    n = 10
    src = comp.par.Anglessrc.eval()
    ang = None
    if src is not None:
        try:
            if src.numChans >= n:
                ang = numpy.array([float(src[i].eval()) for i in range(n)])
            elif src.numChans == 1 and src.numSamples >= n:
                ang = numpy.array([float(src[0][i]) for i in range(n)])
        except Exception:
            ang = None
    if ang is None:
        #  Pas de lames a lire : on tourne a l horloge, avec le decalage en
        #  helice. C'est ce que fait le simulateur, qui n'a pas de moteurs.
        base = (absTime.seconds * float(comp.par.Toursparseconde) * 360.0) % 360.0
        ang = base + float(comp.par.Ecarthelice) * numpy.arange(n)

    ecart = float(comp.par.Ecartcm)
    e = 1.0 / float(comp.par.Cmparunite)
    z = (4.5 - numpy.arange(n)) * ecart * e
    #  gris 120 pour la lame 0, gris 60 pour les neuf autres
    g = numpy.full(n, 60.0 / 255.0)
    g[0] = 120.0 / 255.0
    g = g * float(comp.par.Eclatcadres)
    scriptOp.numSamples = n
    zz = numpy.zeros(n)
    for nom, val in (('tx', zz), ('ty', zz), ('tz', z),
                     ('rx', zz), ('ry', zz), ('rz', ang),
                     ('r', g), ('g', g), ('b', g)):
        scriptOp.appendChan(nom).vals = numpy.asarray(val, dtype=numpy.float32)
    #  PAS me.time.rate ICI : lire me.time rend le Script CHOP dependant du
    #  temps, donc recuit a chaque image -- ce qu'on cherche precisement a
    #  eviter puisque rien de ce qu'il sort ne depend du temps.
    scriptOp.rate = project.cookRate
    return
'''

cb_cadres = enfant(cv, 'cadres_callbacks', textDAT, -400, -200)
cb_cadres.text = CODE_CADRES
cadres = enfant(cv, 'cadres', scriptCHOP, -150, -200)
cadres.par.callbacks = cb_cadres
cadres.comment = "Dix echantillons : angle, profondeur et gris de chaque lame."

geo_cadres = enfant(cv, 'geo_cadres', geometryCOMP, 100, -200)
for _d in geo_cadres.children:
    if getattr(_d, 'render', False) and _d.name != 'cadre':
        _d.render = False          # le torusPOP par defaut, voir plus haut
CODE_CADRE = '''# Le contour d'UNE lame, a l'angle zero : quatre barres fines.
#
# PAS UN Wireframe SOP. Il fabrique bien les aretes, mais l'INSTANCIATEUR NE
# LES TRANSFORME PAS : on obtient une seule lame, immobile, quel que soit le
# nombre d'instances demande et quelle que soit la source. Verifie en branchant
# 31 424 instances dessus : une seule apparaissait. Un polygone ordinaire, lui,
# s'instancie normalement -- d'ou ces quatre quadrilateres ecrits a la main.
#
# PAS UNE PLAQUE PLEINE NON PLUS : elle masquerait le cube. Le simulateur ne
# dessine que le CONTOUR du rectangle (volumetric3D.js:535-548), trait de 1 px.

import numpy


def onCook(scriptOp):
    scriptOp.clear()
    comp = parent()
    cm = float(comp.par.Cmparunite)
    L = (160.0 / 2.0) / cm          # demi-longueur, 80 cm
    W = (8.0 / 2.0) / cm            # demi-largeur, 4 cm
    e = float(comp.par.Traitcadres) / cm
    e = min(e, W * 0.9)
    barres = ((-L, L, -W, -W + e),          # bord bas
              (-L, L, W - e, W),            # bord haut
              (-L, -L + e, -W + e, W - e),  # bord gauche
              (L - e, L, -W + e, W - e))    # bord droit
    for x0, x1, y0, y1 in barres:
        pr = scriptOp.appendPoly(4, closed=True, addPoints=True)
        for i, (x, y) in enumerate(((x0, y0), (x1, y0), (x1, y1), (x0, y1))):
            pr[i].point.x, pr[i].point.y, pr[i].point.z = x, y, 0.0
    return
'''

cb_cadre = enfant(cv, 'cadre_callbacks', textDAT, -400, -380)
cb_cadre.text = CODE_CADRE
cadre = enfant(geo_cadres, 'cadre', scriptSOP, 0, 0)
cadre.par.callbacks = cb_cadre
cadre.render = True
cadre.comment = ("Le contour d'UNE lame, a l'angle zero : quatre barres fines, "
                 "160 x 8 cm. Les dix sont des instances.")
#  BLANC ici, et non le rouge des LED : c'est la couleur d'instance qui porte
#  le gris 120 du panneau 0 et le gris 60 des neuf autres, et elle MULTIPLIE
#  celle du materiau. Un materiau rouge donnerait des contours rouges.
mat_gris = enfant(cv, 'constant_gris', constantMAT, -150, -440)
mat_gris.par.colorr = mat_gris.par.colorg = mat_gris.par.colorb = 1.0
geo_cadres.par.material = mat_gris
for _mort in ('ligne1',):          # residus de versions precedentes
    _o = cv.op(_mort)
    if _o is not None:
        _o.destroy()
_o = geo_cadres.op('fil')
if _o is not None:
    _o.destroy()
geo_cadres.par.instancing = True
geo_cadres.par.instanceop = cadres
#  LES SIX CANAUX, pas seulement ceux qui varient : laisser tx, ty, rx et ry
#  vides est sans effet ici, mais les nommer rend le reglage lisible.
geo_cadres.par.instancetx, geo_cadres.par.instancety, geo_cadres.par.instancetz = 'tx', 'ty', 'tz'
geo_cadres.par.instancerx, geo_cadres.par.instancery, geo_cadres.par.instancerz = 'rx', 'ry', 'rz'
geo_cadres.par.instancecolorop = cadres
geo_cadres.par.instancer, geo_cadres.par.instanceg, geo_cadres.par.instanceb = 'r', 'g', 'b'
geo_cadres.par.instancecolormode = 'multiply'


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
#  Le rendu doit voir les DEUX geometries, le nuage et les contours. Un
#  renderTOP n'accepte qu'un operateur : on le laisse donc sur le COMP qui les
#  contient tous les deux, et ce sont les drapeaux de rendu qui decident.
rendu.par.geometry = cv
#  fond NOIR PUR repeint a chaque image, aucune accumulation (:503). Toute la
#  rememanence est deja dans la couleur de chaque point : un Feedback TOP
#  rajouterait des arcs baveux et une trainee qui depend du framerate.
rendu.par.bgcolorr = rendu.par.bgcolorg = rendu.par.bgcolorb = 0.0
rendu.par.bgcolora = 1.0
#  PAS DE TRI PAR TRANSPARENCE. Nos fragments sont OPAQUES -- le nuanceur jette
#  les LED eteintes au lieu de les melanger -- et trier des centaines de
#  milliers de triangles a chaque image coute cher pour rien.
rendu.par.transparency = 'alphatocoverage'
sortie = enfant(cv, 'out', nullTOP, 480, 0)
if not sortie.inputs:
    sortie.inputConnectors[0].connect(rendu)
#  SURTOUT PAS sortie.viewer = True. Un viseur allume force TOUTE la chaine a
#  cuire a chaque image, meme quand personne ne regarde : le rendu coutait 222 ms
#  par image, le Script CHOP 39, le nuanceur 18 -- 279 ms pour un budget de 50.
#  TouchDesigner s'est retrouve affame au point que le panneau SORTIE_SPECTACLE
#  ne cuisait plus DU TOUT (une seule cuisson contre 4 000 pour ce rendu) : plus
#  aucun clic n'y arrivait, ni sur le catalogue d'effets ni sur les molettes de
#  vitesse et d'ecart. Les reglages n'avaient pas bouge -- c'est l'affichage qui
#  etait mort. On laisse donc le viseur ETEINT : CUBE_3D ne cuit que lorsqu'on
#  le regarde vraiment, par real_Move ou en ouvrant son viseur a la main.
sortie.viewer = False

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
