"""Héros animé : squelette, maillage rigide (chaque pièce suit un seul os) et animations.

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


# --------------------------------------------------------------------------- maillage (pièces rigides)
def box(size, center, mat, bone):
    return {"size": size, "center": center, "mat": mat, "bone": bone}


PARTS = [
    box((0.48, 0.32, 0.10), (0, 0, 0.55), "Cuir", "hanches"),
    box((0.10, 0.04, 0.08), (0, 0.17, 0.55), "Or", "hanches"),
    box((0.46, 0.30, 0.42), (0, 0, 0.81), "Tunique", "torse"),
    box((0.32, 0.30, 0.32), (0, 0.01, 1.20), "Peau", "tete"),
    box((0.35, 0.33, 0.12), (0, -0.01, 1.38), "Cheveux", "tete"),
    box((0.35, 0.10, 0.24), (0, -0.14, 1.26), "Cheveux", "tete"),
    box((0.46, 0.05, 0.62), (0, -0.20, 0.72), "Cape", "cape"),
    box((0.05, 0.20, 0.05), (0.31, 0.0, 0.53), "Cuir", "epee"),
    box((0.30, 0.05, 0.05), (0.31, 0.11, 0.53), "Or", "epee"),
    box((0.08, 0.95, 0.025), (0.31, 0.60, 0.53), "Acier", "epee"),
    box((0.06, 0.40, 0.46), (-0.40, 0.03, 0.66), "Tunique", "avantbras.L"),
    box((0.04, 0.12, 0.12), (-0.44, 0.03, 0.66), "Or", "avantbras.L"),
]
for side, s in (("R", 1), ("L", -1)):
    PARTS += [
        box((0.20, 0.34, 0.12), (0.30 * s, 0, 1.0), "Acier", "torse"),
        box((0.05, 0.02, 0.07), (0.07 * s, 0.165, 1.2), "Noir", "tete"),
        box((0.13, 0.13, 0.25), (0.31 * s, 0, 0.86), "Tunique", f"bras.{side}"),
        box((0.12, 0.12, 0.17), (0.31 * s, 0, 0.655), "Tunique", f"avantbras.{side}"),
        box((0.11, 0.11, 0.10), (0.31 * s, 0, 0.53), "Peau", f"avantbras.{side}"),
        box((0.15, 0.15, 0.25), (0.12 * s, 0, 0.385), "Pantalon", f"cuisse.{side}"),
        box((0.14, 0.14, 0.20), (0.12 * s, 0, 0.17), "Pantalon", f"tibia.{side}"),
        box((0.17, 0.22, 0.12), (0.12 * s, 0.02, 0.06), "Cuir", f"tibia.{side}"),
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
