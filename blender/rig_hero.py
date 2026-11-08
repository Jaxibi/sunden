r"""Héros animé : squelette, maillage rigide (chaque pièce suit un seul os) et animations.

Usage (depuis E:\dev\sunden) :
    D:\dev\Blender\blender.exe -b blender/exemple_hackslash.blend --python blender/rig_hero.py

Produit :
    blender/heros_anime.blend        le héros riggé et ses actions, modifiable dans Blender
    renders/heros_animations.png     planche de contrôle (une ligne par animation, 15 i/s)
    assets/models/hero.glb           export pour Godot (Skeleton3D + AnimationPlayer)

Conventions des poses : voir rig_utils.py. Pour ce personnage :
    X+ : jambe / bras vers l'avant, mais buste vers l'arrière (X- = se pencher en avant)
    Z+ : tourner vers la gauche (vu de dessus)
    Y+ : bras gauche vers l'extérieur ; Y- : bras droit vers l'extérieur
"""
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gltf_utils  # noqa: E402
import rig_utils  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT_BLEND = os.path.join(HERE, "heros_anime.blend")
OUT_GLB = os.path.join(ROOT, "assets", "models", "hero.glb")
OUT_SHEET = os.path.join(ROOT, "renders", "heros_animations.png")

rig_utils.clean_scene()

# --------------------------------------------------------------------------- squelette
BONES = [
    ("racine", (0, 0, 0), (0, 0.25, 0), None),
    ("hanches", (0, 0, 0.5), (0, 0, 0.62), "racine"),
    ("torse", (0, 0, 0.62), (0, 0, 1.05), "hanches"),
    ("tete", (0, 0, 1.05), (0, 0, 1.42), "torse"),
    ("cape", (0, -0.18, 1.02), (0, -0.2, 0.42), "torse"),
]
for side, s in (("R", 1), ("L", -1)):
    BONES += [
        (f"bras.{side}", (0.31 * s, 0, 0.98), (0.31 * s, 0, 0.74), "torse"),
        (f"avantbras.{side}", (0.31 * s, 0, 0.74), (0.31 * s, 0, 0.55), f"bras.{side}"),
        (f"cuisse.{side}", (0.12 * s, 0, 0.5), (0.12 * s, 0, 0.27), "hanches"),
        (f"tibia.{side}", (0.12 * s, 0, 0.27), (0.12 * s, 0, 0.04), f"cuisse.{side}"),
    ]
BONES.append(("epee", (0.31, 0, 0.53), (0.31, 0.35, 0.53), "avantbras.R"))
rig = rig_utils.Rig("Heros", BONES)


# --------------------------------------------------------------------------- maillage (volumes sculptés)
def part(shape, size, center, mat, bone, **kw):
    return {"shape": shape, "size": size, "center": center, "mat": mat, "bone": bone, **kw}


PARTS = [
    # Hanches : basque de tunique évasée + ceinture cintrée + boucle dorée
    part("rounded_box", (0.44, 0.32, 0.19), (0, 0, 0.50), "Tunique", "hanches",
         top=(0.82, 0.82), bottom=(1.12, 1.08), bevel=0.22, power=0.82),
    part("limb", (0.42, 0.31, 0.09), (0, 0, 0.57), "Cuir", "hanches", power=0.82),
    part("dome", (0.12, 0.07, 0.11), (0, 0.16, 0.57), "Or", "hanches", rot=(-90, 0, 0)),

    # Torse en V athlétique + baudrier en cuir + foulard rouge autour du cou
    part("rounded_box", (0.45, 0.31, 0.42), (0, 0, 0.80), "Tunique", "torse",
         bottom=(0.78, 0.80), mid=(0.96, 0.96), top=(1.08, 1.04), bevel=0.26, power=0.84),
    part("limb", (0.46, 0.32, 0.07), (0, 0.01, 0.81), "Cuir", "torse", rot=(0, 28, 0)),
    part("limb", (0.37, 0.34, 0.12), (0, -0.01, 1.01), "Cape", "torse",
         bottom=(1.06, 1.06), top=(0.86, 0.88)),

    # Tête : cou, visage ovale sculpté, chevelure volumineuse en mèches
    part("limb", (0.16, 0.16, 0.10), (0, 0, 1.05), "Peau", "tete"),
    part("rounded_box", (0.33, 0.32, 0.33), (0, 0.02, 1.21), "Peau", "tete",
         bottom=(0.78, 0.82), mid=(1.0, 1.0), top=(0.92, 0.94), bevel=0.30, power=0.88),
    part("dome", (0.38, 0.37, 0.22), (0, -0.01, 1.33), "Cheveux", "tete", flare=1.04),
    part("limb", (0.17, 0.24, 0.11), (0.05, 0.12, 1.34), "Cheveux", "tete",
         rot=(25, 15, -22), bottom=(0.45, 0.45), top=(1.0, 1.0)),
    part("dome", (0.36, 0.22, 0.28), (0, -0.11, 1.24), "Cheveux", "tete", rot=(-55, 0, 0)),
    part("limb", (0.24, 0.14, 0.18), (0, -0.16, 1.14), "Cheveux", "tete",
         rot=(-35, 0, 0), bottom=(0.4, 0.4), top=(1.0, 1.0)),

    # Cape trapézoïdale plissée
    part("cape", (0.50, 0.10, 0.66), (0, -0.20, 0.70), "Cape", "cape", rot=(8, 0, 0)),

    # Épée : pommeau rond, fusée en cuir, garde profilée, lame large en losange à pointe
    part("dome", (0.09, 0.09, 0.09), (0.31, -0.09, 0.53), "Or", "epee", rot=(-90, 0, 0)),
    part("limb", (0.06, 0.18, 0.06), (0.31, 0.01, 0.53), "Cuir", "epee", rot=(90, 0, 0)),
    part("rounded_box", (0.34, 0.07, 0.07), (0.31, 0.11, 0.53), "Or", "epee",
         bottom=(0.75, 0.75), top=(1.05, 1.05), bevel=0.22, smooth=False),
    part("blade", (0.14, 0.96, 0.055), (0.31, 0.61, 0.53), "Acier", "epee"),

    # Bouclier en écu incurvé + bordure et blason dorés
    part("shield", (0.08, 0.44, 0.52), (-0.40, 0.04, 0.65), "Tunique", "avantbras.L"),
    part("rounded_box", (0.09, 0.39, 0.07), (-0.40, 0.04, 0.89), "Or", "avantbras.L", bevel=0.2, smooth=False),
    part("dome", (0.07, 0.15, 0.18), (-0.44, 0.04, 0.67), "Or", "avantbras.L", rot=(0, -90, 0)),
]
for side, s in (("R", 1), ("L", -1)):
    PARTS += [
        # Épaulettes bombées avec liseré doré
        part("dome", (0.24, 0.34, 0.18), (0.29 * s, 0, 0.99), "Acier", "torse",
             rot=(0, 22 * s, 0), flare=1.08),
        part("limb", (0.25, 0.35, 0.05), (0.30 * s, 0, 0.93), "Or", "torse",
             rot=(0, 22 * s, 0)),
        # Oreilles, mèches latérales et yeux
        part("dome", (0.06, 0.08, 0.10), (0.165 * s, 0.0, 1.20), "Peau", "tete", rot=(0, 80 * s, 0)),
        part("limb", (0.09, 0.14, 0.22), (0.16 * s, 0.04, 1.24), "Cheveux", "tete",
             rot=(12, -10 * s, 0), bottom=(0.45, 0.5), top=(1.0, 1.0)),
        part("rounded_box", (0.055, 0.03, 0.075), (0.075 * s, 0.168, 1.20), "Noir", "tete", bevel=0.25),
        # Bras fuselés, brassards de cuir et poings ronds
        part("limb", (0.15, 0.15, 0.25), (0.31 * s, 0, 0.86), "Tunique", f"bras.{side}",
             top=(1.06, 1.06), bottom=(0.85, 0.85)),
        part("limb", (0.14, 0.14, 0.18), (0.31 * s, 0, 0.66), "Cuir", f"avantbras.{side}",
             top=(1.08, 1.08), bottom=(0.82, 0.82)),
        part("dome", (0.12, 0.13, 0.12), (0.31 * s, 0.01, 0.53), "Peau", f"avantbras.{side}",
             rot=(180, 0, 0)),
        # Jambes fuselées et bottes à revers
        part("limb", (0.17, 0.17, 0.25), (0.12 * s, 0, 0.385), "Pantalon", f"cuisse.{side}",
             top=(1.08, 1.08), bottom=(0.84, 0.84)),
        part("limb", (0.14, 0.14, 0.16), (0.12 * s, 0, 0.21), "Pantalon", f"tibia.{side}",
             top=(1.0, 1.0), bottom=(0.85, 0.85)),
        part("limb", (0.17, 0.18, 0.11), (0.12 * s, 0.0, 0.13), "Cuir", f"tibia.{side}",
             top=(1.12, 1.12), bottom=(0.88, 0.88)),
        part("dome", (0.17, 0.25, 0.11), (0.12 * s, 0.04, 0.055), "Cuir", f"tibia.{side}",
             flare=1.05),
    ]
rig.build_mesh(PARTS)


def hips(z):
    return {"hanches": (0, 0, z)}


# --------------------------------------------------------------------------- poses
LEGS_STANCE = {"cuisse.L": (10, 0, 0), "tibia.L": (-8, 0, 0), "cuisse.R": (-6, 0, 0), "tibia.R": (-6, 0, 0)}
SHIELD = {"bras.L": (15, 0, 0), "avantbras.L": (60, 0, -30)}
SWORD_REST = {"bras.R": (20, 0, 0), "avantbras.R": (50, 0, 0), "epee": (-90, 0, 0)}
IDLE_A = {**LEGS_STANCE, **SHIELD, **SWORD_REST, "cape": (-5, 0, 0)}
IDLE_B = {**IDLE_A, "torse": (-3, 0, 0), "bras.R": (24, 0, 0), "bras.L": (18, 0, 0), "cape": (-9, 0, 0)}

RUN_ARMS = {"avantbras.L": (60, 0, -30), "avantbras.R": (60, 0, 0), "epee": (-90, 0, 0)}
RUN = [
    {**RUN_ARMS, "cuisse.L": (45, 0, 0), "tibia.L": (-15, 0, 0), "cuisse.R": (-40, 0, 0), "tibia.R": (-70, 0, 0),
     "bras.L": (-25, 0, 0), "bras.R": (25, 0, 0), "torse": (-12, 0, -8), "tete": (8, 0, 8), "cape": (-35, 0, 0)},
    {**RUN_ARMS, "cuisse.L": (0, 0, 0), "tibia.L": (-10, 0, 0), "cuisse.R": (10, 0, 0), "tibia.R": (-90, 0, 0),
     "bras.L": (0, 0, 0), "bras.R": (10, 0, 0), "torse": (-12, 0, 0), "tete": (8, 0, 0), "cape": (-45, 0, 0)},
    {**RUN_ARMS, "cuisse.L": (-40, 0, 0), "tibia.L": (-70, 0, 0), "cuisse.R": (45, 0, 0), "tibia.R": (-15, 0, 0),
     "bras.L": (25, 0, 0), "bras.R": (-10, 0, 0), "torse": (-12, 0, 8), "tete": (8, 0, -8), "cape": (-35, 0, 0)},
    {**RUN_ARMS, "cuisse.L": (10, 0, 0), "tibia.L": (-90, 0, 0), "cuisse.R": (0, 0, 0), "tibia.R": (-10, 0, 0),
     "bras.L": (0, 0, 0), "bras.R": (10, 0, 0), "torse": (-12, 0, 0), "tete": (8, 0, 0), "cape": (-45, 0, 0)},
]

LEGS_A = {"cuisse.L": (25, 0, 0), "tibia.L": (-15, 0, 0), "cuisse.R": (-20, 0, 0), "tibia.R": (-20, 0, 0)}
LEGS_B = {"cuisse.R": (25, 0, 0), "tibia.R": (-15, 0, 0), "cuisse.L": (-20, 0, 0), "tibia.L": (-20, 0, 0)}
GUARD = {"bras.L": (30, 0, 0), "avantbras.L": (70, 0, -40)}
# Coup 1 : de droite à gauche (l'épée balaie d'environ -100° à +95° autour de l'avant)
A1_WIND = {**LEGS_A, **GUARD, "torse": (0, 0, -40), "tete": (0, 0, 25), "bras.R": (80, 0, -60),
           "epee": (-90, 0, 0), "cape": (-15, 0, 0)}
A1_HIT = {**LEGS_A, **GUARD, "torse": (-8, 0, 35), "tete": (0, 0, -25), "bras.R": (85, 0, 60),
          "epee": (-90, 0, 10), "cape": (-25, 0, 0)}
A1_HOLD = {**A1_HIT, "torse": (-5, 0, 30), "bras.R": (75, 0, 55)}
# Coup 2 : revers de gauche à droite
A2_WIND = {**LEGS_B, **GUARD, "torse": (-5, 0, 45), "tete": (0, 0, -30), "bras.R": (85, 0, 70),
           "epee": (-90, 0, 15), "cape": (-15, 0, 0)}
A2_HIT = {**LEGS_B, **GUARD, "torse": (-8, 0, -35), "tete": (0, 0, 25), "bras.R": (80, 0, -70),
          "epee": (-90, 0, -10), "cape": (-25, 0, 0)}
A2_HOLD = {**A2_HIT, "torse": (-5, 0, -30), "bras.R": (75, 0, -60)}
# Coup 3 : accroupi, bras tendus ; la rotation complète est faite par le code
CROUCH = {"cuisse.L": (40, 0, 0), "tibia.L": (-45, 0, 0), "cuisse.R": (-25, 0, 0), "tibia.R": (-45, 0, 0)}
A3_WIND = {**CROUCH, "torse": (-12, 0, 40), "tete": (0, 0, -30), "bras.R": (85, 0, -90), "epee": (-90, 0, 0),
           "bras.L": (40, 0, 60), "avantbras.L": (30, 0, 0), "cape": (-20, 0, 0)}
A3_SPIN = {**CROUCH, "torse": (-5, 0, -10), "tete": (0, 0, 10), "bras.R": (88, 0, -90), "epee": (-90, 0, 0),
           "bras.L": (0, 60, 0), "avantbras.L": (0, 0, 0), "cape": (-60, 0, 0)}

TUCK = {"torse": (-50, 0, 0), "tete": (-20, 0, 0), "cuisse.L": (100, 0, 0), "tibia.L": (-120, 0, 0),
        "cuisse.R": (100, 0, 0), "tibia.R": (-120, 0, 0), "bras.L": (60, 0, 0), "avantbras.L": (60, 0, -30),
        "bras.R": (60, 0, 0), "avantbras.R": (60, 0, 0), "epee": (-90, 0, 0), "cape": (-30, 0, 0)}

HURT = {**LEGS_STANCE, "torse": (25, 0, 0), "tete": (20, 0, 0), "bras.R": (0, -40, 0), "avantbras.R": (20, 0, 0),
        "epee": (-90, 0, 0), "bras.L": (0, 40, 0), "avantbras.L": (20, 0, 0), "cape": (-20, 0, 0)}
KNEEL = {"cuisse.L": (85, 0, 0), "tibia.L": (-85, 0, 0), "cuisse.R": (-5, 0, 0), "tibia.R": (-90, 0, 0),
         "torse": (-25, 0, 0), "tete": (-20, 0, 0), "bras.R": (10, 0, 0), "avantbras.R": (20, 0, 0),
         "epee": (-60, 0, 0), "bras.L": (5, 0, 0), "avantbras.L": (30, 0, -20), "cape": (-5, 0, 0)}

# --------------------------------------------------------------------------- animations (30 i/s)
rig.action("repos", [(0, IDLE_A), (20, IDLE_B, hips(-0.015)), (40, IDLE_A)])
rig.action("course", [(0, RUN[0]), (4, RUN[1], hips(0.05)), (8, RUN[2]), (12, RUN[3], hips(0.05)), (16, RUN[0])])
# attaques : préparation / coup actif / récupération = 3 / 3 / 7 images (doit correspondre à hero.gd)
rig.action("attaque_1", [(0, IDLE_A), (3, A1_WIND, hips(-0.05)), (6, A1_HIT, hips(-0.05)),
                     (9, A1_HOLD, hips(-0.04)), (13, IDLE_A)])
rig.action("attaque_2", [(0, A1_HIT, hips(-0.05)), (3, A2_WIND, hips(-0.05)), (6, A2_HIT, hips(-0.05)),
                     (9, A2_HOLD, hips(-0.04)), (13, IDLE_A)])
# coup tournoyant : 5 / 5 / 10 images
rig.action("attaque_3", [(0, A2_HIT, hips(-0.05)), (5, A3_WIND, hips(-0.12)), (8, A3_SPIN, hips(-0.1)),
                     (10, {**A3_SPIN, "torse": (-5, 0, -20)}, hips(-0.08)), (20, IDLE_A)])
# roulade : 8 images, le bassin fait un tour complet
roll = [(0, {**IDLE_A, "torse": (-20, 0, 0)}, hips(-0.05))]
for f in range(1, 8):
    roll.append((f, {**TUCK, "hanches": (-45 * f, 0, 0)}, hips(-0.08)))
roll.append((8, {**IDLE_A, "hanches": (-360, 0, 0)}))
rig.action("esquive", roll)
rig.action("touche", [(0, IDLE_A), (2, HURT, hips(-0.04)), (8, IDLE_A)])
rig.action("mort", [(0, HURT, hips(-0.04)), (6, KNEEL, hips(-0.27)), (12, {**KNEEL, "torse": (-35, 0, 0)}, hips(-0.27)),
                (20, {**KNEEL, "torse": (-10, 0, 0), "racine": (0, 85, 0)}, {**hips(-0.27), "racine": (0, 0, 0.22)}),
                (24, {**KNEEL, "torse": (-10, 0, 0), "racine": (0, 90, 0)}, {**hips(-0.27), "racine": (0, 0, 0.2)})])

rig.reset_pose()
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

# --------------------------------------------------------------------------- planche de contrôle
SHEET = [("repos", 4), ("course", 2), ("attaque_1", 2), ("attaque_2", 2), ("attaque_3", 2),
         ("esquive", 1), ("touche", 2), ("mort", 2)]
rows = rig_utils.render_rows(rig, SHEET, target_z=0.62)
rig_utils.save_sheet(rows, OUT_SHEET)

# --------------------------------------------------------------------------- export Godot
rig.reset_pose()
gltf_utils.to_principled()
gltf_utils.export_glb(OUT_GLB, [rig.arm, rig.body], animations=True)

print("RESULT " + json.dumps({
    "bones": len(BONES), "parts": len(PARTS), "verts": len(rig.body.data.vertices),
    "actions": {a.name: list(a.frame_range) for a in bpy.data.actions},
    "sheet": [f"{n}: {len(r)} images" for (n, _), r in zip(SHEET, rows)],
}))
