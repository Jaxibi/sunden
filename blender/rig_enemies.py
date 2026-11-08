"""Ennemis animés : slime (corps souple) et squelette (pièces rigides).

Usage (depuis E:\\dev\\sunden) :
    D:\\dev\\Blender\\blender.exe -b blender/exemple_hackslash.blend --python blender/rig_enemies.py

Produit :
    blender/ennemis_animes.blend       les deux ennemis riggés et leurs actions
    renders/ennemis_animations.png     planche de contrôle (slime puis squelette, une ligne par animation)
    assets/models/slime.glb            export Godot
    assets/models/skeleton.glb         export Godot

Noms d'animations attendus par scripts/enemy.gd :
    repos, saut (slime) / marche (squelette), preparation, attaque, touche
    apparition et mort (squelette uniquement ; le slime apparaît et meurt par le code)
Les durées de preparation / attaque / touche / apparition sont recalées par le code sur les
durées de jeu (windup_time, attack_time...) : on peut les retoucher librement ici.

Conventions des poses : voir rig_utils.py (X+ = membre vers l'avant / buste vers l'arrière).
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
WHICH = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else ""
if WHICH not in ("slime", "squelette"):
    raise SystemExit("Préciser l'ennemi après -- : slime ou squelette")

rig_utils.clean_scene()


def box(size, center, mat, bone):
    return {"size": size, "center": center, "mat": mat, "bone": bone}


def build_slime():
    # =========================================================================== SLIME
    slime = rig_utils.Rig("Slime", [
        ("racine", (0, 0, 0), (0, 0.25, 0), None),
        ("corps", (0, 0, 0), (0, 0, 0.3), "racine"),        # base : écrasement / étirement
        ("haut", (0, 0, 0.3), (0, 0, 0.66), "corps"),       # sommet : balancement
    ])


    def slime_weights(co):
        w = min(max((co.z - 0.12) / 0.36, 0.0), 1.0)
        return {"corps": 1.0 - w, "haut": w}


    slime.build_mesh([
        {"shape": "sphere", "size": (0.5, 0.5, 0.36), "center": (0, 0, 0.3), "mat": "Slime",
         "weights": slime_weights, "segments": 8, "rings": 5},
        box((0.07, 0.04, 0.12), (0.15, 0.44, 0.36), "Noir", "haut"),
        box((0.07, 0.04, 0.12), (-0.15, 0.44, 0.36), "Noir", "haut"),
    ])


    def sq(sx, sz, haut=(0, 0, 0), jump=0.0):
        """Pose de slime : échelle horizontale/verticale du corps, inclinaison du sommet, hauteur de saut."""
        return ({"haut": haut}, {"racine": (0, 0, jump)}, {"corps": (sx, sx, sz)})


    def skey(frame, pose):
        return (frame, *pose)


    slime.action("repos", [skey(0, sq(1, 1)), skey(15, sq(1.06, 0.92, (0, 4, 0))), skey(30, sq(1, 1))])
    slime.action("saut", [skey(0, sq(1.25, 0.7, (-5, 0, 0))), skey(3, sq(0.85, 1.25, (-12, 0, 0), 0.06)),
                          skey(6, sq(1.0, 1.05, (-8, 0, 0), 0.22)), skey(9, sq(0.9, 1.15, (5, 0, 0), 0.07)),
                          skey(12, sq(1.25, 0.7, (-5, 0, 0)))])
    slime.action("preparation", [skey(0, sq(1, 1)), skey(8, sq(1.35, 0.6, (12, 0, 0))),
                                 skey(10, sq(1.35, 0.6, (12, 0, 7))), skey(12, sq(1.38, 0.58, (12, 0, -7))),
                                 skey(14, sq(1.4, 0.56, (13, 0, 7))), skey(15, sq(1.4, 0.55, (14, 0, 0)))])
    slime.action("attaque", [skey(0, sq(0.8, 1.35, (-20, 0, 0), 0.05)), skey(5, sq(1.05, 0.95, (-10, 0, 0), 0.55)),
                             skey(9, sq(1.3, 0.7, (5, 0, 0))), skey(10, sq(1.3, 0.7, (5, 0, 0)))])
    slime.action("touche", [skey(0, sq(1.35, 0.62, (15, 0, 0))), skey(3, sq(0.85, 1.2, (-8, 0, 0))),
                            skey(6, sq(1.1, 0.9)), skey(10, sq(1, 1))])
    slime.reset_pose()
    sheet = [("repos", 3), ("saut", 1), ("preparation", 1), ("attaque", 1), ("touche", 1)]
    return slime, sheet, 0.35, "slime.glb"


def build_skeleton():
    # =========================================================================== SQUELETTE
    SK_BONES = [
        ("racine", (0, 0, 0), (0, 0.25, 0), None),
        ("hanches", (0, 0, 0.5), (0, 0, 0.6), "racine"),
        ("torse", (0, 0, 0.6), (0, 0, 1.08), "hanches"),
        ("tete", (0, 0, 1.08), (0, 0, 1.42), "torse"),
        ("machoire", (0, -0.06, 1.13), (0, 0.12, 1.13), "tete"),
    ]
    for side, s in (("R", 1), ("L", -1)):
        SK_BONES += [
            (f"bras.{side}", (0.27 * s, 0, 1.0), (0.27 * s, 0, 0.79), "torse"),
            (f"avantbras.{side}", (0.27 * s, 0, 0.79), (0.27 * s, 0, 0.58), f"bras.{side}"),
            (f"cuisse.{side}", (0.11 * s, 0, 0.5), (0.11 * s, 0, 0.26), "hanches"),
            (f"tibia.{side}", (0.11 * s, 0, 0.26), (0.11 * s, 0, 0.02), f"cuisse.{side}"),
        ]
    SK_BONES.append(("epee", (0.27, 0, 0.55), (0.27, 0.3, 0.55), "avantbras.R"))
    skel = rig_utils.Rig("Squelette", SK_BONES)

    SK_PARTS = [
        box((0.32, 0.16, 0.10), (0, 0, 0.52), "Os", "hanches"),
        box((0.07, 0.07, 0.32), (0, 0, 0.74), "Os", "torse"),
        box((0.30, 0.28, 0.24), (0, 0.02, 1.27), "Os", "tete"),
        box((0.04, 0.02, 0.04), (0, 0.165, 1.2), "Noir", "tete"),
        box((0.22, 0.20, 0.06), (0, 0.05, 1.12), "Os", "machoire"),
        box((0.04, 0.14, 0.04), (0.27, 0.0, 0.55), "Cuir", "epee"),
        box((0.18, 0.04, 0.04), (0.27, 0.08, 0.55), "Rouille", "epee"),
        box((0.07, 0.75, 0.025), (0.27, 0.47, 0.55), "Rouille", "epee"),
    ]
    for k in range(3):
        SK_PARTS.append(box((0.38 - 0.05 * k, 0.2, 0.05), (0, 0, 0.98 - 0.1 * k), "Os", "torse"))
    for side, s in (("R", 1), ("L", -1)):
        SK_PARTS += [
            box((0.08, 0.03, 0.08), (0.07 * s, 0.16, 1.28), "Noir", "tete"),
            box((0.07, 0.07, 0.21), (0.27 * s, 0, 0.895), "Os", f"bras.{side}"),
            box((0.07, 0.07, 0.20), (0.27 * s, 0, 0.69), "Os", f"avantbras.{side}"),
            box((0.08, 0.08, 0.07), (0.27 * s, 0, 0.56), "Os", f"avantbras.{side}"),
            box((0.08, 0.08, 0.24), (0.11 * s, 0, 0.38), "Os", f"cuisse.{side}"),
            box((0.08, 0.08, 0.22), (0.11 * s, 0, 0.15), "Os", f"tibia.{side}"),
            box((0.10, 0.16, 0.05), (0.11 * s, 0.03, 0.025), "Os", f"tibia.{side}"),
        ]
    skel.build_mesh(SK_PARTS)


    def hips(z, extra=None):
        return {"hanches": (0, 0, z), **(extra or {})}


    IDLE_A = {"torse": (-8, 0, 0), "tete": (10, 0, 0), "bras.R": (15, 0, 0), "avantbras.R": (40, 0, 0),
              "epee": (-80, 0, 0), "bras.L": (5, 15, 0), "avantbras.L": (20, 0, 0),
              "cuisse.L": (8, 0, 0), "tibia.L": (-10, 0, 0), "cuisse.R": (-5, 0, 0), "tibia.R": (-10, 0, 0)}
    IDLE_JAW = {**IDLE_A, "machoire": (-20, 0, 0)}
    IDLE_B = {**IDLE_A, "torse": (-11, 0, 4), "tete": (14, 6, 0), "machoire": (-25, 0, 0), "bras.L": (8, 18, 0)}

    WALK_ARMS = {"bras.R": (15, 0, 0), "avantbras.R": (40, 0, 0), "epee": (-80, 0, 0), "avantbras.L": (20, 0, 0)}
    WALK = [
        {**WALK_ARMS, "cuisse.L": (30, 0, 0), "tibia.L": (-10, 0, 0), "cuisse.R": (-25, 0, 0), "tibia.R": (-35, 0, 0),
         "bras.L": (-20, 15, 0), "torse": (-12, 0, -6), "tete": (12, 0, 8)},
        {**WALK_ARMS, "cuisse.L": (0, 0, 0), "tibia.L": (-5, 0, 0), "cuisse.R": (15, 0, 0), "tibia.R": (-70, 0, 0),
         "bras.L": (0, 15, 0), "torse": (-12, 0, 0), "tete": (12, 8, 0), "machoire": (-15, 0, 0)},
        {**WALK_ARMS, "cuisse.L": (-25, 0, 0), "tibia.L": (-35, 0, 0), "cuisse.R": (30, 0, 0), "tibia.R": (-10, 0, 0),
         "bras.L": (20, 15, 0), "torse": (-12, 0, 6), "tete": (12, 0, -8)},
        {**WALK_ARMS, "cuisse.L": (15, 0, 0), "tibia.L": (-70, 0, 0), "cuisse.R": (0, 0, 0), "tibia.R": (-5, 0, 0),
         "bras.L": (0, 15, 0), "torse": (-12, 0, 0), "tete": (12, -8, 0), "machoire": (-15, 0, 0)},
    ]

    PREP = {"torse": (10, 0, -20), "tete": (5, 0, 0), "machoire": (-30, 0, 0), "bras.R": (165, 0, -15),
            "avantbras.R": (15, 0, 0), "epee": (-70, 0, 0), "bras.L": (40, 30, 0), "avantbras.L": (20, 0, 0),
            "cuisse.L": (20, 0, 0), "tibia.L": (-15, 0, 0), "cuisse.R": (-15, 0, 0), "tibia.R": (-15, 0, 0)}
    PREP2 = {**PREP, "torse": (12, 0, -22), "bras.R": (170, 0, -15), "machoire": (-35, 0, 0)}
    CHOP = {"torse": (-30, 0, 10), "tete": (-5, 0, 0), "bras.R": (70, 0, 10), "avantbras.R": (10, 0, 0),
            "epee": (-95, 0, 0), "bras.L": (-20, 20, 0), "avantbras.L": (20, 0, 0),
            "cuisse.L": (35, 0, 0), "tibia.L": (-25, 0, 0), "cuisse.R": (-25, 0, 0), "tibia.R": (-10, 0, 0)}
    HIT = {**IDLE_A, "torse": (25, 0, 10), "tete": (30, 15, 0), "machoire": (-35, 0, 0),
           "bras.R": (-10, -30, 0), "bras.L": (-10, 40, 0)}
    ARMS_UP = {**IDLE_A, "torse": (-30, 0, 0), "tete": (20, 0, 0), "bras.R": (160, 0, 0), "bras.L": (160, 0, 0),
               "avantbras.R": (10, 0, 0), "avantbras.L": (10, 0, 0), "epee": (-90, 0, 0), "machoire": (-30, 0, 0)}
    SLUMP = {"cuisse.L": (70, 0, 0), "tibia.L": (-110, 0, 0), "cuisse.R": (70, 0, 0), "tibia.R": (-110, 0, 0),
             "torse": (-30, 0, 0), "tete": (30, 0, 0), "machoire": (-30, 0, 0),
             "bras.R": (10, -20, 0), "bras.L": (10, 20, 0), "avantbras.R": (20, 0, 0), "epee": (-60, 0, 0)}
    PILE = {**SLUMP, "cuisse.L": (85, 0, 0), "tibia.L": (-140, 0, 0), "cuisse.R": (85, 0, 0), "tibia.R": (-140, 0, 0),
            "torse": (-75, 0, 10), "tete": (50, 0, 20), "bras.R": (-20, -40, 0), "bras.L": (-20, 40, 0),
            "epee": (-30, 0, 40)}

    skel.action("repos", [(0, IDLE_A, hips(-0.02)), (6, IDLE_JAW, hips(-0.02)), (10, IDLE_A, hips(-0.025)),
                          (20, IDLE_B, hips(-0.035)), (30, IDLE_JAW, hips(-0.025)), (34, IDLE_A, hips(-0.02)),
                          (40, IDLE_A, hips(-0.02))])
    skel.action("marche", [(0, WALK[0], hips(-0.04)), (6, WALK[1], hips(0.0)), (12, WALK[2], hips(-0.04)),
                           (18, WALK[3], hips(0.0)), (24, WALK[0], hips(-0.04))])
    skel.action("preparation", [(0, IDLE_A, hips(-0.02)), (10, PREP, hips(-0.03)), (16, PREP2, hips(-0.04))])
    skel.action("attaque", [(0, PREP2, hips(-0.04)), (3, CHOP, hips(-0.08)),
                            (8, {**CHOP, "torse": (-25, 0, 8), "bras.R": (62, 0, 10)}, hips(-0.07))])
    skel.action("touche", [(0, IDLE_A, hips(-0.02)), (2, HIT, hips(-0.03)),
                           (6, {**IDLE_A, "torse": (5, 0, 0)}, hips(-0.02)), (10, IDLE_A, hips(-0.02))])
    skel.action("apparition", [(0, ARMS_UP, {"racine": (0, 0, -1.45)}), (8, ARMS_UP, {"racine": (0, 0, -0.35)}),
                               (12, {**IDLE_B, "torse": (-15, 0, 0)}, {"racine": (0, 0, -0.03)}),
                               (14, IDLE_A, hips(-0.02))])
    skel.action("mort", [(0, HIT, hips(-0.03)), (5, SLUMP, hips(-0.25)), (11, PILE, hips(-0.42)),
                         (18, {**PILE, "tete": (60, 0, 30)}, hips(-0.45))])
    skel.reset_pose()
    sheet = [("repos", 4), ("marche", 2), ("preparation", 2), ("attaque", 1), ("touche", 1),
             ("apparition", 1), ("mort", 2)]
    return skel, sheet, 0.62, "skeleton.glb"


# =========================================================================== planche + export
rig, sheet, target_z, glb_name = build_slime() if WHICH == "slime" else build_skeleton()
rig.reset_pose()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{WHICH}_anime.blend"))

rows = rig_utils.render_rows(rig, sheet, target_z=target_z)
rig_utils.save_sheet(rows, os.path.join(ROOT, "renders", f"{WHICH}_animations.png"))

rig.reset_pose()
gltf_utils.to_principled()
gltf_utils.export_glb(os.path.join(ROOT, "assets", "models", glb_name), [rig.arm, rig.body], animations=True)

print("RESULT " + json.dumps({
    "enemy": WHICH, "actions": {a.name: list(a.frame_range) for a in bpy.data.actions}, "rows": len(rows),
}))
