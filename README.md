# Sunden — prototype hack & slash en 3D pixel art

Godot 4.7 (Forward+). Le jeu est rendu en 320×180 puis agrandi d'un facteur entier, sans lissage.

## Lancer

Ouvrir le dossier dans Godot 4.7, puis F5. Ou en ligne de commande :

```bash
D:\dev\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64.exe --path E:\dev\sunden
```

| Action    | Clavier            | Manette |
|-----------|--------------------|---------|
| Bouger    | ZQSD / WASD / flèches | stick gauche |
| Attaquer (combo ×3) | J / clic gauche | X |
| Esquiver  | Espace / K / clic droit | A |
| Réapparaître au brasero (après une chute) | R | Start |

## Niveau 1 : « La Crypte Gluante »

Forêt de Sunden (tutoriel) → Crypte d'Émeraude (4 salles en boucle, alcôve secrète) → le Roi Gluant.
Intentions, plan, rythme et chiffres : [LEVEL_DESIGN.md](LEVEL_DESIGN.md).

- `tools/compose_level1.py` dessine la carte en ASCII (1 case = 1 m), vérifie que tout est atteignable
  et écrit `levels/niveau1.json` (carte + herses, rencontres, boss, zones, indices, coffres).
  Le JSON se modifie aussi à la main ; la légende des caractères est en tête du script.
- `blender/build_props.py` exporte les décors et objets (`assets/models/props.glb`).
- `scripts/level/level_builder.gd` construit le niveau depuis le JSON : sols, murs (bas côté caméra),
  arbres et herbe en MultiMesh, objets, ennemis, chemin A* pour les monstres, zones et indices.
- `scripts/level/` : `encounter.gd` (salle fermée à vagues), `gate.gd` (herse), `spike_trap.gd`,
  `breakable.gd` (jarres, caisses), `heart_pickup.gd`, `brazier.gd` (point de retour),
  `chest.gd`, `boss_slime.gd` (3 phases) et `shockwave.gd`.

```bash
python tools/compose_level1.py
```

## Organisation

- `blender/generate_example.py` : construit la scène Blender et la rend en pixel art.
- `blender/export_godot.py` : exporte le niveau en `.glb` dans `assets/models/`.
- `blender/rig_hero.py` : héros avec squelette et animations
  (`repos`, `course`, `attaque_1/2/3`, `esquive`, `touche`, `mort`) → `assets/models/hero.glb`.
- `blender/rig_enemies.py` : slime (`repos`, `saut`, `preparation`, `attaque`, `touche`) et squelette
  (`repos`, `marche`, `preparation`, `attaque`, `touche`, `apparition`, `mort`) → `slime.glb`, `skeleton.glb`.
- `blender/rig_utils.py`, `blender/gltf_utils.py` : outils communs (rig en blocs, poses, planches, export).
- Chaque script de rig enregistre un `.blend` retouchable (`heros_anime`, `slime_anime`, `squelette_anime`)
  et une planche de contrôle dans `renders/` (une ligne par animation).
- `shaders/toon.gdshader` : ombrage en paliers (mêmes teintes que dans Blender).
- `shaders/outline.gdshader` : contour d'un pixel (profondeur + normales).
- `scripts/pixel_camera.gd` : caméra orthographique alignée sur la grille de pixels, décalage sous-pixel, tremblements.
- `scripts/main.gd` : agrandissement entier, déroulement du niveau (brasero, réapparition, musique), contrôles.
- `scripts/hero.gd`, `scripts/enemy.gd` : combat (combo, esquive, télégraphes, recul).
- `scripts/stepped_animator.gd` : lecture des animations par paliers, recalage sur les durées de jeu.
- `scripts/juice.gd` : arrêt sur image, tremblement, éclats.
- `scripts/sound.gd` (autoload `Sound`) : effets à variantes aléatoires, musique et ambiance en boucle.

## Son

Direction audio : [AUDIO_THEME.md](AUDIO_THEME.md) (instruments acoustiques, ré dorien, niveaux).
Tous les sons sont générés par MiniMax Music 3 dans ComfyUI avec `tools/generate_audio.py`,
qui contient la liste des prompts. Le modèle joue de la musique continue : le script lui demande
de répéter lentement chaque geste avec des silences, puis découpe les meilleures attaques
(enregistrements bruts gardés dans `audio_raw/`, ignoré par Godot).

ComfyUI doit tourner sur `http://127.0.0.1:8188`, puis :

```bash
"C:\Users\cleme\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe" tools/generate_audio.py
```

- sans argument : génère ce qui manque ;
- avec un ou plusieurs noms (`sword_hit slime_death`) : régénère ces sons ;
- `--retrim` : redécoupe depuis `audio_raw/` sans régénérer ;
- `tools/audio_report.py` : durée, crête et enveloppe de chaque fichier.

Pour ajouter un son : une entrée dans `SOUNDS` (generate_audio.py), puis `Sound.play("nom")` dans le jeu.
Les bus `Music`, `Ambience` et `SFX` (et le limiteur du Master) sont dans `default_bus_layout.tres`.

## Modifier les modèles

1. Modifier `blender/exemple_hackslash.blend`, ou `generate_example.py` puis le relancer.
2. Réexporter :

```bash
D:\dev\Blender\blender.exe -b blender/exemple_hackslash.blend --python blender/export_godot.py
```

```bash
D:\dev\Blender\blender.exe -b blender/exemple_hackslash.blend --python blender/rig_hero.py
```

```bash
D:\dev\Blender\blender.exe -b blender/exemple_hackslash.blend --python blender/rig_enemies.py -- slime
```

```bash
D:\dev\Blender\blender.exe -b blender/exemple_hackslash.blend --python blender/rig_enemies.py -- squelette
```

Godot réimporte les `.glb` automatiquement. Les noms d'actions comptent (utilisés par les scripts),
ainsi que `Pilier*`, `Mur*`, `Rocher*`… dans le niveau (collisions).

Durées :
- héros : les durées des attaques dans `hero.gd` (`windup`, `active`, `recovery`) correspondent aux
  images des actions Blender à 30 i/s ; si on retouche une attaque, garder les deux en accord ;
- ennemis : `preparation`, `attaque`, `touche` et `apparition` sont recalées automatiquement sur
  `windup_time`, `attack_time`… (réglables dans `slime.tscn` / `skeleton.tscn`).

`anim_fps` (15 par défaut) règle la cadence « image par image » ; 0 = animation fluide.

## Tests

- `--selftest` (sans fenêtre) : héros invincible ; casse des jarres, vide la 1re salle, bat le boss,
  et affiche un bilan (herses rouvertes, sortie ouverte…).
- `--screenshot=renders/visite.png` : visite du niveau en captures (`visite_1.png`, `visite_2.png`…),
  boss compris.

```bash
Godot_v4.7.2-stable_win64_console.exe --headless --path . -- --selftest
```

```bash
Godot_v4.7.2-stable_win64_console.exe --path . -- --screenshot=renders/visite.png
```
