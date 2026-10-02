# ============================================================================
# DESINSTALLER_ANIMATION_CUBE -- retire completement l'option animation-cube
#
# Utilisable SANS Textport : glisser ce fichier depuis le Finder dans le
# reseau de TouchDesigner (un Text DAT se cree), puis clic droit sur le
# noeud -> Run Script. (Ou au Textport : exec(open('...').read()))
#
# Ce que ca fait, dans l'ordre sur :
#   1. remet l'expression d'origine sur le switch panel_mask_output
#      (celle sauvegardee dans ANIMATION_CUBE/sauvegarde, sinon celle
#      du projet livre) ;
#   2. remet la vue 'led' de SORTIE_SPECTACLE sur MOTIFS_LED/out ;
#   3. supprime la section bouton, le module ANIMATION_CUBE et le
#      commentaire COMMENT_57.
# La chaine LED retombe au bit pres sur le comportement d'origine.
# Ensuite : Fichier -> Enregistrer sous.
# ============================================================================

import json

CHEMIN_SCALE = '/project1/scale'
NOM_MODULE = 'ANIMATION_CUBE'
NOM_SECTION = 'cube_anime'
NOM_COMMENT = 'COMMENT_57_ANIMATION_CUBE'
EXPR_INDEX_ORIGINE = ("2 if op('MOTIFS_LED').par.Motif.eval() != 'off' "
                      "else int(op('MASK_TEXTURE_BY_ANGLE_NO_GSWITCH_TD').par.Masque)")
EXPR_VUE_LED_ORIGINE = "parent.sortie.parent().op('MOTIFS_LED/out')"


def _detruire(chemin):
    o = op(chemin)
    if o:
        o.destroy()


def desinstallation():
    scale = op(CHEMIN_SCALE)
    if not scale:
        print('Introuvable :', CHEMIN_SCALE)
        return
    sw = scale.op('panel_mask_output')
    vue_led = scale.op('SORTIE_SPECTACLE/haut/droite/led')
    expr_index = EXPR_INDEX_ORIGINE
    expr_vue = EXPR_VUE_LED_ORIGINE
    comp = scale.op(NOM_MODULE)
    if comp and comp.op('sauvegarde'):
        try:
            d = json.loads(comp.op('sauvegarde').text)
            expr_index = d.get('index', expr_index) or expr_index
            expr_vue = d.get('vue_led', expr_vue) or expr_vue
        except Exception:
            pass
    if sw:
        sw.par.index.expr = expr_index
        print('panel_mask_output : expression d origine remise.')
    if vue_led:
        vue_led.par.top.expr = expr_vue
        print('vue led de SORTIE_SPECTACLE : remise sur MOTIFS_LED/out.')
    _detruire(CHEMIN_SCALE + '/SORTIE_SPECTACLE/PANNEAU_COMMANDES/' + NOM_SECTION)
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)
    print('ANIMATION_CUBE, bouton et commentaire retires.')
    print('Penser a : Fichier > Enregistrer sous.')


desinstallation()
