# ============================================================================
# DESINSTALLER_ANNEAU_CONE -- retire completement l'anneau-cone
#
# Utilisable SANS Textport : glisser ce fichier dans le reseau (un Text DAT
# se cree), puis clic droit sur le noeud -> Run Script.
#
# Remet l'expression du switch panel_mask_output telle qu'elle etait avant
# l'anneau (sauvegarde dans ANNEAU_CONE/sauvegarde ; sinon l'enveloppe du
# cube si ANIMATION_CUBE est present, sinon l'expression d'origine du
# projet), retire le bouton et la ligne d'etat de SORTIE_SPECTACLE, rend au
# bouton du cube son comportement d'origine, puis supprime le module et le
# commentaire. Desinstaller l'anneau AVANT le cube si les deux doivent partir.
# Ensuite : Fichier -> Enregistrer sous.
# ============================================================================

import json

CHEMIN_SCALE = '/project1/scale'
NOM_MODULE = 'ANNEAU_CONE'
NOM_COMMENT = 'COMMENT_58_ANNEAU_CONE'
EXPR_INDEX_ORIGINE = ("2 if op('MOTIFS_LED').par.Motif.eval() != 'off' "
                      "else int(op('MASK_TEXTURE_BY_ANGLE_NO_GSWITCH_TD').par.Masque)")


def _detruire(chemin):
    o = op(chemin)
    if o:
        o.destroy()


def desinstallation_anneau():
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
        print('panel_mask_output : expression sans anneau remise.')
    if commandes:
        _detruire(commandes.path + '/cube_anime/bouton_anneau')
        _detruire(commandes.path + '/cube_anime/etat_anneau')
        _detruire(commandes.path + '/animations_3d')
        section = commandes.op('cube_anime')
        if section is not None:
            etat_cube = section.op('etat')
            if etat_cube is not None:
                etat_cube.par.alignorder = 2
            clic_cube = section.op('bouton/clic')
            if clic_cube is not None:
                clic_cube.text = (
                    "# Le clic sur le bouton bascule ANIMATION_CUBE.Actif.\n"
                    "def onOffToOn(panelValue):\n"
                    "\tp = op('/project1/scale/ANIMATION_CUBE').par.Actif\n"
                    "\tp.val = 0 if p else 1\n"
                    "\treturn\n")
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)
    print('ANNEAU_CONE, bouton et commentaire retires.')
    print('Penser a : Fichier > Enregistrer sous.')


desinstallation_anneau()
