# ============================================================================
# INSTALLER_REDETECTION_TEENSY -- la carte rebranchee est redetectee toute seule
#
# A executer le projet SAISON_9 ouvert :
#   exec(open('.../touchdesigner/INSTALLER_REDETECTION_TEENSY.py').read())
# REJOUABLE : s'il trouve sa marque, il ne fait rien.
#
# LE DEFAUT (6 octobre 2026, apres-midi). Le pilote moteur part avec
# TouchDesigner ; s'il n'a pas le port serie a ce moment-la (Teensy branchee
# apres), il ne l'ouvre jamais et les reglages de MOTEURS_TEENSY n'ont aucun
# effet. L'horloge affichait « carte absente : brancher la Teensy puis
# DETECTER » -- et ne l'effacait jamais, meme port revenu.
#
# LA CORRECTION, dans le DAT MOTEURS_TEENSY/horloge (et dans le CODE_HORLOGE
# de la copie de l'installeur Teensy rangee dans le projet, INSTALLER_TEENSY,
# pour qu'une reinstallation la garde). A chaque image on note si le port est
# present. Quand il REAPPARAIT :
#   - pilote dans son processus (Fildedie) : on arrete le processus par
#     _fil_arreter() -- il desarme et rend le port -- et tick() en relance un
#     neuf a l'image suivante, avec le port cette fois (c'est le chemin que
#     prend deja le module quand le processus meurt) ;
#   - pilote dans TouchDesigner : detecter_port(), comme le bouton DETECTER.
# Le message « carte absente » est remplace par « carte rebranchee ». Au
# chargement du fichier, le premier relevé ne declenche rien : port_vu part
# de None (le storage, sauve avec le .toe, ne doit pas commander un
# redemarrage a l'ouverture -- regle de COMMENT_49).
#
# A reporter dans le depot panneaux-led-rotatifs
# (choregraphie_reelle/INSTALLER_CONTAINER_TEENSY.py, CODE_HORLOGE) : ce
# script ne touche qu'au projet ouvert. La copie INSTALLER_TEENSY rangee dans
# le projet est PLUS ANCIENNE que le DAT horloge vivant (elle n'a pas la garde
# « sans carte » du 26 septembre) : le script l'ignore alors et le dit.
# ============================================================================

MARQUE = 'REDETECTION AUTOMATIQUE DE LA CARTE'

BLOC = '''    # REDETECTION AUTOMATIQUE DE LA CARTE (6 octobre 2026, demande de
    # Benjamin ; INSTALLER_REDETECTION_TEENSY.py du depot animation-cube).
    # Le port vient-il de reapparaitre ? Alors on redetecte sans clic.
    import glob as _glob
    try:
        _port = str(_comp_h.par.Port.eval())
        _ports = sorted(_glob.glob('/dev/cu.usbmodem*'))
        _present = _os.path.exists(_port) or bool(_ports)
        _vu = _comp_h.fetch('port_vu', None)
        if _vu is False and _present:
            _m = pilote.module
            if not _os.path.exists(_port) and _ports:
                _comp_h.par.Port.val = _ports[0]
            _fil = getattr(_m, '_fil', [None])
            if _fil and _fil[0] is not None:
                # pilote dans son processus, parti sans le port : on l'arrete,
                # tick() en relance un neuf a l'image suivante (Fildedie coche)
                _m._dire(_m._fil_arreter())
            elif not bool(_comp_h.par.Fildedie.eval()):
                _m.detecter_port()
            _comp_h.par.Chmot.val = ('carte rebranchee : port redetecte automatiquement (%s)'
                                     % _os.path.basename(str(_comp_h.par.Port.eval())))
        elif _present and 'veille' in str(_comp_h.par.Chmot.eval()):
            _comp_h.par.Chmot.val = 'carte presente : %s' % _os.path.basename(_port)
        if _vu != _present:
            _comp_h.store('port_vu', _present)
    except Exception:
        pass
'''

ANCRE_COMP = "    _comp_h = me.parent()\n"      # juste apres la lecture du conteneur, AVANT la garde « sans carte »
ANCRE_START = "    me.parent().par.Arme.val = False\n    return\n"
LIGNE_START = ("    me.parent().par.Arme.val = False\n"
               "    me.parent().store('port_vu', None)   # redetection : premier releve neutre\n"
               "    return\n")


def patcher(texte, nom):
    #  LE BLOC DOIT ETRE EN TETE DE onFrameStart. Une premiere version l'avait
    #  mis apres la garde « sans carte », qui SORT de la fonction tant que le
    #  port manque : l'absence n'etait jamais memorisee, le retour jamais vu.
    #  On retire donc un bloc deja present (ancienne ou nouvelle place) avant
    #  de le reposer au bon endroit : relancer le script est toujours sur.
    deja = BLOC in texte
    texte = texte.replace(BLOC, '')
    if texte.count(ANCRE_COMP) != 1:
        return texte, 'ANCRE INTROUVABLE (%d) : rien fait' % texte.count(ANCRE_COMP)
    i = texte.index(ANCRE_COMP)
    if 'def onFrameStart' not in texte[:i]:
        return texte, 'onFrameStart introuvable avant l ancre : rien fait'
    texte = texte.replace(ANCRE_COMP, ANCRE_COMP + BLOC)
    if LIGNE_START not in texte:
        if texte.count(ANCRE_START) != 1:
            return texte, 'ancre de onStart introuvable : bloc pose, onStart non modifie'
        texte = texte.replace(ANCRE_START, LIGNE_START)
    return texte, ('replace au bon endroit' if deja else 'patche')


mt = op('/project1/scale/MOTEURS_TEENSY')
assert mt is not None, 'MOTEURS_TEENSY introuvable'
horloge = mt.op('horloge')
horloge.text, r1 = patcher(horloge.text, 'horloge')
print('MOTEURS_TEENSY/horloge : %s' % r1)
inst = op('/project1/scale/INSTALLER_TEENSY')
if inst is not None:
    inst.text, r2 = patcher(inst.text, 'INSTALLER_TEENSY')
    print('INSTALLER_TEENSY (copie de l installeur dans le projet) : %s' % r2)
else:
    print('INSTALLER_TEENSY absent du projet : seul le DAT horloge est patche')
mt.store('port_vu', None)
print('port : %s | Chmot : %s' % (mt.par.Port.eval(), mt.par.Chmot.eval()))
