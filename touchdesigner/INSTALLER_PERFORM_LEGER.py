# ============================================================================
# INSTALLER_PERFORM_LEGER -- le mode Perform qui ne fait qu'envoyer aux ESP32
#
# A executer le projet SAISON_9 ouvert, APRES INSTALLER_CUBE_3D :
#   exec(open('.../touchdesigner/INSTALLER_PERFORM_LEGER.py').read())
# REJOUABLE : relancer met a jour au lieu de creer un doublon.
#
# POURQUOI (Benjamin, 8 octobre 2026). Mesure du 6 octobre : avec l'editeur
# de reseau ouvert sur /project1/scale, TouchDesigner cuit 17 images/s ; en
# mode Perform, 36. Or la chaine LED envoie une trame par image cuite, et les
# rubans WS2812 de 1 280 LED plafonnent a 26 trames/s (38,4 ms par trame).
# Sous 26 images/s, c'est TouchDesigner qui bride les panneaux ; au-dessus, le
# ruban. Le mode Perform allege est fait pour tenir au-dessus : une seule
# fenetre, petite, qui montre le volume imprime par CUBE_3D en 320 x 180 et
# les boutons des deux cubes ; toutes les autres fenetres du projet sont
# fermees pendant le mode et rouvertes a la sortie. L'envoi aux ESP32
# (end_every_frame -> td_send16_panels, DESTINATION 'esp') continue tel quel :
# il ne depend d'aucune fenetre.
#
# CE QUE FAIT L'INSTALLEUR
#   PERFORM_LEGER            containerCOMP 800 x 420 : la vue (CUBE_3D/out),
#                            une ligne d'etat (images/s reelles, maitre,
#                            source des angles, carte, envoi) et quatre
#                            boutons : LANCER LE CUBE, LANCER LE CUBE
#                            STATIQUE, TOUT ETEINDRE, RETOUR EDITEUR.
#   PERFORM_LEGER/logique    entrer() : ferme les autres fenetres (liste
#                            gardee), declare FENETRE_PERFORM_LEGER fenetre
#                            Perform, ui.performMode = True, Actif = 1 ;
#                            sortir() : l'inverse, et SORTIE_SPECTACLE
#                            redevient la fenetre Perform (touche Perform).
#   PERFORM_LEGER/veille     Execute DAT : si l'on quitte le mode par la
#                            touche Echap, sortir() est appele quand meme ;
#                            met a jour la ligne d'etat une fois par seconde
#                            (pas une expression par image).
#   FENETRE_PERFORM_LEGER    windowCOMP de la fenetre.
#   CUBE_3D/rendu            320 x 180 quand PERFORM_LEGER.Actif, 640 x 360
#                            sinon (expression sur la resolution).
#   bouton PERFORM LEGER     dans la section ANIMATION CUBE de SORTIE_SPECTACLE,
#                            sous LANCER VASARELY.
#
# LES BOUTONS DU CUBE NE SONT PAS RECOPIES : ils appellent le texte du bouton
# correspondant de SORTIE_SPECTACLE (un bouton, un texte -- regle du 6 oct.).
# ============================================================================

RACINE = '/project1/scale'
scale = op(RACINE)
assert scale is not None, "Introuvable : " + RACINE
cv = scale.op('CUBE_3D')
assert cv is not None, "CUBE_3D absent : installer INSTALLER_CUBE_3D d'abord."


def enfant(parent_, nom, type_op, x, y):
    o = parent_.op(nom)
    if o is None:
        o = parent_.create(type_op, nom)
        if o.name != nom and parent_.op(nom) is None:
            o.name = nom
        o.nodeX, o.nodeY = x, y
    return o


FOND = (0.035, 0.04, 0.052)
FOND_BOUTON = (0.115, 0.128, 0.158)
ACCENT = (0.08, 0.68, 0.92)
TEXTE = (0.91, 0.93, 0.97)

pl = enfant(scale, 'PERFORM_LEGER', containerCOMP, 2400, -10450)
pl.par.w, pl.par.h = 800, 420      # 800 : quatre etiquettes de 23 caracteres a 9 pt
pl.par.bgcolorr, pl.par.bgcolorg, pl.par.bgcolorb = FOND
pl.par.bgalpha = 1
pl.comment = ("Le mode Perform allege : une seule petite fenetre, le volume imprime "
              "en 320 x 180, les boutons des cubes. Tout le reste est ferme ; "
              "l'envoi aux ESP32 continue.")
pg = None
for p in pl.customPages:
    if p.name == 'Perform':
        pg = p
if pg is None:
    pg = pl.appendCustomPage('Perform')
deja = [q.name for q in pg.pars]
if 'Actif' not in deja:
    q = pg.appendToggle('Actif', label='Mode Perform allege en cours')[0]
    q.val = False
    q.help = ("Coche par entrer(), decoche par sortir(). CUBE_3D lit ce toggle pour "
              "rendre en 320 x 180.")
if 'Entrer' not in deja:
    pg.appendPulse('Entrer', label='Entrer en Perform allege')
if 'Sortir' not in deja:
    pg.appendPulse('Sortir', label="Sortir, rouvrir l'editeur et les fenetres")

# --- la vue : CUBE_3D/out, tout l'espace sauf la barre -----------------------
vue = enfant(pl, 'vue', containerCOMP, 0, 0)
vue.par.hmode, vue.par.vmode = 'fill', 'fixed'
vue.par.h.expr = 'parent().height - 60'
vue.par.y = 60
vue.par.topfill = 'best'
#  CHEMIN RELATIF DEPUIS 'vue' : op('x') cherche dans PERFORM_LEGER, '../' est
#  /project1/scale. Deux '../' pointaient sur /project1 : vue noire, sans erreur.
vue.par.top.expr = "op('../CUBE_3D/out') if op('../CUBE_3D/out') else None"
vue.par.bgcolorr, vue.par.bgcolorg, vue.par.bgcolorb = 0.0, 0.0, 0.0
vue.par.bgalpha = 1
vue.comment = "Ce que les pales impriment, en 320 x 180 pendant le mode."

etat = enfant(pl, 'etat', textCOMP, 0, -120)
etat.par.hmode, etat.par.vmode = 'fill', 'fixed'
etat.par.h = 22
etat.par.y.expr = 'parent().height - me.height'
etat.par.fontsize = 9
try:
    etat.par.fontsizeunits = 'points'
except Exception:
    pass
etat.par.alignx = 'left'
etat.par.bgalpha = 0.55
etat.par.bgcolorr, etat.par.bgcolorg, etat.par.bgcolorb = FOND
etat.par.fontcolorr, etat.par.fontcolorg, etat.par.fontcolorb = TEXTE
etat.par.clickthrough = True
etat.par.text = 'mode Perform allege'
etat.comment = "Ligne d'etat, ecrite une fois par seconde par 'veille' (pas une expression par image)."

# --- la barre de boutons -----------------------------------------------------
barre = enfant(pl, 'barre', containerCOMP, 0, -240)
barre.par.hmode, barre.par.vmode = 'fill', 'fixed'
barre.par.h = 60
barre.par.y = 0
barre.par.align = 'horizlr'
barre.par.spacing = 6
for m in ('marginl', 'marginr', 'margint', 'marginb'):
    setattr(barre.par, m, 8)
barre.par.bgcolorr, barre.par.bgcolorg, barre.par.bgcolorb = FOND
barre.par.bgalpha = 1

CB_CUBE = """# LANCER LE CUBE : le MEME texte que le bouton de SORTIE_SPECTACLE (un bouton, un texte).
def onOffToOn(panelValue):
\tb = op('/project1/scale/SORTIE_SPECTACLE/PANNEAU_COMMANDES/cube_anime/bouton/clic')
\tif b is not None:
\t\tb.module.onOffToOn(panelValue)
\treturn
"""
CB_STATIQUE = """# LANCER LE CUBE STATIQUE : le MEME texte que le bouton de SORTIE_SPECTACLE.
def onOffToOn(panelValue):
\tb = op('/project1/scale/SORTIE_SPECTACLE/PANNEAU_COMMANDES/cube_anime/bouton_statique/clic')
\tif b is not None:
\t\tb.module.onOffToOn(panelValue)
\treturn
"""
CB_ETEINDRE = """# TOUT ETEINDRE : aucun maitre, la chaine d'origine (motifs, variations) reprend.
def onOffToOn(panelValue):
\tfor nom in ('/project1/scale/ANIMATION_CUBE', '/project1/scale/ANNEAU_CONE', '/project1/scale/VASARELY'):
\t\to = op(nom)
\t\tif o is not None:
\t\t\to.par.Actif = 0
\treturn
"""
CB_EDITEUR = """# RETOUR EDITEUR : quitte le mode, rouvre les fenetres, rend la touche Perform a SORTIE_SPECTACLE.
def onOffToOn(panelValue):
\top('/project1/scale/PERFORM_LEGER/logique').module.sortir()
\treturn
"""
M = "op('/project1/scale/ANIMATION_CUBE')"
BOUTONS = (
    ('cube', 0, '(%s.par.Actif and not %s.par.Cubestatique)' % (M, M), 'CUBE EN MARCHE', 'LANCER LE CUBE', CB_CUBE),
    ('statique', 1, '(%s.par.Actif and %s.par.Cubestatique)' % (M, M), 'CUBE STATIQUE EN MARCHE', 'LANCER LE CUBE STATIQUE', CB_STATIQUE),
    ('eteindre', 2, 'False', 'TOUT ETEINDRE', 'TOUT ETEINDRE', CB_ETEINDRE),
    ('editeur', 3, 'False', 'RETOUR EDITEUR', 'RETOUR EDITEUR', CB_EDITEUR),
)
for nom, ordre, actif, texte_on, texte_off, cb in BOUTONS:
    b = enfant(barre, nom, containerCOMP, ordre * 160, 0)
    b.par.hmode, b.par.vmode = 'fill', 'fill'
    b.par.alignorder = ordre
    for c, a, f in (('bgcolorr', ACCENT[0], FOND_BOUTON[0]), ('bgcolorg', ACCENT[1], FOND_BOUTON[1]),
                    ('bgcolorb', ACCENT[2], FOND_BOUTON[2])):
        getattr(b.par, c).expr = '%r if %s else %r' % (a, actif, f)
    b.par.bgalpha.expr = '0.98 if me.panel.inside else 0.85'
    for c, v in zip(('borderar', 'borderag', 'borderab'), ACCENT):
        getattr(b.par, c).val = v
    b.par.borderaalpha.expr = '1.0 if %s else 0.2' % actif
    for bd in ('leftborder', 'rightborder', 'topborder', 'bottomborder'):
        setattr(b.par, bd, 'bordera')
    e = enfant(b, 'etiquette', textCOMP, 0, 0)
    e.par.text.expr = "'%s' if %s else '%s'" % (texte_on, actif, texte_off)
    e.par.hmode, e.par.vmode = 'fill', 'fill'
    e.par.fontsize = 9
    try:
        e.par.fontsizeunits = 'points'
    except Exception:
        pass
    e.par.fontcolorr, e.par.fontcolorg, e.par.fontcolorb = TEXTE
    e.par.bgalpha = 0
    e.par.clickthrough = True
    clic = enfant(b, 'clic', panelexecuteDAT, 0, -100)
    clic.par.panelvalue = 'select'
    clic.par.offtoon = True
    clic.par.valuechange = False
    clic.text = cb

# --- la logique : entrer / sortir ----------------------------------------------
CODE_LOGIQUE = '''# PERFORM_LEGER/logique -- entrer() et sortir(). Appele par les boutons, les
# pulses Entrer / Sortir, et par 'veille' quand on quitte le mode par Echap.
FENETRE = '/project1/scale/FENETRE_PERFORM_LEGER'
SPECTACLE = '/project1/scale/FENETRE_SORTIE_SPECTACLE'


def _pl():
    return op('/project1/scale/PERFORM_LEGER')


def entrer():
    pl = _pl()
    if pl.par.Actif.eval():
        return 'deja en Perform allege'
    fermees = []
    for w in op('/project1/scale').findChildren(type=windowCOMP):
        if w.path != FENETRE and w.isOpen:
            fermees.append(w.path)
            try:
                w.par.winclose.pulse()
            except Exception:
                pass
    pl.store('fenetres_fermees', fermees)
    f = op(FENETRE)
    if f is not None:
        try:
            f.par.setperform.pulse()      # c'est elle que la touche Perform ouvre, pendant le mode
        except Exception:
            pass
    pl.par.Actif = 1
    ui.performMode = True
    return 'Perform allege : %d fenetre(s) fermee(s)' % len(fermees)


def sortir():
    pl = _pl()
    if ui.performMode:
        ui.performMode = False
    pl.par.Actif = 0
    for chemin in pl.fetch('fenetres_fermees', []):
        w = op(chemin)
        if w is not None and not w.isOpen:
            try:
                w.par.winopen.pulse()
            except Exception:
                pass
    pl.store('fenetres_fermees', [])
    s = op(SPECTACLE)
    if s is not None:
        try:
            s.par.setperform.pulse()      # la touche Perform redonne le spectacle en plein ecran
        except Exception:
            pass
    return 'retour editeur'
'''
logique = enfant(pl, 'logique', textDAT, -400, 0)
logique.text = CODE_LOGIQUE

CB_PULSES = """# Les pulses Entrer / Sortir de la page Perform.
def onPulse(par):
\tm = op('logique').module
\tif par.name == 'Entrer':
\t\tprint(m.entrer())
\telif par.name == 'Sortir':
\t\tprint(m.sortir())
\treturn
"""
pulses = enfant(pl, 'pulses', parameterexecuteDAT, -400, -100)
for _nom, _val in (('op', '..'), ('pars', 'Entrer Sortir'), ('onpulse', True)):
    _p = getattr(pulses.par, _nom, None)
    if _p is not None:
        _p.val = _val
pulses.text = CB_PULSES

CODE_VEILLE = '''# PERFORM_LEGER/veille -- une fois par seconde : la ligne d'etat, et le retour
# automatique si l'on a quitte le mode par la touche Echap.
import time

def onFrameStart(frame):
\tpl = me.parent()
\tif pl.par.Actif.eval() and not ui.performMode:
\t\top('logique').module.sortir()
\tt = time.time()
\tif t - float(pl.fetch('t_etat', 0.0)) < 1.0:
\t\treturn
\tpl.store('t_etat', t)
\ttry:
\t\tsc = op('/project1/scale')
\t\tcv = sc.op('CUBE_3D')
\t\tfps = cv.fetch('fps_reel', None) if cv else None
\t\tmaitre = 'aucun (motifs)'
\t\tfor nom, lib in (('VASARELY', 'Vasarely'), ('ANNEAU_CONE', 'anneau'), ('ANIMATION_CUBE', 'cube')):
\t\t\to = sc.op(nom)
\t\t\tif o is not None and o.par.Actif.eval():
\t\t\t\tmaitre = lib
\t\t\t\tif nom == 'ANIMATION_CUBE' and o.par.Cubestatique.eval():
\t\t\t\t\tmaitre = 'cube statique'
\t\t\t\tbreak
\t\tml = sc.op('MOTIFS_LED')
\t\tangles = 'angles Teensy' if (ml is not None and ml.par.Anglesreels.eval()) else 'angles consigne'
\t\tmt = sc.op('MOTEURS_TEENSY')
\t\tcarte = str(mt.par.Chmot.eval())[:48] if mt is not None else '-'
\t\tres = '%dx%d' % (cv.op('rendu').width, cv.op('rendu').height) if cv else '-'
\t\tpl.op('etat').par.text = ('%s img/s reelles  |  %s  |  %s  |  carte : %s  |  vue %s  |  envoi ESP32 <= 26 trames/s'
\t\t                          % ('%.0f' % fps if fps else '?', maitre, angles, carte, res))
\texcept Exception as e:
\t\tpl.op('etat').par.text = 'etat indisponible : %s' % e
\treturn
'''
veille = enfant(pl, 'veille', executeDAT, -400, -200)
veille.par.framestart = True
veille.text = CODE_VEILLE

# --- la fenetre ----------------------------------------------------------------
fen = enfant(scale, 'FENETRE_PERFORM_LEGER', windowCOMP, 2400, -10600)
fen.par.winop = pl
fen.par.title = 'Perform allege -- envoi aux ESP32'
fen.par.size = 'custom'
fen.par.winw, fen.par.winh = 800, 420
fen.par.borders = True
fen.comment = "La seule fenetre du mode Perform allege."

# --- CUBE_3D : 320 x 180 pendant le mode ----------------------------------------
rendu = cv.op('rendu')
rendu.par.outputresolution = 'custom'
rendu.par.resolutionw.expr = "320 if (op('../PERFORM_LEGER') and op('../PERFORM_LEGER').par.Actif) else 640"
rendu.par.resolutionh.expr = "180 if (op('../PERFORM_LEGER') and op('../PERFORM_LEGER').par.Actif) else 360"

# --- le compteur d'images de CUBE_3D donne aussi les images/s reelles ---------
cpt = cv.op('compteur_images')
if cpt is not None and 'fps_reel' not in (cpt.text or ''):
    cpt.text = ("import time\n"
                "def onFrameStart(frame):\n"
                "\tc = me.parent()\n"
                "\tn = int(c.fetch('images_cuites', 0)) + 1\n"
                "\tc.store('images_cuites', n)\n"
                "\tif n % 30 == 0:\n"
                "\t\tt = time.time(); t0 = c.fetch('t_fps', None)\n"
                "\t\tif t0 is not None and t > t0:\n"
                "\t\t\tc.store('fps_reel', round(30.0 / (t - t0), 1))\n"
                "\t\tc.store('t_fps', t)\n"
                "\treturn\n")

# --- le bouton PERFORM LEGER dans SORTIE_SPECTACLE -----------------------------
section = scale.op('SORTIE_SPECTACLE/PANNEAU_COMMANDES/cube_anime')
if section is not None:
    b = enfant(section, 'bouton_perform', containerCOMP, 0, -300)
    b.par.h.expr = 'parent.commandes.par.Hauteurbouton * 1.8'
    b.par.hmode = 'fill'
    b.par.alignorder = 3.5
    for c, f in (('bgcolorr', 'Fondboutonr'), ('bgcolorg', 'Fondboutong'), ('bgcolorb', 'Fondboutonb')):
        getattr(b.par, c).expr = 'parent.commandes.par.' + f
    b.par.bgalpha.expr = '0.98 if me.panel.inside else 0.82'
    for c, e in (('borderar', 'Accentr'), ('borderag', 'Accentg'), ('borderab', 'Accentb')):
        getattr(b.par, c).expr = 'parent.commandes.par.' + e
    b.par.borderaalpha = 0.16
    for bd in ('leftborder', 'rightborder', 'topborder', 'bottomborder'):
        setattr(b.par, bd, 'bordera')
    e = enfant(b, 'etiquette', textCOMP, 0, 0)
    e.par.text = 'PERFORM LEGER (envoi ESP32)'
    e.par.hmode, e.par.vmode = 'fill', 'fill'
    e.par.fontsize = 10
    try:
        e.par.fontsizeunits = 'points'
    except Exception:
        pass
    for c, t in (('fontcolorr', 'Texter'), ('fontcolorg', 'Texteg'), ('fontcolorb', 'Texteb')):
        getattr(e.par, c).expr = 'parent.commandes.par.' + t
    e.par.bgalpha = 0
    e.par.clickthrough = True
    clic = enfant(b, 'clic', panelexecuteDAT, 0, -100)
    clic.par.panelvalue = 'select'
    clic.par.offtoon = True
    clic.par.valuechange = False
    clic.text = """# PERFORM LEGER : une seule petite fenetre, l'envoi aux ESP32 continue.
def onOffToOn(panelValue):
\tprint(op('/project1/scale/PERFORM_LEGER/logique').module.entrer())
\treturn
"""

print('=' * 66)
print('PERFORM_LEGER installe')
print('=' * 66)
print('  fenetre      : %s (%dx%d)' % (fen.path, fen.par.winw.eval(), fen.par.winh.eval()))
print('  vue          : CUBE_3D/out en 320x180 pendant le mode (640x360 sinon)')
print('  entrer       : bouton PERFORM LEGER dans SORTIE_SPECTACLE, ou PERFORM_LEGER.Entrer')
print('  sortir       : RETOUR EDITEUR dans la fenetre, Echap, ou PERFORM_LEGER.Sortir')
mauvais = [(x.path, x.errors()) for x in pl.findChildren() if x.errors()]
print('  erreurs      : %s' % (mauvais if mauvais else 'aucune'))
