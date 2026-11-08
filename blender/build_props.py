"""Bibliothèque de décors et d'objets du niveau 1, exportée en un seul props.glb.

Usage (depuis E:\\dev\\sunden) :
    D:\\dev\\Blender\\blender.exe -b blender/exemple_hackslash.blend --python blender/build_props.py

Chaque objet est un empty racine « P_<Nom> » à l'origine (base au sol), ses pièces en enfants.
Godot (scripts/level_builder.gd) duplique ces racines pour construire le niveau.
Noms utilisés par le code : P_Piques_Pointes (monte/descend), P_Coffre_Couvercle (s'ouvre),
*_Flamme / *_Coeur (flammes : lumière ajoutée, éteintes sur le brasero jusqu'à l'allumage).
"""
import json
import math
import os
import random
import sys
from math import radians

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gltf_utils  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "models", "props.glb")
random.seed(11)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
COL = bpy.context.scene.collection


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def mat(name, hex_color=None):
    """Matériau existant du fichier d'exemple, ou nouveau matériau de couleur unie."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.diffuse_color = srgb(hex_color)
    return m


M = {
    "pierre": mat("Pierre"), "pierre_sombre": mat("PierreSombre"), "mousse": mat("Mousse"),
    "tronc": mat("Tronc"), "feuille1": mat("Feuillage1"), "feuille2": mat("Feuillage2"),
    "bois": mat("Bois"), "bois_sombre": mat("BoisSombre"), "acier": mat("Acier"), "or": mat("Or"),
    "noir": mat("Noir"), "os": mat("Os"), "flamme": mat("Flamme"), "coeur_flamme": mat("FlammeCoeur"),
    "touffe": mat("TouffeHerbe"),
    "terre_cuite": mat("TerreCuite", "#c4703f"), "fer": mat("Fer", "#5b5664"),
    "coeur": mat("CoeurVie", "#e8434f"), "gemme": mat("Gemme", "#5fd0e8"),
}


def root(name):
    e = bpy.data.objects.new(name, None)
    COL.objects.link(e)
    return e


def prim(kind, name, parent, loc, mat_key, scale=(1, 1, 1), rot=(0, 0, 0), **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(location=loc, rotation=[radians(a) for a in rot], **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(M[mat_key])
    for c in list(o.users_collection):
        c.objects.unlink(o)
    COL.objects.link(o)
    o.parent = parent
    return o


def box(name, parent, size, loc, mat_key, rot=(0, 0, 0)):
    return prim("cube", name, parent, loc, mat_key, scale=size, rot=rot, size=1)


def jitter(o, amount):
    for v in o.data.vertices:
        v.co += Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * amount


# --------------------------------------------------------------------------- nature
r = root("P_Arbre")
prim("cylinder", "P_Arbre_Tronc", r, (0, 0, 0.5), "tronc", vertices=6, radius=0.16, depth=1.0)
prim("cone", "P_Arbre_F1", r, (0, 0, 1.35), "feuille1", rot=(0, 0, 10), vertices=6, radius1=0.95, radius2=0, depth=1.3)
prim("cone", "P_Arbre_F2", r, (0, 0, 2.0), "feuille1", rot=(0, 0, 40), vertices=6, radius1=0.68, radius2=0, depth=1.05)

r = root("P_Arbre2")
prim("cylinder", "P_Arbre2_Tronc", r, (0, 0, 0.6), "tronc", vertices=6, radius=0.18, depth=1.2)
prim("cone", "P_Arbre2_F1", r, (0, 0, 1.5), "feuille2", vertices=6, radius1=1.05, radius2=0, depth=1.4)
prim("cone", "P_Arbre2_F2", r, (0, 0, 2.2), "feuille2", rot=(0, 0, 30), vertices=6, radius1=0.8, radius2=0, depth=1.2)
prim("cone", "P_Arbre2_F3", r, (0, 0, 2.8), "feuille2", rot=(0, 0, 15), vertices=6, radius1=0.5, radius2=0, depth=0.9)

r = root("P_Rocher")
o = prim("ico_sphere", "P_Rocher_A", r, (0, 0, 0.18), "pierre", scale=(1, 1, 0.7), subdivisions=1, radius=0.45)
jitter(o, 0.08)
o = prim("ico_sphere", "P_Rocher_B", r, (0.32, 0.18, 0.1), "pierre_sombre", scale=(1, 1, 0.7), subdivisions=1, radius=0.24)
jitter(o, 0.05)

r = root("P_Touffe")
prim("cone", "P_Touffe_A", r, (0, 0, 0.09), "touffe", vertices=3, radius1=0.12, radius2=0, depth=0.18)
prim("cone", "P_Touffe_B", r, (0.09, 0.05, 0.07), "touffe", rot=(0, 0, 50), vertices=3, radius1=0.09, radius2=0, depth=0.14)

# --------------------------------------------------------------------------- architecture
r = root("P_Pilier")
box("P_Pilier_Base", r, (0.9, 0.9, 0.25), (0, 0, 0.125), "pierre_sombre")
prim("cylinder", "P_Pilier_Fut", r, (0, 0, 1.25), "pierre", vertices=8, radius=0.32, depth=2.0)
box("P_Pilier_Chapiteau", r, (0.8, 0.8, 0.2), (0, 0, 2.35), "pierre_sombre")
box("P_Pilier_Mousse", r, (0.82, 0.3, 0.08), (0, 0.25, 2.47), "mousse")

r = root("P_PilierBrise")
box("P_PilierBrise_Base", r, (0.9, 0.9, 0.25), (0, 0, 0.125), "pierre_sombre")
o = prim("cylinder", "P_PilierBrise_Fut", r, (0, 0, 0.6), "pierre", vertices=8, radius=0.32, depth=0.7)
box("P_PilierBrise_Eclat", r, (0.3, 0.25, 0.2), (0.35, -0.3, 0.1), "pierre", rot=(0, 0, 25))

r = root("P_Torche")
prim("cylinder", "P_Torche_Pied", r, (0, 0, 0.6), "bois_sombre", vertices=6, radius=0.06, depth=1.2)
box("P_Torche_Coupe", r, (0.22, 0.22, 0.12), (0, 0, 1.22), "fer")
box("P_Torche_Flamme", r, (0.18, 0.18, 0.26), (0, 0, 1.38), "flamme")
box("P_Torche_Coeur", r, (0.09, 0.09, 0.15), (0, 0, 1.42), "coeur_flamme", rot=(0, 0, 45))

r = root("P_Stele")
box("P_Stele_Pierre", r, (0.55, 0.22, 0.9), (0, 0, 0.45), "pierre")
box("P_Stele_Sommet", r, (0.45, 0.2, 0.12), (0, 0, 0.96), "pierre_sombre")
box("P_Stele_Mousse", r, (0.57, 0.12, 0.1), (0, -0.06, 0.88), "mousse")
for i in range(3):
    box(f"P_Stele_Ligne{i}", r, (0.32 - 0.06 * i, 0.02, 0.04), (0, 0.115, 0.68 - 0.13 * i), "noir")

r = root("P_Ossements")
box("P_Ossements_Crane", r, (0.2, 0.18, 0.17), (0, 0, 0.085), "os", rot=(0, 0, 20))
box("P_Ossements_Orbite1", r, (0.05, 0.02, 0.05), (0.02, 0.09, 0.1), "noir", rot=(0, 0, 20))
for i in range(3):
    box(f"P_Ossements_Os{i}", r, (0.05, 0.34, 0.05), (0.2 - 0.12 * i, -0.15 + 0.1 * i, 0.025), "os",
        rot=(0, 0, random.uniform(-70, 70)))

# --------------------------------------------------------------------------- objets de jeu
r = root("P_Jarre")
prim("uv_sphere", "P_Jarre_Panse", r, (0, 0, 0.2), "terre_cuite", scale=(1, 1, 0.85), segments=8, ring_count=5, radius=0.24)
prim("cylinder", "P_Jarre_Col", r, (0, 0, 0.43), "terre_cuite", vertices=8, radius=0.12, depth=0.12)
prim("cylinder", "P_Jarre_Bord", r, (0, 0, 0.5), "bois_sombre", vertices=8, radius=0.15, depth=0.04)

r = root("P_Caisse")
box("P_Caisse_Corps", r, (0.6, 0.6, 0.6), (0, 0, 0.3), "bois")
box("P_Caisse_Cerclage1", r, (0.62, 0.62, 0.08), (0, 0, 0.12), "bois_sombre")
box("P_Caisse_Cerclage2", r, (0.62, 0.62, 0.08), (0, 0, 0.48), "bois_sombre")

r = root("P_Coeur")
prim("uv_sphere", "P_Coeur_G", r, (-0.07, 0, 0.2), "coeur", segments=8, ring_count=5, radius=0.1)
prim("uv_sphere", "P_Coeur_D", r, (0.07, 0, 0.2), "coeur", segments=8, ring_count=5, radius=0.1)
prim("cone", "P_Coeur_Pointe", r, (0, 0, 0.1), "coeur", rot=(180, 0, 0), vertices=8, radius1=0.16, radius2=0, depth=0.18)

r = root("P_Brasero")
box("P_Brasero_Socle", r, (0.55, 0.55, 0.1), (0, 0, 0.05), "pierre_sombre")
prim("cylinder", "P_Brasero_Pied", r, (0, 0, 0.32), "pierre", vertices=8, radius=0.13, depth=0.45)
prim("cylinder", "P_Brasero_Vasque", r, (0, 0, 0.6), "fer", vertices=8, radius=0.38, depth=0.18)
box("P_Brasero_Braises", r, (0.5, 0.5, 0.06), (0, 0, 0.7), "noir")
box("P_Brasero_Flamme", r, (0.32, 0.32, 0.38), (0, 0, 0.9), "flamme")
box("P_Brasero_Coeur", r, (0.16, 0.16, 0.22), (0, 0, 0.92), "coeur_flamme", rot=(0, 0, 45))

r = root("P_Herse")                                       # une case de large, le long de X
for i, x in enumerate((-0.36, -0.12, 0.12, 0.36)):
    box(f"P_Herse_Barreau{i}", r, (0.07, 0.07, 1.7), (x, 0, 0.85), "fer")
    prim("cone", f"P_Herse_Pointe{i}", r, (x, 0, -0.06), "fer", rot=(180, 0, 0), vertices=4, radius1=0.06, radius2=0, depth=0.12)
box("P_Herse_Traverse1", r, (1.0, 0.07, 0.07), (0, 0, 0.55), "fer")
box("P_Herse_Traverse2", r, (1.0, 0.07, 0.07), (0, 0, 1.45), "fer")

r = root("P_Piques")
box("P_Piques_Plaque", r, (0.96, 0.96, 0.06), (0, 0, 0.03), "pierre_sombre")
pointes = bpy.data.objects.new("P_Piques_Pointes", None)
COL.objects.link(pointes)
pointes.parent = r
for i in range(3):
    for j in range(3):
        x, y = (i - 1) * 0.3, (j - 1) * 0.3
        box(f"P_Piques_Trou{i}{j}", r, (0.1, 0.1, 0.01), (x, y, 0.065), "noir")
        prim("cone", f"P_Piques_Pique{i}{j}", pointes, (x, y, 0.17), "acier", vertices=4, radius1=0.06, radius2=0, depth=0.34)

r = root("P_Coffre")
box("P_Coffre_Corps", r, (0.8, 0.5, 0.42), (0, 0, 0.21), "bois")
box("P_Coffre_Bande1", r, (0.08, 0.52, 0.44), (-0.28, 0, 0.21), "or")
box("P_Coffre_Bande2", r, (0.08, 0.52, 0.44), (0.28, 0, 0.21), "or")
couvercle = bpy.data.objects.new("P_Coffre_Couvercle", None)    # charnière à l'arrière
COL.objects.link(couvercle)
couvercle.parent = r
couvercle.location = (0, -0.25, 0.42)
box("P_Coffre_Toit", couvercle, (0.82, 0.52, 0.16), (0, 0.26, 0.08), "bois")
box("P_Coffre_ToitBande", couvercle, (0.86, 0.06, 0.18), (0, 0.52, 0.08), "or")
box("P_Coffre_Serrure", r, (0.12, 0.05, 0.14), (0, 0.27, 0.36), "or")

r = root("P_Couronne")                                    # posée sur le Roi Gluant
prim("cylinder", "P_Couronne_Bandeau", r, (0, 0, 0.07), "or", vertices=10, radius=0.42, depth=0.14)
for i in range(6):
    a = i * math.tau / 6
    prim("cone", f"P_Couronne_Fleuron{i}", r, (math.cos(a) * 0.38, math.sin(a) * 0.38, 0.25), "or",
         vertices=4, radius1=0.09, radius2=0, depth=0.24)
prim("uv_sphere", "P_Couronne_Gemme", r, (0, 0.42, 0.08), "gemme", segments=6, ring_count=4, radius=0.08)

# --------------------------------------------------------------------------- export
roots = [o for o in bpy.data.objects if o.parent is None]
everything = list(bpy.data.objects)
gltf_utils.to_principled()
gltf_utils.export_glb(OUT, everything)
print("RESULT " + json.dumps({"props": sorted(o.name for o in roots), "objects": len(everything)}))
