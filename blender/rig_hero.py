r"""Héros animé : squelette, 3 ensembles d'équipement (Tissu, Cuir, Plates) et animations.

Usage (depuis E:\dev\sunden) :
    D:\dev\Blender\blender.exe -b blender/exemple_hackslash.blend --python blender/rig_hero.py

Produit :
    blender/heros_anime.blend        le héros riggé, ses 3 tenues et ses actions
    renders/heros_equipements.png    planche comparative des 3 ensembles (Tissu, Cuir, Plates)
    renders/heros_animations.png     planche de contrôle complète des animations
    assets/models/hero.glb           export pour Godot (Skeleton3D + Equip_Tissu/Cuir/Plates + AnimationPlayer)
    assets/models/hero_tissu.glb     export individuel tenue Tissu
    assets/models/hero_cuir.glb      export individuel tenue Cuir
    assets/models/hero_plates.glb    export individuel tenue Plates

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
OUT_EQUIP_SHEET = os.path.join(ROOT, "renders", "heros_equipements.png")

rig_utils.clean_scene()


def ensure_mat(name, hex_color):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    h = hex_color.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
    m = bpy.data.materials["Tunique"].copy()
    m.name = name
    m.diffuse_color = lin + (1.0,)
    for n in m.node_tree.nodes:
        if n.type == "VECT_MATH":
            n.inputs[1].default_value = lin
    return m


# Nuances complémentaires pour bien différencier les 3 ensembles d'équipement
ensure_mat("TissuClair", "#dfd9ec")
ensure_mat("CuirClair", "#b88248")
ensure_mat("CapeVerte", "#52994e")
ensure_mat("AcierSombre", "#8693a6")

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


# --------------------------------------------------------------------------- 3 ensembles d'équipement
def part(shape, size, center, mat, bone, **kw):
    return {"shape": shape, "size": size, "center": center, "mat": mat, "bone": bone, **kw}


def base_head(hair_band_mat=None):
    """Tête sculptée et chevelure en mèches (commune aux tenues Tissu et Cuir)."""
    pts = [
        part("limb", (0.16, 0.16, 0.10), (0, 0, 1.05), "Peau", "tete"),
        part("rounded_box", (0.33, 0.32, 0.33), (0, 0.02, 1.21), "Peau", "tete",
             bottom=(0.78, 0.82), mid=(1.0, 1.0), top=(0.92, 0.94), bevel=0.30, power=0.88),
        part("dome", (0.38, 0.37, 0.21), (0, -0.01, 1.33), "Cheveux", "tete", flare=1.04),
        part("limb", (0.17, 0.24, 0.11), (0.05, 0.12, 1.34), "Cheveux", "tete",
             rot=(25, 15, -22), bottom=(0.45, 0.45), top=(1.0, 1.0)),
        part("dome", (0.36, 0.22, 0.28), (0, -0.11, 1.24), "Cheveux", "tete", rot=(-55, 0, 0)),
        part("limb", (0.24, 0.14, 0.18), (0, -0.16, 1.14), "Cheveux", "tete",
             rot=(-35, 0, 0), bottom=(0.4, 0.4), top=(1.0, 1.0)),
    ]
    if hair_band_mat:
        pts.append(part("limb", (0.355, 0.345, 0.055), (0, 0.01, 1.29), hair_band_mat, "tete", power=0.85))
    for s in (1, -1):
        pts += [
            part("dome", (0.06, 0.08, 0.10), (0.165 * s, 0.0, 1.20), "Peau", "tete", rot=(0, 80 * s, 0)),
            part("limb", (0.09, 0.14, 0.22), (0.16 * s, 0.04, 1.24), "Cheveux", "tete",
                 rot=(12, -10 * s, 0), bottom=(0.45, 0.5), top=(1.0, 1.0)),
            part("rounded_box", (0.055, 0.03, 0.075), (0.075 * s, 0.168, 1.20), "Noir", "tete", bevel=0.25),
        ]
    return pts


# 1) ENSEMBLE TISSU : Robe de Mage-Lame, diadème d'or, pèlerine souple, manches bouffantes, targe runique
PARTS_TISSU = base_head(hair_band_mat="Or") + [
    # Diadème frontal à joyau + col-capuchon drapé
    part("dome", (0.08, 0.05, 0.09), (0, 0.175, 1.30), "Cape", "tete", rot=(-90, 0, 0)),
    part("limb", (0.40, 0.36, 0.14), (0, -0.02, 1.00), "Cape", "torse",
         bottom=(1.12, 1.10), top=(0.86, 0.88)),
    # Tunique drapée en tissu + étole runique claire et or sur le devant + ceinture dorée nouée
    part("rounded_box", (0.43, 0.29, 0.42), (0, 0, 0.80), "Tunique", "torse",
         bottom=(0.76, 0.78), mid=(0.94, 0.94), top=(1.04, 1.02), bevel=0.28, power=0.86),
    part("rounded_box", (0.16, 0.31, 0.40), (0, 0.01, 0.80), "TissuClair", "torse", bevel=0.20),
    part("limb", (0.41, 0.31, 0.10), (0, 0, 0.57), "Or", "hanches", power=0.84),
    # Longue basque de robe évasée + pan d'étole frontal jusqu'aux genoux
    part("rounded_box", (0.47, 0.35, 0.28), (0, 0, 0.45), "Tunique", "hanches",
         top=(0.78, 0.78), bottom=(1.18, 1.14), bevel=0.22, power=0.84),
    part("rounded_box", (0.15, 0.37, 0.30), (0, 0.01, 0.44), "TissuClair", "hanches",
         top=(0.85, 0.85), bottom=(1.08, 1.02), bevel=0.18),
    # Longue cape mystique bicolore
    part("cape", (0.48, 0.10, 0.70), (0, -0.19, 0.68), "Cape", "cape", rot=(8, 0, 0)),
    # Lame fine runique + garde en croissant doré
    part("dome", (0.08, 0.08, 0.08), (0.31, -0.08, 0.53), "Or", "epee", rot=(-90, 0, 0)),
    part("limb", (0.055, 0.18, 0.055), (0.31, 0.01, 0.53), "TissuClair", "epee", rot=(90, 0, 0)),
    part("limb", (0.28, 0.08, 0.06), (0.31, 0.11, 0.53), "Or", "epee", bend=(0.0, 0.06)),
    part("blade", (0.10, 0.98, 0.045), (0.31, 0.62, 0.53), "Acier", "epee"),
    # Petite Targe mystique ronde et dorée
    part("dome", (0.09, 0.36, 0.36), (-0.39, 0.04, 0.66), "TissuClair", "avantbras.L", rot=(0, -90, 0)),
    part("limb", (0.06, 0.38, 0.38), (-0.38, 0.04, 0.66), "Or", "avantbras.L", rot=(0, 90, 0)),
    part("dome", (0.07, 0.14, 0.14), (-0.42, 0.04, 0.66), "Cape", "avantbras.L", rot=(0, -90, 0)),
]
for side, s in (("R", 1), ("L", -1)):
    PARTS_TISSU += [
        # Épaules souples en pèlerine d'étoffe (sans plaques de métal)
        part("dome", (0.21, 0.29, 0.14), (0.26 * s, 0, 0.97), "Cape", "torse",
             rot=(0, 28 * s, 0), flare=1.05),
        # Manches bouffantes en tissu resserrées par un bracelet d'or
        part("limb", (0.16, 0.16, 0.25), (0.31 * s, 0, 0.86), "Tunique", f"bras.{side}",
             top=(0.95, 0.95), mid=(1.15, 1.15), bottom=(0.90, 0.90)),
        part("limb", (0.16, 0.16, 0.17), (0.31 * s, 0, 0.66), "Tunique", f"avantbras.{side}",
             top=(1.12, 1.12), mid=(1.18, 1.18), bottom=(0.75, 0.75)),
        part("limb", (0.13, 0.13, 0.05), (0.31 * s, 0, 0.58), "Or", f"avantbras.{side}"),
        part("dome", (0.12, 0.13, 0.12), (0.31 * s, 0.01, 0.53), "Peau", f"avantbras.{side}", rot=(180, 0, 0)),
        # Jambes de robe et chaussons souples en étoffe
        part("limb", (0.16, 0.16, 0.24), (0.12 * s, 0, 0.38), "Tunique", f"cuisse.{side}",
             top=(1.10, 1.10), bottom=(0.92, 0.92)),
        part("limb", (0.13, 0.13, 0.18), (0.12 * s, 0, 0.19), "TissuClair", f"tibia.{side}",
             top=(1.0, 1.0), bottom=(0.85, 0.85)),
        part("dome", (0.15, 0.24, 0.10), (0.12 * s, 0.04, 0.05), "Pantalon", f"tibia.{side}", flare=1.02),
    ]


# 2) ENSEMBLE CUIR : Brigandine de Rôdeur, épaulière asymétrique cloutée, cape courte verte, rondache
PARTS_CUIR = base_head(hair_band_mat="CuirClair") + [
    # Cache-cou de rôdeur + pourpoint de cuir fauve moulé + plastron et baudriers croisés à boucle d'or
    part("limb", (0.36, 0.33, 0.12), (0, -0.01, 1.01), "CapeVerte", "torse",
         bottom=(1.04, 1.04), top=(0.88, 0.88)),
    part("rounded_box", (0.45, 0.31, 0.42), (0, 0, 0.80), "CuirClair", "torse",
         bottom=(0.78, 0.80), mid=(0.96, 0.96), top=(1.06, 1.04), bevel=0.25, power=0.84),
    part("rounded_box", (0.38, 0.32, 0.22), (0, 0.01, 0.86), "Cuir", "torse",
         bottom=(0.85, 0.90), top=(1.04, 1.02), bevel=0.22),
    part("limb", (0.47, 0.33, 0.06), (0, 0.01, 0.80), "BoisSombre", "torse", rot=(0, 30, 0)),
    part("limb", (0.47, 0.33, 0.06), (0, 0.01, 0.80), "BoisSombre", "torse", rot=(0, -30, 0)),
    part("dome", (0.09, 0.06, 0.09), (0, 0.165, 0.81), "Or", "torse", rot=(-90, 0, 0)),
    # Ceinture utilitaire à sacoches latérales + basque de cuir clouté
    part("rounded_box", (0.43, 0.31, 0.17), (0, 0, 0.51), "CuirClair", "hanches",
         top=(0.84, 0.84), bottom=(1.08, 1.05), bevel=0.20, power=0.82),
    part("limb", (0.43, 0.32, 0.09), (0, 0, 0.57), "BoisSombre", "hanches", power=0.82),
    part("rounded_box", (0.11, 0.06, 0.09), (0, 0.16, 0.57), "Or", "hanches", bevel=0.2),
    part("rounded_box", (0.09, 0.14, 0.12), (-0.22, 0.06, 0.54), "Cuir", "hanches", bevel=0.22),
    part("rounded_box", (0.09, 0.14, 0.12), (0.22, -0.05, 0.54), "Cuir", "hanches", bevel=0.22),
    # Épaulette asymétrique : lourde spallière de cuir fauve cloutée d'or à gauche, patte agile à droite
    part("dome", (0.25, 0.35, 0.19), (-0.29, 0, 0.99), "CuirClair", "torse", rot=(0, -22, 0), flare=1.08),
    part("limb", (0.26, 0.36, 0.05), (-0.30, 0, 0.93), "Cuir", "torse", rot=(0, -22, 0)),
    part("dome", (0.08, 0.08, 0.06), (-0.31, 0.10, 1.04), "Or", "torse", rot=(-45, -25, 0)),
    part("dome", (0.19, 0.28, 0.12), (0.28, 0, 0.98), "Cuir", "torse", rot=(0, 22, 0)),
    # Cape courte d'éclaireur vert forêt
    part("cape", (0.46, 0.09, 0.50), (0, -0.19, 0.77), "CapeVerte", "cape", rot=(10, 0, 0)),
    # Épée bâtarde de mercenaire
    part("dome", (0.08, 0.08, 0.08), (0.31, -0.08, 0.53), "Or", "epee", rot=(-90, 0, 0)),
    part("limb", (0.06, 0.18, 0.06), (0.31, 0.01, 0.53), "Cuir", "epee", rot=(90, 0, 0)),
    part("rounded_box", (0.30, 0.06, 0.06), (0.31, 0.11, 0.53), "Or", "epee", bevel=0.2, smooth=False),
    part("blade", (0.13, 0.94, 0.05), (0.31, 0.60, 0.53), "Acier", "epee"),
    # Rondache bombée en bois fauve cerclée de cuir et d'acier
    part("dome", (0.10, 0.44, 0.44), (-0.40, 0.04, 0.66), "CuirClair", "avantbras.L", rot=(0, -90, 0)),
    part("limb", (0.07, 0.45, 0.45), (-0.39, 0.04, 0.66), "Cuir", "avantbras.L", rot=(0, 90, 0)),
    part("dome", (0.08, 0.15, 0.15), (-0.44, 0.04, 0.66), "Acier", "avantbras.L", rot=(0, -90, 0)),
]
for side, s in (("R", 1), ("L", -1)):
    PARTS_CUIR += [
        part("limb", (0.15, 0.15, 0.25), (0.31 * s, 0, 0.86), "CapeVerte", f"bras.{side}",
             top=(1.06, 1.06), bottom=(0.85, 0.85)),
        part("limb", (0.145, 0.145, 0.18), (0.31 * s, 0, 0.66), "Cuir", f"avantbras.{side}",
             top=(1.08, 1.08), bottom=(0.82, 0.82)),
        part("dome", (0.12, 0.13, 0.12), (0.31 * s, 0.01, 0.53), "CuirClair", f"avantbras.{side}", rot=(180, 0, 0)),
        part("limb", (0.17, 0.17, 0.25), (0.12 * s, 0, 0.385), "Pantalon", f"cuisse.{side}",
             top=(1.08, 1.08), bottom=(0.84, 0.84)),
        part("dome", (0.13, 0.10, 0.12), (0.12 * s, 0.06, 0.27), "CuirClair", f"cuisse.{side}", rot=(-90, 0, 0)),
        part("limb", (0.14, 0.14, 0.16), (0.12 * s, 0, 0.21), "Pantalon", f"tibia.{side}",
             top=(1.0, 1.0), bottom=(0.85, 0.85)),
        part("limb", (0.175, 0.185, 0.13), (0.12 * s, 0.0, 0.14), "Cuir", f"tibia.{side}",
             top=(1.14, 1.14), bottom=(0.88, 0.88)),
        part("dome", (0.17, 0.25, 0.11), (0.12 * s, 0.04, 0.055), "CuirClair", f"tibia.{side}", flare=1.05),
    ]


# 3) ENSEMBLE PLATES : Harnois complet de Chevalier, grand heaume à panache, lourdes spallières, grand écu
PARTS_PLATES = [
    # Grand Heaume intégral en acier poli + visière en T sombre + crête d'or + grand panache écarlate
    part("limb", (0.20, 0.20, 0.10), (0, 0, 1.05), "AcierSombre", "tete"),
    part("rounded_box", (0.35, 0.35, 0.34), (0, 0.01, 1.22), "Acier", "tete",
         bottom=(0.88, 0.90), mid=(1.02, 1.02), top=(0.94, 0.94), bevel=0.28, power=0.84),
    part("dome", (0.36, 0.36, 0.18), (0, 0.0, 1.35), "Acier", "tete", flare=1.02),
    part("rounded_box", (0.06, 0.34, 0.09), (0, 0.02, 1.38), "Or", "tete", bevel=0.22),
    # Fente de visière en T + mentonnière blindée
    part("rounded_box", (0.24, 0.04, 0.05), (0, 0.175, 1.24), "Noir", "tete", bevel=0.2),
    part("rounded_box", (0.05, 0.04, 0.15), (0, 0.178, 1.18), "Noir", "tete", bevel=0.2),
    part("limb", (0.35, 0.34, 0.10), (0, 0.02, 1.11), "Or", "tete", power=0.82),
    # Panache / plumet rouge flottant à l'arrière du heaume
    part("dome", (0.14, 0.24, 0.28), (0, -0.16, 1.36), "Cape", "tete", rot=(-45, 0, 0), flare=1.1),
    part("limb", (0.12, 0.16, 0.24), (0, -0.23, 1.22), "Cape", "tete",
         rot=(-30, 0, 0), bottom=(0.35, 0.35), top=(1.0, 1.0)),

    # Cuirasse bombée en acier poli + gorgerin royal doré + plastron gravé
    part("limb", (0.40, 0.36, 0.12), (0, 0.0, 1.01), "Or", "torse",
         bottom=(1.08, 1.08), top=(0.86, 0.88)),
    part("rounded_box", (0.48, 0.34, 0.43), (0, 0.01, 0.80), "Acier", "torse",
         bottom=(0.80, 0.82), mid=(1.02, 1.04), top=(1.10, 1.06), bevel=0.26, power=0.82),
    part("rounded_box", (0.20, 0.36, 0.34), (0, 0.02, 0.82), "Or", "torse",
         bottom=(0.65, 0.90), top=(1.05, 1.02), bevel=0.22),

    # Hanches : tassettes blindées en acier + tabard royal bleu et or
    part("rounded_box", (0.46, 0.34, 0.20), (0, 0, 0.50), "Acier", "hanches",
         top=(0.84, 0.84), bottom=(1.16, 1.10), bevel=0.22, power=0.80),
    part("rounded_box", (0.18, 0.36, 0.24), (0, 0.01, 0.48), "Tunique", "hanches",
         top=(0.85, 0.85), bottom=(1.05, 1.02), bevel=0.18),
    part("limb", (0.45, 0.34, 0.09), (0, 0, 0.58), "Or", "hanches", power=0.82),
    part("dome", (0.14, 0.08, 0.13), (0, 0.175, 0.58), "Or", "hanches", rot=(-90, 0, 0)),

    # Grande cape royale écarlate
    part("cape", (0.54, 0.11, 0.70), (0, -0.21, 0.68), "Cape", "cape", rot=(8, 0, 0)),

    # Grande Épée Royale (Espadon de chevalier)
    part("dome", (0.11, 0.11, 0.11), (0.31, -0.10, 0.53), "Or", "epee", rot=(-90, 0, 0)),
    part("limb", (0.065, 0.19, 0.065), (0.31, 0.01, 0.53), "Cape", "epee", rot=(90, 0, 0)),
    part("rounded_box", (0.38, 0.08, 0.08), (0.31, 0.11, 0.53), "Or", "epee",
         bottom=(0.75, 0.75), top=(1.1, 1.1), bevel=0.22, smooth=False),
    part("blade", (0.16, 1.02, 0.06), (0.31, 0.64, 0.53), "Acier", "epee"),

    # Grand Écu de Tournoi (Pavois royal)
    part("shield", (0.09, 0.48, 0.58), (-0.41, 0.04, 0.65), "Tunique", "avantbras.L"),
    part("rounded_box", (0.10, 0.44, 0.08), (-0.41, 0.04, 0.91), "Or", "avantbras.L", bevel=0.2, smooth=False),
    part("dome", (0.08, 0.18, 0.22), (-0.45, 0.04, 0.67), "Or", "avantbras.L", rot=(0, -90, 0)),
    part("rounded_box", (0.10, 0.12, 0.08), (-0.41, 0.04, 0.40), "Or", "avantbras.L", bevel=0.2, smooth=False),
]
for side, s in (("R", 1), ("L", -1)):
    PARTS_PLATES += [
        # Lourdes spallières de joute à double étage + médaillons d'or
        part("dome", (0.28, 0.38, 0.22), (0.31 * s, 0, 1.00), "Acier", "torse",
             rot=(0, 18 * s, 0), flare=1.12),
        part("limb", (0.29, 0.39, 0.06), (0.32 * s, 0, 0.92), "Or", "torse",
             rot=(0, 18 * s, 0)),
        part("dome", (0.10, 0.10, 0.06), (0.19 * s, 0.15, 0.97), "Or", "torse", rot=(-70, 0, 0)),
        # Bras en acier, canons d'avant-bras et gantelets blindés
        part("limb", (0.165, 0.165, 0.25), (0.31 * s, 0, 0.86), "AcierSombre", f"bras.{side}",
             top=(1.08, 1.08), bottom=(0.90, 0.90)),
        part("limb", (0.16, 0.16, 0.19), (0.31 * s, 0, 0.66), "Acier", f"avantbras.{side}",
             top=(1.12, 1.12), bottom=(0.88, 0.88)),
        part("dome", (0.13, 0.14, 0.13), (0.31 * s, 0.01, 0.53), "Acier", f"avantbras.{side}",
             rot=(180, 0, 0)),
        # Cuissots, genouillères dorées, grèves d'acier et solerets blindés
        part("limb", (0.185, 0.185, 0.25), (0.12 * s, 0, 0.385), "AcierSombre", f"cuisse.{side}",
             top=(1.10, 1.10), bottom=(0.90, 0.90)),
        part("dome", (0.14, 0.11, 0.13), (0.12 * s, 0.07, 0.27), "Or", f"cuisse.{side}", rot=(-90, 0, 0)),
        part("limb", (0.165, 0.165, 0.20), (0.12 * s, 0, 0.18), "Acier", f"tibia.{side}",
             top=(1.08, 1.08), bottom=(0.92, 0.92)),
        part("dome", (0.18, 0.26, 0.12), (0.12 * s, 0.04, 0.055), "Acier", f"tibia.{side}",
             flare=1.08),
    ]

body_tissu = rig.build_mesh(PARTS_TISSU, "Equip_Tissu")
body_cuir = rig.build_mesh(PARTS_CUIR, "Equip_Cuir")
body_plates = rig.build_mesh(PARTS_PLATES, "Equip_Plates")


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

# --------------------------------------------------------------------------- planches de contrôle
# 1) Planche comparative des 3 équipements (lignes : Tissu, Cuir, Plates sur poses clés)
EQUIP_SPEC = [("repos", 20), ("course", 4), ("attaque_1", 3), ("attaque_3", 5)]
equip_rows = []
for b in (body_tissu, body_cuir, body_plates):
    rig.body = b
    r = rig_utils.render_rows(rig, EQUIP_SPEC, target_z=0.64)
    # Concatène les poses clés sur une seule ligne par tenue
    equip_rows.append([cell for row in r for cell in row[:3]])
rig_utils.save_sheet(equip_rows, OUT_EQUIP_SHEET, upscale=4)

# 2) Planche complète d'animations (sur l'armure de Plates)
rig.body = body_plates
SHEET = [("repos", 4), ("course", 2), ("attaque_1", 2), ("attaque_2", 2), ("attaque_3", 2),
         ("esquive", 1), ("touche", 2), ("mort", 2)]
rows = rig_utils.render_rows(rig, SHEET, target_z=0.62)
rig_utils.save_sheet(rows, OUT_SHEET)

# --------------------------------------------------------------------------- export Godot
rig.reset_pose()
gltf_utils.to_principled()
models_dir = os.path.join(ROOT, "assets", "models")
gltf_utils.export_glb(OUT_GLB, [rig.arm, body_tissu, body_cuir, body_plates], animations=True)
gltf_utils.export_glb(os.path.join(models_dir, "hero_tissu.glb"), [rig.arm, body_tissu], animations=True)
gltf_utils.export_glb(os.path.join(models_dir, "hero_cuir.glb"), [rig.arm, body_cuir], animations=True)
gltf_utils.export_glb(os.path.join(models_dir, "hero_plates.glb"), [rig.arm, body_plates], animations=True)

print("RESULT " + json.dumps({
    "bones": len(BONES),
    "sets": {
        "Equip_Tissu": len(body_tissu.data.vertices),
        "Equip_Cuir": len(body_cuir.data.vertices),
        "Equip_Plates": len(body_plates.data.vertices),
    },
    "actions": {a.name: list(a.frame_range) for a in bpy.data.actions},
    "equip_sheet": OUT_EQUIP_SHEET,
}))
