# ============================================================================
# REPARER_ERREUR_TEXT1 -- l'erreur qui remplit le Textport 8 fois par seconde
#
#   AttributeError: 'NoneType' object has no attribute 'eval'
#   dans /project1/scale/text1, lance par chotext1...pexecDat (CHOP Execute
#   sur lfo4, canal pulse, 8 Hz).
#
# CE QUI SE PASSE
#   text1 envoie les dix angles rz0..rz9 (lus dans shuffle1) vers les sorties
#   OSC osc_rz0..9 et vers rz_values_for_mask. Quand la chaine rz est en
#   erreur en amont, shuffle1 n'a plus ces canaux et text1 plante -- a chaque
#   impulsion de lfo4, d'ou le flot de tracebacks.
#
# LA CAUSE LA PLUS PROBABLE ICI
#   audiofilein1 pointe sur '../Signs Full - Audio et Synthese_debut.mp3',
#   un chemin RELATIF au dossier du .toe. La copie du projet ouverte depuis
#   le depot animation-cube-a-faire-dans-TD ne retrouve plus ce fichier
#   (il vit dans 'Ameliorer controle panneaux rotation TD/'), la branche
#   audio-reactive de la rotation casse, et text1 plante.
#   Ce n'est PAS lie a ANIMATION_CUBE : l'erreur existait, le Textport
#   ouvert la rend simplement visible.
#
# CE QUE FAIT CE SCRIPT (textport) :
#   exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/REPARER_ERREUR_TEXT1.py').read())
#
#   1. Diagnostic : etat de la chaine rz, canaux presents dans shuffle1,
#      fichier audio trouve ou non.
#   2. Si le mp3 manque et qu'il existe a l'emplacement connu, remet le
#      chemin ABSOLU dans audiofilein1 (l'ancien est garde en storage).
#   3. Durcit text1 : s'il manque des canaux, il N'ENVOIE RIEN (surtout pas
#      des zeros aux moteurs) et le dit UNE fois dans le textport, au lieu
#      de planter. Comportement strictement identique quand tout va bien.
#      L'original est conserve dans le DAT text1_origine.
#
# Pour revenir en arriere :  retablir_text1()  et  retablir_audio()
# Ensuite : Fichier -> Enregistrer sous.
# ============================================================================

import os

CHEMIN_SCALE = '/project1/scale'
MP3_CONNU = ('/Users/oslive/Documents/Ameliorer controle panneaux rotation TD/'
             'Signs Full - Audio et Synthese_debut.mp3')
MARQUE = 'Version durcie'

TEXT1_DURCI = """# Envoi periodique des dix angles rz0..rz9 (declenche 8 fois par seconde
# par lfo4 via le CHOP Execute) vers les sorties OSC et le masque Max.
# Version durcie : si des canaux rz manquent dans shuffle1 (chaine rz en
# erreur : audio introuvable, Teensy absente...), on N'ENVOIE RIEN plutot
# que de planter -- et surtout plutot que d'envoyer des zeros aux moteurs.
# Le changement d'etat est signale UNE fois dans le textport.
# L'original est conserve dans text1_origine (retablir_text1() du depot).
chop = op('shuffle1')  # ou le chemin complet
if chop is None:
    manquants = ['shuffle1 introuvable']
else:
    manquants = [('rz' + str(i)) for i in range(10) if chop['rz' + str(i)] is None]

if manquants != me.fetch('rz_manquants', None, search=False):
    me.store('rz_manquants', manquants)
    if manquants:
        debug('text1 : canaux absents dans shuffle1 (' + ', '.join(manquants)
              + ') -- envoi saute. Verifier la chaine rz : audiofilein1, '
              'rz_mode, Teensy.')
    else:
        debug('text1 : chaine rz retablie, envoi des angles repris.')

if not manquants:
    rz_values = [chop['rz' + str(i)].eval() for i in range(10)]

    # Publie les dix positions vers la deuxieme entree du masque transpose depuis Max.
    mask_positions = op('rz_values_for_mask')
    if mask_positions:
        for i, value in enumerate(rz_values):
            mask_positions[0, i] = float(value) % 360.0

    for i, value in enumerate(rz_values):
        addr = '/rz' + str(i)
        dat_name = 'osc_rz' + str(i)
        dat = op(dat_name)
        if dat:
            dat.sendOSC(addr, [float(value)])
        else:
            debug(dat_name + ' manquant')
"""


def _chemin_absolu(p):
    if not p:
        return p
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(project.folder, p))


def reparer():
    scale = op(CHEMIN_SCALE)
    assert scale, 'Introuvable : ' + CHEMIN_SCALE
    print('')
    print('DIAGNOSTIC DE LA CHAINE rz')

    # 1. Les canaux que text1 attend
    shuffle = scale.op('shuffle1')
    if shuffle is not None:
        noms = [c.name for c in shuffle.chans()]
        manquants = [('rz' + str(i)) for i in range(10) if ('rz' + str(i)) not in noms]
        print('  shuffle1 : %d canaux (%s)' % (len(noms), ', '.join(noms[:12]) or 'aucun'))
        print('  canaux attendus manquants : %s' % (', '.join(manquants) if manquants else 'aucun'))
    else:
        print('  shuffle1 : INTROUVABLE')

    # 2. Les erreurs le long de la chaine
    for nom in ('math13', 'rz_out', 'rz_mode', 'switch1', 'rz_preserve_channels',
                'rz_audio_envelope', 'rz_audio_mix', 'audiofilein1'):
        o = scale.op(nom)
        if o is None:
            continue
        e = o.errors()
        if e:
            print('  %s : EN ERREUR -- %s' % (nom, e.strip().splitlines()[0]))
    try:
        print('  mode rotation (Rzenable) : %s' % int(scale.par.Rzenable))
    except Exception:
        pass

    # 3. Le fichier audio
    audio = scale.op('audiofilein1')
    if audio is not None:
        actuel = str(audio.par.file)
        resolu = _chemin_absolu(actuel)
        trouve = os.path.isfile(resolu)
        print('  audiofilein1 : %s' % actuel)
        print('    resolu en : %s -- %s' % (resolu, 'TROUVE' if trouve else 'INTROUVABLE'))
        if not trouve and os.path.isfile(MP3_CONNU):
            scale.store('reparer_audio_origine', actuel)
            audio.par.file = MP3_CONNU
            print('    -> remis sur le chemin absolu connu :')
            print('       ' + MP3_CONNU)
            print("       (l'ancien chemin est garde ; retablir_audio() pour revenir)")
        elif not trouve:
            print('    -> fichier aussi introuvable a l emplacement connu ; a regler a la main.')

    # 4. Durcir text1
    t = scale.op('text1')
    if t is None:
        print('  text1 : INTROUVABLE, rien a durcir')
    elif MARQUE in t.text:
        print('  text1 : deja durci, rien a faire')
    else:
        sauvegarde = scale.op('text1_origine')
        if sauvegarde is None:
            sauvegarde = scale.create(textDAT, 'text1_origine')
            sauvegarde.nodeX, sauvegarde.nodeY = t.nodeX, t.nodeY - 150
            sauvegarde.comment = 'Copie de text1 avant durcissement (REPARER_ERREUR_TEXT1).'
        sauvegarde.text = t.text
        t.text = TEXT1_DURCI
        print('  text1 : durci (plus de plantage, aucun envoi quand des canaux manquent).')
        print('          Original conserve dans text1_origine.')

    print('')
    print('Fait. Si audiofilein1 vient d etre repare, la chaine rz se retablit')
    print('d elle-meme ; text1 le dira une fois dans le textport.')
    print('Penser a : Fichier > Enregistrer sous.')


def retablir_text1():
    scale = op(CHEMIN_SCALE)
    t = scale.op('text1') if scale else None
    s = scale.op('text1_origine') if scale else None
    if t is None or s is None:
        print('Rien a retablir (text1 ou text1_origine introuvable).')
        return
    t.text = s.text
    print('text1 remis a sa version d origine (text1_origine conserve).')


def retablir_audio():
    scale = op(CHEMIN_SCALE)
    audio = scale.op('audiofilein1') if scale else None
    if audio is None:
        print('audiofilein1 introuvable.')
        return
    ancien = scale.fetch('reparer_audio_origine', None, search=False)
    if ancien is None:
        print('Pas de chemin d origine en memoire ; rien change.')
        return
    audio.par.file = ancien
    print('audiofilein1 remis sur : ' + ancien)


reparer()
