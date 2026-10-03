# ============================================================================
# DESINSTALLER_VASARELY -- retire completement l'effet Vasarely
#
# Utilisable SANS Textport : glisser ce fichier dans le reseau (un Text DAT
# se cree), puis clic droit sur le noeud -> Run Script.
#
# Remet l'expression du switch telle qu'avant Vasarely (sauvegarde dans
# VASARELY/sauvegarde, sinon l'enveloppe cube+anneau), retire le bouton et
# la ligne d'etat, rend aux boutons cube et anneau leur exclusivite a deux,
# remonte les lignes d'etat, puis supprime le module et le commentaire.
# Ensuite : Fichier -> Enregistrer sous.
# ============================================================================

import json

CHEMIN_SCALE = '/project1/scale'
NOM_MODULE = 'VASARELY'
NOM_COMMENT = 'COMMENT_59_VASARELY'
EXPR_INDEX_ORIGINE = ("2 if op('MOTIFS_LED').par.Motif.eval() != 'off' "
                      "else int(op('MASK_TEXTURE_BY_ANGLE_NO_GSWITCH_TD').par.Masque)")

CLIC_CUBE_2 = ("# Le clic bascule ANIMATION_CUBE.Actif ; quand il s'allume, il coupe\n"
               "# l'anneau-cone (un seul maitre a la fois sur la chaine LED).\n"
               "def onOffToOn(panelValue):\n"
               "\tp = op('/project1/scale/ANIMATION_CUBE').par.Actif\n"
               "\tp.val = 0 if p else 1\n"
               "\tif p:\n"
               "\t\tautre = op('/project1/scale/ANNEAU_CONE')\n"
               "\t\tif autre is not None:\n"
               "\t\t\tautre.par.Actif = 0\n"
               "\treturn\n")
CLIC_ANNEAU_2 = ("# Le clic bascule ANNEAU_CONE.Actif ; quand il s'allume, il coupe le cube\n"
                 "# (un seul maitre a la fois sur la chaine LED).\n"
                 "def onOffToOn(panelValue):\n"
                 "\tp = op('/project1/scale/ANNEAU_CONE').par.Actif\n"
                 "\tp.val = 0 if p else 1\n"
                 "\tif p:\n"
                 "\t\tautre = op('/project1/scale/ANIMATION_CUBE')\n"
                 "\t\tif autre is not None:\n"
                 "\t\t\tautre.par.Actif = 0\n"
                 "\treturn\n")


def _detruire(chemin):
    o = op(chemin)
    if o:
        o.destroy()


def desinstallation_vasarely():
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
        print('panel_mask_output : expression sans Vasarely remise.')
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
            clic_cube = section.op('bouton/clic')
            if clic_cube is not None:
                clic_cube.text = CLIC_CUBE_2
            clic_anneau = section.op('bouton_anneau/clic')
            if clic_anneau is not None:
                clic_anneau.text = CLIC_ANNEAU_2
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)
    print('VASARELY, bouton et commentaire retires.')
    print('Penser a : Fichier > Enregistrer sous.')


desinstallation_vasarely()
