# ============================================================================
# INSTALLER_ANIMATION_CUBE -- le cube en fil de fer de cube_animatio
#                             dans la chaine LED de SAISON_9
#
# A executer le projet SAISON_9 ouvert (SAISON_9_ANIMATION_CUBE.toe du depot,
# issu de SAISON_9_MOINS_DE_PY_ANNEAUX_SEULS_SANS_VARIATIONS.2) -- soit par
# glisser-deposer du fichier dans le reseau puis clic droit -> Run Script,
# soit au Textport (Alt+T) :
#
#   exec(open('/Users/oslive/Documents/animation-cube-a-faire-dans-TD/touchdesigner/INSTALLER_ANIMATION_CUBE.py').read())
#
# CE QUE CA CONSTRUIT
#   /project1/scale/ANIMATION_CUBE        le module (poses, horloge, GLSL)
#   panel_mask_output                     4e entree + nouvelle expression
#   SORTIE_SPECTACLE/PANNEAU_COMMANDES/cube_anime   la section avec LE BOUTON
#   COMMENT_57_ANIMATION_CUBE             la documentation, style maison
#
# LE PRINCIPE, EN UNE PHRASE
#   Comme le mode CHAMP 3D de MOTIFS_LED : chaque texel de l'image 160x80
#   connait sa position reelle dans l'espace (angle de sa lame via
#   angles_top, profondeur de son panneau) et s'allume si cette position
#   touche une arete du cube de l'image courante de l'animation
#   (300 poses retrouvees dans les images du dossier cube_animatio).
#
# RIEN NE CHANGE tant que le bouton n'est pas presse : Actif est decoche
# a l'installation et l'expression du switch retombe alors exactement sur
# le comportement d'origine.
#
# Relancable sans danger (reinstalle proprement par-dessus).
# Pour tout retirer :  desinstaller()
# Ensuite : Fichier -> Enregistrer sous (ne pas ecraser le .toe d'origine).
# ============================================================================

import json

CHEMIN_SCALE = '/project1/scale'
NOM_MODULE = 'ANIMATION_CUBE'
NOM_SECTION = 'cube_anime'
NOM_COMMENT = 'COMMENT_57_ANIMATION_CUBE'

# Expression d'origine du switch, telle que lue dans le projet livre -- sert
# de secours si la sauvegarde manque au moment de desinstaller.
EXPR_INDEX_ORIGINE = ("2 if op('MOTIFS_LED').par.Motif.eval() != 'off' "
                      "else int(op('MASK_TEXTURE_BY_ANGLE_NO_GSWITCH_TD').par.Masque)")
EXPR_VUE_LED_ORIGINE = "parent.sortie.parent().op('MOTIFS_LED/out')"

# ----------------------------------------------------------------------------
# LES 300 POSES (cx, cy, s, qx, qy, qz, qw, interpolee), copiees de
# poses_cube_animatio.js : centre et demi-cote en demi-largeurs d'image,
# rotation en quaternion (repere camera), interpolee = 1 si l'image manquait.
# ----------------------------------------------------------------------------
POSES_TEXTE = """-0.0000 -0.0000 0.2761 0.0000 -0.0000 -0.0001 1.0000 0
0.0055 0.0055 0.2748 -0.0036 -0.0024 -0.0003 1.0000 1
0.0110 0.0111 0.2736 -0.0072 -0.0048 -0.0006 1.0000 1
0.0165 0.0166 0.2723 -0.0108 -0.0072 -0.0008 0.9999 1
0.0221 0.0222 0.2711 -0.0144 -0.0096 -0.0010 0.9998 1
0.0276 0.0277 0.2698 -0.0180 -0.0120 -0.0012 0.9998 1
0.0331 0.0333 0.2686 -0.0216 -0.0144 -0.0015 0.9997 1
0.0386 0.0388 0.2673 -0.0252 -0.0168 -0.0017 0.9995 1
0.0442 0.0443 0.2660 -0.0288 -0.0192 -0.0019 0.9994 0
0.0485 0.0488 0.2649 -0.0323 -0.0295 -0.0014 0.9990 1
0.0529 0.0533 0.2637 -0.0357 -0.0398 -0.0009 0.9986 0
0.0547 0.0573 0.2631 -0.0393 -0.0506 -0.0015 0.9979 1
0.0566 0.0613 0.2625 -0.0430 -0.0614 -0.0022 0.9972 1
0.0584 0.0653 0.2619 -0.0466 -0.0722 -0.0029 0.9963 1
0.0602 0.0693 0.2614 -0.0502 -0.0830 -0.0035 0.9953 0
0.0662 0.0734 0.2593 -0.0528 -0.0848 -0.0053 0.9950 1
0.0721 0.0775 0.2573 -0.0555 -0.0865 -0.0071 0.9947 1
0.0781 0.0815 0.2553 -0.0581 -0.0883 -0.0089 0.9944 1
0.0841 0.0856 0.2533 -0.0607 -0.0900 -0.0106 0.9940 0
0.0841 0.0894 0.2519 -0.0643 -0.0958 -0.0132 0.9932 1
0.0841 0.0931 0.2505 -0.0678 -0.1016 -0.0157 0.9924 0
0.0902 0.0963 0.2490 -0.0784 -0.1057 -0.0145 0.9912 1
0.0963 0.0994 0.2475 -0.0890 -0.1098 -0.0133 0.9899 1
0.1024 0.1025 0.2460 -0.0996 -0.1139 -0.0121 0.9884 1
0.1085 0.1057 0.2445 -0.1102 -0.1180 -0.0109 0.9868 0
0.1112 0.1094 0.2428 -0.1135 -0.1261 -0.0106 0.9854 1
0.1139 0.1131 0.2411 -0.1167 -0.1342 -0.0103 0.9840 0
0.1165 0.1159 0.2404 -0.1180 -0.1381 -0.0122 0.9833 1
0.1192 0.1188 0.2396 -0.1194 -0.1419 -0.0140 0.9826 1
0.1218 0.1216 0.2389 -0.1207 -0.1458 -0.0158 0.9818 1
0.1245 0.1245 0.2382 -0.1220 -0.1497 -0.0177 0.9810 0
0.1276 0.1282 0.2372 -0.1259 -0.1546 -0.0188 0.9797 1
0.1307 0.1319 0.2363 -0.1298 -0.1595 -0.0199 0.9784 0
0.1338 0.1347 0.2354 -0.1332 -0.1644 -0.0212 0.9771 1
0.1368 0.1375 0.2345 -0.1366 -0.1693 -0.0226 0.9758 1
0.1399 0.1404 0.2336 -0.1400 -0.1742 -0.0239 0.9744 1
0.1429 0.1432 0.2327 -0.1433 -0.1791 -0.0252 0.9730 1
0.1460 0.1460 0.2318 -0.1467 -0.1840 -0.0266 0.9715 1
0.1491 0.1489 0.2309 -0.1501 -0.1889 -0.0279 0.9701 0
0.1520 0.1517 0.2303 -0.1543 -0.1925 -0.0307 0.9686 1
0.1549 0.1545 0.2297 -0.1585 -0.1960 -0.0335 0.9671 1
0.1578 0.1574 0.2291 -0.1628 -0.1996 -0.0363 0.9656 0
0.1599 0.1591 0.2284 -0.1640 -0.2066 -0.0347 0.9640 1
0.1620 0.1609 0.2278 -0.1652 -0.2137 -0.0330 0.9623 0
0.1639 0.1645 0.2267 -0.1748 -0.2172 -0.0394 0.9595 0
0.1662 0.1656 0.2278 -0.1784 -0.2200 -0.0396 0.9582 0
0.1682 0.1674 0.2269 -0.1806 -0.2248 -0.0407 0.9566 1
0.1703 0.1691 0.2260 -0.1828 -0.2296 -0.0418 0.9550 1
0.1724 0.1709 0.2250 -0.1850 -0.2344 -0.0428 0.9534 1
0.1744 0.1726 0.2241 -0.1872 -0.2391 -0.0439 0.9518 0
0.1761 0.1747 0.2240 -0.1913 -0.2419 -0.0486 0.9500 1
0.1778 0.1768 0.2239 -0.1953 -0.2446 -0.0534 0.9483 1
0.1795 0.1789 0.2238 -0.1994 -0.2473 -0.0582 0.9464 0
0.1782 0.1816 0.2227 -0.1996 -0.2569 -0.0597 0.9437 0
0.1808 0.1825 0.2225 -0.2026 -0.2617 -0.0601 0.9417 1
0.1834 0.1833 0.2222 -0.2056 -0.2665 -0.0605 0.9397 1
0.1860 0.1842 0.2220 -0.2086 -0.2713 -0.0609 0.9376 1
0.1886 0.1851 0.2218 -0.2116 -0.2760 -0.0613 0.9356 0
0.1890 0.1861 0.2212 -0.2164 -0.2803 -0.0648 0.9329 1
0.1893 0.1871 0.2206 -0.2212 -0.2846 -0.0683 0.9303 1
0.1897 0.1881 0.2201 -0.2260 -0.2889 -0.0718 0.9275 1
0.1900 0.1891 0.2195 -0.2308 -0.2932 -0.0752 0.9247 0
0.1905 0.1898 0.2192 -0.2341 -0.2969 -0.0780 0.9225 1
0.1911 0.1904 0.2189 -0.2373 -0.3005 -0.0807 0.9202 1
0.1916 0.1911 0.2186 -0.2406 -0.3042 -0.0834 0.9179 1
0.1922 0.1917 0.2183 -0.2439 -0.3079 -0.0862 0.9156 1
0.1927 0.1924 0.2180 -0.2471 -0.3115 -0.0889 0.9132 1
0.1933 0.1930 0.2177 -0.2504 -0.3151 -0.0916 0.9108 1
0.1938 0.1937 0.2174 -0.2536 -0.3188 -0.0943 0.9084 1
0.1944 0.1943 0.2171 -0.2569 -0.3224 -0.0971 0.9059 1
0.1949 0.1950 0.2168 -0.2601 -0.3260 -0.0998 0.9034 1
0.1955 0.1956 0.2165 -0.2633 -0.3296 -0.1025 0.9009 1
0.1960 0.1963 0.2161 -0.2665 -0.3331 -0.1052 0.8983 0
0.1971 0.1950 0.2185 -0.2678 -0.3414 -0.0938 0.8961 0
0.1971 0.1953 0.2183 -0.2714 -0.3460 -0.0984 0.8927 1
0.1970 0.1957 0.2182 -0.2751 -0.3506 -0.1029 0.8893 1
0.1970 0.1960 0.2180 -0.2787 -0.3551 -0.1075 0.8858 1
0.1969 0.1963 0.2179 -0.2823 -0.3597 -0.1120 0.8823 1
0.1969 0.1966 0.2177 -0.2859 -0.3642 -0.1165 0.8787 0
0.1964 0.1974 0.2180 -0.2840 -0.3672 -0.1147 0.8783 0
0.1956 0.1962 0.2183 -0.2886 -0.3706 -0.1211 0.8744 1
0.1947 0.1949 0.2187 -0.2932 -0.3741 -0.1275 0.8705 0
0.1949 0.1940 0.2184 -0.2957 -0.3765 -0.1285 0.8685 1
0.1952 0.1930 0.2181 -0.2981 -0.3788 -0.1295 0.8665 0
0.1935 0.1931 0.2193 -0.3022 -0.3844 -0.1347 0.8619 1
0.1917 0.1932 0.2204 -0.3062 -0.3899 -0.1399 0.8571 0
0.1933 0.1930 0.2187 -0.3055 -0.3913 -0.1351 0.8575 0
0.1920 0.1919 0.2198 -0.3081 -0.3966 -0.1428 0.8529 1
0.1908 0.1907 0.2208 -0.3107 -0.4018 -0.1506 0.8481 0
0.1905 0.1885 0.2196 -0.3098 -0.4030 -0.1478 0.8484 0
0.1874 0.1888 0.2198 -0.3177 -0.4102 -0.1544 0.8408 0
0.1858 0.1884 0.2205 -0.3147 -0.4116 -0.1628 0.8397 0
0.1856 0.1864 0.2208 -0.3201 -0.4144 -0.1633 0.8361 1
0.1855 0.1844 0.2210 -0.3256 -0.4172 -0.1638 0.8325 0
0.1851 0.1834 0.2209 -0.3261 -0.4195 -0.1654 0.8308 0
0.1832 0.1822 0.2215 -0.3300 -0.4230 -0.1711 0.8264 1
0.1813 0.1809 0.2220 -0.3339 -0.4264 -0.1768 0.8219 1
0.1793 0.1797 0.2225 -0.3378 -0.4298 -0.1825 0.8173 0
0.1763 0.1785 0.2239 -0.3354 -0.4360 -0.1792 0.8157 0
0.1746 0.1766 0.2233 -0.3403 -0.4414 -0.1897 0.8083 0
0.1748 0.1733 0.2243 -0.3410 -0.4398 -0.1875 0.8094 0
0.1738 0.1737 0.2258 -0.3413 -0.4452 -0.1913 0.8054 0
0.1708 0.1718 0.2259 -0.3441 -0.4476 -0.1947 0.8021 1
0.1678 0.1699 0.2260 -0.3469 -0.4499 -0.1980 0.7988 0
0.1677 0.1666 0.2266 -0.3489 -0.4541 -0.2016 0.7946 0
0.1629 0.1626 0.2267 -0.3491 -0.4581 -0.2053 0.7913 0
0.1604 0.1625 0.2272 -0.3550 -0.4596 -0.2079 0.7871 0
0.1600 0.1610 0.2284 -0.3540 -0.4636 -0.2112 0.7843 0
0.1586 0.1591 0.2297 -0.3620 -0.4653 -0.2164 0.7782 0
0.1567 0.1551 0.2302 -0.3590 -0.4703 -0.2199 0.7756 0
0.1547 0.1540 0.2314 -0.3628 -0.4711 -0.2245 0.7720 0
0.1532 0.1524 0.2306 -0.3665 -0.4740 -0.2230 0.7690 0
0.1479 0.1479 0.2329 -0.3652 -0.4756 -0.2354 0.7648 0
0.1443 0.1447 0.2329 -0.3677 -0.4817 -0.2375 0.7592 0
0.1420 0.1435 0.2345 -0.3720 -0.4841 -0.2403 0.7547 0
0.1408 0.1404 0.2352 -0.3690 -0.4900 -0.2418 0.7519 0
0.1361 0.1375 0.2355 -0.3741 -0.4888 -0.2489 0.7478 0
0.1347 0.1340 0.2377 -0.3787 -0.4914 -0.2518 0.7427 0
0.1330 0.1334 0.2388 -0.3785 -0.4949 -0.2544 0.7396 0
0.1322 0.1291 0.2397 -0.3810 -0.4987 -0.2537 0.7360 0
0.1233 0.1232 0.2385 -0.3815 -0.5011 -0.2569 0.7331 0
0.1222 0.1204 0.2402 -0.3852 -0.5020 -0.2746 0.7240 0
0.1209 0.1188 0.2419 -0.3890 -0.5013 -0.2731 0.7230 0
0.1151 0.1150 0.2427 -0.3817 -0.5080 -0.2728 0.7224 0
0.1107 0.1111 0.2436 -0.3882 -0.5083 -0.2768 0.7172 0
0.1063 0.1096 0.2439 -0.3896 -0.5065 -0.2802 0.7163 0
0.1019 0.1050 0.2440 -0.3909 -0.5098 -0.2858 0.7111 0
0.1046 0.1029 0.2477 -0.3928 -0.5094 -0.2840 0.7110 0
0.0980 0.0989 0.2467 -0.3950 -0.5107 -0.2920 0.7056 0
0.0991 0.0971 0.2498 -0.3943 -0.5142 -0.2917 0.7036 0
0.0883 0.0918 0.2486 -0.3958 -0.5159 -0.2958 0.6998 0
0.0826 0.0868 0.2497 -0.3967 -0.5157 -0.3023 0.6966 0
0.0805 0.0815 0.2523 -0.3976 -0.5185 -0.3069 0.6920 0
0.0745 0.0776 0.2514 -0.4030 -0.5183 -0.3158 0.6850 0
0.0697 0.0720 0.2550 -0.4166 -0.5368 -0.3130 0.6636 0
0.0675 0.0675 0.2568 -0.4136 -0.5379 -0.3158 0.6632 0
0.0664 0.0643 0.2581 -0.4160 -0.5400 -0.3193 0.6583 0
0.0585 0.0598 0.2595 -0.4157 -0.5407 -0.3231 0.6561 0
0.0574 0.0567 0.2612 -0.4166 -0.5402 -0.3220 0.6564 0
0.0501 0.0489 0.2618 -0.4172 -0.5423 -0.3259 0.6524 0
0.0488 0.0453 0.2649 -0.4063 -0.5541 -0.3535 0.6347 0
0.0459 0.0385 0.2675 -0.4016 -0.5549 -0.3521 0.6378 0
0.0400 0.0362 0.2687 -0.4026 -0.5564 -0.3560 0.6337 0
0.0332 0.0316 0.2701 -0.4011 -0.5602 -0.3616 0.6281 0
0.0307 0.0275 0.2738 -0.4047 -0.5582 -0.3608 0.6281 0
0.0243 0.0210 0.2714 -0.4058 -0.5591 -0.3638 0.6248 0
0.0179 0.0151 0.2756 -0.4101 -0.5582 -0.3730 0.6174 0
0.0164 0.0108 0.2770 -0.4115 -0.5605 -0.3771 0.6118 0
0.0069 0.0051 0.2760 -0.4065 -0.5636 -0.3788 0.6113 0
0.0059 0.0012 0.2814 -0.4099 -0.5628 -0.3850 0.6058 0
0.0009 -0.0023 0.2807 -0.4063 -0.5678 -0.3817 0.6056 0
-0.0117 -0.0087 0.2828 -0.4152 -0.5634 -0.4000 0.5918 0
-0.0090 -0.0135 0.2835 -0.4096 -0.5674 -0.3877 0.5999 0
-0.0174 -0.0189 0.2847 -0.4128 -0.5675 -0.3958 0.5923 1
-0.0258 -0.0244 0.2858 -0.4159 -0.5675 -0.4038 0.5847 0
-0.0266 -0.0290 0.2885 -0.4187 -0.5649 -0.4099 0.5810 0
-0.0310 -0.0351 0.2902 -0.4144 -0.5706 -0.4117 0.5772 0
-0.0410 -0.0418 0.2914 -0.4187 -0.5680 -0.4162 0.5735 0
-0.0439 -0.0464 0.2939 -0.4161 -0.5721 -0.4248 0.5649 0
-0.0535 -0.0530 0.2934 -0.4163 -0.5745 -0.4236 0.5632 0
-0.0598 -0.0574 0.2955 -0.4174 -0.5713 -0.4255 0.5642 0
-0.0620 -0.0649 0.2975 -0.4209 -0.5708 -0.4305 0.5584 0
-0.0724 -0.0663 0.3015 -0.4130 -0.5821 -0.4341 0.5497 0
-0.0773 -0.0735 0.3039 -0.4136 -0.5798 -0.4395 0.5474 0
-0.0824 -0.0798 0.3039 -0.4156 -0.5813 -0.4413 0.5428 0
-0.0846 -0.0867 0.3057 -0.4185 -0.5798 -0.4528 0.5327 0
-0.0981 -0.0940 0.3075 -0.4173 -0.5832 -0.4498 0.5323 0
-0.0985 -0.0998 0.3081 -0.4138 -0.5839 -0.4593 0.5262 0
-0.1060 -0.1032 0.3116 -0.4194 -0.5776 -0.4664 0.5225 0
-0.1075 -0.1094 0.3130 -0.4136 -0.5844 -0.4680 0.5180 0
-0.1180 -0.1167 0.3158 -0.4143 -0.5830 -0.4710 0.5163 1
-0.1285 -0.1241 0.3186 -0.4150 -0.5816 -0.4741 0.5146 0
-0.1332 -0.1310 0.3196 -0.4193 -0.5796 -0.4839 0.5040 0
-0.1391 -0.1355 0.3221 -0.4214 -0.5771 -0.4827 0.5064 0
-0.1447 -0.1409 0.3211 -0.4185 -0.5796 -0.4949 0.4939 0
-0.1492 -0.1469 0.3260 -0.4107 -0.5835 -0.4964 0.4944 0
-0.1550 -0.1541 0.3265 -0.4106 -0.5859 -0.4978 0.4902 0
-0.1665 -0.1589 0.3309 -0.4151 -0.5852 -0.5015 0.4834 0
-0.1735 -0.1671 0.3336 -0.4112 -0.5849 -0.5057 0.4828 0
-0.1737 -0.1718 0.3338 -0.4141 -0.5827 -0.5070 0.4816 0
-0.1798 -0.1780 0.3357 -0.4134 -0.5827 -0.5113 0.4777 1
-0.1860 -0.1843 0.3376 -0.4127 -0.5828 -0.5155 0.4737 1
-0.1921 -0.1905 0.3395 -0.4119 -0.5828 -0.5197 0.4698 0
-0.2001 -0.1960 0.3423 -0.4075 -0.5870 -0.5217 0.4661 0
-0.2011 -0.2015 0.3418 -0.3937 -0.5938 -0.5478 0.4385 0
-0.2152 -0.2052 0.3442 -0.3973 -0.5913 -0.5531 0.4319 0
-0.2145 -0.2102 0.3454 -0.3982 -0.5904 -0.5510 0.4352 0
-0.2174 -0.2173 0.3462 -0.3979 -0.5891 -0.5567 0.4298 1
-0.2203 -0.2244 0.3470 -0.3976 -0.5879 -0.5624 0.4244 0
-0.2318 -0.2284 0.3500 -0.3910 -0.5926 -0.5635 0.4224 0
-0.2361 -0.2361 0.3516 -0.3975 -0.5859 -0.5688 0.4186 0
-0.2423 -0.2419 0.3530 -0.3928 -0.5893 -0.5722 0.4135 0
-0.2488 -0.2458 0.3544 -0.3980 -0.5858 -0.5756 0.4088 0
-0.2549 -0.2499 0.3580 -0.3931 -0.5878 -0.5759 0.4101 0
-0.2569 -0.2580 0.3584 -0.3965 -0.5826 -0.5853 0.4009 0
-0.2637 -0.2618 0.3632 -0.3946 -0.5825 -0.5871 0.4005 0
-0.2675 -0.2653 0.3617 -0.3910 -0.5869 -0.5860 0.3991 0
-0.2802 -0.2745 0.3635 -0.3966 -0.5791 -0.5958 0.3903 0
-0.2819 -0.2754 0.3655 -0.3943 -0.5784 -0.5971 0.3918 0
-0.2844 -0.2840 0.3649 -0.3850 -0.5842 -0.6009 0.3866 0
-0.2877 -0.2871 0.3665 -0.3852 -0.5848 -0.6044 0.3799 0
-0.2911 -0.2888 0.3698 -0.3818 -0.5872 -0.6066 0.3762 0
-0.2995 -0.2951 0.3724 -0.3799 -0.5854 -0.6129 0.3706 0
-0.2968 -0.2968 0.3714 -0.3875 -0.5781 -0.6167 0.3678 0
-0.3051 -0.3014 0.3737 -0.3829 -0.5794 -0.6233 0.3595 0
-0.3064 -0.3072 0.3733 -0.3745 -0.5832 -0.6252 0.3588 0
-0.3080 -0.3104 0.3741 -0.3737 -0.5808 -0.6327 0.3504 0
-0.3118 -0.3117 0.3761 -0.3800 -0.5762 -0.6339 0.3490 0
-0.3159 -0.3181 0.3749 -0.3758 -0.5755 -0.6404 0.3427 0
-0.3177 -0.3201 0.3790 -0.3735 -0.5782 -0.6401 0.3412 0
-0.3272 -0.3235 0.3797 -0.3675 -0.5800 -0.6436 0.3379 0
-0.3270 -0.3282 0.3782 -0.3650 -0.5791 -0.6469 0.3361 0
-0.3283 -0.3303 0.3790 -0.3648 -0.5772 -0.6528 0.3279 1
-0.3296 -0.3324 0.3798 -0.3646 -0.5753 -0.6588 0.3197 0
-0.3343 -0.3348 0.3810 -0.3604 -0.5780 -0.6618 0.3132 0
-0.3326 -0.3345 0.3833 -0.3611 -0.5775 -0.6613 0.3142 0
-0.3301 -0.3378 0.3832 -0.3663 -0.5681 -0.6706 0.3057 0
-0.3389 -0.3376 0.3866 -0.3600 -0.5691 -0.6742 0.3034 0
-0.3435 -0.3437 0.3846 -0.3529 -0.5688 -0.6771 0.3057 0
-0.3432 -0.3442 0.3850 -0.3502 -0.5702 -0.6790 0.3021 1
-0.3429 -0.3446 0.3853 -0.3475 -0.5716 -0.6808 0.2984 0
-0.3475 -0.3433 0.3837 -0.3499 -0.5627 -0.6924 0.2857 0
-0.3470 -0.3443 0.3841 -0.3491 -0.5629 -0.6943 0.2812 1
-0.3464 -0.3454 0.3844 -0.3483 -0.5632 -0.6963 0.2768 0
-0.3462 -0.3451 0.3856 -0.3430 -0.5591 -0.7013 0.2793 0
-0.3450 -0.3464 0.3849 -0.3411 -0.5583 -0.7059 0.2715 1
-0.3438 -0.3476 0.3843 -0.3392 -0.5574 -0.7105 0.2637 0
-0.3401 -0.3417 0.3845 -0.3367 -0.5598 -0.7113 0.2593 0
-0.3466 -0.3433 0.3834 -0.3301 -0.5575 -0.7170 0.2570 0
-0.3445 -0.3411 0.3838 -0.3297 -0.5579 -0.7188 0.2516 0
-0.3443 -0.3468 0.3818 -0.3336 -0.5478 -0.7269 0.2455 0
-0.3410 -0.3400 0.3847 -0.3201 -0.5581 -0.7250 0.2458 0
-0.3392 -0.3357 0.3816 -0.3215 -0.5515 -0.7302 0.2433 0
-0.3387 -0.3354 0.3825 -0.3160 -0.5519 -0.7359 0.2325 0
-0.3341 -0.3364 0.3807 -0.3160 -0.5494 -0.7398 0.2260 0
-0.3353 -0.3349 0.3798 -0.3162 -0.5463 -0.7425 0.2243 1
-0.3366 -0.3334 0.3790 -0.3163 -0.5431 -0.7452 0.2227 0
-0.3258 -0.3250 0.3790 -0.3071 -0.5430 -0.7491 0.2228 0
-0.3260 -0.3292 0.3786 -0.3047 -0.5387 -0.7560 0.2130 0
-0.3277 -0.3259 0.3770 -0.3017 -0.5402 -0.7562 0.2129 0
-0.3252 -0.3231 0.3754 -0.2968 -0.5315 -0.7652 0.2093 0
-0.3176 -0.3182 0.3759 -0.3007 -0.5339 -0.7624 0.2081 0
-0.3157 -0.3153 0.3743 -0.2965 -0.5343 -0.7655 0.2016 1
-0.3137 -0.3124 0.3727 -0.2923 -0.5347 -0.7686 0.1950 0
-0.3089 -0.3107 0.3742 -0.2884 -0.5287 -0.7749 0.1922 0
-0.3051 -0.3043 0.3718 -0.2895 -0.5260 -0.7774 0.1874 1
-0.3014 -0.2979 0.3694 -0.2905 -0.5234 -0.7800 0.1826 0
-0.2963 -0.2991 0.3688 -0.2878 -0.5242 -0.7799 0.1848 0
-0.2860 -0.2925 0.3677 -0.2844 -0.5239 -0.7823 0.1804 0
-0.2909 -0.2888 0.3664 -0.2837 -0.5225 -0.7838 0.1794 0
-0.2802 -0.2809 0.3639 -0.2671 -0.4908 -0.8072 0.1902 0
-0.2739 -0.2729 0.3601 -0.2462 -0.5015 -0.8132 0.1631 0
-0.2650 -0.2702 0.3595 -0.2487 -0.5024 -0.8126 0.1597 0
-0.2641 -0.2641 0.3600 -0.2442 -0.5009 -0.8149 0.1595 0
-0.2589 -0.2598 0.3594 -0.2421 -0.5017 -0.8168 0.1503 0
-0.2508 -0.2544 0.3555 -0.2468 -0.4925 -0.8205 0.1524 0
-0.2474 -0.2492 0.3516 -0.2487 -0.4954 -0.8194 0.1458 0
-0.2432 -0.2441 0.3521 -0.2399 -0.4924 -0.8236 0.1474 1
-0.2391 -0.2391 0.3525 -0.2311 -0.4893 -0.8276 0.1490 0
-0.2333 -0.2313 0.3522 -0.2325 -0.4924 -0.8277 0.1354 0
-0.2297 -0.2281 0.3481 -0.2253 -0.4846 -0.8327 0.1452 0
-0.2244 -0.2263 0.3486 -0.2199 -0.4818 -0.8365 0.1407 0
-0.2150 -0.2173 0.3441 -0.2302 -0.4807 -0.8356 0.1330 0
-0.2155 -0.2147 0.3421 -0.2181 -0.4786 -0.8413 0.1247 0
-0.2043 -0.2037 0.3408 -0.2161 -0.4780 -0.8416 0.1284 0
-0.1979 -0.1983 0.3394 -0.2118 -0.4761 -0.8449 0.1207 1
-0.1916 -0.1929 0.3379 -0.2074 -0.4742 -0.8482 0.1129 1
-0.1852 -0.1875 0.3365 -0.2030 -0.4723 -0.8513 0.1052 0
-0.1809 -0.1825 0.3305 -0.2044 -0.4633 -0.8550 0.1119 0
-0.1754 -0.1761 0.3337 -0.1995 -0.4650 -0.8561 0.1058 0
-0.1702 -0.1708 0.3306 -0.1950 -0.4616 -0.8594 0.1019 1
-0.1650 -0.1655 0.3275 -0.1905 -0.4582 -0.8627 0.0980 1
-0.1598 -0.1601 0.3244 -0.1860 -0.4548 -0.8659 0.0941 0
-0.1547 -0.1515 0.3253 -0.1846 -0.4548 -0.8669 0.0873 0
-0.1481 -0.1459 0.3230 -0.1813 -0.4503 -0.8699 0.0871 1
-0.1415 -0.1403 0.3206 -0.1780 -0.4458 -0.8729 0.0869 1
-0.1349 -0.1347 0.3182 -0.1747 -0.4413 -0.8759 0.0867 0
-0.1248 -0.1276 0.3183 -0.1645 -0.4411 -0.8785 0.0808 0
-0.1205 -0.1194 0.3179 -0.1547 -0.4357 -0.8830 0.0814 0
-0.1120 -0.1162 0.3139 -0.1535 -0.4336 -0.8853 0.0679 0
-0.1077 -0.1095 0.3124 -0.1543 -0.4342 -0.8844 0.0745 0
-0.1034 -0.1036 0.3107 -0.1443 -0.4304 -0.8884 0.0681 0
-0.0964 -0.0963 0.3076 -0.1537 -0.4236 -0.8899 0.0704 0
-0.0912 -0.0915 0.3043 -0.1427 -0.4208 -0.8929 0.0720 1
-0.0861 -0.0868 0.3010 -0.1317 -0.4180 -0.8958 0.0735 0
-0.0801 -0.0807 0.3022 -0.1322 -0.4154 -0.8983 0.0559 0
-0.0756 -0.0729 0.2997 -0.1293 -0.4103 -0.9008 0.0596 0
-0.0649 -0.0661 0.2989 -0.1246 -0.4076 -0.9027 0.0595 0
-0.0643 -0.0612 0.2976 -0.1188 -0.4040 -0.9052 0.0567 0
-0.0576 -0.0567 0.2933 -0.1143 -0.4008 -0.9075 0.0524 0
-0.0514 -0.0513 0.2923 -0.1141 -0.3969 -0.9096 0.0453 0
-0.0440 -0.0455 0.2878 -0.1165 -0.3969 -0.9094 0.0440 0
-0.0406 -0.0396 0.2887 -0.1045 -0.3933 -0.9128 0.0345 0
-0.0305 -0.0334 0.2864 -0.1023 -0.3932 -0.9128 0.0412 0
-0.0284 -0.0289 0.2841 -0.0984 -0.3882 -0.9153 0.0423 0
-0.0200 -0.0212 0.2830 -0.0957 -0.3957 -0.9124 0.0409 0
-0.0157 -0.0158 0.2820 -0.0995 -0.3564 -0.9283 0.0379 0
-0.0150 -0.0088 0.2790 -0.0761 -0.3619 -0.9278 0.0483 0
-0.0099 -0.0035 0.2778 -0.0880 -0.3590 -0.9286 0.0331 0
0.0003 0.0012 0.2768 -0.0854 -0.3533 -0.9310 0.0341 0
"""

# ----------------------------------------------------------------------------
# GLSL du module : l'image 160x80 envoyee aux panneaux
# ----------------------------------------------------------------------------
GLSL_CUBE = """// ANIMATION_CUBE -- un cube en fil de fer FIGE DANS L'ESPACE, que les dix
// lames revelent en tournant. Meme principe que le mode CHAMP 3D de
// MOTIFS_LED : chaque texel connait sa position reelle (x, y par l'angle de
// sa lame, z par la profondeur de son panneau) ; tous echantillonnent UN
// SEUL volume, et l'oeil recompose le cube en persistance retinienne.
//
// Sortie 160 x 80 = dix bandes de 160 x 8, panneau 0 EN BAS -- la meme
// convention que panel_mask_layout et MOTIFS_LED.
// Entree 0 : angles_top (11 x 1), l'angle de chaque panneau en DEGRES.
//
// Toutes les cotes sont en CENTIMETRES : lame de 160 cm (pas 1 cm),
// 8 rangees au pas de 1 cm, panneau s a z = (4.5 - s) * ecart.

uniform vec4 uCube;    // cx, cy, cz : centre du cube (cm) ; w : demi-cote h (cm)
uniform vec3 uR0;      // rotation du cube, ligne 1 : r0 r1 r2
uniform vec3 uR1;      // ligne 2 : r3 r4 r5
uniform vec3 uR2;      // ligne 3 : r6 r7 r8
uniform vec4 uRegle;   // x : demi-epaisseur des aretes (cm), y : ecart panneaux (cm),
                       // z : luminosite 0..1, w : miroir vertical (+1 / -1)
uniform vec4 uCouleur; // couleur des LED allumees

out vec4 fragColor;

// Distance d'un point (repere du cube, demi-cote ramene a 1) aux 12 aretes.
// Par symetrie, trois aretes suffisent : celles qui partent du sommet (1,1,1).
float distanceAretes(vec3 q) {
    vec3 a = abs(q) - 1.0;
    vec3 e = max(a, 0.0);
    return sqrt(min(min(e.x * e.x + a.y * a.y + a.z * a.z,
                        a.x * a.x + e.y * e.y + a.z * a.z),
                        a.x * a.x + a.y * a.y + e.z * e.z));
}

void main() {
    vec2 uv = vUV.st;

    // Quelle lame, a quel angle (en degres, comme partout dans la chaine LED)
    int panneau = int(clamp(uv.y * 10.0, 0.0, 9.0));
    float angle = texelFetch(sTD2DInputs[0], ivec2(panneau, 0), 0).r;
    float th = radians(angle);

    // Position reelle du texel dans le volume, en cm.
    // d le long de la lame (-80..+80), o en travers (8 rangees au pas de 1 cm),
    // z par la profondeur du panneau (panneau 0 devant, a +4.5 ecarts).
    float d = (uv.x - 0.5) * 160.0;
    float j = floor(fract(uv.y * 10.0) * 8.0);
    float o = j - 3.5;
    vec3 P = vec3(d * cos(th) - o * sin(th),
                  uRegle.w * (d * sin(th) + o * cos(th)),
                  (4.5 - float(panneau)) * uRegle.y);

    // Passage dans le repere du cube : q = transposee(R) x (P - centre) / h,
    // puis la regle de volumetric3D.js : allumee si distance x h <= epaisseur.
    vec3 D = P - uCube.xyz;
    vec3 q = (D.x * uR0 + D.y * uR1 + D.z * uR2) / uCube.w;
    float allumee = (distanceAretes(q) * uCube.w <= uRegle.x) ? 1.0 : 0.0;

    fragColor = TDOutputSwizzle(vec4(uCouleur.rgb * (allumee * uRegle.z), 1.0));
}
"""

# ----------------------------------------------------------------------------
# Callbacks du Script CHOP 'pose' : la pose du cube de l'image courante.
# C'est le SEUL python qui tourne a chaque image, et il ne touche qu'une
# ligne de table -- aucune boucle sur les LED, le volume est dans le GLSL.
# ----------------------------------------------------------------------------
CB_POSE = """# pose -- la pose du cube de l'image courante, en canaux CHOP.
# Canaux : cx cy cz h (cm), r0..r8 (matrice de rotation), interp, image, l.
# Portage exact de volumetric3D.js (animationScale / animationPose).
import math

def _echelle(w, ecart):
\t# L (cm par demi-largeur d'image) : le plus grand facteur tel que TOUS les
\t# cubes de la sequence, quelle que soit leur rotation, tiennent dans le
\t# volume (89.5 cm de rayon utile moins l'epaisseur, 4.5 ecarts de
\t# profondeur). Recalcule seulement quand w ou l'ecart changent.
\tcomp = parent()
\tcle = (round(w, 6), round(ecart, 6))
\tif comp.fetch('echelle_cle', None, search=False) == cle:
\t\treturn comp.fetch('echelle_valeur', 0.0, search=False)
\tt = op('poses')
\tzmax = 4.5 * ecart
\tdemi = 79.5
\tL = 1e30
\tfor i in range(t.numRows):
\t\tcx = float(t[i, 0]); cy = float(t[i, 1]); s = float(t[i, 2])
\t\treach = s * math.sqrt(3.0)
\t\tL = min(L, (zmax - w) / reach, (demi - w) / (math.hypot(cx, cy) + reach))
\tL = max(0.0, L)
\tcomp.store('echelle_cle', cle)
\tcomp.store('echelle_valeur', L)
\treturn L

def onCook(scriptOp):
\tscriptOp.clear()
\tcomp = parent()
\tt = op('poses')
\tn = max(1, t.numRows)
\tw = float(comp.par.Epaisseur)
\tecart = float(comp.par.Ecartcm)
\tL = _echelle(w, ecart)
\t# Deux horloges : 'rotation' avance avec les demi-tours reellement balayes
\t# par les lames (une tranche = une seule pose, a n'importe quelle vitesse) ;
\t# 'temps' avance a Images par seconde, comme la simulation p5.
\tif str(comp.par.Modehorloge) == 'rotation':
\t\tavance = float(op('rotation_compteur')['demitours']) * float(comp.par.Imagespardemitour)
\telse:
\t\tavance = float(op('compteur')['v'])
\timage = (int(comp.par.Imageno) + int(avance)) % n
\tcx, cy, s, qx, qy, qz, qw, interp = (float(t[image, c]) for c in range(8))
\tif comp.par.Cubefixe:
\t\t# Cube fixe : centre, non tourne ; ses faces avant et arriere tombent
\t\t# sur le premier et le dernier panneau.
\t\th = min(79.5 / math.sqrt(2.0) * 0.95, 4.5 * ecart)
\t\tcentre = (0.0, 0.0, 0.0)
\t\tR = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
\t\tinterp = 0.0
\telse:
\t\th = L * s
\t\tcentre = (L * cx, L * cy, 0.0)
\t\tx, y, z, w_ = qx, qy, qz, qw
\t\tR = [1 - 2 * (y * y + z * z), 2 * (x * y - z * w_), 2 * (x * z + y * w_),
\t\t     2 * (x * y + z * w_), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w_),
\t\t     2 * (x * z - y * w_), 2 * (y * z + x * w_), 1 - 2 * (x * x + y * y)]
\t\t# La camera des images regardait vers le fond, le volume a z vers le
\t\t# spectateur : on retourne l'axe z (les termes qui croisent z changent
\t\t# de signe), comme dans volumetric3D.js.
\t\tR[2] = -R[2]; R[5] = -R[5]; R[6] = -R[6]; R[7] = -R[7]
\tvaleurs = [('cx', centre[0]), ('cy', centre[1]), ('cz', centre[2]), ('h', h)]
\tvaleurs += [('r%d' % i, R[i]) for i in range(9)]
\tvaleurs += [('interp', float(interp)), ('image', float(image)), ('l', L)]
\tfor nom, v in valeurs:
\t\tscriptOp.appendChan(nom)[0] = v
\treturn
"""

CB_REMETTRE = """# Remettre -- ramene l'animation a l'image 0 (les deux horloges).
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

CB_ROTATION = """# rotation_compteur -- compte les demi-tours REELLEMENT balayes par les lames.
# Lit l'angle de la lame 0 dans angle_lame0 (en degres, un echantillon par
# lame, la MEME source que les motifs : consigne ou positions Teensy selon
# MOTIFS_LED.Anglesreels), le
# deroule pas a pas (saut ramene dans -180..+180) et accumule en demi-tours,
# en valeur absolue : la vitesse peut etre lente, rapide, variable ou
# inversee, l'animation suit toujours vers l'avant.
# C'est l'horloge du mode 'rotation' : une image par demi-tour (reglable)
# DE LA LAME 0. Les lames au moins aussi rapides qu'elle ont la meme
# garantie ; une lame plus lente (ouverture d'eventail avec Ouvrirenretard,
# derive negative, moteur reel plus lent) peut voir la pose changer plus
# d'une fois par passage. A l'arret, l'animation s'arrete aussi -- rien
# n'est balaye, rien ne doit changer.
def onCook(scriptOp):
\tscriptOp.clear()
\tcomp = parent()
\t# angles_choix est UN canal multi-echantillons (un par lame) : on lit
\t# explicitement l'echantillon 0 (lame 0). float(canal) sans index lirait a
\t# l'index du temps courant -- c'est le piege que text1 contourne deja en
\t# passant par shuffle1 (eclatement des echantillons en canaux).
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

CB_BOUTON = """# Le clic sur le bouton bascule ANIMATION_CUBE.Actif.
def onOffToOn(panelValue):
\tp = op('/project1/scale/ANIMATION_CUBE').par.Actif
\tp.val = 0 if p else 1
\treturn
"""

LISEZ_MOI = """ANIMATION_CUBE -- LE CUBE DE cube_animatio SUR LES PANNEAUX

CE QUE C'EST
  Les 300 poses d'un cube en fil de fer, retrouvees dans les images du
  dossier cube_animatio (depot animation-cube-a-faire-dans-TD), rejouees
  en boucle : une image par demi-tour balaye par defaut (voir L'HORLOGE),
  ou 30 images/s en mode temps. Le cube est FIGE DANS L'ESPACE a chaque
  image : les dix lames le revelent en tournant, comme le mode CHAMP 3D
  de MOTIFS_LED, et l'oeil le recompose en persistance retinienne.

LE RESEAU
  poses       Table DAT, 300 lignes : cx, cy, s, qx..qw, interpolee
  vitesse     Images/s x Lecture -> compteur (Speed) : pas de saut
  angle_lame0 / rotation_compteur
              l'angle de la lame 0 (meme source que les motifs), deroule
              et cumule en demi-tours : l'horloge du mode 'rotation'
  pose        Script CHOP : centre (cm), demi-cote h (cm), rotation
              r0..r8, image courante, interp, echelle L
  angles      Select TOP sur MOTIFS_LED/angles_top : l'angle REEL de
              chaque lame, en degres -- consigne ou Teensy selon
              MOTIFS_LED.Anglesreels, comme tous les autres motifs
  cube        GLSL TOP 160x80 : allume un texel si sa position reelle
              touche une arete du cube (distance aux 12 aretes <= w)
  out_led     part en 4e entree du switch panel_mask_output

LA REGLE D'ALLUMAGE (volumetric3D.js)
  q = transposee(R) x (P - centre) / h
  allumee si distanceAretes(q) x h <= Epaisseur
  L'echelle L (environ 61.23 cm par demi-largeur d'image) est la plus
  grande qui fasse tenir TOUS les cubes de la sequence dans le volume ;
  elle se recalcule quand Epaisseur ou Ecartcm changent.

L'HORLOGE SUIT LA ROTATION (mode par defaut)
  Une lame ne peint sa tranche qu'en passant dessus : il lui faut un
  demi-tour. Avancer l'animation au temps (30 img/s) melange donc
  plusieurs poses par secteurs des que la rotation est lente. En mode
  'rotation', l'image n'avance que de Imagespardemitour (1 par defaut)
  a chaque demi-tour REELLEMENT balaye, compte sur les memes angles que
  les motifs, sur LA LAME 0. Pour elle et pour toute lame au moins
  aussi rapide (le projet sauvegarde : derives Rzdrift/Rzaudiospread
  positives, lames 1..9 plus rapides), chaque point n'est peint qu'avec
  UNE pose par passage et une tranche montre au plus DEUX poses
  consecutives (la couture tourne avec les lames) -- au lieu d'un
  melange de 7 a 8 poses a 30 img/s et 2 tours/s. Une lame PLUS LENTE
  que la lame 0 (ouverture d'eventail avec Ouvrirenretard coche, derive
  negative, moteur reel plus lent) peut en montrer trois ou plus le
  temps de la transition ; garantie stricte partout avec
  PHASES_PANNEAUX.Figerecart ou des vitesses egales. La vitesse peut
  etre lente, rapide, variable ou inversee. A 2 tours/s la boucle des
  300 images dure 75 s ; a l'arret des moteurs, l'animation s'arrete.
  Au-dessus de 1 image par demi-tour le melange revient ; en dessous
  (0.5 = une image par tour complet) on est encore plus sur.
  Le mode 'temps' (Images par seconde) reste la pour previsualiser a la
  cadence d'origine. Basculer d'horloge en cours de lecture peut faire
  sauter l'image (les deux compteurs vivent chacun leur vie) ; Remettre
  repart de l'image 0.

QUI PREND LA MAIN
  Actif coche -> le switch panel_mask_output passe sur l'entree 3 : le
  cube part vers les panneaux (ports 9101-9110), le simulateur et le
  rendu 3D (bande_* <- rubans_choix <- panel_mask_output) suivent tout
  seuls. Decoche -> l'expression retombe sur le comportement d'origine,
  au bit pres. MOTIFS_LED et les variations gardent leurs reglages.

REGLAGES (page Cube)
  Actif          le bouton de SORTIE_SPECTACLE fait pareil
  Lecture        pause / lecture de l'animation (sans saut)
  Modehorloge    'rotation' (defaut) : suit les demi-tours balayes ;
                 'temps' : avance a Images par seconde
  Imagespardemitour  images par demi-tour en mode rotation (1 par defaut)
  Imagespersec   cadence du mode temps (30 par defaut)
  Imageno        choix de l'image a l'arret (0..299)
  Remettre       revient a l'image 0
  Cubefixe       un cube immobile centre, pour verifier la geometrie
  Epaisseur      demi-epaisseur des aretes, en cm (4 par defaut)
  Ecartcm        ecart reel entre deux panneaux (10 cm par defaut)
  Couleur        rouge par defaut
  Luminosite     gain simple 0..1
  Miroiry        retourne le haut et le bas si le cube tourne a l'envers
                 par rapport a la video d'origine (calibration)

A SAVOIR
  Le rendu 3D ne montre ces bandes que si TEXTURES_ROTATION.Mode est sur
  Coupe (voir COMMENT_31). La vue 'led' de SORTIE_SPECTACLE pointe
  desormais sur panel_mask_output : elle montre ce qui part VRAIMENT,
  quel que soit le maitre. Pour tout retirer : desinstaller() dans
  INSTALLER_ANIMATION_CUBE (la sauvegarde de l'expression d'origine est
  dans le DAT 'sauvegarde').
"""

TEXTE_COMMENT = """ANIMATION_CUBE -- UN VOLUME JOUE, PAS UN MOTIF REGLE

CE QUI MANQUAIT
  Tous les motifs de la chaine LED sont des REGLAGES : anneaux, tunnels,
  respirations. Aucun ne rejoue un CONTENU prepare image par image.
  L'animation du depot cube_animatio (300 poses d'un cube en fil de fer
  retrouvees dans les images d'origine) est le premier contenu de ce
  genre : un objet 3D qui tourne, se deplace et grossit pendant 10 s.

COMMENT C'EST BRANCHE
  ANIMATION_CUBE fabrique l'image 160x80 (dix bandes de 160x8, panneau 0
  en bas) exactement comme MOTIFS_LED, en lisant les MEMES angles
  (MOTIFS_LED/angles_top). Il est la 4e entree du switch
  panel_mask_output :
    Actif coche   -> index 3, le cube part vers les panneaux
    Actif decoche -> l'expression d'origine reprend, au bit pres
  Panneaux reels, simulateur et rendu 3D suivent tous panel_mask_output,
  donc les trois montrent le cube sans autre branchement.

LE BOUTON
  SORTIE_SPECTACLE / PANNEAU_COMMANDES / cube_anime : LANCER LE CUBE /
  CUBE EN MARCHE, plus la ligne d'etat (image courante, interpolee ou
  non). Style et couleurs pris sur parent.commandes, comme le catalogue.

LA GEOMETRIE, EN CLAIR
  Texel (lame s, colonne k, rangee j), lame a l'angle th (degres) :
    d = (k - 79.5) cm   o = (j - 3.5) cm   z = (4.5 - s) x 10 cm
    P = (d cos th - o sin th, d sin th + o cos th, z)
  Allume si la distance de P aux 12 aretes du cube courant <= 4 cm.
  C'est la regle de volumetric3D.js, verifiee par 20 valeurs de controle
  (positions, echelle L = 61.23, comptes de LED par image) avant portage.

L'HORLOGE SUIT LA ROTATION
  L'animation n'avance pas au temps mais aux demi-tours REELLEMENT
  balayes : l'angle de la lame 0 (meme source que les motifs) est
  deroule et cumule par rotation_compteur, et l'image avance de
  Imagespardemitour (1 par defaut) par demi-tour DE LA LAME 0. Pour
  elle et toute lame au moins aussi rapide : une pose par passage, au
  plus deux poses par tranche, au lieu d'un melange de 7 a 8 -- vitesse
  lente, rapide, variable ou inversee. Une lame plus lente que la
  lame 0 (ouverture d'eventail avec Ouvrirenretard, derive negative,
  moteur reel plus lent) peut en montrer davantage le temps de la
  transition ; Figerecart ou des vitesses egales redonnent la garantie
  partout. Suivre la lame la moins balayee aurait l'inconvenient
  qu'une lame arretee fige tout : la lame 0 est un choix assume.
  A l'arret l'animation s'arrete, puisque rien n'est balaye.
  Le mode 'temps' (30 images/s, comme la simulation p5) reste
  disponible pour previsualiser.

MESURE A L'INSTALLATION
  Voir le textport : echelle L, demi-cote de l'image 0 (16.905 cm
  attendus), nombre de texels allumes a l'angle courant des lames.

POUR TOUT RETIRER
  desinstaller() dans touchdesigner/INSTALLER_ANIMATION_CUBE.py du depot. La
  sauvegarde des expressions d'origine vit dans ANIMATION_CUBE/sauvegarde.
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
    motifs = scale.op('MOTIFS_LED')
    angles_src = scale.op('MOTIFS_LED/angles_top')
    commandes = scale.op('SORTIE_SPECTACLE/PANNEAU_COMMANDES')
    vue_led = scale.op('SORTIE_SPECTACLE/haut/droite/led')
    for o, nom in ((sw, 'panel_mask_output'), (motifs, 'MOTIFS_LED'),
                   (angles_src, 'MOTIFS_LED/angles_top'),
                   (commandes, 'SORTIE_SPECTACLE/PANNEAU_COMMANDES')):
        assert o, "Introuvable : " + nom + " -- ce script vise le projet SAISON_9."

    # ---- Reinstallation : retrouver l'expression d'origine avant de raser ----
    expr_index = sw.par.index.expr or ''
    expr_vue = (vue_led.par.top.expr or '') if vue_led else ''
    ancien = scale.op(NOM_MODULE)
    if ancien:
        sauve = ancien.op('sauvegarde')
        if sauve:
            try:
                d = json.loads(sauve.text)
                expr_index = d.get('index', expr_index)
                expr_vue = d.get('vue_led', expr_vue)
            except Exception:
                pass
    if NOM_MODULE in expr_index:
        expr_index = EXPR_INDEX_ORIGINE
    if 'panel_mask_output' in expr_vue:
        expr_vue = EXPR_VUE_LED_ORIGINE
    if not expr_index.strip():
        # Index fige en constante a la main : on conserve cette valeur telle quelle
        expr_index = str(int(sw.par.index.eval()))

    # Remettre les expressions d'origine AVANT de raser l'ancien module : si la
    # suite echoue, la chaine LED reste sur son comportement d'origine au lieu
    # de referencer un module disparu.
    if NOM_MODULE in (sw.par.index.expr or ''):
        sw.par.index.expr = expr_index
    if vue_led and 'panel_mask_output' in (vue_led.par.top.expr or ''):
        vue_led.par.top.expr = expr_vue
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(commandes.path + '/' + NOM_SECTION)
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)

    # ------------------------------------------------------------------ module
    comp = scale.create(baseCOMP, NOM_MODULE)
    comp.nodeX, comp.nodeY = 2100, -10450
    comp.nodeWidth, comp.nodeHeight = 220, 140
    comp.color = (0.85, 0.25, 0.2)
    comp.comment = ("Le cube de cube_animatio, fige dans l'espace et revele "
                    "par les lames. 4e entree de panel_mask_output.")

    page = comp.appendCustomPage('Cube')
    p = page.appendToggle('Actif', label='CUBE SUR LES PANNEAUX (prend la main)')[0]
    p.val = False
    p = page.appendToggle('Lecture', label="Lire l'animation")[0]
    p.default = True; p.val = True
    p = page.appendMenu('Modehorloge', label="Horloge de l'animation")[0]
    p.menuNames = ['rotation', 'temps']
    p.menuLabels = ['Suit la rotation (une image par demi-tour de lame)',
                    'Au temps (Images par seconde)']
    p.default = 'rotation'; p.val = 'rotation'
    p = page.appendFloat('Imagespardemitour', label='Images par demi-tour (mode rotation)')[0]
    p.default = 1; p.val = 1; p.normMin = 0.1; p.normMax = 4
    p.clampMin = True; p.min = 0.01
    p = page.appendFloat('Imagespersec', label='Images par seconde (mode temps)')[0]
    p.default = 30; p.val = 30; p.normMin = 1; p.normMax = 60; p.clampMin = True; p.min = 1
    p = page.appendInt('Imageno', label="Image no (a l'arret)")[0]
    p.default = 0; p.val = 0; p.normMin = 0; p.normMax = 299
    page.appendPulse('Remettre', label="Revenir a l'image 0")
    p = page.appendToggle('Cubefixe', label='Cube fixe (verification)')[0]
    p.val = False
    p = page.appendFloat('Epaisseur', label='Demi-epaisseur aretes (cm)')[0]
    p.default = 4; p.val = 4; p.normMin = 1; p.normMax = 10; p.clampMin = True; p.min = 1
    p = page.appendFloat('Ecartcm', label='Ecart entre panneaux (cm)')[0]
    p.default = 10; p.val = 10; p.normMin = 1; p.normMax = 30; p.clampMin = True; p.min = 1
    pg = page.appendRGB('Couleur', label='Couleur du cube')
    pg[0].default = 1; pg[0].val = 1
    pg[1].default = 0; pg[1].val = 0
    pg[2].default = 0; pg[2].val = 0
    p = page.appendFloat('Luminosite', label='Luminosite')[0]
    p.default = 1; p.val = 1; p.normMin = 0; p.normMax = 1
    p.clampMin = True; p.clampMax = True; p.min = 0; p.max = 1
    p = page.appendToggle('Miroiry', label='Miroir vertical (calibration)')[0]
    p.val = False

    # ---- poses ----
    poses = comp.create(tableDAT, 'poses')
    poses.nodeX, poses.nodeY = -700, -250
    poses.clear()
    for ligne in POSES_TEXTE.strip().splitlines():
        poses.appendRow(ligne.split())
    assert poses.numRows == 300, 'La table des poses devrait faire 300 lignes.'

    # ---- horloge : pas de saut quand on change la vitesse ou qu'on met en pause
    vitesse = comp.create(constantCHOP, 'vitesse')
    vitesse.nodeX, vitesse.nodeY = -700, 0
    # Dans cette version le Constant CHOP range ses constantes en sequence
    # const0name/const0value (verite terrain : constant9.parm du projet) ;
    # name0/value0 est l'alias herite. Pas de 'or' entre deux getattr : la
    # truthiness d'un Par est sa VALEUR, et une valeur vide ecarterait le
    # parametre canonique au profit de l'alias.
    p_nom = getattr(vitesse.par, 'const0name', None)
    if p_nom is None:
        p_nom = getattr(vitesse.par, 'name0', None)
    p_val = getattr(vitesse.par, 'const0value', None)
    if p_val is None:
        p_val = getattr(vitesse.par, 'value0', None)
    assert p_nom is not None and p_val is not None, \
        'Constant CHOP : parametres de la constante 0 introuvables (version TD inattendue).'
    p_nom.val = 'v'
    p_val.expr = 'parent().par.Imagespersec * parent().par.Lecture'
    compteur = comp.create(speedCHOP, 'compteur')
    compteur.nodeX, compteur.nodeY = -500, 0
    compteur.inputConnectors[0].connect(vitesse)

    remise = comp.create(parameterexecuteDAT, 'remise')
    remise.nodeX, remise.nodeY = -500, -120

    def poser(o, candidats, valeur):
        # Les noms de parametres changent entre versions : on verifie au lieu
        # de deviner, et on previent si rien ne colle.
        for nom in candidats:
            p = getattr(o.par, nom, None)
            if p is not None:
                p.val = valeur
                return True
        print('  (a regler a la main sur %s : aucun parametre parmi %s)'
              % (o.path, candidats))
        return False

    poser(remise, ('op', 'ops'), '..')
    poser(remise, ('pars', 'parm', 'parms'), 'Remettre')
    poser(remise, ('onpulse', 'pulse'), True)
    _texte(remise, CB_REMETTRE)

    # ---- horloge calee sur la rotation : demi-tours reellement balayes ----
    # L'angle de la lame 0, meme source que les motifs (consigne ou Teensy
    # selon MOTIFS_LED.Anglesreels), deroule et cumule par rotation_compteur.
    angle_lame0 = comp.create(selectCHOP, 'angle_lame0')
    angle_lame0.nodeX, angle_lame0.nodeY = -950, -130
    p = getattr(angle_lame0.par, 'chops', None)
    if p is None:
        p = getattr(angle_lame0.par, 'chop', None)
    assert p is not None, 'Select CHOP : parametre chops introuvable (version TD inattendue).'
    p.val = '../MOTIFS_LED/angles_choix'
    rot_cb = comp.create(textDAT, 'rotation_callbacks')
    rot_cb.nodeX, rot_cb.nodeY = -950, -260
    _texte(rot_cb, CB_ROTATION)
    rotation = comp.create(scriptCHOP, 'rotation_compteur')
    rotation.nodeX, rotation.nodeY = -770, -130
    rotation.par.callbacks = 'rotation_callbacks'

    # ---- pose du cube ----
    cb = comp.create(textDAT, 'pose_callbacks')
    cb.nodeX, cb.nodeY = -300, -120
    _texte(cb, CB_POSE)
    pose = comp.create(scriptCHOP, 'pose')
    pose.nodeX, pose.nodeY = -300, 0
    pose.par.callbacks = 'pose_callbacks'

    # ---- angles des lames : la meme source que tous les motifs ----
    angles = comp.create(selectTOP, 'angles')
    angles.nodeX, angles.nodeY = -300, 150
    angles.par.top = '../MOTIFS_LED/angles_top'

    # ---- le GLSL ----
    code = comp.create(textDAT, 'cube_pixel')
    code.nodeX, code.nodeY = -100, -120
    _texte(code, GLSL_CUBE)
    cube = comp.create(glslTOP, 'cube')
    cube.nodeX, cube.nodeY = -100, 80
    cube.par.pixeldat = 'cube_pixel'
    cube.par.outputresolution = 'custom'
    cube.par.resolutionw = 160
    cube.par.resolutionh = 80
    try:
        cube.par.format = 'rgba8fixed'
    except Exception:
        pass
    cube.inputConnectors[0].connect(angles)

    unis = [
        ('uCube', ("op('pose')['cx']", "op('pose')['cy']",
                   "op('pose')['cz']", "op('pose')['h']")),
        ('uR0', ("op('pose')['r0']", "op('pose')['r1']", "op('pose')['r2']", None)),
        ('uR1', ("op('pose')['r3']", "op('pose')['r4']", "op('pose')['r5']", None)),
        ('uR2', ("op('pose')['r6']", "op('pose')['r7']", "op('pose')['r8']", None)),
        ('uRegle', ('parent().par.Epaisseur', 'parent().par.Ecartcm',
                    'parent().par.Luminosite',
                    '-1 if parent().par.Miroiry else 1')),
        ('uCouleur', ('parent().par.Couleurr', 'parent().par.Couleurg',
                      'parent().par.Couleurb', None)),
    ]
    # Dans cette version les uniformes vectoriels du GLSL TOP sont des blocs
    # sequentiels vec0name/vec0valuex..w (verite terrain : MOTIFS_LED/
    # motif_led.parm) et la sequence doit etre etendue au prealable ;
    # uniname0/value0x est le repli pour d'anciennes versions.
    try:
        if cube.seq.vec.numBlocks < len(unis):
            cube.seq.vec.numBlocks = len(unis)
    except Exception:
        pass
    for i, (nom, (ex, ey, ez, ew)) in enumerate(unis):
        p_nom = getattr(cube.par, 'vec%dname' % i, None)
        if p_nom is None:
            p_nom = getattr(cube.par, 'uniname%d' % i, None)
        assert p_nom is not None, \
            'GLSL TOP : parametre de nom d uniforme introuvable (bloc %d).' % i
        p_nom.val = nom
        prefixe = ('vec%dvalue' % i
                   if getattr(cube.par, 'vec%dvaluex' % i, None) is not None
                   else 'value%d' % i)
        getattr(cube.par, prefixe + 'x').expr = ex
        getattr(cube.par, prefixe + 'y').expr = ey
        getattr(cube.par, prefixe + 'z').expr = ez
        if ew is not None:
            getattr(cube.par, prefixe + 'w').expr = ew

    sortie = comp.create(outTOP, 'out_led')
    sortie.nodeX, sortie.nodeY = 150, 80
    sortie.inputConnectors[0].connect(cube)
    sortie.viewer = True

    lisez = comp.create(textDAT, 'LISEZ_MOI')
    lisez.nodeX, lisez.nodeY = -700, 150
    _texte(lisez, LISEZ_MOI)
    lisez.viewer = True

    sauvegarde = comp.create(textDAT, 'sauvegarde')
    sauvegarde.nodeX, sauvegarde.nodeY = -700, -400
    _texte(sauvegarde, json.dumps({'index': expr_index, 'vue_led': expr_vue},
                                  indent=1))

    # ------------------------------------------------- branchement du switch
    # On branche le connecteur de SORTIE DU COMP (cree par l'Out TOP), comme
    # MOTIFS_LED/out_led l'est pour l'entree 2.
    def entrees_module():
        return [i for i, e in enumerate(sw.inputs)
                if e and ('/' + NOM_MODULE) in e.path]
    if not entrees_module():
        comp.outputConnectors[0].connect(sw)
    rang = entrees_module()
    if rang != [3]:
        # On retire le branchement avant de s'arreter : l'expression d'origine
        # est en place, la chaine LED reste intacte.
        try:
            comp.outputConnectors[0].disconnect()
        except Exception:
            pass
        raise AssertionError(
            'out_led devait etre la 4e entree du switch, trouve : %s -- '
            'branchement retire, chaine LED inchangee.' % rang)
    sw.par.index.expr = ("3 if op('ANIMATION_CUBE').par.Actif else (%s)" % expr_index)

    # La vue 'led' du spectacle montre desormais ce qui PART VRAIMENT,
    # quel que soit le maitre (motifs, variations ou cube).
    if vue_led:
        vue_led.par.top.expr = "parent.sortie.parent().op('panel_mask_output')"

    # ------------------------------------------------- la section avec bouton
    section = commandes.create(containerCOMP, NOM_SECTION)
    section.nodeX, section.nodeY = 400, 0
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
    titre.par.text = 'ANIMATION CUBE'
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

    bouton = section.create(containerCOMP, 'bouton')
    bouton.par.h.expr = 'parent.commandes.par.Hauteurbouton * 1.8'
    bouton.par.hmode = 'fill'
    bouton.par.alignorder = 1
    chemin_actif = "op('/project1/scale/ANIMATION_CUBE').par.Actif"
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
    etiquette.par.text.expr = ("'CUBE EN MARCHE' if %s else 'LANCER LE CUBE'"
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
    _texte(clic, CB_BOUTON)

    etat = section.create(textCOMP, 'etat')
    etat.par.text.expr = (
        "'image %d/300%s' % (int(op('/project1/scale/ANIMATION_CUBE/pose')['image']), "
        "' (interpolee)' if op('/project1/scale/ANIMATION_CUBE/pose')['interp'] else '')")
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
    etat.par.alignorder = 2

    # ------------------------------------------------- documentation maison
    comment = scale.create(textDAT, NOM_COMMENT)
    comment.nodeX, comment.nodeY = 2100, -10650
    comment.viewer = True
    _texte(comment, TEXTE_COMMENT)

    # ------------------------------------------------------------- verification
    # L'installation est FINIE ici : la MESURE ne doit jamais la faire echouer.
    print('')
    print('ANIMATION_CUBE installe. MESURE :')
    try:
        sortie.cook(force=True)
        pose.cook(force=True)
        L = float(pose['l'])
        h0 = float(pose['h'])
        img = int(pose['image'])
        ok_l = abs(L - 61.2296) < 0.01
        print('  echelle L = %.4f cm/demi-largeur (attendu 61.2296) : %s'
              % (L, 'OK' if ok_l else 'ECART'))
        if img == 0 and not comp.par.Cubefixe:
            print('  demi-cote image 0 = %.4f cm (attendu 16.9055) : %s'
                  % (h0, 'OK' if abs(h0 - 16.9055) < 0.01 else 'ECART'))
        arr = sortie.numpyArray()
        if arr is not None:
            allumees = int((arr[..., :3].max(axis=-1) > 0.5).sum())
            print("  texels allumes a l'angle courant des lames : %d sur 12800" % allumees)
        else:
            print("  (image pas encore disponible pour le compte de texels)")
    except Exception as e:
        print('  MESURE incomplete (%s) -- l installation elle-meme est terminee.' % e)
    err = comp.errors(recurse=True)
    print('  erreurs dans le module : %s' % (err if err else 'aucune'))
    print('  switch : out_led en entree 3, expression posee ; Actif est DECOCHE,')
    print("  rien ne change tant qu'on n'appuie pas sur le bouton.")
    print('  Bouton : SORTIE_SPECTACLE > panneau de commandes > ANIMATION CUBE.')
    print('  Penser a : Fichier > Enregistrer sous (ne pas ecraser le .toe).')
    return comp


def desinstaller():
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
            expr_index = d.get('index', expr_index)
            expr_vue = d.get('vue_led', expr_vue)
        except Exception:
            pass
    if sw:
        sw.par.index.expr = expr_index
    if vue_led:
        vue_led.par.top.expr = expr_vue
    _detruire(CHEMIN_SCALE + '/SORTIE_SPECTACLE/PANNEAU_COMMANDES/' + NOM_SECTION)
    _detruire(CHEMIN_SCALE + '/' + NOM_MODULE)
    _detruire(CHEMIN_SCALE + '/' + NOM_COMMENT)
    print('ANIMATION_CUBE retire ; expressions d\'origine remises.')
    print('Penser a : Fichier > Enregistrer sous.')


installer()
