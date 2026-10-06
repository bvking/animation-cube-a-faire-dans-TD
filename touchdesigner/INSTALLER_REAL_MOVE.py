# ============================================================================
#  INSTALLER_REAL_MOVE.py
#  Une fenetre « real_Move » : les dix panneaux en rotation aux positions
#  REELLES de la Teensy, et sous eux les chiffres qui les commandent.
#  Plus le basculement des MOTIFS LED sur ces memes positions reelles.
# ============================================================================
#
#  A COLLER dans un textDAT de TouchDesigner, puis « Run Script ».
#  REJOUABLE : relancer met a jour au lieu de creer un doublon.
#  Exige que INSTALLER_CONTAINER_TEENSY et INSTALLER_RENDU_TEENSY aient
#  deja tourne.
#
#  POURQUOI LES CHIFFRES SOUS L'IMAGE. Une image dit si le mouvement est
#  beau ; elle ne dit pas s'il est juste. Le compteur de la Teensy compte
#  les pas qu'elle EMET, pas ceux que l'axe FAIT : aucun decrochage
#  n'apparait nulle part. Voir l'angle, la vitesse et le couple sous les
#  lames qu'ils commandent est le seul moyen de rapprocher les deux.
# ============================================================================

RACINE = '/project1/scale'

CODE_CHIFFRES = r"""# Les positions que la Teensy renvoie, sous les panneaux qu'elles commandent.
#
# ON NE RECALCULE RIEN. Ce fichier derivait lui-meme la vitesse et le couple
# a partir des angles. C'etait une seconde implementation, et elle etait
# fausse : les angles sont REPLIES modulo 360, et deriver un angle replie
# sur une fenetre de 0,8 s aliase des 0,625 tour/s.
#
#     vitesse vraie   ce qu'elle affichait
#        0,600            +0,600
#        1,000            -0,250     <- signe inverse
#        1,500            +0,250
#        1,850            +0,600     <- le regime des essais
#
# Elle n'avait pas non plus les deux filtres du conteneur : le rejet des
# parasites serie (V_IMPOSSIBLE) et le plafond sur la derivee seconde. Une
# seule ligne serie perdue figeait 2,029 N.m dans « couple max » pour toute
# la session.
#
# Le conteneur publie deja vitesses_lames, couples_lames et couples_pic,
# mesures sur les PAS non replies, avec ses filtres eprouves. On les lit.
#
# ET LE SEUIL AFFICHE EST CELUI QUI S'APPLIQUE. Il depend de la vitesse
# courante : la loi n'accorde plus que 0,053 N.m a 1,95 tour/s la ou
# Couplemax en annonce 0,061. Afficher le second faisait taire l'alarme
# precisement la ou le moteur 9 a decroche.

BASE = '/project1/scale/MOTEURS_TEENSY'


def _canaux(nom, prefixe, n=10, defaut=0.0):
    c = op(BASE + '/' + nom)
    if c is None:
        return None
    sortie = []
    for i in range(n):
        try:
            sortie.append(float(c[prefixe + str(i)].eval()))
        except Exception:
            try:
                sortie.append(float(c[i].eval()))
            except Exception:
                sortie.append(defaut)
    return sortie


def _sante():
    c = op(BASE + '/sante_lien')
    if c is None:
        return -1.0, False, 0.061
    def lire(nom, defaut):
        try:
            return float(c[nom].eval())
        except Exception:
            return defaut
    return lire('age', -1.0), lire('muet', 0.0) > 0.5, lire('couple_seuil', 0.061)


def ligne():
    ang = _canaux('angles_reels', 'angle')
    if ang is None:
        return 'MOTEURS_TEENSY/angles_reels absent : lancer INSTALLER_CONTAINER_TEENSY.'
    vit = _canaux('vitesses_lames', 'lame')
    cpl = _canaux('couples_lames', 'lame')
    pic = _canaux('couples_pic', 'lame')
    acc = _canaux('accels_lames', 'lame')     # peut manquer sur un ancien conteneur
    if vit is None or cpl is None or pic is None:
        return ('MOTEURS_TEENSY ne publie pas vitesses_lames / couples_lames / '
                'couples_pic : relancer INSTALLER_CONTAINER_TEENSY.')
    age, muet, seuil = _sante()

    #  L'ECART MOYEN ENTRE LES DIX (Benjamin, 11 septembre 2026, 17 h 32 :
    #  « ajoute une colonne a droite de la 9 que tu nommes ecart moyen, et
    #  fais apparaitre en dessous la moyenne des ecarts entre les dix
    #  moteurs »).
    #   C'est la moyenne des NEUF ecarts entre voisines -- neuf, pas dix : dix
    #   lames font neuf intervalles. Chacun est REPLIE a plus ou moins 180
    #   degres avant d'etre moyenne : les angles arrivent modulo un tour, donc
    #   un ecart de -10 se lit 350 et une moyenne brute dirait n'importe quoi.
    #   A COTE DE L'ETALEMENT, QU'ELLE NE REMPLACE PAS : l'etalement (le plus
    #   grand des neuf moins le plus petit) dit si les lames sont REGULIERES ;
    #   cette moyenne dit de combien elles sont ouvertes. Une hélice a 90 bien
    #   tenue donne -90 de moyenne et 0 d'etalement ; la meme, fendue entre
    #   deux lames, donne toujours -90 de moyenne.
    def _rep(x):
        return ((x + 180.0) % 360.0) - 180.0
    _ec = [_rep(ang[i + 1] - ang[i]) for i in range(9)]
    _ec_moy = sum(_ec) / 9.0
    _ec_eta = max(_ec) - min(_ec)

    t = []
    t.append('PANNEAU      ' + ''.join('%8d' % i for i in range(10))
             + '   ecart moyen')
    t.append('angle  deg   ' + ''.join('%8.1f' % ang[i] for i in range(10))
             + '   %8.1f  deg entre voisines (etalement %.1f)' % (_ec_moy, _ec_eta))
    t.append('vitesse t/s  ' + ''.join('%8.3f' % vit[i] for i in range(10)))
    #  LES DEUX ACCELERATIONS, ET ELLES NE DISENT PAS LA MEME CHOSE
    #  (11 septembre 2026, Benjamin : « je veux voir la vitesse instantanee de
    #  chaque moteur, et l'acceleration instantanee de chaque moteur »).
    #    COMMANDEE : _a_mvt, ce que le pilote DEMANDE a cette lame -- la
    #      rotation commune plus sa part de figure. C'est elle qui fixe le
    #      couple demande. En helice ancree elle vaut jusqu'a NEUF FOIS celle
    #      de la lame 1 ; centree, 4,5 fois.
    #    SUBIE : la derivee seconde des positions RAPPORTEES, bornee et
    #      lissee par mesurer_lames(). C'est ce que la lame fait vraiment.
    #  Les voir cote a cote est le seul moyen de savoir si la carte a suivi.
    if acc is not None:
        t.append('accel cmd    ' + ''.join('%8.0f' % acc[i] for i in range(10))
                 + '   pas/s2 demandes')
    _ksub = 3200.0 / (0.0853 * 2.0 * 3.14159265358979)
    t.append('accel subie  ' + ''.join('%8.0f' % (cpl[i] * _ksub) for i in range(10))
             + '   pas/s2 tires des positions')
    cel = []
    for i in range(10):
        x = cpl[i]
        cel.append(('%7.4f*' % x) if x > seuil else ('%8.4f' % x))
    t.append('couple  N.m  ' + ''.join(cel) + ('   seuil %.3f a cette vitesse' % seuil))
    t.append('couple max   ' + ''.join('%8.4f' % pic[i] for i in range(10)))

    # GARDE 12 -- CE QUE L'IMAGE NE PEUT PAS DIRE.
    # Le temoin d'avant etait « les dix angles valent zero » : il n'attrapait
    # que la carte JAMAIS branchee. Le 2 septembre a 19h23, la Teensy s'est
    # re-enumeree en pleine session ; les angles sont restes figes sur des
    # valeurs NON NULLES, 28422 trames sont parties sans qu'une seule revienne,
    # et l'image aurait montre dix lames immobiles -- impossibles a distinguer
    # d'une machine a l'arret.
    t.append('')
    if muet:
        t.append('   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        t.append('   LA CARTE S EST TUE DEPUIS %.0f SECONDES.' % age)
        t.append('   CE QUI EST AFFICHE DATE. Les lames au-dessus ne bougent pas')
        t.append('   parce que plus rien n arrive, pas parce qu elles sont a')
        t.append('   l arret. Une liaison serie morte ne produit aucune erreur :')
        t.append('   relancer le conteneur pour rouvrir le port.')
        t.append('   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    elif age < 0.0:
        t.append('   la carte n a encore rien dit : conteneur desarme, ou port ferme.')
    elif not any(abs(x) > 1e-9 for x in ang):
        t.append('   la carte parle (derniere ligne il y a %.1f s) et rapporte zero' % age)
        t.append('   sur les dix : son compteur est a l origine, rien d anormal.')
    else:
        t.append('   liaison vivante : derniere ligne recue il y a %.1f s.' % age)
    return chr(10).join(t)
"""

scale = op(RACINE)
rendu = scale.op('RENDU_TEENSY')
if rendu is None:
    raise RuntimeError("RENDU_TEENSY absent : lancer d'abord INSTALLER_RENDU_TEENSY")
sortie_panneaux = rendu.op('out')
if sortie_panneaux is None:
    raise RuntimeError("RENDU_TEENSY/out absent")

# ---------------------------------------------------------------------------
#  1. LA FENETRE real_Move : les panneaux en haut, les chiffres dessous
# ---------------------------------------------------------------------------
led = scale.op('MOTIFS_LED')

#  LE PARAMETRE D'ABORD, LA LIAISON ENSUITE.
#  Il etait cree soixante lignes plus BAS que le bouton qui s'y lie : au
#  premier passage hasattr(led.par, 'Anglesreels') etait faux, le bouton
#  restait mort, et il fallait relancer l'installeur sans savoir pourquoi.
#  Un installeur rejouable doit marcher DU PREMIER COUP.
if led is not None:
    _pg = None
    for _p in led.customPages:
        if _p.name == 'Angles':
            _pg = _p
    if _pg is None:
        _pg = led.appendCustomPage('Angles')
    if 'Anglesreels' not in [q.name for q in _pg.pars]:
        _q = _pg.appendToggle('Anglesreels', label='MOTIFS SUR LES ANGLES REELS')[0]
        _q.default = False
        _q.val = False
        _q.help = ("Decoche : le motif est dessine sur la CONSIGNE. Coche : sur "
                   "les positions que la Teensy RAPPORTE. Le retard du suiveur "
                   "atteint plusieurs tours et decale le motif d'autant -- c'est "
                   "donc coche qu'il faut jouer, DES QUE LA CARTE PARLE. Sans "
                   "carte, les dix angles valent zero et le motif se fige.")

rm = scale.op('real_Move')
if rm is None:
    rm = scale.create(containerCOMP, 'real_Move')
    rm.nodeX, rm.nodeY = rendu.nodeX, rendu.nodeY - 300
rm.par.w, rm.par.h = 1280, 900
rm.par.align = 'verttb'
rm.par.bgcolorr, rm.par.bgcolorg, rm.par.bgcolorb = 0.043, 0.051, 0.063
rm.comment = ("Les dix panneaux aux positions REELLES de la Teensy, et sous eux "
              "les chiffres qui les commandent. Une image dit si le mouvement est "
              "beau, pas s'il est juste.")


def enfant(parent, nom, type_op, x, y):
    o = parent.op(nom)
    if o is None:
        o = parent.create(type_op, nom)
        # TouchDesigner suffixe parfois le nom demande -- on le remet, sinon
        # la relance suivante croit l'operateur absent et en cree un second.
        if o.name != nom and parent.op(nom) is None:
            o.name = nom
        o.nodeX, o.nodeY = x, y
    return o


# --- le haut : les panneaux en rotation ------------------------------------
haut = enfant(rm, 'panneaux', containerCOMP, 0, 200)
haut.par.hmode, haut.par.vmode = 'fill', 'fill'
# L'ordre d'empilement d'une disposition verttb ne suit PAS la position des
# noeuds : il faut le dire. 0 en haut, 2 en bas.
haut.par.alignorder = 0
#  L'image du haut bascule entre l'instant et le volume balaye. L'expression
#  est GARDEE : CUBE_3D peut ne pas etre installe, et une expression qui leve
#  a chaque cuisson rendrait le panneau rouge au lieu de se taire.
haut.par.top.expr = ("op('../CUBE_3D/out') if (parent().par.Volume and "
                     "op('../CUBE_3D/out')) else op('../RENDU_TEENSY/out')")
haut.par.topfill = 'best'
haut.par.bgcolorr, haut.par.bgcolorg, haut.par.bgcolorb = 0.02, 0.02, 0.025
haut.comment = "Les dix panneaux, angles rapportes par la Teensy."

# --- le bas : les chiffres --------------------------------------------------
#  LA BOITE SUIT LE TABLEAU, PAS L'INVERSE (6 octobre 2026).
#  Elle etait restee a 210 px de haut et 13 px de police : la taille du
#  tableau d'ORIGINE. Depuis se sont ajoutees deux lignes d'acceleration,
#  la colonne « ecart moyen », et un bandeau d'alarme de sept lignes.
#  Mesure sur Menlo a fontsizex 13 : 10,00 px par caractere exactement,
#  22,22 px par ligne.
#        il faut                    il y avait
#        142 caracteres = 1420 px   1184 px visibles -- la bande « volume »
#                                   en masque 96 sur les 1280
#        15 lignes      =  328 px    210 px
#  Donc l'en-tete PANNEAU etait rognee en haut, l'alarme coupee en bas, et
#  « ecart moyen » passait sous le curseur de volume : on lisait « deg
#  entre vo ». Un tableau qu'on ne lit qu'a moitie ne sert a rien -- c'est
#  lui, et pas l'image, qui dit si le mouvement est JUSTE.
#  1280 reste le plafond d'une cle non commerciale : c'est donc la police
#  qui cede, 10,5 (142 car. = 1147 px, sous les 1184 visibles), et la
#  boite qui monte a 280 (15 lignes = 265 px).
bas = enfant(rm, 'donnees', containerCOMP, 0, -100)
bas.par.hmode, bas.par.vmode = 'fill', 'fixed'
bas.par.h = 280
bas.par.alignorder = 1
bas.par.align = 'none'
bas.par.topfill = 'horizontal'
bas.par.bgcolorr, bas.par.bgcolorg, bas.par.bgcolorb = 0.043, 0.051, 0.063

fmt = enfant(bas, 'format', textDAT, -400, 0)
fmt.text = CODE_CHIFFRES

txt = enfant(bas, 'texte', textTOP, 0, 0)
# L'expression ne doit jamais pouvoir lever : elle est evaluee a chaque
# cuisson, y compris quand le frere n'existe pas encore. Et './format'
# designerait un ENFANT du textTOP, pas un frere.
txt.par.text.expr = "(op('format').module.ligne() if op('format') else '')"
txt.par.legacyfontselection = False
txt.par.fontfile = ''
txt.par.font = 'Menlo'          # monospace : les colonnes doivent s'aligner
txt.par.fontsizex = 10.5
txt.par.linespacing = 1.25
txt.par.alignx, txt.par.aligny = 'left', 'center'
txt.par.fontcolorr, txt.par.fontcolorg, txt.par.fontcolorb = 0.91, 0.92, 0.93
txt.par.bgcolorr, txt.par.bgcolorg, txt.par.bgcolorb = 0.043, 0.051, 0.063
txt.par.outputresolution = 'custom'
# 1280 est le plafond d'une cle non commerciale
txt.par.resolutionw, txt.par.resolutionh = 1280, 280
bas.par.top = txt

# --- la barre du bas : l'interrupteur des motifs ----------------------------
#  Le meme reglage que la case de MOTIFS_LED, mais a portee de main dans la
#  fenetre ou l'on regarde le resultat. La LIAISON est bidirectionnelle :
#  cocher ici coche la-bas, et reciproquement -- il n'y a donc qu'un seul
#  etat, et pas deux qui pourraient se contredire.
barre = enfant(rm, 'reglages', containerCOMP, 0, -300)
barre.par.hmode, barre.par.vmode = 'fill', 'fixed'
barre.par.h = 52
barre.par.alignorder = 2
barre.par.align = 'horizlr'
barre.par.spacing = 14
barre.par.marginl, barre.par.margint = 14, 8
barre.par.bgcolorr, barre.par.bgcolorg, barre.par.bgcolorb = 0.07, 0.08, 0.10

bouton = enfant(barre, 'motifs_reels', buttonCOMP, 0, 0)
bouton.par.buttontype = 'toggledown'
bouton.par.hmode, bouton.par.vmode = 'fixed', 'fixed'
bouton.par.w, bouton.par.h = 420, 36
bouton.par.alignallow = 'allow'
#  L'ordre d'une disposition horizlr ne suit pas la position des noeuds,
#  pas plus que celui d'une verttb : il faut le dire ici aussi.
bouton.par.alignorder = 0
# buttonCOMP : l'etiquette est par.label, la couleur du texte par.color*,
# le fond par.bgcolor*. Il n'y a PAS de textlabel ni de couleur de selection.
bouton.par.label = 'MOTIFS SUR LES ANGLES REELS'
bouton.par.fontsize = 14
bouton.par.bgcolorr, bouton.par.bgcolorg, bouton.par.bgcolorb = 0.10, 0.12, 0.15
bouton.par.colorr, bouton.par.colorg, bouton.par.colorb = 0.88, 0.90, 0.92
bouton.comment = ("Lie a MOTIFS_LED.Anglesreels. Decoche : le motif est dessine "
                  "sur la CONSIGNE. Coche : sur les positions que la Teensy "
                  "RAPPORTE -- le retard du suiveur atteint plusieurs tours et "
                  "decale le motif d'autant.")

# LIAISON BIDIRECTIONNELLE : cocher ici coche la case de MOTIFS_LED, et
# reciproquement. Il n'y a donc qu'un seul etat, pas deux qui pourraient se
# contredire.
if led is not None and hasattr(led.par, 'Anglesreels'):
    _v0 = getattr(bouton.par, 'value0', None)
    if _v0 is not None:
        _v0.mode = ParMode.BIND
        _v0.bindExpr = "op('/project1/scale/MOTIFS_LED').par.Anglesreels"

etiquette = enfant(barre, 'note', textCOMP, 250, 0)
etiquette.par.hmode, etiquette.par.vmode = 'fixed', 'fixed'
#  LA NOTE RETRECIT POUR LES FLECHES. La barre ne dispose que de 1184 px
#  utiles -- la bande « volume » masque les 96 de droite -- et il en faut
#  14 + 420 (interrupteur) + 14 + 238 (fleches) + 14 = 700 avant elle.
#  LE BOUTON DU VOLUME, entre les fleches et la note. La barre ne dispose que
#  de 1184 px utiles : 14 + 420 + 14 + 238 + 14 + 170 + 14 = 884 avant elle.
bouton_vol = enfant(barre, 'volume_balaye', buttonCOMP, 750, 0)
bouton_vol.par.buttontype = 'toggledown'
bouton_vol.par.hmode, bouton_vol.par.vmode = 'fixed', 'fixed'
bouton_vol.par.w, bouton_vol.par.h = 170, 36
bouton_vol.par.alignallow = 'allow'
bouton_vol.par.alignorder = 2
bouton_vol.par.label = 'VOLUME BALAYE'
bouton_vol.par.fontsize = 12
for _p, _v in (('bgcolorr', 0.10), ('bgcolorg', 0.12), ('bgcolorb', 0.15),
               ('colorr', 0.88), ('colorg', 0.90), ('colorb', 0.92)):
    _q = getattr(bouton_vol.par, _p, None)
    if _q is not None:
        _q.val = _v
bouton_vol.comment = ("Bascule le haut de la fenetre entre l'INSTANT "
                      "(RENDU_TEENSY, dix segments) et le VOLUME BALAYE "
                      "(CUBE_3D, ou le cube se voit).")
_v0 = getattr(bouton_vol.par, 'value0', None)
if _v0 is not None:
    _v0.mode = ParMode.BIND
    _v0.bindExpr = "op('/project1/scale/real_Move').par.Volume"

etiquette.par.w, etiquette.par.h = 300, 36
etiquette.par.alignallow = 'allow'
etiquette.par.alignorder = 3
#  L'EXPRESSION EST GARDEE, comme celle du texte des chiffres soixante
#  lignes plus haut. Sans garde, elle plante a chaque cuisson quand
#  MOTIFS_LED est absent -- et MOTIFS_LED ne vit que dans le .toe, aucun
#  script du depot ne le cree.
#  LE TEXTE TIENT DANS SA BOITE. Elle est passee de 680 a 300 px pour faire
#  place aux fleches et au bouton du volume : la phrase longue y serait coupee
#  en plein mot, exactement le defaut corrige sur le tableau de chiffres.
etiquette.par.text.expr = (
    "(('motifs : angles REELS'"
    "  if op('/project1/scale/MOTIFS_LED').par.Anglesreels"
    "  else 'motifs : CONSIGNE')"
    " if op('/project1/scale/MOTIFS_LED')"
    " and hasattr(op('/project1/scale/MOTIFS_LED').par, 'Anglesreels')"
    " else 'MOTIFS_LED absent')")
for _p, _v in (('fontsize', 13), ('alignx', 'left'),
               ('bgcolorr', 0.07), ('bgcolorg', 0.08), ('bgcolorb', 0.10),
               ('colorr', 0.62), ('colorg', 0.66), ('colorb', 0.72)):
    _q = getattr(etiquette.par, _p, None)
    if _q is not None:
        _q.val = _v

# --- les fleches de point de vue, dans la meme barre ------------------------
#  POURQUOI UNE CAMERA A PART. cam1 est la SEULE cameraCOMP du projet et elle
#  sert TROIS rendus : render1, RENDU_TEENSY/render_teensy et
#  recorded_real_Move/render_rejeu. INSTALLER_RENDU_TEENSY ligne 137 l'assume
#  -- « meme point de vue que le rendu de consigne ». Faire tourner cam1 depuis
#  real_Move deplacerait donc AUSSI le rendu principal, sans que rien ne le
#  signale. real_Move recoit sa propre camera ; on ne touche pas a cam1.
#
#  POURQUOI ON N'ECRIT PAS rx/ry/rz. cam1 a par.lookat = cible_camera, et tant
#  que lookat est renseigne les trois rotations sont INERTES : elles valent 0 et
#  ecrire dedans ne change strictement rien a l'image. C'est le piege, parce que
#  ce sont precisement les parametres qu'on croit devoir utiliser. COMMENT_38
#  ligne 39 archive le reglage d'avant lookat -- t (0,0,10) r (-5,25,10) --
#  preuve que l'approche par rotation a ete abandonnee volontairement.
#  On garde donc lookat et on ne deplace que la POSITION de la camera, sur une
#  sphere centree sur la cible. L'orientation suit toute seule et la cible reste
#  au centre de l'image a n'importe quel angle : aucune vue ne peut se perdre.
#
#  LA VUE D'ORIGINE EST LE DEFAUT. Azimut 22,24 deg, elevation 7,32 deg,
#  distance 7,461 : ce sont les coordonnees spheriques de cam1 (2,8 / 0,95 /
#  4,6) autour de la cible (0 / 0 / -2,25). Installer les fleches ne change donc
#  RIEN a l'image tant qu'on n'en a pas presse une.
VUE_DEFAUT = {'Azimut': 22.24, 'Elevation': 7.32, 'Distance': 7.461}

_pg = None
for _p in rm.customPages:
    if _p.name == 'Vue':
        _pg = _p
if _pg is None:
    _pg = rm.appendCustomPage('Vue')
_deja = [q.name for q in _pg.pars]


def _reglage_vue(nom, label, mini, maxi, aide):
    #  On ne REECRIT pas un reglage existant : relancer l'installeur ne doit pas
    #  ramener la vue au defaut sous les yeux de celui qui vient de la regler.
    if nom not in _deja:
        q = _pg.appendFloat(nom, label=label)[0]
        q.default = VUE_DEFAUT[nom]
        q.val = VUE_DEFAUT[nom]
        q.normMin, q.normMax = mini, maxi
        q.help = aide
    return getattr(rm.par, nom)


_reglage_vue('Azimut', 'Azimut (deg)', -180.0, 180.0,
             "Tour de la camera autour de la cible, dans le plan horizontal. "
             "Cyclique : passe de 180 a -180 sans butee.")
_reglage_vue('Elevation', 'Elevation (deg)', -89.0, 89.0,
             "Hauteur de la camera au-dessus du plan de la cible. Bornee a "
             "plus ou moins 89 : a 90 exactement la camera est a la verticale "
             "et lookat n'a plus d'horizon pour orienter l'image.")
if 'Volume' not in _deja:
    #  LE HAUT DE real_Move MONTRE DEUX CHOSES TRES DIFFERENTES.
    #  Decoche : RENDU_TEENSY, l'INSTANT -- les dix lames a l'angle qu'elles
    #  ont maintenant. C'est juste pour piloter les panneaux, et c'est
    #  structurellement incapable de ressembler a un cube : dix segments.
    #  Coche : CUBE_3D, le VOLUME BALAYE d'un demi-tour, avec les contours des
    #  dix lames. C'est ce que l'oeil recompose, et c'est la qu'un cube se voit.
    _q = _pg.appendToggle('Volume', label='VOLUME BALAYE (au lieu de l instant)')[0]
    _q.default = False
    _q.val = False
    _q.help = ("Decoche : le rendu d'un INSTANT, dix lames minces -- ce qui part "
               "aux panneaux. Coche : le volume balaye d'un demi-tour avec les "
               "contours des dix lames, c'est-a-dire ce que l'oeil recompose. "
               "Un cube ne peut se voir que coche.")
_reglage_vue('Distance', 'Distance', 1.0, 30.0,
             "Eloignement de la camera. La cible reste au centre quel que "
             "soit l'eloignement.")

cam_ref = scale.op('cam1')
cible = scale.op('cible_camera')
rendu_top = rendu.op('render_teensy')
fleches_ok = False

if cam_ref is None or cible is None or rendu_top is None:
    #  ON LE DIT. Un bloc saute en silence est la facon dont cet installeur
    #  s'est deja trompe trois fois : la fenetre s'installait, le rapport
    #  annoncait « real_Move installe », et la moitie du travail manquait.
    print("")
    print("  ATTENTION : pas de fleches de point de vue.")
    for _o, _n in ((cam_ref, 'cam1'), (cible, 'cible_camera'),
                   (rendu_top, 'RENDU_TEENSY/render_teensy')):
        if _o is None:
            print("    introuvable : " + _n)
    print("")
else:
    cam = scale.op('cam_real_move')
    if cam is None:
        cam = scale.create(cameraCOMP, 'cam_real_move')
        cam.nodeX, cam.nodeY = cam_ref.nodeX, cam_ref.nodeY - 160
    #  Meme optique que cam1 : seul le POINT DE VUE doit differer, pas le
    #  cadrage. Sinon on comparerait deux images qui ne different pas que par
    #  l'angle, et le reglage ne voudrait plus rien dire.
    for _p in ('projection', 'fov', 'orthowidth', 'near', 'far'):
        _src = getattr(cam_ref.par, _p, None)
        _dst = getattr(cam.par, _p, None)
        if _src is not None and _dst is not None:
            _dst.val = _src.eval()
    cam.par.lookat = cible
    cam.comment = ("Le point de vue de real_Move, et de lui seul. cam1 sert "
                   "trois rendus : la deplacer bougerait aussi le rendu "
                   "principal. lookat vise cible_camera, donc seules tx/ty/tz "
                   "comptent -- rx/ry/rz sont inertes tant que lookat est mis.")

    #  Spherique -> cartesien, autour de la cible. L'expression lit la cible au
    #  lieu de figer (0, 0, -2,25) : si on deplace cible_camera, la camera suit.
    _A = "math.radians(op('real_Move').par.Azimut)"
    _E = "math.radians(op('real_Move').par.Elevation)"
    _D = "op('real_Move').par.Distance"
    cam.par.tx.expr = ("op('cible_camera').par.tx + %s * math.cos(%s) * math.sin(%s)"
                       % (_D, _E, _A))
    cam.par.ty.expr = "op('cible_camera').par.ty + %s * math.sin(%s)" % (_D, _E)
    cam.par.tz.expr = ("op('cible_camera').par.tz + %s * math.cos(%s) * math.cos(%s)"
                       % (_D, _E, _A))
    rendu_top.par.camera = cam

    CB_FLECHE = '''# Une fleche de point de vue. Elle n'ajoute qu'un pas au reglage
# correspondant de real_Move ; c'est l'expression de cam_real_move qui traduit
# ensuite azimut/elevation/distance en position de camera. Le bouton ne connait
# donc ni la camera, ni la trigonometrie : il ne sait qu'incrementer un nombre.
def onOffToOn(panelValue):
    b = panelValue.owner
    rm = b.parent(3)                      # bouton -> vue -> reglages -> real_Move
    nom = b.fetch('reglage', '')
    if not nom:                           # le bouton de retour a la vue d'origine
        for n in ('Azimut', 'Elevation', 'Distance'):
            q = getattr(rm.par, n)
            q.val = q.default
        return
    q = getattr(rm.par, nom)
    v = q.eval() + float(b.fetch('pas', 0.0))
    if nom == 'Azimut':
        # Le tour est CYCLIQUE : buter a 180 obligerait a revenir en arriere
        # pour voir l'autre cote, alors qu'il n'y a pas de bord a un cercle.
        v = ((v + 180.0) % 360.0) - 180.0
    else:
        # L'elevation et la distance, elles, ont de vraies butees : au-dela
        # lookat perd son horizon, ou la camera passe dans la geometrie.
        v = max(q.normMin, min(q.normMax, v))
    q.val = v
    return
'''

    #  LES SEPT BOUTONS. Pas, en degres : 15 pour le tour (24 pas pour un tour
    #  complet), 10 pour la hauteur, 1 unite pour l'eloignement.
    FLECHES = (('tour_moins', '\u25c0', 'Azimut', -15.0, 'tourner a gauche'),
               ('tour_plus', '\u25b6', 'Azimut', 15.0, 'tourner a droite'),
               ('haut', '\u25b2', 'Elevation', 10.0, 'monter'),
               ('bas', '\u25bc', 'Elevation', -10.0, 'descendre'),
               ('loin', '\u2212', 'Distance', 1.0, 's eloigner'),
               ('pres', '+', 'Distance', -1.0, 's approcher'),
               ('defaut', '\u21ba', '', 0.0, 'revenir a la vue d origine'))

    vue = enfant(barre, 'vue', containerCOMP, 500, 0)
    vue.par.hmode, vue.par.vmode = 'fixed', 'fixed'
    vue.par.w, vue.par.h = 238, 36
    vue.par.align = 'horizlr'
    vue.par.spacing = 4
    vue.par.alignallow = 'allow'
    vue.par.alignorder = 1
    for _p, _v in (('bgcolorr', 0.07), ('bgcolorg', 0.08), ('bgcolorb', 0.10)):
        getattr(vue.par, _p).val = _v
    vue.comment = ("Les sept fleches de point de vue. Elles ecrivent Azimut, "
                   "Elevation et Distance sur real_Move ; cam_real_move suit "
                   "par expression.")

    for _i, (_nom, _glyphe, _reglage, _pas, _aide) in enumerate(FLECHES):
        b = enfant(vue, _nom, buttonCOMP, _i * 40, 0)
        b.par.buttontype = 'momentary'
        b.par.hmode, b.par.vmode = 'fixed', 'fixed'
        b.par.w, b.par.h = 30, 30
        b.par.alignallow = 'allow'
        b.par.alignorder = _i
        b.par.label = _glyphe
        b.par.fontsize = 15
        for _p, _v in (('bgcolorr', 0.10), ('bgcolorg', 0.12), ('bgcolorb', 0.15),
                       ('colorr', 0.88), ('colorg', 0.90), ('colorb', 0.92)):
            _q = getattr(b.par, _p, None)
            if _q is not None:
                _q.val = _v
        #  Le bouton PORTE son role : le callback est le meme pour les sept, il
        #  le lit ici. Un callback par bouton aurait fait sept textes a tenir
        #  d'accord entre eux.
        b.store('reglage', _reglage)
        b.store('pas', _pas)
        b.comment = _aide
        _clic = b.op('clic') or b.create(panelexecuteDAT, 'clic')
        _clic.par.panelvalue = 'select'
        _clic.par.offtoon = True
        _clic.par.valuechange = False
        _clic.text = CB_FLECHE
    fleches_ok = True

fen = scale.op('FENETRE_REAL_MOVE')
if fen is None:
    fen = scale.create(windowCOMP, 'FENETRE_REAL_MOVE')
    fen.nodeX, fen.nodeY = rm.nodeX + 250, rm.nodeY
fen.par.winop = rm
fen.par.title = 'real_Move'
fen.par.winw, fen.par.winh = 1280, 900
fen.par.borders = True
fen.par.justifyh, fen.par.justifyv = 'right', 'bottom'
fen.par.opendialog = False

# ---------------------------------------------------------------------------
#  2. LES MOTIFS LED SUIVENT LES POSITIONS REELLES
# ---------------------------------------------------------------------------
#  MOTIFS_LED/angles lisait PHASES_PANNEAUX/angles_phases : la CONSIGNE. Le
#  motif etait donc dessine pour un angle que la lame n'avait pas encore --
#  le retard du suiveur atteint plusieurs tours, et il DECALE LE MOTIF.
#  On insere un aiguillage. Par defaut il reste sur la consigne : basculer
#  sans la carte branchee figerait le motif, les dix angles valant zero.
bascule_ok = False
#  LE TROISIEME ECHEC SILENCIEUX. Ce bloc est saute des que MOTIFS_LED/angles
#  manque -- et il peut manquer sans que rien ne cloche : le LISEZ_MOI de
#  l'AGL decrit la source des angles sous le nom « rz_replie », pas
#  « angles ». Saute, l'installeur annoncait quand meme « real_Move installe »
#  et la bascule n'existait pas. On dit ce qu'on a trouve a la place.
if led is not None and led.op('angles') is None:
    _enfants = sorted(o.name for o in led.children
                      if o.family == 'CHOP') if hasattr(led, 'children') else []
    print("")
    print("  ATTENTION : MOTIFS_LED existe mais n'a pas d'enfant « angles ».")
    print("  La bascule des motifs sur les angles reels N'A PAS ete installee.")
    if _enfants:
        print("  CHOP trouves dans MOTIFS_LED : " + ", ".join(_enfants))
        print("  Si la source des angles porte un autre nom -- le LISEZ_MOI de")
        print("  l'AGL parle de « rz_replie » -- le dire pour corriger la ligne.")
    print("")

if led is not None and led.op('angles') is not None:
    reel = enfant(led, 'angles_reels', selectCHOP, -600, -150)
    reel.par.chop = '../RENDU_TEENSY/rz'
    reel.par.channames = 'rz'
    reel.comment = "Les angles REELS, dans la meme forme que angles_phases."

    choix = enfant(led, 'angles_choix', switchCHOP, -400, -80)
    virtuel = led.op('angles')
    if len(choix.inputs) < 2:
        virtuel.outputConnectors[0].connect(choix.inputConnectors[0])
        reel.outputConnectors[0].connect(choix.inputConnectors[1])
    choix.comment = ("0 = la CONSIGNE de TouchDesigner, 1 = les positions REELLES "
                     "de la Teensy. Le retard du suiveur atteint plusieurs tours : "
                     "dessiner le motif sur la consigne le decale d'autant.")

    #  Anglesreels a deja ete cree en tete, avant le bouton qui s'y lie.
    choix.par.index.expr = "1 if parent().par.Anglesreels else 0"

    haut_top = led.op('angles_top')
    if haut_top is not None:
        # 'nom' = frere, './nom' = enfant : angles_choix est un FRERE
        haut_top.par.chop = 'angles_choix'
    bascule_ok = True

for x in (txt, fmt, haut, bas, rm):
    try:
        x.cook(force=True)
    except Exception:
        pass

#  MOTIFS_LED ABSENT : ON LE DIT. RENDU_TEENSY manquant leve une exception
#  quarante lignes plus haut ; MOTIFS_LED manquant ne faisait rien du tout,
#  et l'installeur annoncait « real_Move installe » comme si de rien n'etait.
#  Il ne vit que dans le .toe : aucun script du depot ne le cree.
if led is None:
    print("")
    print("  ATTENTION : MOTIFS_LED est absent de " + RACINE + ".")
    print("  La fenetre real_Move est installee et fonctionne, mais LES MOTIFS")
    print("  LED NE PEUVENT PAS BASCULER sur les angles reels : ni interrupteur,")
    print("  ni parametre Anglesreels. MOTIFS_LED ne vit que dans le .toe --")
    print("  aucun script du depot ne le cree. Ouvrir le bon .toe, ou s'en")
    print("  passer si l'on ne veut que les panneaux et les chiffres.")
    print("")

# ---------------------------------------------------------------------------
#  3. LE VOLUME DU SON, A DROITE DE LA FENETRE
# ---------------------------------------------------------------------------
#  Demande de Benjamin, 3 septembre. Le son sort de /project1/scale/audiodevout1
#  -- le seul audioDeviceOut actif du projet ; celui de audioAnalysis est
#  inactif. La bande sort de la disposition verticale (alignallow = ignore) et
#  s'ancre sur le bord droit, sinon elle s'empilerait sous les chiffres.
SORTIE_AUDIO = '/project1/scale/audiodevout1'

sortie_audio = op(SORTIE_AUDIO)
if sortie_audio is None:
    print("")
    print("  ATTENTION : " + SORTIE_AUDIO + " est introuvable.")
    print("  Le curseur de volume n'a pas ete pose : il n'y a rien a regler.")
    print("")
else:
    bande = enfant(rm, 'volume', containerCOMP, 320, 200)
    bande.par.alignallow = 'ignore'      # la disposition verticale l'ignore
    bande.par.hmode, bande.par.vmode = 'fixed', 'fixed'
    bande.par.w = 96
    bande.par.h.expr = 'parent().height'
    bande.par.x.expr = 'parent().width - me.width'
    bande.par.y = 0
    bande.par.align = 'verttb'
    for _p, _v in (('bgcolorr', 0.055), ('bgcolorg', 0.065), ('bgcolorb', 0.080)):
        try:
            getattr(bande.par, _p).val = _v
        except Exception:
            pass
    bande.comment = ("Le volume du son qui sort de TouchDesigner. Le curseur "
                     "pilote " + SORTIE_AUDIO + ".volume, par liaison : on peut "
                     "aussi taper la valeur sur l'operateur audio, les deux "
                     "restent d'accord.")

    titre = enfant(bande, 'titre', textCOMP, 0, 200)
    titre.par.hmode, titre.par.vmode = 'fill', 'fixed'
    titre.par.h = 26
    titre.par.alignorder = 0
    titre.par.text = 'VOLUME'
    for _p, _v in (('fontsize', 11), ('alignx', 'center'),
                   ('bgcolorr', 0.055), ('bgcolorg', 0.065), ('bgcolorb', 0.080),
                   ('colorr', 0.62), ('colorg', 0.66), ('colorb', 0.72)):
        _q = getattr(titre.par, _p, None)
        if _q is not None:
            _q.val = _v

    curseur = enfant(bande, 'curseur', sliderCOMP, 0, 0)
    curseur.par.hmode, curseur.par.vmode = 'fill', 'fill'
    curseur.par.alignorder = 1
    curseur.par.slidertype = 'sliderv'          # vertical : la valeur est value1
    curseur.par.valuerange1l, curseur.par.valuerange1h = 0.0, 1.0
    curseur.par.clampvl, curseur.par.clampvh = True, True
    curseur.comment = ("Zero en bas, un en haut. C'est value1 qui compte sur un "
                       "slider vertical -- value0 est l'axe horizontal et ne "
                       "sert pas ici.")

    valeur = enfant(bande, 'valeur', textCOMP, 0, -200)
    valeur.par.hmode, valeur.par.vmode = 'fill', 'fixed'
    valeur.par.h = 30
    valeur.par.alignorder = 2
    valeur.par.text.expr = (
        "'%.2f' % op('" + SORTIE_AUDIO + "').par.volume"
        " if op('" + SORTIE_AUDIO + "') else 'audio absent'")
    for _p, _v in (('fontsize', 15), ('alignx', 'center'),
                   ('bgcolorr', 0.055), ('bgcolorg', 0.065), ('bgcolorb', 0.080),
                   ('colorr', 0.85), ('colorg', 0.87), ('colorb', 0.90)):
        _q = getattr(valeur.par, _p, None)
        if _q is not None:
            _q.val = _v

    #  LA SORTIE AUDIO SUIT LE CURSEUR, PAR LIAISON. Une expression rendrait
    #  le parametre de volume illisible depuis l'operateur audio ; une liaison
    #  laisse les deux modifiables et d'accord.
    #  ON NE PERD PAS LE VOLUME EN PLACE : il devient la position du curseur.
    _avant = None
    try:
        _avant = float(sortie_audio.par.volume.eval())
    except Exception:
        _avant = None
    _chemin_curseur = curseur.path
    if _avant is not None and str(sortie_audio.par.volume.mode) != 'ParMode.BIND':
        curseur.par.value1.val = _avant
    try:
        sortie_audio.par.volume.mode = ParMode.BIND
        sortie_audio.par.volume.bindExpr = "op('" + _chemin_curseur + "').par.value1"
        print("")
        print("  VOLUME : curseur pose a droite de real_Move, lie a "
              + SORTIE_AUDIO + ".")
        if _avant is not None:
            print("  Volume trouve en place : %.3f -- repris comme position "
                  "de depart." % _avant)
    except Exception as _e:
        print("  ATTENTION : la liaison du volume a echoue : %r" % (_e,))

#  LA PLACE RESTANTE, DITE A CHAQUE INSTALLATION. Le tableau a deja grandi
#  deux fois sans que la boite suive, et la coupe ne se voit PAS : le texte
#  est centre, il perd ses bords en silence -- aucune erreur, aucun operateur
#  rouge, juste une colonne qui manque. Tant que les deux marges ci-dessous
#  sont positives, rien n'est rogne ; si l'une passe sous zero, c'est qu'une
#  ligne ou une colonne vient d'etre ajoutee et qu'il faut remonter la boite.
#  Metrique Menlo mesuree : 10,00 px par caractere et 22,22 px par ligne a
#  fontsizex 13, proportionnel ensuite.
LIGNES_MAX, COLONNES_MAX = 15, 142      # bandeau d'alarme deploye
_k = txt.par.fontsizex.eval() / 13.0
_larg = COLONNES_MAX * 10.0 * _k
_haut = 17.0 * _k + (LIGNES_MAX - 1) * 22.2222 * _k
_bande = rm.op('volume')
_dispo_l = bas.width - (_bande.width if _bande is not None else 0.0)
_dispo_h = bas.par.h.eval()
_marge_l, _marge_h = _dispo_l - _larg, _dispo_h - _haut

mauvais = [(x.path, x.errors()) for x in rm.findChildren() if x.errors()]
print("=" * 66)
print("real_Move installe")
print("=" * 66)
print("  fenetre        FENETRE_REAL_MOVE, 1280x900, titre « real_Move »")
print("  en haut        les dix panneaux, angles rapportes par la Teensy")
print("  en bas         angle, vitesse, couple et couple maximum, par panneau")
print("  motifs LED     aiguillage pose : %s" % ("oui" if bascule_ok else "NON -- MOTIFS_LED introuvable"))
print("                 case « MOTIFS SUR LES ANGLES REELS », decochee par defaut")
print("  interrupteur   dans la fenetre real_Move, lie a la case de MOTIFS_LED")
if fleches_ok:
    print("  point de vue   sept fleches dans la barre, camera cam_real_move")
    print("                 azimut %.1f deg, elevation %.1f deg, distance %.2f"
          % (rm.par.Azimut.eval(), rm.par.Elevation.eval(), rm.par.Distance.eval()))
    print("                 cam1 n'est PAS touchee : elle sert aussi render1")
else:
    print("  point de vue   NON POSE -- voir l'avertissement plus haut")
print("  place          pire cas %d car. x %d lignes = %.0f x %.0f px"
      % (COLONNES_MAX, LIGNES_MAX, _larg, _haut))
print("                 boite %.0f x %.0f px -- marge %.0f en largeur, %.0f en hauteur"
      % (_dispo_l, _dispo_h, _marge_l, _marge_h))
if _marge_l < 0 or _marge_h < 0:
    print("  ATTENTION      LE TABLEAU NE TIENT PLUS DANS SA BOITE.")
    print("                 Il est rogne en silence : remonter bas.par.h et")
    print("                 txt.par.resolutionh, ou baisser txt.par.fontsizex.")
print()
print("  erreurs        %s" % (mauvais if mauvais else "aucune"))
