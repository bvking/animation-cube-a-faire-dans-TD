# ============================================================================
# INSTALLER_VASARELY -- une grille op-art bombee/creusee sur les panneaux
#
# Dans l'esprit de la serie Vega de Vasarely : une grille reguliere de
# N x N cellules colorees, deformee par une ou plusieurs calottes spheriques
# qui la font paraitre bombee ou creusee. Meme principe que ANIMATION_CUBE
# et ANNEAU_CONE : le motif est FIGE DANS L'ESPACE (plan frontal du disque
# balaye, comme le mode TABLEAU de MOTIFS_LED), chaque texel retrouve sa
# cellule par la deformation INVERSE (rendu par pixel), et le relief respire
# au rythme des demi-tours reellement balayes par les lames.
#
# A executer le projet SAISON_9 ouvert, APRES le cube et l'anneau
# (le bouton vient se placer sous LANCER L ANNEAU) :
#   - glisser ce fichier dans le reseau puis clic droit -> Run Script,
#   - ou au Textport :
#     exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/INSTALLER_VASARELY.py').read())
#
# RIEN NE CHANGE tant que le bouton n'est pas presse (Actif decoche).
# Un seul maitre a la fois : chaque bouton (cube, anneau, vasarely) coupe
# les deux autres. Relancable sans danger.
# Pour tout retirer : desinstaller() (ou DESINSTALLER a venir du depot).
# Ensuite : Fichier -> Enregistrer sous.
# ============================================================================

import json

CHEMIN_SCALE = '/project1/scale'
NOM_MODULE = 'VASARELY'
NOM_COMMENT = 'COMMENT_59_VASARELY'
EXPR_INDEX_ORIGINE = ("2 if op('MOTIFS_LED').par.Motif.eval() != 'off' "
                      "else int(op('MASK_TEXTURE_BY_ANGLE_NO_GSWITCH_TD').par.Masque)")

# ----------------------------------------------------------------------------
# GLSL : l'image 160x80 envoyee aux panneaux, rendu PAR PIXEL en sens inverse
# ----------------------------------------------------------------------------
GLSL_VASARELY = """// VASARELY -- grille op-art bombee/creusee (esprit serie Vega), FIGEE DANS
// L'ESPACE : le motif vit dans le plan frontal du disque balaye (le carre
// [-80,+80] cm, normalise en [0,1]^2, y vers le bas comme le volume), et les
// lames le revelent en tournant. Rendu PAR PIXEL en SENS INVERSE : chaque
// texel part de sa position reelle a l'ecran, DEFAIT la deformation
// spherique (formule opposee : asin pour une bosse, sin pour un creux) pour
// retrouver son point de grille, puis en deduit cellule, motif et couleur.
// L'ombrage est une teinte plate par cellule, calculee au centre de la
// cellule par la deformation DIRECTE -- comme la reference du prompt.
//
// Sortie 160 x 80 = dix bandes de 160 x 8, panneau 0 EN BAS.
// Entree 0 : angles_top (11 x 1), l'angle de chaque panneau en DEGRES.
// Toutes les lames montrent la MEME image frontale : le tableau traverse
// les dix profondeurs comme un prisme (voir le mode TABLEAU de MOTIFS_LED).

uniform vec4 uParam;   // x: relief effectif (radians, signe : >0 bosse),
                       // y: rayon (fraction de la demi-largeur, r = y*0.5/n),
                       // z: densite N (cellules par cote), w: ombrage k 0..1
uniform vec4 uMode;    // x: motif (0 carres, 1 cercles, 2 damier, 3 grille),
                       // y: disposition (0 une sphere, 1 2x2, 2 3x3,
                       //    3 2x2 bosses/creux alternes), z: palette 0..2,
                       // w: luminosite 0..1
uniform vec4 uCentre;  // x,y : centre de la sphere unique (disposition 0)

out vec4 fragColor;

const vec3 LUM = vec3(-0.48, -0.6, 0.64);   // lumiere de l'ombrage

// t ecran -> t grille (sens INVERSE) ; a signe, b = |a|
float versGrille(float t, float a, float b, float sb) {
    return (a > 0.0) ? asin(t * sb) / b : sin(b * t) / sb;
}
// t grille -> angle theta sur la calotte (celui du sens direct)
float thetaDirect(float t, float a, float b, float sb) {
    return (a > 0.0) ? b * t : asin(t * sb);
}

void main() {
    vec2 uv = vUV.st;
    int panneau = int(clamp(uv.y * 10.0, 0.0, 9.0));
    float angle = texelFetch(sTD2DInputs[0], ivec2(panneau, 0), 0).r;
    float th = radians(angle);

    // Position reelle du texel dans le plan frontal, en cm puis en [0,1]^2
    float dd = (uv.x - 0.5) * 160.0;
    float oo = floor(fract(uv.y * 10.0) * 8.0) - 3.5;
    vec2 P = vec2(dd * cos(th) - oo * sin(th),
                  dd * sin(th) + oo * cos(th)) / 160.0 + 0.5;

    // La ou les spheres, analytiques selon la disposition (pas de tableau) :
    // centres ((i+0.5)/n, (j+0.5)/n), r = rayon*0.5/n, non chevauchantes.
    int dispo = int(uMode.y + 0.5);
    int n = (dispo == 0) ? 1 : ((dispo == 2) ? 3 : 2);
    float relief = uParam.x;

    vec2 Pg = P;             // point de grille (identite hors de tout disque)
    float theta = 0.0, signe = 0.0;
    vec2 radial = vec2(0.0);
    vec2 Cact = vec2(0.5);
    float ract = 1.0, aact = 0.0;
    bool dansSphere = false;

    for (int i = 0; i < 3 && !dansSphere; i++)
    for (int j = 0; j < 3 && !dansSphere; j++) {
        if (i >= n || j >= n) continue;
        vec2 C = (dispo == 0) ? uCentre.xy
                              : vec2((float(i) + 0.5) / float(n),
                                     (float(j) + 0.5) / float(n));
        float r = uParam.y * 0.5 / float(n);
        float a = relief * ((dispo == 3 && ((i + j) % 2 == 1)) ? -1.0 : 1.0);
        vec2 dv = P - C;
        float d = length(dv);
        if (d >= r || abs(a) < 1e-3) continue;
        float b = abs(a), sb = sin(b);
        float t = d / r;
        float tg = versGrille(t, a, b, sb);
        float k = (t < 1e-4) ? ((a > 0.0) ? sb / b : b / sb) : tg / t;
        Pg = C + dv * k;
        theta = thetaDirect(tg, a, b, sb);
        signe = sign(a);
        radial = (d > 1e-6) ? dv / d : vec2(0.0);
        Cact = C; ract = r; aact = a;
        dansSphere = true;
    }

    // Cellule et position locale dans la grille reguliere
    float N = max(uParam.z, 2.0);
    vec2 g = clamp(Pg, 0.0, 0.9999) * N;
    float fi = floor(g.x), fj = floor(g.y);
    vec2 loc = fract(g);

    // Rampes de couleurs le long de la diagonale
    float tdiag = (fi + fj) / (2.0 * N - 2.0);
    int pal = int(uMode.z + 0.5);
    vec3 fondA = vec3(0.039, 0.133, 0.431), fondB = vec3(0.149, 0.471, 0.839);
    vec3 formA = vec3(0.941, 0.478, 0.078), formB = vec3(1.0, 0.839, 0.251);
    if (pal == 1) {        // braise, assortie au spectacle
        fondA = vec3(0.08, 0.0, 0.0);  fondB = vec3(0.35, 0.04, 0.04);
        formA = vec3(1.0, 0.13, 0.0);  formB = vec3(1.0, 0.67, 0.0);
    } else if (pal == 2) { // nuit
        fondA = vec3(0.0, 0.0, 0.06);  fondB = vec3(0.06, 0.13, 0.25);
        formA = vec3(0.88, 0.94, 1.0); formB = vec3(0.25, 0.75, 1.0);
    }
    vec3 fond = mix(fondA, fondB, tdiag);
    vec3 forme = mix(formA, formB, tdiag);

    // Motif de la cellule
    int motif = int(uMode.x + 0.5);
    bool surForme;
    if (motif == 0)      surForme = max(abs(loc.x - 0.5), abs(loc.y - 0.5)) < 0.3;
    else if (motif == 1) surForme = length(loc - 0.5) < 0.36;
    else if (motif == 2) surForme = ((int(fi) + int(fj)) % 2) == 1;
    else                 surForme = min(loc.x, 1.0 - loc.x) < 0.05
                                 || min(loc.y, 1.0 - loc.y) < 0.05;
    vec3 couleur = surForme ? forme : fond;

    // Ombrage : teinte plate par cellule, au CENTRE de la cellule, sens direct
    float f = 1.0;
    if (dansSphere) {
        vec2 cc = (vec2(fi, fj) + 0.5) / N;
        vec2 dvc = cc - Cact;
        float dc = length(dvc);
        if (dc < ract && dc > 1e-6) {
            float b = abs(aact), sb = sin(b);
            float tc = dc / ract;
            float thc = thetaDirect(tc, aact, b, sb);
            vec2 u = dvc / dc;
            f = (sign(aact) * sin(thc) * dot(u, LUM.xy) + cos(thc) * LUM.z) / LUM.z;
        }
    }
    float k = clamp(uParam.w, 0.0, 1.0);
    if (f >= 1.0) couleur = mix(couleur, vec3(1.0), min(0.6, (f - 1.0) * k * 1.2));
    else          couleur *= 1.0 - min(1.0, 1.0 - f) * k * 0.75;

    fragColor = TDOutputSwizzle(vec4(couleur * clamp(uMode.w, 0.0, 1.0), 1.0));
}
"""

# ----------------------------------------------------------------------------
# Callbacks
# ----------------------------------------------------------------------------
CB_ROTATION = """# rotation_compteur -- compte les demi-tours REELLEMENT balayes par les lames.
# Lit l'angle de la lame 0 dans angle_lame0 (en degres, un echantillon par
# lame, la MEME source que les motifs), le deroule pas a pas (saut ramene
# dans -180..+180) et accumule en demi-tours, en valeur absolue.
# C'est l'horloge du mode 'rotation' : la respiration du relief avance avec
# le balayage, a n'importe quelle vitesse, et se fige moteurs arretes.
def onCook(scriptOp):
\tscriptOp.clear()
\tcomp = parent()
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

CB_FORME = """# forme -- le relief effectif du moment, en canaux CHOP.
# phase = demi-tours balayes / Demitoursparcycle (mode rotation), ou
#         secondes de lecture / Periode (mode temps).
# Animer coche : relief effectif = Relief * cos(2*pi*phase) -- les bosses
# deviennent creux et reviennent, au rythme du balayage. Decoche : relief
# constant. Canaux : phase, relief (radians, signe), reliefdeg (pour l'etat).
import math

def onCook(scriptOp):
\tscriptOp.clear()
\tcomp = parent()
\tif str(comp.par.Modehorloge) == 'rotation':
\t\tphase = float(op('rotation_compteur')['demitours']) / max(float(comp.par.Demitoursparcycle), 1e-6)
\telse:
\t\tphase = float(op('compteur')['v']) / max(float(comp.par.Periode), 1e-6)
\trelief_deg = float(comp.par.Relief)
\tif comp.par.Animer:
\t\trelief_deg = relief_deg * math.cos(2.0 * math.pi * phase)
\tfor nom, v in (('phase', phase),
\t               ('relief', math.radians(relief_deg)),
\t               ('reliefdeg', relief_deg)):
\t\tscriptOp.appendChan(nom)[0] = v
\treturn
"""

CB_REMETTRE = """# Remettre -- ramene la respiration du relief a sa phase 0.
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

CB_BOUTON_VASARELY = """# Le clic bascule VASARELY.Actif ; en s'allumant il coupe le cube et
# l'anneau (un seul maitre a la fois sur la chaine LED).
def onOffToOn(panelValue):
\tp = op('/project1/scale/VASARELY').par.Actif
\tp.val = 0 if p else 1
\tif p:
\t\tfor autre in ('/project1/scale/ANIMATION_CUBE', '/project1/scale/ANNEAU_CONE'):
\t\t\to = op(autre)
\t\t\tif o is not None:
\t\t\t\to.par.Actif = 0
\treturn
"""



LISEZ_MOI = """VASARELY -- LA GRILLE OP-ART BOMBEE, REVELEE PAR LES LAMES

CE QUE C'EST
  Une grille reguliere de N x N cellules colorees (carres, cercles,
  damier ou quadrillage), deformee par une ou plusieurs calottes
  spheriques qui la font paraitre bombee ou creusee -- le trompe-l'oeil
  de la serie Vega de Vasarely. Le tableau est FIGE dans le plan
  frontal du disque balaye (le carre de -80 a +80 cm, y vers le bas) ;
  toutes les lames montrent la meme image a leur profondeur, comme le
  mode TABLEAU de MOTIFS_LED, et l'oeil la recompose en persistance.

LE RENDU, PAR PIXEL ET EN SENS INVERSE
  Chaque texel part de sa position reelle (angle de SA lame lu dans
  MOTIFS_LED/angles_top, rayon le long de la lame, rangee), la ramene
  dans [0,1]^2, puis DEFAIT la deformation : pour une bosse on applique
  la formule du creux (asin), pour un creux celle de la bosse (sin) --
  les deux sont inverses l'une de l'autre (verifie a 5e-16 pres). On
  retrouve ainsi la cellule d'origine, son motif et sa couleur.
  L'ombrage est une teinte plate par cellule, calculee au centre de la
  cellule par la formule directe, lumiere (-0.48, -0.6, 0.64).

LE RESEAU
  angle_lame0 / rotation_compteur   l'horloge du mode 'rotation'
  vitesse -> compteur (Speed)       les secondes, pour le mode 'temps'
  forme       Script CHOP : phase et relief effectif (radians)
  vasarely    GLSL TOP 160x80 : tout le motif, zero python par texel
  out_led     vers le switch panel_mask_output (entree ajoutee)

L'ANIMATION DU RELIEF
  Animer coche (defaut) : relief effectif = Relief x cos(2 pi phase).
  Les bosses s'aplatissent, deviennent creux, et reviennent -- en
  Demitoursparcycle demi-tours balayes (8 par defaut, soit 2 s a
  2 tours/s), ou en Periode secondes en mode temps. L'horloge suit la
  lame 0, comme le cube et l'anneau. Remettre revient a la phase 0,
  Lecture fige tout.

REGLAGES (page Vasarely)
  Actif          le bouton de SORTIE_SPECTACLE fait pareil
  Relief         -90 a +90 degres (bosse / creux), 80 par defaut
  Rayon          0.3 a 1 (fraction de la demi-largeur), 0.84
  Densite        cellules par cote, 8 a 36, 20 par defaut
  Ombrage        intensite 0..1, 0.4
  Motif          carres / cercles / damier / grille
  Disposition    une sphere (Centrex/Centrey) / 2x2 / 3x3 /
                 2x2 bosses et creux alternes
  Palette        vega (bleu/orange d'origine) / braise / nuit
  Animer, Lecture, Modehorloge, Demitoursparcycle, Periode, Luminosite

VERIFICATIONS DU PROMPT
  Relief 0 -> grille parfaitement reguliere (le warp est ignore sous
  1e-3 rad). Deformation continue au bord des disques (t'=1 en t=1).
  A 90 degres le centre est agrandi de pi/2 (1.5708, verifie). Aucun
  liseret ni vide : rendu par pixel, et le disque balaye (rayon max
  79.58 cm) tient entierement dans le carre du tableau.

QUI PREND LA MAIN
  Actif coche -> le switch panel_mask_output bascule sur ce module :
  panneaux reels, simulateur et rendu 3D suivent. Chaque bouton (cube,
  anneau, vasarely) coupe les deux autres. Tout decoche -> la chaine
  d'origine, au bit pres.
"""

TEXTE_COMMENT = """VASARELY -- LE TROMPE-L'OEIL QUI N'EXISTE SUR AUCUNE LAME

CE QUE C'EST
  La serie Vega de Vasarely sur l'afficheur : une grille de cellules
  colorees, bombee ou creusee par des calottes spheriques, figee dans
  le plan frontal du disque balaye. Troisieme animation apres le cube
  joue (COMMENT_57) et l'anneau respirant (COMMENT_58), meme ossature :
  module a bouton, entree dediee du switch panel_mask_output, horloge
  calee sur les demi-tours reellement balayes.

LE POINT TECHNIQUE
  Rendu PAR PIXEL en SENS INVERSE : chaque texel defait la deformation
  (asin pour une bosse, sin pour un creux -- formules inverses l'une de
  l'autre, verifiees a 5e-16) pour retrouver sa cellule dans la grille
  reguliere. Pas de polygones, pas de liserets, aucun python par texel.
  L'ombrage est plat par cellule, calcule au centre de cellule par la
  formule directe : c'est lui qui vend le relief.

LE RELIEF RESPIRE
  relief effectif = Relief x cos(2 pi phase), la phase avancant avec
  le balayage (8 demi-tours par cycle par defaut). Bosse -> plat ->
  creux -> retour : le trompe-l'oeil s'inverse sous les yeux, et
  s'arrete avec les moteurs. La disposition '2x2 alternes' mele bosses
  et creux simultanes.

UN SEUL MAITRE A LA FOIS
  Le bouton LANCER VASARELY (sous LANCER L ANNEAU) coupe le cube et
  l'anneau en s'allumant ; leurs boutons font de meme. Tout decoche
  rend la main a la chaine d'origine, au bit pres.
"""


def _detruire(chemin):
    o = op(chemin)
    if o:
        o.destroy()


def _texte(dat, contenu):
    dat.text = contenu


def installer():
    scale = op(CHEMIN_SCALE)
    assert scale, "Introuvable : " + CHEMIN_SCALE
    sw = scale.op('panel_mask_output')
    motifs = scale.op('MOTIFS_LED/angles_choix')
    commandes = scale.op('SORTIE_SPECTACLE/PANNEAU_COMMANDES')
    for o, nom in ((sw, 'panel_mask_output'), (motifs, 'MOTIFS_LED/angles_choix'),
                   (commandes, 'SORTIE_SPECTACLE/PANNEAU_COMMANDES')):
        assert o, 'Introuvable : ' + nom
    section = commandes.op('cube_anime')
    assert section, "Installer d'abord ANIMATION_CUBE (la section du bouton)."

    # ---- expression interieure du switch (reinstallation comprise) ----------
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
            expr_interieure = EXPR_INDEX_ORIGINE
            for nom_mod, rang_mod in (('ANIMATION_CUBE', 3), ('ANNEAU_CONE', 4)):
                if scale.op(nom_mod):
                    expr_interieure = ("%d if op('%s').par.Actif else (%s)"
                                       % (rang_mod, nom_mod, expr_interieure))
        else:
            expr_interieure = expr_actuelle or str(int(sw.par.index.eval()))
    if NOM_MODULE in (sw.par.index.expr or ''):
        sw.par.index.expr = expr_interieure
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(section.path + '/bouton_vasarely')
    _detruire(section.path + '/etat_vasarely')
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)

    # ------------------------------------------------------------------ module
    comp = scale.create(baseCOMP, NOM_MODULE)
    comp.nodeX, comp.nodeY = 2100, -11300
    comp.nodeWidth, comp.nodeHeight = 220, 140
    comp.color = (0.95, 0.75, 0.15)
    comp.comment = ('Grille op-art bombee/creusee (Vasarely, serie Vega), '
                    'figee dans le plan frontal. Entree dediee de panel_mask_output.')

    page = comp.appendCustomPage('Vasarely')
    p = page.appendToggle('Actif', label='VASARELY SUR LES PANNEAUX (prend la main)')[0]
    p.val = False
    p = page.appendToggle('Lecture', label='Faire vivre le relief')[0]
    p.default = True; p.val = True
    p = page.appendToggle('Animer', label='Relief anime (cos de la phase)')[0]
    p.default = True; p.val = True
    p = page.appendMenu('Modehorloge', label='Horloge du relief')[0]
    p.menuNames = ['rotation', 'temps']
    p.menuLabels = ['Suit la rotation (Demi-tours par cycle)',
                    'Au temps (Periode en secondes)']
    p.default = 'rotation'; p.val = 'rotation'
    p = page.appendFloat('Demitoursparcycle', label='Demi-tours par cycle')[0]
    p.default = 8; p.val = 8; p.normMin = 1; p.normMax = 32
    p.clampMin = True; p.min = 0.5
    p = page.appendFloat('Periode', label='Periode (s, mode temps)')[0]
    p.default = 4; p.val = 4; p.normMin = 0.5; p.normMax = 20
    p.clampMin = True; p.min = 0.1
    p = page.appendFloat('Relief', label='Relief (degres, - = creux)')[0]
    p.default = 80; p.val = 80; p.normMin = -90; p.normMax = 90
    p.clampMin = True; p.clampMax = True; p.min = -90; p.max = 90
    p = page.appendFloat('Rayon', label='Rayon (fraction demi-largeur)')[0]
    p.default = 0.84; p.val = 0.84; p.normMin = 0.3; p.normMax = 1
    p.clampMin = True; p.clampMax = True; p.min = 0.05; p.max = 1
    p = page.appendInt('Densite', label='Densite (cellules par cote)')[0]
    p.default = 20; p.val = 20; p.normMin = 8; p.normMax = 36
    p.clampMin = True; p.clampMax = True; p.min = 2; p.max = 64
    p = page.appendFloat('Ombrage', label='Ombrage (intensite)')[0]
    p.default = 0.4; p.val = 0.4; p.normMin = 0; p.normMax = 1
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 1
    p = page.appendMenu('Motif', label='Motif des cellules')[0]
    p.menuNames = ['carres', 'cercles', 'damier', 'grille']
    p.menuLabels = ['Carres inscrits (60 pour cent)', 'Cercles (rayon 0.36)',
                    'Damier', 'Quadrillage']
    p.default = 'carres'; p.val = 'carres'
    p = page.appendMenu('Disposition', label='Disposition des spheres')[0]
    p.menuNames = ['une', 'deux', 'trois', 'alterne']
    p.menuLabels = ['Une sphere au centre (deplacable)', '2 x 2', '3 x 3',
                    '2 x 2 bosses et creux alternes']
    p.default = 'une'; p.val = 'une'
    p = page.appendFloat('Centrex', label='Centre X (sphere unique)')[0]
    p.default = 0.5; p.val = 0.5; p.normMin = 0; p.normMax = 1
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 1
    p = page.appendFloat('Centrey', label='Centre Y (sphere unique)')[0]
    p.default = 0.5; p.val = 0.5; p.normMin = 0; p.normMax = 1
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 1
    p = page.appendMenu('Palette', label='Palette')[0]
    p.menuNames = ['vega', 'braise', 'nuit']
    p.menuLabels = ['Vega (bleu / orange, la reference)',
                    'Braise (rouges du spectacle)', 'Nuit (bleu froid)']
    p.default = 'vega'; p.val = 'vega'
    p = page.appendFloat('Luminosite', label='Luminosite')[0]
    p.default = 1; p.val = 1; p.normMin = 0; p.normMax = 1
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 1
    page.appendPulse('Remettre', label='Revenir a la phase 0')

    # ---- horloges (memes patrons que l'anneau) ----
    vitesse = comp.create(constantCHOP, 'vitesse')
    vitesse.nodeX, vitesse.nodeY = -700, 0
    p_nom = getattr(vitesse.par, 'const0name', None)
    if p_nom is None:
        p_nom = getattr(vitesse.par, 'name0', None)
    p_val = getattr(vitesse.par, 'const0value', None)
    if p_val is None:
        p_val = getattr(vitesse.par, 'value0', None)
    assert p_nom is not None and p_val is not None, 'Constant CHOP : parametres introuvables.'
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

    forme_cb = comp.create(textDAT, 'forme_callbacks')
    forme_cb.nodeX, forme_cb.nodeY = -300, -120
    _texte(forme_cb, CB_FORME)
    forme = comp.create(scriptCHOP, 'forme')
    forme.nodeX, forme.nodeY = -300, 0
    forme.par.callbacks = 'forme_callbacks'

    # ---- le GLSL ----
    code = comp.create(textDAT, 'vasarely_pixel')
    code.nodeX, code.nodeY = -100, -120
    _texte(code, GLSL_VASARELY)
    vas = comp.create(glslTOP, 'vasarely')
    vas.nodeX, vas.nodeY = -100, 80
    vas.par.pixeldat = 'vasarely_pixel'
    vas.par.outputresolution = 'custom'
    vas.par.resolutionw = 160
    vas.par.resolutionh = 80
    try:
        vas.par.format = 'rgba8fixed'
    except Exception:
        pass
    angles = comp.create(selectTOP, 'angles')
    angles.nodeX, angles.nodeY = -300, 150
    angles.par.top = '../MOTIFS_LED/angles_top'
    vas.inputConnectors[0].connect(angles)

    unis = [
        ('uParam', ("op('forme')['relief']", 'parent().par.Rayon',
                    'parent().par.Densite', 'parent().par.Ombrage')),
        ('uMode', ("['carres','cercles','damier','grille'].index(parent().par.Motif.eval())",
                   "['une','deux','trois','alterne'].index(parent().par.Disposition.eval())",
                   "['vega','braise','nuit'].index(parent().par.Palette.eval())",
                   'parent().par.Luminosite')),
        ('uCentre', ('parent().par.Centrex', 'parent().par.Centrey', '0', '0')),
    ]
    try:
        if vas.seq.vec.numBlocks < len(unis):
            vas.seq.vec.numBlocks = len(unis)
    except Exception:
        pass
    for i, (nom, (ex, ey, ez, ew)) in enumerate(unis):
        p_nom = getattr(vas.par, 'vec%dname' % i, None)
        if p_nom is None:
            p_nom = getattr(vas.par, 'uniname%d' % i, None)
        assert p_nom is not None, 'GLSL TOP : nom d uniforme introuvable (bloc %d).' % i
        p_nom.val = nom
        prefixe = ('vec%dvalue' % i
                   if getattr(vas.par, 'vec%dvaluex' % i, None) is not None
                   else 'value%d' % i)
        getattr(vas.par, prefixe + 'x').expr = ex
        getattr(vas.par, prefixe + 'y').expr = ey
        getattr(vas.par, prefixe + 'z').expr = ez
        getattr(vas.par, prefixe + 'w').expr = ew

    sortie = comp.create(outTOP, 'out_led')
    sortie.nodeX, sortie.nodeY = 150, 80
    sortie.inputConnectors[0].connect(vas)
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
        raise AssertionError('Entree du switch inattendue : %s -- branchement retire.' % rang)
    sw.par.index.expr = ("%d if op('VASARELY').par.Actif else (%s)"
                         % (rang[0], expr_interieure))

    # --------------------------------------- le bouton, sous celui de l'anneau
    etat_cube = section.op('etat')
    if etat_cube is not None:
        etat_cube.par.alignorder = 4
    etat_anneau = section.op('etat_anneau')
    if etat_anneau is not None:
        etat_anneau.par.alignorder = 5
    #  Les boutons du cube et de l'anneau ne sont PAS reecrits : chacun porte
    #  son propre texte, qui coupe deja les deux autres maitres (regle du
    #  6 octobre 2026 : une seule source par bouton).

    chemin_actif = "op('/project1/scale/VASARELY').par.Actif"
    bouton = section.create(containerCOMP, 'bouton_vasarely')
    bouton.par.h.expr = 'parent.commandes.par.Hauteurbouton * 1.8'
    bouton.par.hmode = 'fill'
    bouton.par.alignorder = 3
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
    etiquette.par.text.expr = ("'VASARELY EN MARCHE' if %s else 'LANCER VASARELY'"
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
    _texte(clic, CB_BOUTON_VASARELY)

    etat = section.create(textCOMP, 'etat_vasarely')
    etat.par.text.expr = (
        "'vasarely : relief %d deg' % int(op('/project1/scale/VASARELY/forme')['reliefdeg'])")
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
    etat.par.alignorder = 6

    comment = scale.create(textDAT, NOM_COMMENT)
    comment.nodeX, comment.nodeY = 2100, -11500
    comment.viewer = True
    _texte(comment, TEXTE_COMMENT)

    # ------------------------------------------------------------- MESURE
    print('')
    print('VASARELY installe. MESURE :')
    try:
        sortie.cook(force=True)
        forme.cook(force=True)
        print('  relief effectif : %.1f deg (phase %.3f)'
              % (float(forme['reliefdeg']), float(forme['phase'])))
        arr = sortie.numpyArray()
        if arr is not None:
            moy = float(arr[..., :3].mean())
            print('  luminance moyenne de l image : %.3f (doit etre > 0)' % moy)
    except Exception as e:
        print('  MESURE incomplete (%s) -- l installation est terminee.' % e)
    err = comp.errors(recurse=True)
    print('  erreurs dans le module : %s' % (err if err else 'aucune'))
    print('  switch : entree %d ; Actif est DECOCHE.' % rang[0])
    print('  Bouton : SORTIE_SPECTACLE > ANIMATION CUBE > LANCER VASARELY')
    print('  Penser a : Fichier > Enregistrer sous (nom finissant par Vasarely).')
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
        expr_interieure = EXPR_INDEX_ORIGINE
        for nom_mod, rang_mod in (('ANIMATION_CUBE', 3), ('ANNEAU_CONE', 4)):
            if scale.op(nom_mod):
                expr_interieure = ("%d if op('%s').par.Actif else (%s)"
                                   % (rang_mod, nom_mod, expr_interieure))
    if sw:
        sw.par.index.expr = expr_interieure
    if commandes:
        section = commandes.op('cube_anime')
        _detruire(commandes.path + '/cube_anime/bouton_vasarely')
        _detruire(commandes.path + '/cube_anime/etat_vasarely')
        if section is not None:
            etat_cube = section.op('etat')
            if etat_cube is not None:
                etat_cube.par.alignorder = 3
            etat_anneau = section.op('etat_anneau')
            if etat_anneau is not None:
                etat_anneau.par.alignorder = 4
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)
    print('VASARELY retire ; switch et boutons remis a l etat cube+anneau.')
    print('Penser a : Fichier > Enregistrer sous.')


installer()
