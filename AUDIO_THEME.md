# Direction audio — Sunden

Hack & slash en 3D pixel art : un chevalier à l'épée et au bouclier défend des ruines de pierre
au milieu d'une forêt de sapins, éclairées par des torches, contre des vagues de slimes et de squelettes.
Ton : aventure de conte, nerveuse mais lumineuse — jamais horrifique.

## Signature timbrale (tous les sons en font partie)

Instruments acoustiques uniquement, comme une petite troupe folk-médiévale renforcée de percussions d'orchestre :

| Rôle | Instruments |
|---|---|
| Fer, lame, impacts du héros | enclume accordée, crotales, cymbale suspendue frottée à l'archet, timbales |
| Bois, mouvement, esquive | bodhrán et tambours sur cadre balayés aux balais, wood-block, shaker en bois |
| Slime (souple, comique) | marimba grave en palissandre, contrebasse pizzicato, glissandos de violoncelle |
| Squelette (sec, osseux) | xylophone sec, « bones » (percussion folk en os), col legno des cordes |
| Musique | vielle à roue, flûte en bois, luth, cordes spiccato, cors, bodhrán, timbales |

## Tonalité

**Ré dorien (D Dorian).** Les earcons utilisent les notes de la gamme (ré, mi, fa, sol, la, si, do) :
- succès / coups portés : quinte ré–la, notes aiguës (D5, A5) ;
- dégâts reçus / mort : triton ou seconde mineure dans le grave (D2–G#2, E2–F2) ;
- télégraphes ennemis : mouvements montants qui « annoncent » (glissando vers la).

## Espace

Clairière de forêt entourée de ruines : **réverbération naturelle de pierre, courte et ouverte**
(« short open-air stone ruin reverb »). Les SFX restent secs et proches ; la musique a un peu plus d'air.

## Hiérarchie des niveaux

| Famille | Peak cible | Bus Godot |
|---|---|---|
| Coups portés, mort ennemie | -3 dB | SFX (0 dB) |
| Swings, esquive, télégraphes | -6 dB | SFX |
| Pas | -18 dB | SFX |
| Stingers (vague, mort du héros) | -2 dB | SFX |
| Musique de combat | -10 dB | Music (-9 dB) |
| Nappe d'ambiance | -12 dB | Ambience (-12 dB) |

Master : limiteur à -1 dB.

## Génération

Tous les sons sont générés avec MiniMax Music 3 (ComfyUI, workflow `sound_and_music`) par
`tools/generate_audio.py`, qui contient la liste complète des prompts. Aucune synthèse par le code.
