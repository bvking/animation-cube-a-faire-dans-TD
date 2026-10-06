# ============================================================================
# INSTALLER_ANNEAU_CONE -- un cone de revolution qui respire, sur les panneaux
#
# Sur le MEME principe que ANIMATION_CUBE : la forme est FIGEE DANS L'ESPACE
# aux vraies cotes (un cone d'axe z, la paroi seule s'allume), la chaine LED
# est prise par une entree supplementaire du switch panel_mask_output, et
# l'horloge suit par defaut la rotation reellement balayee par les lames.
# La BASE (au fond, lame 9) et le SOMMET (devant, lame 0) grandissent et
# retrecissent -- en opposition par defaut : le cone bascule en respirant.
#
# A executer le projet SAISON_9 ouvert, APRES INSTALLER_ANIMATION_CUBE
# (le bouton vient se placer sous CUBE EN MARCHE dans SORTIE_SPECTACLE) :
#   - glisser ce fichier dans le reseau puis clic droit -> Run Script,
#   - ou au Textport :
#     exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/INSTALLER_ANNEAU_CONE.py').read())
#
# RIEN NE CHANGE tant que le bouton n'est pas presse (Actif decoche).
# Un seul maitre a la fois : allumer l'anneau coupe le cube, et inversement.
# Relancable sans danger. Pour tout retirer : DESINSTALLER_ANNEAU_CONE.py.
# Ensuite : Fichier -> Enregistrer sous.
# ============================================================================

import json

CHEMIN_SCALE = '/project1/scale'
NOM_MODULE = 'ANNEAU_CONE'
NOM_COMMENT = 'COMMENT_58_ANNEAU_CONE'
EXPR_INDEX_ORIGINE = ("2 if op('MOTIFS_LED').par.Motif.eval() != 'off' "
                      "else int(op('MASK_TEXTURE_BY_ANGLE_NO_GSWITCH_TD').par.Masque)")

# ----------------------------------------------------------------------------
# GLSL : l'image 160x80 envoyee aux panneaux. Un cone d'axe z : chaque lame
# n'allume que la paroi au rayon de SA profondeur. Pas besoin de l'angle :
# un cone est invariant par rotation -- c'est l'horloge qui suit les lames.
# ----------------------------------------------------------------------------
GLSL_CONE = """// ANNEAU_CONE -- la paroi d'un cone de revolution, FIGEE DANS L'ESPACE.
// Sortie 160 x 80 = dix bandes de 160 x 8, panneau 0 EN BAS (convention
// panel_mask_layout / MOTIFS_LED). Toutes les cotes en CENTIMETRES.
// La base est AU FOND (lame 9, z = -45), le sommet DEVANT (lame 0, z = +45).
// Un cone est invariant par rotation : pas besoin de l'angle des lames ici ;
// c'est l'horloge (rotation_compteur) qui se cale sur leur balayage.

uniform vec4 uForme;   // x: rayon a la base (cm), y: rayon au sommet (cm),
                       // z: demi-epaisseur de la paroi (cm), w: libre
uniform vec4 uCouleur; // rgb: couleur ; a: luminosite 0..1

out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    int panneau = int(clamp(uv.y * 10.0, 0.0, 9.0));

    // Distance reelle du texel a l'axe : d le long de la lame, o en travers
    // (8 rangees au pas de 1 cm), comme dans ANIMATION_CUBE.
    float d = (uv.x - 0.5) * 160.0;
    float j = floor(fract(uv.y * 10.0) * 8.0);
    float o = j - 3.5;
    float r = length(vec2(d, o));

    // Profondeur normalisee : 0 au fond (lame 9, la BASE), 1 devant (le SOMMET)
    float t = (4.5 - float(panneau)) / 9.0 + 0.5;
    float R = mix(uForme.x, uForme.y, t);

    float allume = (abs(r - R) <= uForme.z) ? 1.0 : 0.0;
    fragColor = TDOutputSwizzle(vec4(uCouleur.rgb * (allume * uCouleur.a), 1.0));
}
"""

# ----------------------------------------------------------------------------
# Callbacks
# ----------------------------------------------------------------------------
CB_ROTATION = """# rotation_compteur -- compte les demi-tours REELLEMENT balayes par les lames.
# Lit l'angle de la lame 0 dans angle_lame0 (en degres, un echantillon par
# lame, la MEME source que les motifs : consigne ou positions Teensy selon
# MOTIFS_LED.Anglesreels), le deroule pas a pas (saut ramene dans -180..+180)
# et accumule en demi-tours, en valeur absolue : vitesse lente, rapide,
# variable ou inversee, la respiration suit toujours vers l'avant.
# A l'arret des moteurs, la forme se fige -- rien n'est balaye.
def onCook(scriptOp):
\tscriptOp.clear()
\tcomp = parent()
\t# Un canal multi-echantillons (un par lame) : on lit explicitement
\t# l'echantillon 0. float(canal) sans index lirait a l'index du temps.
\tsrc = op('angle_lame0')
\tangle = None
\tif src is not None and src.numChans and src.numSamples:
\t\tangle = float(src[0][0])
\tdernier = comp.fetch('rot_dernier', None, search=False)
\ttotal = float(comp.fetch('rot_demitours', 0.0, search=False))
\tif angle is not None and dernier is not None:
\t\td = (angle - dernier + 180.0) % 360.0 - 180.0
\t\tif comp.par.Lecture:
\t\t\ttotal += abs(d) / 180.0
\tif angle is not None:
\t\tcomp.store('rot_dernier', angle)
\tcomp.store('rot_demitours', total)
\tscriptOp.appendChan('demitours')[0] = total
\treturn
"""

CB_FORME = """# forme -- les deux rayons du cone a cet instant, en canaux CHOP.
# phase = demi-tours balayes / Demitoursparcycle (mode rotation), ou
#         secondes de lecture / Periode (mode temps).
# rbase et rsommet oscillent de +/- Amplitude autour de leur rayon de repos,
# en opposition si Opposition est coche (quand la base grandit, le sommet
# retrecit : le cone bascule). Bornes : 0 .. 79.5 - Epaisseur, pour que la
# paroi reste entiere sur les lames.
import math

def onCook(scriptOp):
\tscriptOp.clear()
\tcomp = parent()
\tif str(comp.par.Modehorloge) == 'rotation':
\t\tphase = float(op('rotation_compteur')['demitours']) / max(float(comp.par.Demitoursparcycle), 1e-6)
\telse:
\t\tphase = float(op('compteur')['v']) / max(float(comp.par.Periode), 1e-6)
\tamp = float(comp.par.Amplitude)
\tdec = math.pi if comp.par.Opposition else 0.0
\tborne = max(79.5 - float(comp.par.Epaisseur), 0.0)
\trb = float(comp.par.Rayonbase) + amp * math.sin(2.0 * math.pi * phase)
\trs = float(comp.par.Rayonsommet) + amp * math.sin(2.0 * math.pi * phase + dec)
\trb = min(max(rb, 0.0), borne)
\trs = min(max(rs, 0.0), borne)
\tfor nom, v in (('rbase', rb), ('rsommet', rs), ('phase', phase)):
\t\tscriptOp.appendChan(nom)[0] = v
\treturn
"""

CB_REMETTRE = """# Remettre -- ramene la respiration a sa phase 0 (les deux horloges).
def onPulse(par):
\tif par.name == 'Remettre':
\t\tc = op('compteur')
\t\tp = getattr(c.par, 'resetpulse', None)
\t\tif p is None:
\t\t\tp = getattr(c.par, 'reset', None)
\t\tif p is not None:
\t\t\tp.pulse()
\t\tparent().store('rot_demitours', 0.0)
\treturn
"""

CB_BOUTON_ANNEAU = """# Le clic bascule ANNEAU_CONE.Actif ; en s'allumant il coupe les autres
# maitres de la chaine LED (cube, Vasarely) : un seul maitre a la fois.
# CHAQUE BOUTON NE CONNAIT QUE LUI-MEME ET LA LISTE DES AUTRES : aucun
# installeur ne reecrit le bouton d'un autre module (regle du 6 octobre 2026).
def onOffToOn(panelValue):
\tp = op('/project1/scale/ANNEAU_CONE').par.Actif
\tp.val = 0 if p else 1
\tif p:
\t\tfor autre in ('/project1/scale/ANIMATION_CUBE', '/project1/scale/VASARELY'):
\t\t\to = op(autre)
\t\t\tif o is not None:
\t\t\t\to.par.Actif = 0
\treturn
"""


LISEZ_MOI = """ANNEAU_CONE -- LA PAROI D'UN CONE QUI RESPIRE

CE QUE C'EST
  Un cone de revolution d'axe z, fige dans l'espace : chaque lame
  n'allume que la paroi au rayon de SA profondeur (base au fond, lame 9 ;
  sommet devant, lame 0), et l'oeil recompose le cone en persistance.
  La base et le sommet grandissent et retrecissent de +/- Amplitude --
  en opposition par defaut : le cone bascule en respirant, jusqu'a
  s'inverser quand les deux rayons se croisent.

LE RESEAU
  angle_lame0 / rotation_compteur
              l'angle de la lame 0 (meme source que les motifs), deroule
              et cumule en demi-tours : l'horloge du mode 'rotation'
  vitesse -> compteur (Speed)   les secondes de lecture, pour le mode 'temps'
  forme       Script CHOP : rbase et rsommet (cm) a cet instant, bornes
              a 0 .. 79.5 - Epaisseur
  cone        GLSL TOP 160x80 : |distance a l'axe - rayon de la lame| <=
              Epaisseur. Pas d'entree : un cone est invariant par rotation
  out_led     vers le switch panel_mask_output (entree ajoutee)

L'HORLOGE SUIT LA ROTATION (mode par defaut)
  La phase de respiration avance avec les demi-tours REELLEMENT balayes
  (Demitoursparcycle par cycle, 8 par defaut : a 2 tours/s, une
  respiration dure 2 s). Vitesse lente, rapide, variable ou inversee :
  la forme evolue au rythme du balayage, et se fige moteurs arretes.
  L'horloge suit la lame 0 : pendant une ouverture d'eventail, les
  lames en retard respirent avec un leger decalage -- sans gravite
  pour une forme continue.
  La respiration etant continue, la paroi glisse doucement d'un secteur
  a l'autre pendant un passage -- c'est voulu, comme la RESPIRATION de
  MOTIFS_LED. Le mode 'temps' (Periode en secondes) previsualise sans
  rotation.

QUI PREND LA MAIN
  Actif coche -> le switch panel_mask_output passe sur l'entree de ce
  module : panneaux reels, simulateur et rendu 3D suivent. Un seul
  maitre a la fois : le bouton coupe ANIMATION_CUBE en s'allumant, et
  inversement. Decoche -> tout redevient comme avant, au bit pres.

REGLAGES (page Anneau)
  Actif            le bouton de SORTIE_SPECTACLE fait pareil
  Lecture          fige / relance la respiration (sans saut)
  Modehorloge      'rotation' (defaut) ou 'temps'
  Demitoursparcycle  demi-tours par respiration (8)
  Periode          duree d'une respiration en mode temps (2 s)
  Rayonbase        rayon de repos a la base, au fond (60 cm)
  Rayonsommet      rayon de repos au sommet, devant (20 cm)
  Amplitude        ampleur de la respiration (25 cm)
  Opposition       base et sommet en opposition de phase (coche)
  Epaisseur        demi-epaisseur de la paroi (4 cm)
  Couleur          bleu par defaut
  Luminosite       gain simple 0..1
  Remettre         revient a la phase 0

POUR TOUT RETIRER
  DESINSTALLER_ANNEAU_CONE.py du depot (ou desinstaller() au Textport).
  La sauvegarde de l'expression du switch vit dans le DAT 'sauvegarde'.
  Desinstaller l'anneau AVANT le cube si les deux doivent partir.
"""

TEXTE_COMMENT = """ANNEAU_CONE -- UN VOLUME SIMPLE QUI RESPIRE, APRES LE CUBE JOUE

CE QUE C'EST
  La paroi d'un cone de revolution d'axe z, base au fond (lame 9) et
  sommet devant (lame 0), dont les deux rayons grandissent et
  retrecissent de +/- Amplitude -- en opposition par defaut, si bien que
  le cone bascule et s'inverse en respirant. Construit sur le modele
  d'ANIMATION_CUBE (COMMENT_57) : vraies cotes en cm, chaine LED prise
  par une entree du switch panel_mask_output, horloge calee sur les
  demi-tours reellement balayes (une respiration = Demitoursparcycle
  demi-tours, 8 par defaut), mode temps en secours.

LA DIFFERENCE AVEC LE CUBE
  Un cone est invariant par rotation : le GLSL n'a pas besoin de l'angle
  des lames, seulement de leur profondeur. Et la forme etant continue,
  la respiration n'est pas quantifiee par demi-tour comme les images du
  cube : la paroi glisse doucement d'un secteur a l'autre, comme la
  RESPIRATION de MOTIFS_LED.

UN SEUL MAITRE A LA FOIS
  Le bouton ANNEAU (sous CUBE EN MARCHE, section ANIMATION CUBE) coupe le
  cube en s'allumant, et le bouton du cube coupe l'anneau : les deux
  modules ne se battent jamais pour le switch. Decocher les deux rend la
  main a la chaine d'origine (motifs, variations), au bit pres.

POUR TOUT RETIRER
  DESINSTALLER_ANNEAU_CONE.py (retirer l'anneau AVANT le cube).
"""


def _detruire(chemin):
    o = op(chemin)
    if o:
        o.destroy()


def _texte(dat, contenu):
    dat.text = contenu


def installer():
    scale = op(CHEMIN_SCALE)
    assert scale, "Introuvable : " + CHEMIN_SCALE + " -- ouvrir le projet SAISON_9 d'abord."
    sw = scale.op('panel_mask_output')
    motifs = scale.op('MOTIFS_LED/angles_choix')
    commandes = scale.op('SORTIE_SPECTACLE/PANNEAU_COMMANDES')
    for o, nom in ((sw, 'panel_mask_output'), (motifs, 'MOTIFS_LED/angles_choix'),
                   (commandes, 'SORTIE_SPECTACLE/PANNEAU_COMMANDES')):
        assert o, "Introuvable : " + nom + " -- ce script vise le projet SAISON_9."

    # ---- Reinstallation : retrouver l'expression interieure du switch -------
    expr_actuelle = sw.par.index.expr or ''
    ancien = scale.op(NOM_MODULE)
    expr_interieure = None
    if ancien and ancien.op('sauvegarde'):
        try:
            expr_interieure = json.loads(ancien.op('sauvegarde').text).get('index')
        except Exception:
            pass
    if not expr_interieure:
        if NOM_MODULE in expr_actuelle:
            # Pas de sauvegarde exploitable : secours raisonnable
            if scale.op('ANIMATION_CUBE'):
                expr_interieure = ("3 if op('ANIMATION_CUBE').par.Actif else (%s)"
                                   % EXPR_INDEX_ORIGINE)
            else:
                expr_interieure = EXPR_INDEX_ORIGINE
        else:
            expr_interieure = expr_actuelle or str(int(sw.par.index.eval()))

    # Expression interieure remise AVANT de raser : un echec plus loin laisse
    # la chaine LED sur son comportement sans anneau.
    if NOM_MODULE in (sw.par.index.expr or ''):
        sw.par.index.expr = expr_interieure
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(commandes.path + '/cube_anime/bouton_anneau')
    _detruire(commandes.path + '/cube_anime/etat_anneau')
    _detruire(commandes.path + '/animations_3d')
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)

    # ------------------------------------------------------------------ module
    comp = scale.create(baseCOMP, NOM_MODULE)
    comp.nodeX, comp.nodeY = 2100, -10900
    comp.nodeWidth, comp.nodeHeight = 220, 140
    comp.color = (0.2, 0.55, 0.9)
    comp.comment = ("La paroi d'un cone qui respire (base et sommet en "
                    "opposition). Entree supplementaire de panel_mask_output.")

    page = comp.appendCustomPage('Anneau')
    p = page.appendToggle('Actif', label='ANNEAU SUR LES PANNEAUX (prend la main)')[0]
    p.val = False
    p = page.appendToggle('Lecture', label='Faire respirer')[0]
    p.default = True; p.val = True
    p = page.appendMenu('Modehorloge', label="Horloge de la respiration")[0]
    p.menuNames = ['rotation', 'temps']
    p.menuLabels = ['Suit la rotation (Demi-tours par cycle)',
                    'Au temps (Periode en secondes)']
    p.default = 'rotation'; p.val = 'rotation'
    p = page.appendFloat('Demitoursparcycle', label='Demi-tours par respiration')[0]
    p.default = 8; p.val = 8; p.normMin = 1; p.normMax = 32
    p.clampMin = True; p.min = 0.5
    p = page.appendFloat('Periode', label='Periode (s, mode temps)')[0]
    p.default = 2; p.val = 2; p.normMin = 0.2; p.normMax = 10
    p.clampMin = True; p.min = 0.1
    p = page.appendFloat('Rayonbase', label='Rayon a la base, au fond (cm)')[0]
    p.default = 60; p.val = 60; p.normMin = 0; p.normMax = 79
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 79
    p = page.appendFloat('Rayonsommet', label='Rayon au sommet, devant (cm)')[0]
    p.default = 20; p.val = 20; p.normMin = 0; p.normMax = 79
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 79
    p = page.appendFloat('Amplitude', label='Amplitude de respiration (cm)')[0]
    p.default = 25; p.val = 25; p.normMin = 0; p.normMax = 79
    p.clampMin = True; p.min = 0
    p = page.appendToggle('Opposition', label='Base et sommet en opposition')[0]
    p.default = True; p.val = True
    p = page.appendFloat('Epaisseur', label='Demi-epaisseur de la paroi (cm)')[0]
    p.default = 4; p.val = 4; p.normMin = 1; p.normMax = 10
    p.clampMin = True; p.min = 0.5
    pg = page.appendRGB('Couleur', label="Couleur de l'anneau")
    for par_c, v in zip(pg, (0.0, 0.45, 1.0)):
        par_c.default = v; par_c.val = v
    p = page.appendFloat('Luminosite', label='Luminosite')[0]
    p.default = 1; p.val = 1; p.normMin = 0; p.normMax = 1
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 1
    page.appendPulse('Remettre', label='Revenir a la phase 0')

    # ---- horloges ----
    vitesse = comp.create(constantCHOP, 'vitesse')
    vitesse.nodeX, vitesse.nodeY = -700, 0
    # Pas de 'or' entre deux getattr : la truthiness d'un Par est sa VALEUR,
    # et une valeur vide ecarterait le parametre canonique au profit de l'alias.
    p_nom = getattr(vitesse.par, 'const0name', None)
    if p_nom is None:
        p_nom = getattr(vitesse.par, 'name0', None)
    p_val = getattr(vitesse.par, 'const0value', None)
    if p_val is None:
        p_val = getattr(vitesse.par, 'value0', None)
    assert p_nom is not None and p_val is not None, \
        'Constant CHOP : parametres de la constante 0 introuvables.'
    p_nom.val = 'v'
    p_val.expr = '1.0 * parent().par.Lecture'
    compteur = comp.create(speedCHOP, 'compteur')
    compteur.nodeX, compteur.nodeY = -500, 0
    compteur.inputConnectors[0].connect(vitesse)

    angle_lame0 = comp.create(selectCHOP, 'angle_lame0')
    angle_lame0.nodeX, angle_lame0.nodeY = -950, -130
    p = getattr(angle_lame0.par, 'chops', None)
    if p is None:
        p = getattr(angle_lame0.par, 'chop', None)
    assert p is not None, 'Select CHOP : parametre chops introuvable.'
    p.val = '../MOTIFS_LED/angles_choix'
    rot_cb = comp.create(textDAT, 'rotation_callbacks')
    rot_cb.nodeX, rot_cb.nodeY = -950, -260
    _texte(rot_cb, CB_ROTATION)
    rotation = comp.create(scriptCHOP, 'rotation_compteur')
    rotation.nodeX, rotation.nodeY = -770, -130
    rotation.par.callbacks = 'rotation_callbacks'

    remise = comp.create(parameterexecuteDAT, 'remise')
    remise.nodeX, remise.nodeY = -500, -120
    for noms, valeur in ((('op', 'ops'), '..'),
                         (('pars', 'parm', 'parms'), 'Remettre'),
                         (('onpulse', 'pulse'), True)):
        for nom in noms:
            par_x = getattr(remise.par, nom, None)
            if par_x is not None:
                par_x.val = valeur
                break
        else:
            print('  (a regler a la main sur %s : %s)' % (remise.path, noms))
    _texte(remise, CB_REMETTRE)

    # ---- la forme ----
    forme_cb = comp.create(textDAT, 'forme_callbacks')
    forme_cb.nodeX, forme_cb.nodeY = -300, -120
    _texte(forme_cb, CB_FORME)
    forme = comp.create(scriptCHOP, 'forme')
    forme.nodeX, forme.nodeY = -300, 0
    forme.par.callbacks = 'forme_callbacks'

    # ---- le GLSL ----
    code = comp.create(textDAT, 'cone_pixel')
    code.nodeX, code.nodeY = -100, -120
    _texte(code, GLSL_CONE)
    cone = comp.create(glslTOP, 'cone')
    cone.nodeX, cone.nodeY = -100, 80
    cone.par.pixeldat = 'cone_pixel'
    cone.par.outputresolution = 'custom'
    cone.par.resolutionw = 160
    cone.par.resolutionh = 80
    try:
        cone.par.format = 'rgba8fixed'
    except Exception:
        pass

    unis = [
        ('uForme', ("op('forme')['rbase']", "op('forme')['rsommet']",
                    'parent().par.Epaisseur', '0')),
        ('uCouleur', ('parent().par.Couleurr', 'parent().par.Couleurg',
                      'parent().par.Couleurb', 'parent().par.Luminosite')),
    ]
    try:
        if cone.seq.vec.numBlocks < len(unis):
            cone.seq.vec.numBlocks = len(unis)
    except Exception:
        pass
    for i, (nom, (ex, ey, ez, ew)) in enumerate(unis):
        p_nom = getattr(cone.par, 'vec%dname' % i, None)
        if p_nom is None:
            p_nom = getattr(cone.par, 'uniname%d' % i, None)
        assert p_nom is not None, 'GLSL TOP : nom d uniforme introuvable (bloc %d).' % i
        p_nom.val = nom
        prefixe = ('vec%dvalue' % i
                   if getattr(cone.par, 'vec%dvaluex' % i, None) is not None
                   else 'value%d' % i)
        getattr(cone.par, prefixe + 'x').expr = ex
        getattr(cone.par, prefixe + 'y').expr = ey
        getattr(cone.par, prefixe + 'z').expr = ez
        getattr(cone.par, prefixe + 'w').expr = ew

    sortie = comp.create(outTOP, 'out_led')
    sortie.nodeX, sortie.nodeY = 150, 80
    sortie.inputConnectors[0].connect(cone)
    sortie.viewer = True

    lisez = comp.create(textDAT, 'LISEZ_MOI')
    lisez.nodeX, lisez.nodeY = -700, 150
    _texte(lisez, LISEZ_MOI)
    lisez.viewer = True

    sauvegarde = comp.create(textDAT, 'sauvegarde')
    sauvegarde.nodeX, sauvegarde.nodeY = -700, -400
    _texte(sauvegarde, json.dumps({'index': expr_interieure}, indent=1))

    # ------------------------------------------------- branchement du switch
    def entrees_module():
        return [i for i, e in enumerate(sw.inputs)
                if e and ('/' + NOM_MODULE) in e.path]
    if not entrees_module():
        comp.outputConnectors[0].connect(sw)
    rang = entrees_module()
    if len(rang) != 1:
        try:
            comp.outputConnectors[0].disconnect()
        except Exception:
            pass
        raise AssertionError(
            'Entree du switch inattendue pour out_led : %s -- branchement '
            'retire, chaine LED inchangee.' % rang)
    sw.par.index.expr = ("%d if op('ANNEAU_CONE').par.Actif else (%s)"
                         % (rang[0], expr_interieure))

    # --------------------------------------------- le bouton, sous le cube
    section = commandes.op('cube_anime')
    if section is None:
        # Cube pas installe : section a nous, meme style maison
        section = commandes.create(containerCOMP, 'animations_3d')
        section.nodeX, section.nodeY = 400, -200
        section.par.w = 230
        section.par.hmode = 'fixed'
        section.par.vmode = 'fill'
        section.par.alignorder = 50
        section.par.align = 'verttb'
        section.par.spacing = 4
        for m in ('marginl', 'marginr', 'margint', 'marginb'):
            setattr(section.par, m, 6)
        for c, e in (('bgcolorr', 'Fondsectionr'), ('bgcolorg', 'Fondsectiong'),
                     ('bgcolorb', 'Fondsectionb')):
            getattr(section.par, c).expr = 'parent.commandes.par.' + e
        section.par.bgalpha = 1
        for c, e in (('borderar', 'Accentr'), ('borderag', 'Accentg'),
                     ('borderab', 'Accentb')):
            getattr(section.par, c).expr = 'parent.commandes.par.' + e
        section.par.borderaalpha = 0.35
        for b in ('leftborder', 'rightborder', 'topborder', 'bottomborder'):
            setattr(section.par, b, 'bordera')
        titre = section.create(textCOMP, 'titre')
        titre.par.text = 'ANNEAU CONE'
        titre.par.h.expr = 'parent.commandes.par.Hauteurtitre'
        titre.par.hmode = 'fill'
        titre.par.fontsize = 13
        try:
            titre.par.fontsizeunits = 'points'
        except Exception:
            pass
        for c, e in (('fontcolorr', 'Accentr'), ('fontcolorg', 'Accentg'),
                     ('fontcolorb', 'Accentb')):
            getattr(titre.par, c).expr = 'parent.commandes.par.' + e
        titre.par.alignx = 'left'
        titre.par.bgalpha = 0
        titre.par.alignorder = 0
    else:
        # La section ANIMATION CUBE accueille aussi l'anneau, juste sous le
        # bouton du cube ; son titre ne change pas.
        etat_cube = section.op('etat')
        if etat_cube is not None:
            etat_cube.par.alignorder = 3
        #  Le bouton du cube n'est PAS reecrit : son propre texte (INSTALLER_
        #  ANIMATION_CUBE) coupe deja l'anneau et Vasarely. Une seule source.

    chemin_actif = "op('/project1/scale/ANNEAU_CONE').par.Actif"
    bouton = section.create(containerCOMP, 'bouton_anneau')
    bouton.par.h.expr = 'parent.commandes.par.Hauteurbouton * 1.8'
    bouton.par.hmode = 'fill'
    bouton.par.alignorder = 2
    for c, a, f in (('bgcolorr', 'Accentr', 'Fondboutonr'),
                    ('bgcolorg', 'Accentg', 'Fondboutong'),
                    ('bgcolorb', 'Accentb', 'Fondboutonb')):
        getattr(bouton.par, c).expr = ('parent.commandes.par.%s if %s else '
                                       'parent.commandes.par.%s' % (a, chemin_actif, f))
    bouton.par.bgalpha.expr = '0.98 if me.panel.inside else 0.82'
    for c, e in (('borderar', 'Accentr'), ('borderag', 'Accentg'),
                 ('borderab', 'Accentb')):
        getattr(bouton.par, c).expr = 'parent.commandes.par.' + e
    bouton.par.borderaalpha.expr = '1.0 if %s else 0.16' % chemin_actif
    for b in ('leftborder', 'rightborder', 'topborder', 'bottomborder'):
        setattr(bouton.par, b, 'bordera')

    etiquette = bouton.create(textCOMP, 'etiquette')
    etiquette.par.text.expr = ('"ANNEAU EN MARCHE" if %s else "LANCER L ANNEAU"'
                               % chemin_actif)
    etiquette.par.hmode = 'fill'
    etiquette.par.vmode = 'fill'
    etiquette.par.fontsize = 10
    try:
        etiquette.par.fontsizeunits = 'points'
    except Exception:
        pass
    for c, e in (('fontcolorr', 'Texter'), ('fontcolorg', 'Texteg'),
                 ('fontcolorb', 'Texteb')):
        getattr(etiquette.par, c).expr = 'parent.commandes.par.' + e
    etiquette.par.bgalpha = 0
    etiquette.par.clickthrough = True

    clic = bouton.create(panelexecuteDAT, 'clic')
    clic.par.panelvalue = 'select'
    clic.par.offtoon = True
    clic.par.valuechange = False
    _texte(clic, CB_BOUTON_ANNEAU)

    etat = section.create(textCOMP, 'etat_anneau')
    etat.par.text.expr = (
        "'anneau : base %d / sommet %d cm' % "
        "(int(op('/project1/scale/ANNEAU_CONE/forme')['rbase']), "
        "int(op('/project1/scale/ANNEAU_CONE/forme')['rsommet']))")
    etat.par.h = 20
    etat.par.hmode = 'fill'
    etat.par.fontsize = 8.5
    try:
        etat.par.fontsizeunits = 'points'
    except Exception:
        pass
    for c, e in (('fontcolorr', 'Texter'), ('fontcolorg', 'Texteg'),
                 ('fontcolorb', 'Texteb')):
        getattr(etat.par, c).expr = 'parent.commandes.par.' + e
    etat.par.alignx = 'left'
    etat.par.bgalpha = 0
    etat.par.clickthrough = True
    etat.par.alignorder = 4

    # ------------------------------------------------- documentation maison
    comment = scale.create(textDAT, NOM_COMMENT)
    comment.nodeX, comment.nodeY = 2100, -11100
    comment.viewer = True
    _texte(comment, TEXTE_COMMENT)

    # ------------------------------------------------------------- MESURE
    print('')
    print('ANNEAU_CONE installe. MESURE :')
    try:
        sortie.cook(force=True)
        forme.cook(force=True)
        rb = float(forme['rbase'])
        rs = float(forme['rsommet'])
        print('  rayons a cet instant : base %.1f cm, sommet %.1f cm' % (rb, rs))
        arr = sortie.numpyArray()
        if arr is not None:
            allumees = int((arr[..., :3].max(axis=-1) > 0.05).sum())
            print('  texels allumes : %d sur 12800' % allumees)
    except Exception as e:
        print('  MESURE incomplete (%s) -- l installation elle-meme est terminee.' % e)
    err = comp.errors(recurse=True)
    print('  erreurs dans le module : %s' % (err if err else 'aucune'))
    print('  switch : entree %d, expression posee ; Actif est DECOCHE.' % rang[0])
    print('  Bouton : SORTIE_SPECTACLE > ANIMATION CUBE > LANCER L ANNEAU')
    print('  (il coupe le cube en s allumant, et inversement).')
    print('  Penser a : Fichier > Enregistrer sous.')
    return comp


def desinstaller():
    scale = op(CHEMIN_SCALE)
    if not scale:
        print('Introuvable :', CHEMIN_SCALE)
        return
    sw = scale.op('panel_mask_output')
    commandes = scale.op('SORTIE_SPECTACLE/PANNEAU_COMMANDES')
    expr_interieure = None
    comp = scale.op(NOM_MODULE)
    if comp and comp.op('sauvegarde'):
        try:
            expr_interieure = json.loads(comp.op('sauvegarde').text).get('index')
        except Exception:
            pass
    if not expr_interieure:
        if scale.op('ANIMATION_CUBE'):
            expr_interieure = ("3 if op('ANIMATION_CUBE').par.Actif else (%s)"
                               % EXPR_INDEX_ORIGINE)
        else:
            expr_interieure = EXPR_INDEX_ORIGINE
    if sw:
        sw.par.index.expr = expr_interieure
    if commandes:
        _detruire(commandes.path + '/cube_anime/bouton_anneau')
        _detruire(commandes.path + '/cube_anime/etat_anneau')
        _detruire(commandes.path + '/animations_3d')
        section = commandes.op('cube_anime')
        if section is not None:
            etat_cube = section.op('etat')
            if etat_cube is not None:
                etat_cube.par.alignorder = 2
            #  Le bouton du cube garde son texte : il ignore un module absent.
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)
    print('ANNEAU_CONE retire ; switch et bouton du cube remis comme avant.')
    print('Penser a : Fichier > Enregistrer sous.')


installer()
