"""Scène d'exemple « hack & slash en 3D pixel art », générée et rendue sans interface.

Usage (depuis E:\\dev\\sunden) :
    D:\\dev\\Blender\\blender.exe -b --factory-startup --python blender/generate_example.py

Produit :
    blender/exemple_hackslash.blend   la scène, modifiable dans Blender
    renders/exemple_lowres.png        le rendu natif (basse résolution)
    renders/exemple_x4.png            le même agrandi x4 au plus proche voisin (rendu « pixel art »)
"""
import json
import math
import os
import random
from math import radians

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Vector

# --------------------------------------------------------------------------- réglages
try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = r"E:\dev\sunden"
OUT_BLEND = os.path.join(ROOT, "blender", "exemple_hackslash.blend")
OUT_DIR = os.path.join(ROOT, "renders")
RES_X, RES_Y, UPSCALE = 320, 180, 4      # rendu natif 320x180, affiché x4 = 1280x720
ORTHO_SCALE = 11.0                        # largeur visible en mètres -> ~29 px par mètre
CAM_PITCH, CAM_YAW = 55.0, 45.0           # vue plongeante 3/4, axe isométrique
random.seed(7)

os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Orientation caméra, utile pour placer les éléments par rapport à l'écran
CAM_ROT = Euler((radians(CAM_PITCH), 0.0, radians(CAM_YAW)))
R = CAM_ROT.to_matrix()
SCREEN_RIGHT = (R @ Vector((1, 0, 0))).normalized()
_fwd = R @ Vector((0, 0, -1))
SCREEN_FAR = Vector((_fwd.x, _fwd.y, 0)).normalized()     # « vers le haut de l'écran » au sol


# --------------------------------------------------------------------------- collections
def make_collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


COL_DECOR = make_collection("Decor")
COL_PERSOS = make_collection("Personnages")
COL_NOLINE = make_collection("SansContour")   # effets, herbe : exclus du contour Freestyle


# --------------------------------------------------------------------------- matériaux
def srgb(hex_color):
    h = hex_color.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


# Paliers de lumière du shader toon : ombre teintée violet, mi-ombre, lumière, point chaud
TOON_STEPS = [(0.00, "#6f679e"), (0.10, "#b9b3d1"), (0.42, "#ffffff"), (1.30, "#fff1d6")]
_mats = {}


def toon(name, color):
    """Ombrage toon : diffuse -> Shader to RGB -> rampe constante -> x couleur -> émission."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    mul = nt.nodes.new("ShaderNodeVectorMath")
    emi = nt.nodes.new("ShaderNodeEmission")

    # la rampe va de 0 à 1 : on divise l'entrée par le dernier palier pour garder le point chaud
    top = TOON_STEPS[-1][0]
    ramp_in = nt.nodes.new("ShaderNodeMath")
    ramp_in.operation = "DIVIDE"
    ramp_in.inputs[1].default_value = top
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    cr.elements[0].position, cr.elements[0].color = 0.0, srgb(TOON_STEPS[0][1])
    cr.elements[1].position, cr.elements[1].color = 1.0, srgb(TOON_STEPS[-1][1])
    for pos, col in TOON_STEPS[1:-1]:
        cr.elements.new(pos / top).color = srgb(col)

    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = srgb(color)[:3]
    emi.inputs["Strength"].default_value = 1.0

    nt.links.new(diff.outputs[0], s2r.inputs[0])
    nt.links.new(s2r.outputs[0], ramp_in.inputs[0])
    nt.links.new(ramp_in.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], emi.inputs["Color"])
    nt.links.new(emi.outputs[0], out.inputs["Surface"])
    m.diffuse_color = srgb(color)
    _mats[name] = m
    return m


def glow(name, color, strength=1.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Color"].default_value = srgb(color)
    emi.inputs["Strength"].default_value = strength
    nt.links.new(emi.outputs[0], out.inputs["Surface"])
    _mats[name] = m
    return m


M = {
    "herbe1": toon("Herbe1", "#5fa84a"), "herbe2": toon("Herbe2", "#63ad4d"),
    "herbe3": toon("Herbe3", "#5aa346"), "terre": toon("Terre", "#9a7650"),
    "dalle1": toon("Dalle1", "#a7a3a8"), "dalle2": toon("Dalle2", "#94909a"),
    "pierre": toon("Pierre", "#8d8a96"), "pierre_sombre": toon("PierreSombre", "#6c6875"),
    "mousse": toon("Mousse", "#4e8a3c"), "tronc": toon("Tronc", "#6b4a32"),
    "feuille1": toon("Feuillage1", "#3f8f45"), "feuille2": toon("Feuillage2", "#4fa04a"),
    "bois": toon("Bois", "#a0703f"), "bois_sombre": toon("BoisSombre", "#6e4a2b"),
    "peau": toon("Peau", "#f0c19a"), "cheveux": toon("Cheveux", "#e0702e"),
    "tunique": toon("Tunique", "#3d6fb8"), "acier": toon("Acier", "#c9d2dc"),
    "pantalon": toon("Pantalon", "#3a3a52"), "cuir": toon("Cuir", "#7a4e2d"),
    "cape": toon("Cape", "#c23a3a"), "or": toon("Or", "#e8b83a"),
    "noir": toon("Noir", "#1c1a24"), "slime": toon("Slime", "#7fd35a"),
    "os": toon("Os", "#e6dfc8"), "rouille": toon("Rouille", "#9b5a3a"),
    "herbe_touffe": toon("TouffeHerbe", "#86c95e"),
    "flash": glow("FlashImpact", "#ffffff"), "slash": glow("TraineeEpee", "#e9fbff"),
    "etincelle": glow("Etincelle", "#ffe066"), "flamme": glow("Flamme", "#ff8a2a"),
    "flamme_coeur": glow("FlammeCoeur", "#fff27a"),
}


# --------------------------------------------------------------------------- formes
def _relink(o, col):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)


def prim(kind, name, loc, scale=(1, 1, 1), rot=(0, 0, 0), mat=None, col=COL_DECOR, parent=None, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if mat:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    _relink(o, col)
    return o


def box(name, size, loc, mat, **kw):
    return prim("cube", name, loc, scale=size, mat=mat, size=1, **kw)


def empty(name, loc, rot_z=0.0, col=COL_PERSOS, parent=None):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    e.rotation_euler = (0, 0, rot_z)
    e.parent = parent
    col.objects.link(e)
    return e


def jitter(o, amount):
    for v in o.data.vertices:
        v.co += Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * amount


def facing(direction):
    """Angle Z pour qu'un objet dont l'avant est +Y regarde dans `direction`."""
    return math.atan2(-direction.x, direction.y)


# --------------------------------------------------------------------------- sol
def build_ground():
    me = bpy.data.meshes.new("Sol")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=28, y_segments=28, size=14)
    bm.to_mesh(me)
    bm.free()
    names = ["herbe1", "herbe2", "herbe3", "terre", "dalle1", "dalle2"]
    for n in names:
        me.materials.append(M[n])
    near = -SCREEN_FAR
    for p in me.polygons:
        c = p.center
        along = c.x * near.x + c.y * near.y
        across = abs(c.x * SCREEN_RIGHT.x + c.y * SCREEN_RIGHT.y)
        if c.length < 3.4:
            idx = random.choice([4, 4, 5])                       # dalles de l'arène
        elif along > 0 and across < 1.0 + 0.4 * random.random():
            idx = random.choice([3, 3, 4])                       # chemin vers la caméra
        else:
            idx = random.choices([0, 1, 2, 3], weights=[5, 3, 3, 0.4])[0]
        p.material_index = idx
    o = bpy.data.objects.new("Sol", me)
    COL_DECOR.objects.link(o)
    return o


# --------------------------------------------------------------------------- personnages
def build_hero(pos, look_dir):
    h = empty("Heros", pos, facing(look_dir))
    P = dict(col=COL_PERSOS, parent=h)
    for s in (-1, 1):
        box(f"Botte{s}", (0.17, 0.22, 0.12), (0.12 * s, 0.02, 0.06), M["cuir"], **P)
        box(f"Jambe{s}", (0.15, 0.15, 0.38), (0.12 * s, 0.0, 0.31), M["pantalon"], **P)
        box(f"Epaulette{s}", (0.2, 0.34, 0.12), (0.3 * s, 0.0, 1.0), M["acier"], **P)
    box("Torse", (0.46, 0.3, 0.48), (0, 0, 0.76), M["tunique"], **P)
    box("Ceinture", (0.48, 0.32, 0.08), (0, 0, 0.55), M["cuir"], **P)
    box("Boucle", (0.1, 0.04, 0.08), (0, 0.17, 0.55), M["or"], **P)
    box("Tete", (0.32, 0.3, 0.32), (0, 0.01, 1.2), M["peau"], **P)
    box("Cheveux", (0.35, 0.33, 0.12), (0, -0.01, 1.38), M["cheveux"], **P)
    box("CheveuxArriere", (0.35, 0.1, 0.24), (0, -0.14, 1.26), M["cheveux"], **P)
    for s in (-1, 1):
        box(f"Oeil{s}", (0.05, 0.02, 0.07), (0.07 * s, 0.165, 1.2), M["noir"], **P)
    box("Cape", (0.48, 0.05, 0.78), (0, -0.21, 0.7), M["cape"], rot=(radians(18), 0, 0), **P)
    # bras droit tendu, épée en fin de coup
    box("BrasDroit", (0.13, 0.42, 0.13), (0.3, 0.2, 0.95), M["tunique"], rot=(0, 0, radians(-25)), **P)
    sword = empty("Epee", (0.42, 0.42, 0.95), radians(-55), parent=h)
    S = dict(col=COL_PERSOS, parent=sword)
    box("Poignee", (0.05, 0.18, 0.05), (0, 0, 0), M["cuir"], **S)
    box("Garde", (0.3, 0.05, 0.05), (0, 0.1, 0), M["or"], **S)
    box("Lame", (0.08, 0.95, 0.025), (0, 0.6, 0), M["acier"], **S)
    # bras gauche et bouclier
    box("BrasGauche", (0.13, 0.13, 0.4), (-0.32, 0.05, 0.82), M["tunique"], **P)
    box("Bouclier", (0.42, 0.06, 0.5), (-0.36, 0.2, 0.82), M["tunique"], rot=(0, 0, radians(25)), **P)
    box("BouclierBosse", (0.12, 0.05, 0.12), (-0.38, 0.24, 0.82), M["or"], rot=(0, 0, radians(25)), **P)
    build_slash_arc(h)
    return h


def build_slash_arc(hero):
    """Traînée d'épée : ruban en arc, épais côté lame, effilé vers la fin."""
    me = bpy.data.meshes.new("TraineeEpee")
    bm = bmesh.new()
    n = 12
    rows = []
    for i in range(n + 1):
        t = i / n
        a = radians(38 + 115 * t)
        r_out = 1.55 - 0.1 * t
        r_in = r_out - 0.55 * (1 - t) ** 1.3 - 0.03
        z = 0.95 + 0.12 * t
        rows.append((bm.verts.new((math.cos(a) * r_in, math.sin(a) * r_in, z)),
                     bm.verts.new((math.cos(a) * r_out, math.sin(a) * r_out, z))))
    for (a0, b0), (a1, b1) in zip(rows, rows[1:]):
        bm.faces.new((a0, b0, b1, a1))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["slash"])
    o = bpy.data.objects.new("TraineeEpee", me)
    o.parent = hero
    COL_NOLINE.objects.link(o)


def build_slime(name, pos, look_at, hit=False):
    d = (look_at - pos)
    root = empty(name, pos, facing(Vector((d.x, d.y, 0))))
    tilt = (radians(-20), 0, 0) if hit else (0, 0, 0)
    prim("uv_sphere", f"{name}_Corps", (0, 0, 0.3), scale=(0.5, 0.5, 0.36), rot=tilt,
         mat=M["flash"] if hit else M["slime"], col=COL_PERSOS, parent=root,
         segments=8, ring_count=5, radius=1.0)
    if not hit:
        for s in (-1, 1):
            box(f"{name}_Oeil{s}", (0.07, 0.04, 0.12), (0.15 * s, 0.44, 0.36), M["noir"],
                col=COL_PERSOS, parent=root)
    return root


def build_skeleton(name, pos, look_at):
    d = (look_at - pos)
    r = empty(name, pos, facing(Vector((d.x, d.y, 0))))
    P = dict(col=COL_PERSOS, parent=r)
    for s in (-1, 1):
        box(f"{name}_Jambe{s}", (0.08, 0.08, 0.5), (0.11 * s, 0, 0.25), M["os"], **P)
        box(f"{name}_Bras{s}", (0.07, 0.07, 0.42), (0.27 * s, 0.05, 0.82), M["os"], **P)
    box(f"{name}_Bassin", (0.32, 0.16, 0.1), (0, 0, 0.52), M["os"], **P)
    box(f"{name}_Colonne", (0.07, 0.07, 0.3), (0, 0, 0.7), M["os"], **P)
    for k in range(3):
        box(f"{name}_Cote{k}", (0.38 - 0.05 * k, 0.2, 0.05), (0, 0, 0.98 - 0.1 * k), M["os"], **P)
    box(f"{name}_Crane", (0.3, 0.28, 0.28), (0, 0.02, 1.25), M["os"], **P)
    for s in (-1, 1):
        box(f"{name}_Orbite{s}", (0.08, 0.03, 0.08), (0.07 * s, 0.16, 1.27), M["noir"], **P)
    box(f"{name}_Epee", (0.06, 0.06, 0.8), (0.3, 0.25, 0.85), M["rouille"],
        rot=(radians(60), 0, 0), **P)
    return r


def build_sparks(center, count=10):
    for i in range(count):
        a = random.uniform(0, 2 * math.pi)
        r = random.uniform(0.35, 0.85)
        off = Vector((math.cos(a) * r, math.sin(a) * r, random.uniform(0.15, 0.95)))
        s = random.choice([0.07, 0.09, 0.12])
        box(f"Etincelle{i}", (s, s, s), center + off, random.choice([M["etincelle"], M["flash"]]),
            col=COL_NOLINE)


# --------------------------------------------------------------------------- décor
def build_tree(i, pos, k):
    prim("cylinder", f"Arbre{i}_Tronc", pos + Vector((0, 0, 0.5 * k)), scale=(k, k, k),
         mat=M["tronc"], vertices=6, radius=0.16, depth=1.0)
    leaf = random.choice([M["feuille1"], M["feuille2"]])
    prim("cone", f"Arbre{i}_Feuilles1", pos + Vector((0, 0, 1.35 * k)), scale=(k, k, k),
         rot=(0, 0, random.random()), mat=leaf, vertices=6, radius1=0.95, radius2=0, depth=1.3)
    prim("cone", f"Arbre{i}_Feuilles2", pos + Vector((0, 0, 2.0 * k)), scale=(k, k, k),
         rot=(0, 0, random.random()), mat=leaf, vertices=6, radius1=0.68, radius2=0, depth=1.05)


def build_rock(i, pos, r):
    o = prim("ico_sphere", f"Rocher{i}", pos + Vector((0, 0, r * 0.35)), scale=(1, 1, 0.7),
             rot=(0, 0, random.random() * 6), mat=random.choice([M["pierre"], M["pierre_sombre"]]),
             subdivisions=1, radius=r)
    jitter(o, r * 0.18)


def build_pillar(i, pos, height, broken=False):
    box(f"Pilier{i}_Base", (0.9, 0.9, 0.25), pos + Vector((0, 0, 0.125)), M["pierre_sombre"])
    if broken:
        prim("cylinder", f"Pilier{i}_Tombe", pos + Vector((0.2, 1.1, 0.33)),
             rot=(radians(90), 0, radians(20)), mat=M["pierre"], vertices=8, radius=0.32, depth=1.8)
        height = 0.6
    prim("cylinder", f"Pilier{i}_Fut", pos + Vector((0, 0, 0.25 + height / 2)), mat=M["pierre"],
         vertices=8, radius=0.32, depth=height)
    if not broken:
        box(f"Pilier{i}_Chapiteau", (0.8, 0.8, 0.2), pos + Vector((0, 0, 0.35 + height)), M["pierre_sombre"])
        box(f"Pilier{i}_Mousse", (0.82, 0.3, 0.08), pos + Vector((0.0, 0.25, 0.47 + height)), M["mousse"])


def build_torch(i, pos):
    prim("cylinder", f"Torche{i}_Pied", pos + Vector((0, 0, 0.6)), mat=M["bois_sombre"],
         vertices=6, radius=0.06, depth=1.2)
    box(f"Torche{i}_Coupe", (0.22, 0.22, 0.12), pos + Vector((0, 0, 1.22)), M["bois_sombre"])
    box(f"Torche{i}_Flamme", (0.18, 0.18, 0.26), pos + Vector((0, 0, 1.38)), M["flamme"], col=COL_NOLINE)
    box(f"Torche{i}_Coeur", (0.09, 0.09, 0.15), pos + Vector((0, 0, 1.42)), M["flamme_coeur"],
        col=COL_NOLINE, rot=(0, 0, radians(45)))
    ld = bpy.data.lights.new(f"Torche{i}_Lumiere", "POINT")
    ld.energy = 140
    ld.color = (1.0, 0.62, 0.3)
    ld.shadow_soft_size = 0.0
    lo = bpy.data.objects.new(f"Torche{i}_Lumiere", ld)
    lo.location = pos + Vector((0, 0, 1.7))
    COL_DECOR.objects.link(lo)


def build_decor():
    build_ground()
    far, right = SCREEN_FAR, SCREEN_RIGHT
    # mur en ruine au fond de l'arène
    for k in range(-5, 6):
        h = random.choice([0.6, 0.9, 1.2, 1.5, 0.4]) if abs(k) > 1 else random.choice([0.3, 0.5])
        p = far * 5.4 + right * (k * 0.95)
        box(f"Mur{k}", (0.95, 0.6, h), Vector((p.x, p.y, h / 2)), M["pierre"],
            rot=(0, 0, facing(far)))
        if random.random() < 0.4:
            box(f"Mur{k}_Mousse", (0.97, 0.3, 0.08), Vector((p.x, p.y, h + 0.03)), M["mousse"],
                rot=(0, 0, facing(far)))
    # piliers aux quatre coins de l'arène
    for i, a in enumerate((45, 135, 225, 315)):
        p = Vector((math.cos(radians(a + 45)), math.sin(radians(a + 45)), 0)) * 4.0
        build_pillar(i, p, random.uniform(1.6, 2.4), broken=(i == 2))
    # torches près des piliers du fond
    build_torch(0, far * 3.3 + right * 2.2)
    build_torch(1, far * 3.3 - right * 2.2)
    # arbres et rochers autour
    placed = 0
    while placed < 22:
        p = Vector((random.uniform(-12, 12), random.uniform(-12, 12), 0))
        if p.length < 6.0:
            continue
        build_tree(placed, p, random.uniform(0.85, 1.35))
        placed += 1
    for i in range(14):
        a = random.uniform(0, 2 * math.pi)
        d = random.uniform(3.6, 9.0)
        build_rock(i, Vector((math.cos(a) * d, math.sin(a) * d, 0)), random.uniform(0.2, 0.5))
    # caisses au bord du chemin
    for i, off in enumerate((1.6, 2.1)):
        p = -far * 4.5 + right * off + far * (0.6 * i)
        box(f"Caisse{i}", (0.6, 0.6, 0.6), Vector((p.x, p.y, 0.3 + 0.6 * i * 0)), M["bois"],
            rot=(0, 0, radians(15 * i)))
        box(f"Caisse{i}_Cerclage", (0.62, 0.62, 0.08), Vector((p.x, p.y, 0.3)), M["bois_sombre"],
            rot=(0, 0, radians(15 * i)))
    # touffes d'herbe (sans contour pour ne pas bruiter l'image)
    for i in range(90):
        p = Vector((random.uniform(-11, 11), random.uniform(-11, 11), 0))
        if p.length < 3.6:
            continue
        prim("cone", f"Touffe{i}", p + Vector((0, 0, 0.09)), rot=(0, 0, random.random() * 3),
             mat=M["herbe_touffe"], col=COL_NOLINE, vertices=3, radius1=0.12, radius2=0, depth=0.18)


# --------------------------------------------------------------------------- caméra, lumière, rendu
def build_camera(target):
    cd = bpy.data.cameras.new("Camera")
    cd.type = "ORTHO"
    cd.ortho_scale = ORTHO_SCALE
    cd.clip_start, cd.clip_end = 0.1, 100.0
    cam = bpy.data.objects.new("Camera", cd)
    cam.rotation_euler = CAM_ROT
    scene.collection.objects.link(cam)
    scene.camera = cam
    desired = target - (R @ Vector((0, 0, -1))) * 30.0
    # alignement sur la grille de pixels (même principe que le script Godot)
    texel = ORTHO_SCALE / RES_X
    local = R.transposed() @ desired
    local.x = round(local.x / texel) * texel
    local.y = round(local.y / texel) * texel
    cam.location = R @ local
    return cam


def build_lights():
    sd = bpy.data.lights.new("Soleil", "SUN")
    sd.energy = 3.2
    sd.angle = 0.0
    sun = bpy.data.objects.new("Soleil", sd)
    sun.rotation_euler = Euler((radians(42), 0, radians(160)))   # vient de l'avant-gauche de la caméra
    scene.collection.objects.link(sun)
    w = bpy.data.worlds.new("Ciel")
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = w.node_tree.nodes.get("Background") or w.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = srgb("#3c4a72")
    bg.inputs["Strength"].default_value = 0.6
    scene.world = w


def setup_render():
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = RES_X, RES_Y, 100
    r.filter_size = 0.0                       # pas d'anti-crénelage : pixels nets
    r.film_transparent = False
    r.image_settings.file_format = "PNG"
    scene.eevee.taa_render_samples = 1
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    # contour d'un pixel via Freestyle
    r.use_freestyle = True
    r.line_thickness_mode = "ABSOLUTE"
    r.line_thickness = 1.0
    vl = scene.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("Contour")
    ls.select_by_collection = True
    ls.collection = COL_NOLINE
    ls.collection_negation = "EXCLUSIVE"
    ls.select_silhouette = True
    ls.select_border = False
    ls.select_crease = True
    ls.linestyle.color = srgb("#1f1830")[:3]
    ls.linestyle.thickness = 1.0


def upscale_nearest(src, dst, factor):
    img = bpy.data.images.load(src)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    big = px.reshape(h, w, 4).repeat(factor, 0).repeat(factor, 1)
    out = bpy.data.images.new("x4", w * factor, h * factor, alpha=True)
    out.pixels.foreach_set(big.ravel())
    out.filepath_raw = dst
    out.file_format = "PNG"
    out.save()


# --------------------------------------------------------------------------- assemblage
hero_pos = -SCREEN_RIGHT * 0.9
hit_pos = hero_pos + SCREEN_RIGHT * 2.0 + SCREEN_FAR * 0.3
build_decor()
build_hero(hero_pos, hit_pos - hero_pos)
build_slime("SlimeTouche", hit_pos, hero_pos, hit=True)
build_sparks(hit_pos + Vector((0, 0, 0.1)))
build_slime("Slime2", hero_pos + SCREEN_RIGHT * 2.6 + SCREEN_FAR * 2.1, hero_pos)
build_slime("Slime3", hero_pos + SCREEN_RIGHT * 3.3 - SCREEN_FAR * 1.2, hero_pos)
build_skeleton("Squelette1", hero_pos - SCREEN_RIGHT * 1.9 + SCREEN_FAR * 1.6, hero_pos)
build_skeleton("Squelette2", hero_pos + SCREEN_RIGHT * 1.0 + SCREEN_FAR * 3.0, hero_pos)
build_camera(Vector((0, 0, 0.6)))
build_lights()
setup_render()

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

low = os.path.join(OUT_DIR, "exemple_lowres.png")
big = os.path.join(OUT_DIR, "exemple_x4.png")
scene.render.filepath = low
bpy.ops.render.render(write_still=True)
upscale_nearest(low, big, UPSCALE)

print("RESULT " + json.dumps({
    "engine": scene.render.engine,
    "objects": len(bpy.data.objects),
    "blend": OUT_BLEND, "lowres": low, "upscaled": big,
}))
