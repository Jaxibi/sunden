"""Exporte le décor et les ennemis de la scène d'exemple en .glb pour Godot.

Usage (depuis E:\\dev\\sunden) :
    D:\\dev\\Blender\\blender.exe -b blender/exemple_hackslash.blend --python blender/export_godot.py

Produit dans assets/models/ :
    level.glb     le décor (sol, ruines, arbres, torches...)
    slime.glb     un slime
    skeleton.glb  un squelette

Le héros animé est produit à part par rig_hero.py (hero.glb).
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gltf_utils  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "assets", "models")
os.makedirs(OUT, exist_ok=True)

FX_PREFIXES = ("Etincelle", "TraineeEpee")


def descendants(obj):
    out = [obj]
    for c in obj.children:
        out += descendants(c)
    return out


def export_character(root_name, file_name):
    root = bpy.data.objects[root_name]
    saved = root.matrix_world.copy()
    root.matrix_world = Matrix.Identity(4)          # centré à l'origine, regard vers +Y Blender = -Z Godot
    bpy.context.view_layer.update()
    objs = descendants(root)
    gltf_utils.export_glb(os.path.join(OUT, file_name), objs)
    root.matrix_world = saved
    return {"file": file_name, "objects": len(objs)}


gltf_utils.to_principled()
report = {}

level_objs = []
for col_name in ("Decor", "SansContour"):
    for o in bpy.data.collections[col_name].objects:
        if o.type == "MESH" and not o.name.startswith(FX_PREFIXES):
            level_objs.append(o)
gltf_utils.export_glb(os.path.join(OUT, "level.glb"), level_objs)
report["level"] = {"file": "level.glb", "objects": len(level_objs)}
report["slime"] = export_character("Slime2", "slime.glb")
report["skeleton"] = export_character("Squelette1", "skeleton.glb")
print("RESULT " + json.dumps(report))
