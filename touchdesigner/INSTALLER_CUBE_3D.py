# ============================================================================
# INSTALLER_CUBE_3D -- CE QUE LES PALES IMPRIMENT : le volume que voit l'oeil
#
# A executer le projet SAISON_9 ouvert :
#   exec(open('.../touchdesigner/INSTALLER_CUBE_3D.py').read())
# REJOUABLE : relancer met a jour au lieu de creer un doublon, et retire les
# restes de la version precedente.
#
# ----------------------------------------------------------------------------
# POURQUOI CE MODULE A ETE REFAIT (6 octobre 2026, 15 h)
#
# La premiere version dessinait un balayage IDEAL : quatre-vingt-dix pas de
# 2 degres, une helice de 18 degres, 2 tours/s tenus par l'horloge de
# TouchDesigner, et elle ne lisait les vraies lames que pour tracer leurs
# contours. Le cube qu'on y voyait etait celui que la theorie promet, pas
# celui que les pales impriment. Benjamin l'a dit sans detour : « ne triche
# pas, je veux voir exactement ce que les pales impriment sur les LED ».
#
# Cette version n'invente plus rien. A chaque image de TouchDesigner :
#   - on prend l'image 160 x 80 REELLEMENT envoyee aux panneaux
#     (panel_mask_output : cube, anneau, Vasarely ou variation, peu importe) ;
#   - on prend l'angle REEL de chacune des dix lames (MOTIFS_LED/angles_top :
#     la consigne, ou les positions rapportees par la Teensy quand « MOTIFS
#     SUR LES ANGLES REELS » est coche -- la source qui a servi a calculer
#     l'image, ni plus ni moins) ;
#   - chaque LED allumee est deposee a sa position dans l'espace, tout le
#     long de l'arc que la lame a parcouru depuis l'image precedente : entre
#     deux envois les LED gardent leur etat, elles TRAINENT ;
#   - chaque depot est date ; il palit ensuite comme dans l'oeil,
#     b = 1 - age / Persistance, et s'eteint sous 3 %.
#
# CONSEQUENCE VOULUE. A lames lentes on ne voit pas de cube, seulement des
# morceaux. Le cube n'apparait entier que si chaque lame balaye un demi-tour
# en moins d'une persistance (a 0,2 s : 2,5 tours/s ; a 1,2 tour/s, un
# demi-tour prend 0,42 s et l'oeil n'en garde qu'un secteur de 84 degres),
# et l'ecart entre lames decide de la facon dont les morceaux se
# repartissent. C'est la realite de la machine, pas un reglage de l'apercu.
#
# ----------------------------------------------------------------------------
# COMMENT C'EST FAIT (tout sur le processeur graphique, rien par LED en python)
#
#   atlas       GLSL TOP 320 x 801 en flottants 32 bits, reboucle par un
#               Feedback TOP : dix tranches de 160 x 160 voxels de 1 cm, en
#               deux colonnes de cinq (la tranche s a la colonne s // 5 et a
#               la rangee s % 5 ; la cle non commerciale plafonne une texture
#               a 1280 px), plus une ligne memoire tout en haut (l'angle de
#               chaque lame a l'image precedente). Chaque voxel garde la
#               couleur de son dernier depot et sa DATE (alpha =
#               absTime.seconds). Le Feedback TOP demarre sur 'vide', une
#               image noire du meme format.
#   impression  le nuanceur du GLSL TOP. Pour chaque voxel (x, y) de la
#               tranche s, il parcourt l'arc de la lame s entre l'angle
#               precedent a0 et l'angle courant a1 par pas de Pasarc degres,
#               ramene le voxel dans le repere de la lame
#                   d = x cos th + y sin th        o = -x sin th + y cos th
#               et, si |d| < 80 et |o| < 4, lit la LED (colonne floor(d + 80),
#               rangee floor(o + 4)) dans l'image envoyee : allumee -> depot.
#               C'est l'inverse exact de la position d'une LED dans
#               ANIMATION_CUBE : x = d cos th - o sin th, y = d sin th + o cos
#               th, d = k - 79,5, o = j - 3,5, panneau 0 en bas de l'image,
#               8 rangees par bande, le miroir vertical de la chaine LED.
#   tranches    dix rectangles de 160 x 160 cm instancies a la profondeur
#               z = (4,5 - s) x ecart, textures par l'atlas (GLSL MAT 'oeil') :
#               luminosite 1 - age / Persistance, extinction sous 3 %, fusion
#               ADDITIVE sans test de profondeur -- les dix tranches
#               s'additionnent comme la lumiere dans l'oeil.
#   cadres      les dix contours de lames, aux memes angles reels.
#   cam         suit les fleches de real_Move (Azimut, Elevation, Distance).
#   rendu / out ce que montrent real_Move (VOLUME BALAYE) et, quand un cube a
#               la main, le bandeau RENDU 3D de SORTIE_SPECTACLE.
#
# LE PIEGE DU RENDER TOP (6 octobre, matin). Son parametre Geometry attend
# des OBJETS 3D (geometryCOMP, nullCOMP...), pas un baseCOMP : pointe sur
# CUBE_3D lui-meme (`..`), il rendait du NOIR PUR -- 0 pixel sur 921 600,
# contours compris. On nomme les geometries.
# ============================================================================

RACINE = '/project1/scale'
CM_PAR_UNITE = 160.0   # la lame fait 160 cm et le SOP du rig 1,000 unite
VOX = 160              # voxels par cote de tranche : 1 cm
NB = 10                # lames
#  DEUX COLONNES DE CINQ TRANCHES : la cle non commerciale de TouchDesigner
#  limite une texture a 1280 x 1280, et dix tranches empilees font 1600 lignes.
#  La tranche s est dans la colonne s // 5, a la rangee s % 5 ; la ligne
#  memoire des angles est la derniere (y = 800).
COLONNES, RANGEES = 2, 5
LARGEUR_ATLAS, HAUTEUR_ATLAS = VOX * COLONNES, VOX * RANGEES + 1

scale = op(RACINE)
assert scale is not None, "Introuvable : " + RACINE + " -- ouvrir le projet SAISON_9 d'abord."

cv = scale.op('CUBE_3D')
if cv is None:
    cv = scale.create(baseCOMP, 'CUBE_3D')
    anim = scale.op('ANIMATION_CUBE')
    if anim is not None:
        cv.nodeX, cv.nodeY = anim.nodeX, anim.nodeY - 260
cv.comment = ("CE QUE LES PALES IMPRIMENT : l'image reellement envoyee aux "
              "panneaux, deposee aux angles reels des dix lames, avec la "
              "remanence de l'oeil. Aucun balayage invente.")


def enfant(parent_, nom, type_op, x, y):
    o = parent_.op(nom)
    if o is None:
        o = parent_.create(type_op, nom)
        if o.name != nom and parent_.op(nom) is None:
            o.name = nom
        o.nodeX, o.nodeY = x, y
    return o


# --- menage de la version precedente (le balayage ideal) ---------------------
for _nom in ('voxels', 'voxels_callbacks', 'voxels_callbacks1', 'geo_voxels',
             'constant1', 'remanence', 'remanence_sommet', 'remanence_pixel',
             'remanence_pixel1', 'remanence_vertex', 'remanence_info',
             'cadres_callbacks1', 'ligne1'):
    _o = cv.op(_nom)
    if _o is not None:
        _o.destroy()
for _nom in ('Posesrc', 'Rafraichissements', 'Ecarthelice', 'Epaisseur',
             'Toursparseconde', 'Remanenceanimee', 'Phaseremanence',
             'Tailleled', 'Paliers'):
    _p = getattr(cv.par, _nom, None)
    if _p is not None:
        try:
            _p.destroy()
        except Exception:
            pass

# --- les reglages ------------------------------------------------------------
pg = None
for p in cv.customPages:
    if p.name == 'Volume':
        pg = p
if pg is None:
    pg = cv.appendCustomPage('Volume')
deja = [q.name for q in pg.pars]

REGLAGES = (
    ('Imagesrc', 'op', "Image envoyee aux panneaux (TOP)", None, None, None,
     "L'image 160 x 80 REELLEMENT envoyee : panel_mask_output, quel que soit "
     "le maitre (cube, anneau, Vasarely, variation). Dix bandes de 160 x 8, "
     "panneau 0 en bas."),
    ('Anglessrc', 'op', 'Angles des lames (TOP)', None, None, None,
     "MOTIFS_LED/angles_top : l'angle de chaque lame en degres, consigne ou "
     "positions Teensy selon « MOTIFS SUR LES ANGLES REELS » -- la meme "
     "source que celle qui calcule l'image. Aucune horloge interne."),
    ('Persistance', 'float', "Persistance de l'oeil (s)", 0.2, 0.02, 1.0,
     "Duree pendant laquelle un depot reste visible, en palissant "
     "lineairement : b = 1 - age / Persistance, extinction sous 3 %. Le "
     "simulateur p5 prend 0,3 s ; l'oeil tient plutot 0,1 a 0,2 s. A 0,2 s, "
     "une lame a 1,2 tour/s ne laisse qu'un secteur de 84 degres."),
    ('Pasarc', 'float', "Pas de l'arc (deg)", 2.0, 0.5, 10.0,
     "Entre deux images, la lame a tourne : on depose les LED tout le long "
     "de l'arc, par pas de cette taille. 2 degres = le pas de "
     "rafraichissement du simulateur ; plus fin ne change rien a 1 cm."),
    ('Seuil', 'float', 'Seuil LED allumee', 0.02, 0.0, 0.5,
     "Une LED compte comme allumee si l'un de ses canaux depasse ce seuil."),
    ('Ecartcm', 'float', 'Ecart entre panneaux (cm)', 10.0, 1.0, 30.0,
     "La profondeur de la tranche s vaut (4,5 - s) fois cet ecart."),
    ('Miroiry', 'toggle', 'Miroir vertical (comme ANIMATION_CUBE)', 0, 0, 1,
     "Retourne l'axe y, exactement comme Miroiry dans ANIMATION_CUBE : "
     "c'est la convention de la chaine LED, pas un choix de l'apercu. "
     "Suit ANIMATION_CUBE.Miroiry par expression tant qu'on n'y touche pas."),
    ('Traitcadres', 'float', 'Epaisseur du trait des cadres (cm)', 1.0, 0.2, 5.0,
     "Largeur des quatre barres qui dessinent le contour d'une lame."),
    ('Eclatcadres', 'float', 'Eclat des contours', 1.0, 0.0, 4.0,
     "Multiplie le gris des contours : 120 pour la lame 0, 60 pour les "
     "autres (volumetric3D.js). Monter si les contours se perdent."),
    ('Cmparunite', 'float', 'Centimetres par unite de scene', CM_PAR_UNITE,
     80.0, 320.0,
     "Le rig du projet mesure 1,000 unite pour une lame de 160 cm."),
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
    else:
        q = pg.appendFloat(nom, label=label)[0]
        q.default = defaut
        q.val = defaut
        q.normMin, q.normMax = mini, maxi
    q.help = aide
if 'Effacer' not in deja:
    pg.appendPulse('Effacer', label="Effacer l'impression")
_src = cv.par.Imagesrc.eval()
if _src is None or not _src.isTOP:
    cv.par.Imagesrc = scale.op('panel_mask_output')
_src = cv.par.Anglessrc.eval()
if _src is None or not _src.isTOP:
    #  La version precedente y mettait le CHOP angles_choix ; ici il faut le
    #  TOP (angles_top = le meme angles_choix converti en 11 x 1).
    _a = scale.op('MOTIFS_LED/angles_top')
    if _a is not None:
        cv.par.Anglessrc = _a
if scale.op('ANIMATION_CUBE') is not None and cv.par.Miroiry.mode != ParMode.EXPRESSION \
        and not cv.par.Miroiry.eval():
    cv.par.Miroiry.expr = "op('../ANIMATION_CUBE').par.Miroiry if op('../ANIMATION_CUBE') else 0"

# --- les deux entrees : l'image envoyee, les angles reels -------------------
image = enfant(cv, 'image', selectTOP, -700, 100)
image.par.top.expr = "parent().par.Imagesrc.eval().path if parent().par.Imagesrc.eval() else ''"
image.comment = "L'image 160 x 80 reellement envoyee aux panneaux."
angles = enfant(cv, 'angles', selectTOP, -700, -20)
angles.par.top.expr = "parent().par.Anglessrc.eval().path if parent().par.Anglessrc.eval() else ''"
angles.comment = "L'angle reel de chaque lame, en degres (11 x 1)."

# --- l'impression : le GLSL TOP reboucle -------------------------------------
CODE_IMPRESSION = '''// IMPRESSION -- depose les LED allumees aux angles reels des lames.
// Entrees : 0 = l'atlas de l'image precedente (Feedback), 1 = l'image
// envoyee aux panneaux (160 x 80), 2 = les angles des lames (11 x 1, deg).
// Sortie 320 x 801 : dix tranches de 160 x 160 voxels de 1 cm en deux
// colonnes de cinq (tranche s : colonne s / 5, rangee s % 5), puis une
// ligne memoire (l'angle de chaque lame a cette image).
uniform vec4 uRegle;   // x : maintenant (s) ; y : pas de l'arc (deg) ;
                       // z : miroir vertical (+1 / -1) ; w : seuil LED allumee
out vec4 fragColor;

const int NB = 10;     // lames
const int H = 160;     // voxels par cote
const int RANGEES = 5; // tranches par colonne

float replie180(float a) { return mod(a + 180.0, 360.0) - 180.0; }

void main() {
	ivec2 p = ivec2(gl_FragCoord.xy);
	if (p.y >= RANGEES * H) {
		// la ligne memoire : l'angle courant de chaque lame, pour l'image suivante
		if (p.x < NB) {
			float a = texelFetch(sTD2DInputs[2], ivec2(p.x, 0), 0).r;
			fragColor = TDOutputSwizzle(vec4(a, 0.0, 0.0, 1.0));
		} else {
			fragColor = TDOutputSwizzle(vec4(0.0));
		}
		return;
	}
	int s = (p.x / H) * RANGEES + (p.y / H);
	int px = p.x - (p.x / H) * H;
	int py = p.y - (p.y / H) * H;
	vec4 res = texelFetch(sTD2DInputs[0], p, 0);
	vec4 mem = texelFetch(sTD2DInputs[0], ivec2(s, RANGEES * H), 0);
	float a1 = texelFetch(sTD2DInputs[2], ivec2(s, 0), 0).r;
	float a0 = (mem.a > 0.5) ? mem.r : a1;
	float da = replie180(a1 - a0);
	int n = clamp(int(abs(da) / max(0.1, uRegle.y)) + 1, 1, 90);
	// le centre du voxel, en cm, dans le repere du volume (y selon la chaine LED)
	float x = float(px) - 79.5;
	float y = (float(py) - 79.5) * uRegle.z;
	for (int i = 0; i < n; i++) {
		float th = radians(a0 + da * (float(i) + 0.5) / float(n));
		float c = cos(th), sn = sin(th);
		float d = x * c + y * sn;        // le long de la lame
		float o = -x * sn + y * c;       // en travers
		if (abs(d) < 80.0 && abs(o) < 4.0) {
			int k = int(floor(d + 80.0));
			int j = int(floor(o + 4.0));
			vec4 led = texelFetch(sTD2DInputs[1], ivec2(k, s * 8 + j), 0);
			if (max(led.r, max(led.g, led.b)) > uRegle.w) {
				res = vec4(led.rgb, uRegle.x);   // depot date de maintenant
			}
		}
	}
	fragColor = TDOutputSwizzle(res);
}
'''
dat_imp = enfant(cv, 'impression_pixel', textDAT, -400, 60)
dat_imp.text = CODE_IMPRESSION
atlas = enfant(cv, 'atlas', glslTOP, -150, 100)
atlas.par.pixeldat = dat_imp
atlas.par.outputresolution = 'custom'
atlas.par.resolutionw = LARGEUR_ATLAS
atlas.par.resolutionh = HAUTEUR_ATLAS
atlas.par.format = 'rgba32float'
atlas.par.vec0name = 'uRegle'
atlas.par.vec0valuex.expr = 'absTime.seconds'
atlas.par.vec0valuey.expr = 'parent().par.Pasarc'
atlas.par.vec0valuez.expr = '-1 if parent().par.Miroiry else 1'
atlas.par.vec0valuew.expr = 'parent().par.Seuil'
atlas.comment = ("Dix tranches de 160 x 160 voxels de 1 cm (rgb : couleur du dernier "
                 "depot, alpha : sa date) et une ligne memoire d'angles.")
vide = enfant(cv, 'vide', constantTOP, -700, 220)
vide.par.outputresolution = 'custom'
vide.par.resolutionw = LARGEUR_ATLAS
vide.par.resolutionh = HAUTEUR_ATLAS
vide.par.format = 'rgba32float'
vide.par.colorr = vide.par.colorg = vide.par.colorb = vide.par.alpha = 0.0
vide.comment = "L'atlas vide : ce que le Feedback TOP sort au depart et apres Effacer."
feedback = enfant(cv, 'feedback', feedbackTOP, -400, 160)
#  Un Feedback TOP a besoin de SON ENTREE (l'image initiale) ET de la cible
#  qu'il reboucle ; sans entree : « Not enough sources specified ».
if not feedback.inputs or feedback.inputs[0].path != vide.path:
    feedback.inputConnectors[0].connect(vide)
feedback.par.top = atlas
feedback.comment = "Reboucle l'atlas : chaque image repart de la precedente."
#  Les DAT que le GLSL TOP a crees tout seul (atlas_pixel, atlas_compute) ne
#  servent pas : c'est impression_pixel qui est branche.
for _nom in ('atlas_pixel', 'atlas_compute'):
    _o = cv.op(_nom)
    if _o is not None:
        _o.destroy()
for i, src in ((0, feedback), (1, image), (2, angles)):
    if not (len(atlas.inputs) > i and atlas.inputs[i] is not None and atlas.inputs[i].path == src.path):
        atlas.inputConnectors[i].connect(src)

CB_EFFACER = """# Effacer -- vide l'atlas (le Feedback TOP repart de zero).
def onPulse(par):
\tif par.name == 'Effacer':
\t\tp = getattr(op('feedback').par, 'resetpulse', None)
\t\tif p is not None:
\t\t\tp.pulse()
\treturn
"""
remise = enfant(cv, 'remise', parameterexecuteDAT, -400, -60)
for _nom, _val in (('op', '..'), ('pars', 'Effacer'), ('onpulse', True)):
    _p = getattr(remise.par, _nom, None)
    if _p is not None:
        _p.val = _val
remise.text = CB_EFFACER

# --- l'oeil : les dix tranches texturees par l'atlas ------------------------
CODE_OEIL_SOMMET = '''// Chaque tranche est une instance du rectangle : son rang est sa profondeur.
out Vertex {
	vec2 uv;
	flat int tranche;
} oVert;

void main() {
	vec4 worldSpacePos = TDDeform(P);
	gl_Position = TDWorldToProj(worldSpacePos);
	vec3 t = TDInstanceTexCoord(uv[0]);
	oVert.uv = t.st;
	oVert.tranche = TDInstanceID();
}
'''
CODE_OEIL_PIXEL = '''// La remanence de l'oeil, par voxel : b = 1 - age / persistance.
uniform sampler2D sAtlas;
uniform vec4 uRegle;   // x : maintenant (s) ; y : persistance (s) ;
                       // z : seuil d'extinction ; w : voxels par cote (160)
in Vertex {
	vec2 uv;
	flat int tranche;
} iVert;
out vec4 fragColor;

void main() {
	int n = int(uRegle.w);
	int s = iVert.tranche;
	ivec2 p = ivec2((s / 5) * n + clamp(int(iVert.uv.x * float(n)), 0, n - 1),
	                (s - (s / 5) * 5) * n + clamp(int(iVert.uv.y * float(n)), 0, n - 1));
	vec4 v = texelFetch(sAtlas, p, 0);
	if (v.a <= 0.0) discard;                       // jamais imprime
	float b = 1.0 - (uRegle.x - v.a) / max(1e-6, uRegle.y);
	if (b <= uRegle.z) discard;                    // ETEINT, pas juste sombre
	fragColor = TDOutputSwizzle(vec4(v.rgb * clamp(b, 0.0, 1.0), 1.0));
}
'''
dat_vs = enfant(cv, 'oeil_sommet', textDAT, -400, -200)
dat_vs.text = CODE_OEIL_SOMMET
dat_ps = enfant(cv, 'oeil_pixel', textDAT, -400, -280)
dat_ps.text = CODE_OEIL_PIXEL
mat_oeil = enfant(cv, 'oeil', glslMAT, -150, -240)
mat_oeil.par.vdat = dat_vs
mat_oeil.par.pdat = dat_ps
mat_oeil.par.sampler0name = 'sAtlas'
mat_oeil.par.sampler0top = atlas
mat_oeil.par.sampler0filter = 'nearest'
mat_oeil.par.vec0name = 'uRegle'
mat_oeil.par.vec0valuex.expr = 'absTime.seconds'
mat_oeil.par.vec0valuey.expr = 'parent().par.Persistance'
mat_oeil.par.vec0valuez = 0.03
mat_oeil.par.vec0valuew = VOX
#  FUSION ADDITIVE, SANS PROFONDEUR : les dix tranches s'ajoutent comme la
#  lumiere dans l'oeil, quel que soit l'ordre de dessin.
mat_oeil.par.blending = True
mat_oeil.par.srcblend = 'one'
mat_oeil.par.destblend = 'one'
mat_oeil.par.depthtest = False
mat_oeil.par.depthwriting = False
mat_oeil.comment = "Lit l'atlas : luminosite 1 - age / persistance, additif."
for _nom in ('oeil_vertex', 'oeil_pixel1'):      # crees tout seuls par le glslMAT
    _o = cv.op(_nom)
    if _o is not None:
        _o.destroy()

CODE_TRANCHES = '''# Les dix tranches : une par lame, a sa profondeur.
import numpy


def onCook(scriptOp):
    scriptOp.clear()
    comp = parent()
    n = 10
    e = 1.0 / float(comp.par.Cmparunite)
    z = (4.5 - numpy.arange(n)) * float(comp.par.Ecartcm) * e
    zz = numpy.zeros(n)
    scriptOp.numSamples = n
    for nom, val in (('tx', zz), ('ty', zz), ('tz', z)):
        scriptOp.appendChan(nom).vals = numpy.asarray(val, dtype=numpy.float32)
    scriptOp.rate = project.cookRate
    return
'''
cb_tr = enfant(cv, 'tranches_callbacks', textDAT, -400, -400)
cb_tr.text = CODE_TRANCHES
tranches = enfant(cv, 'tranches', scriptCHOP, -150, -400)
tranches.par.callbacks = cb_tr
_o = cv.op('tranches_callbacks1')                # cree tout seul par le scriptCHOP
if _o is not None:
    _o.destroy()
tranches.comment = "Dix echantillons : la profondeur de chaque tranche."

geo_tr = enfant(cv, 'geo_tranches', geometryCOMP, 100, 100)
for _d in geo_tr.children:
    if getattr(_d, 'render', False) and _d.name != 'tranche':
        _d.render = False          # le torusPOP depose par defaut dans tout geometryCOMP neuf
tranche = enfant(geo_tr, 'tranche', rectangleSOP, 0, 0)
tranche.par.sizex.expr = '160.0 / parent(2).par.Cmparunite'
tranche.par.sizey.expr = '160.0 / parent(2).par.Cmparunite'
tranche.par.texture = 'face'   # sans quoi uv[0] n'existe pas et l'atlas n'est pas lu
tranche.render = True
tranche.comment = "Une tranche de 160 x 160 cm, instanciee dix fois en profondeur."
geo_tr.par.instancing = True
geo_tr.par.instanceop = tranches
geo_tr.par.instancetx, geo_tr.par.instancety, geo_tr.par.instancetz = 'tx', 'ty', 'tz'
geo_tr.par.material = mat_oeil
for n in ('tx', 'ty', 'tz'):
    getattr(geo_tr.par, n).val = 0.0

# --- les contours des dix panneaux, aux angles reels ------------------------
CODE_CADRES = '''# Les dix contours de panneaux : angle REEL, profondeur, couleur.
import numpy


def onCook(scriptOp):
    scriptOp.clear()
    comp = parent()
    n = 10
    #  ON NE RELIT PAS LA CARTE GRAPHIQUE : numpyArray() sur le TOP des angles
    #  coutait 1,5 ms par cuisson (un rapatriement GPU -> CPU). Le TOP est un
    #  choptoTOP : on lit le CHOP qui est derriere, deja sur le processeur.
    ang = None
    try:
        src = comp.par.Anglessrc.eval()
        chop = src.par.chop.eval() if src is not None and hasattr(src.par, 'chop') else None
        if chop is not None and chop.numSamples >= n:
            ang = numpy.array([float(chop[0][i]) for i in range(n)])
    except Exception:
        ang = None
    if ang is None:
        try:
            a = op('angles').numpyArray()
            ang = numpy.array([float(a[0, i, 0]) for i in range(n)])
        except Exception:
            ang = numpy.zeros(n)
    ecart = float(comp.par.Ecartcm)
    e = 1.0 / float(comp.par.Cmparunite)
    z = (4.5 - numpy.arange(n)) * ecart * e
    g = numpy.full(n, 60.0 / 255.0)
    g[0] = 120.0 / 255.0
    g = g * float(comp.par.Eclatcadres)
    scriptOp.numSamples = n
    zz = numpy.zeros(n)
    for nom, val in (('tx', zz), ('ty', zz), ('tz', z),
                     ('rx', zz), ('ry', zz), ('rz', ang),
                     ('r', g), ('g', g), ('b', g)):
        scriptOp.appendChan(nom).vals = numpy.asarray(val, dtype=numpy.float32)
    scriptOp.rate = project.cookRate
    return
'''
cb_cadres = enfant(cv, 'cadres_callbacks', textDAT, -400, -520)
cb_cadres.text = CODE_CADRES
cadres = enfant(cv, 'cadres', scriptCHOP, -150, -520)
cadres.par.callbacks = cb_cadres
cadres.comment = "Dix echantillons : angle reel, profondeur et gris de chaque lame."

geo_cadres = enfant(cv, 'geo_cadres', geometryCOMP, 100, -200)
for _d in geo_cadres.children:
    if getattr(_d, 'render', False) and _d.name != 'cadre':
        _d.render = False
CODE_CADRE = '''# Le contour d'UNE lame, a l'angle zero : quatre barres fines (160 x 8 cm).
import numpy


def onCook(scriptOp):
    scriptOp.clear()
    comp = parent()
    cm = float(comp.par.Cmparunite)
    L = (160.0 / 2.0) / cm
    W = (8.0 / 2.0) / cm
    e = float(comp.par.Traitcadres) / cm
    e = min(e, W * 0.9)
    barres = ((-L, L, -W, -W + e), (-L, L, W - e, W),
              (-L, -L + e, -W + e, W - e), (L - e, L, -W + e, W - e))
    for x0, x1, y0, y1 in barres:
        pr = scriptOp.appendPoly(4, closed=True, addPoints=True)
        for i, (x, y) in enumerate(((x0, y0), (x1, y0), (x1, y1), (x0, y1))):
            pr[i].point.x, pr[i].point.y, pr[i].point.z = x, y, 0.0
    return
'''
cb_cadre = enfant(cv, 'cadre_callbacks', textDAT, -400, -640)
cb_cadre.text = CODE_CADRE
cadre = enfant(geo_cadres, 'cadre', scriptSOP, 0, 0)
cadre.par.callbacks = cb_cadre
cadre.render = True
_o = geo_cadres.op('fil')
if _o is not None:
    _o.destroy()
mat_gris = enfant(cv, 'constant_gris', constantMAT, -150, -640)
mat_gris.par.colorr = mat_gris.par.colorg = mat_gris.par.colorb = 1.0
geo_cadres.par.material = mat_gris
geo_cadres.par.instancing = True
geo_cadres.par.instanceop = cadres
geo_cadres.par.instancetx, geo_cadres.par.instancety, geo_cadres.par.instancetz = 'tx', 'ty', 'tz'
geo_cadres.par.instancerx, geo_cadres.par.instancery, geo_cadres.par.instancerz = 'rx', 'ry', 'rz'
geo_cadres.par.instancecolorop = cadres
geo_cadres.par.instancer, geo_cadres.par.instanceg, geo_cadres.par.instanceb = 'r', 'g', 'b'
geo_cadres.par.instancecolormode = 'multiply'

# --- la camera : les fleches de real_Move ------------------------------------
import math

AZIMUT, ELEVATION, OCCUPATION = 34.38, 20.05, 0.84
SILHOUETTE = 1.1193
cible = enfant(cv, 'cible', nullCOMP, 100, -340)
cible.par.tx = cible.par.ty = cible.par.tz = 0.0
cam = enfant(cv, 'cam', cameraCOMP, 100, -460)
cam.par.lookat = cible
cam.par.fov = 45.0
_d = SILHOUETTE / (OCCUPATION * 2.0 * math.tan(math.radians(cam.par.fov.eval() / 2.0)))
_a, _e = math.radians(AZIMUT), math.radians(ELEVATION)
_rmv = scale.op('real_Move')
if _rmv is not None and all(hasattr(_rmv.par, n) for n in ('Azimut', 'Elevation', 'Distance')):
    _RM = "op('../real_Move').par."
    cam.par.tx.expr = (_RM + "Distance * math.cos(math.radians(" + _RM + "Elevation)) "
                       "* math.sin(math.radians(" + _RM + "Azimut))")
    cam.par.ty.expr = _RM + "Distance * math.sin(math.radians(" + _RM + "Elevation))"
    cam.par.tz.expr = (_RM + "Distance * math.cos(math.radians(" + _RM + "Elevation)) "
                       "* math.cos(math.radians(" + _RM + "Azimut))")
else:
    cam.par.tx = _d * math.cos(_e) * math.sin(_a)
    cam.par.ty = _d * math.sin(_e)
    cam.par.tz = _d * math.cos(_e) * math.cos(_a)
cam.comment = ("Suit les fleches de real_Move (Azimut, Elevation, Distance), cible a "
               "l'origine ; sans real_Move, la vue de base du simulateur p5.")

# --- le rendu ----------------------------------------------------------------
rendu = enfant(cv, 'rendu', renderTOP, 320, 0)
rendu.par.camera = cam
rendu.par.geometry = 'geo_tranches geo_cadres'   # des OBJETS, jamais le baseCOMP (voir en tete)
rendu.par.bgcolorr = rendu.par.bgcolorg = rendu.par.bgcolorb = 0.0
rendu.par.bgcolora = 1.0
rendu.par.transparency = 'sortedblending'
sortie = enfant(cv, 'out', nullTOP, 480, 0)
if not sortie.inputs:
    sortie.inputConnectors[0].connect(rendu)
#  SURTOUT PAS sortie.viewer = True : un viseur allume force toute la chaine a
#  cuire meme quand personne ne regarde. CUBE_3D ne cuit que par real_Move ou
#  le bandeau de SORTIE_SPECTACLE.
sortie.viewer = False

# --- le bandeau RENDU 3D de SORTIE_SPECTACLE, quand un cube a la main -------
vue3d = scale.op('SORTIE_SPECTACLE/haut/simulation')
if vue3d is not None:
    sauve = cv.op('sauvegarde_rendu_spectacle')
    if sauve is None:
        sauve = enfant(cv, 'sauvegarde_rendu_spectacle', textDAT, -400, -760)
        sauve.text = (vue3d.par.top.expr if vue3d.par.top.mode == ParMode.EXPRESSION
                      else vue3d.par.top.val)
        sauve.comment = ("Le TOP d'origine du bandeau RENDU 3D de SORTIE_SPECTACLE "
                         "(haut/simulation), pour le remettre a la main.")
    _S = "parent.sortie.parent()"
    vue3d.par.top.expr = ("%s.op('CUBE_3D/out') if (%s.op('ANIMATION_CUBE') and "
                          "%s.op('ANIMATION_CUBE').par.Actif and %s.op('CUBE_3D/out')) "
                          "else %s.op('TRAINEES_LUMIERE/out')" % (_S, _S, _S, _S, _S))

# --- un compteur d'images REELLEMENT cuites (diagnostic de cadence) ----------
#  absTime.frame suit l'horloge murale et affiche toujours 60 ; seul un compteur
#  incremente a chaque image dit la verite. Lecture :
#     n0 = op('CUBE_3D').fetch('images_cuites') ... attendre ... (n1 - n0) / secondes
#  Mesure du 6 octobre 2026 : 17 images/s avec l'editeur de reseau ouvert sur
#  /project1/scale (3 900 noeuds), 36 images/s en mode Perform.
cpt = enfant(cv, 'compteur_images', executeDAT, -700, -500)
cpt.par.framestart = True
cpt.text = ("def onFrameStart(frame):\n\tc = me.parent()\n"
            "\tc.store('images_cuites', int(c.fetch('images_cuites', 0)) + 1)\n\treturn\n")
cpt.comment = "Compte les images reellement cuites (diagnostic de cadence)."

print('=' * 66)
print("CUBE_3D installe : l'impression reelle des LED")
print('=' * 66)
try:
    atlas.cook(force=True)
    import numpy as _np
    _a = atlas.numpyArray()
    _imp = int((_a[:VOX * RANGEES, :, 3] > 0).sum())
    _mem = [round(float(v), 1) for v in _a[VOX * RANGEES, :NB, 0]]
    print('  atlas                : %d x %d, %s' % (_a.shape[1], _a.shape[0], atlas.par.format.eval()))
    print('  voxels deja imprimes : %d (une seule image : normal si petit)' % _imp)
    print('  angles memorises     : %s' % _mem)
except Exception as _err:
    print('  (mesure impossible : %s)' % _err)
mauvais = [(x.path, x.errors()) for x in cv.findChildren() if x.errors()]
print('  image                : %s' % (cv.par.Imagesrc.eval().path if cv.par.Imagesrc.eval() else 'AUCUNE'))
print('  angles               : %s' % (cv.par.Anglessrc.eval().path if cv.par.Anglessrc.eval() else 'AUCUNS'))
print('  a regarder           : %s (real_Move : VOLUME BALAYE ; bandeau RENDU 3D quand un cube a la main)' % sortie.path)
print('  erreurs              : %s' % (mauvais if mauvais else 'aucune'))
