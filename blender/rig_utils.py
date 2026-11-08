"""Outils de rig pour les personnages en blocs (héros et ennemis).

- Rig(name, bones)        : armature ; bones = [(nom, tête, queue, parent), ...]
- rig.build_mesh(parts)   : maillage ; chaque pièce suit un os (ou des poids donnés par une fonction)
- rig.action(name, keys)  : animation ; keys = [(image, rotations, translations?, échelles?), ...]
- render_sheet(...)       : planche de contrôle, une ligne par animation

Les poses sont écrites autour des axes de l'armature (X = droite du personnage, Y = avant, Z = haut),
en degrés, relativement au parent. Le personnage regarde +Y (Blender) = -Z (Godot).
"""
import math
import os
from math import cos, radians, sin, pi

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

FPS = 30
PIXELS_PER_METER = 320.0 / 11.0     # même densité que le jeu


def clean_scene():
    """Garde matériaux, caméra, soleil et réglages de rendu ; supprime le reste et les actions."""
    for o in list(bpy.data.objects):
        if not (o.type == "CAMERA" or (o.type == "LIGHT" and o.data.type == "SUN")):
            bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    bpy.context.scene.render.fps = FPS


class Rig:
    def __init__(self, name, bones):
        scene = bpy.context.scene
        self.arm = bpy.data.objects.new(name, bpy.data.armatures.new(name + "_Squelette"))
        scene.collection.objects.link(self.arm)
        vl = bpy.context.view_layer
        for o in scene.objects:
            if o is not None:
                o.select_set(False)
        vl.objects.active = self.arm
        self.arm.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        ebs = self.arm.data.edit_bones
        for bname, head, tail, parent in bones:
            eb = ebs.new(bname)
            eb.head, eb.tail, eb.roll = head, tail, 0.0
            if parent:
                eb.parent = ebs[parent]
        bpy.ops.object.mode_set(mode="OBJECT")
        self.bone_names = [b[0] for b in bones]
        self.pb = self.arm.pose.bones
        for pb in self.pb:
            pb.rotation_mode = "QUATERNION"
        self.rest = {pb.name: pb.bone.matrix_local.to_quaternion() for pb in self.pb}
        self._last = {}
        self.body = None
        self.bodies = []

    # ------------------------------------------------------------------ maillage
    @staticmethod
    def _ring_prism(bm, rings, matrix, smooth=True):
        """Construit un volume fermé à partir d'une liste d'anneaux [(x, y, z), ...] de même taille."""
        verts = []
        ring_verts = []
        for r in rings:
            rv = [bm.verts.new(matrix @ Vector(pt)) for pt in r]
            verts.extend(rv)
            ring_verts.append(rv)
        n = len(rings[0])
        faces = []
        for r0, r1 in zip(ring_verts[:-1], ring_verts[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append(bm.faces.new((r0[i], r0[j], r1[j], r1[i])))
        # Bouchons bas et haut
        bot_c = sum((v.co for v in ring_verts[0]), Vector()) / n
        top_c = sum((v.co for v in ring_verts[-1]), Vector()) / n
        vb = bm.verts.new(bot_c)
        vt = bm.verts.new(top_c)
        verts.extend([vb, vt])
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((ring_verts[0][j], ring_verts[0][i], vb)))
            faces.append(bm.faces.new((ring_verts[-1][i], ring_verts[-1][j], vt)))
        for f in faces:
            f.smooth = smooth
        return verts, faces

    @classmethod
    def _create_shape(cls, bm, p, matrix):
        shape = p.get("shape", "box")
        smooth = p.get("smooth", shape in ("sphere", "rounded_box", "limb", "dome", "cape"))
        if shape == "sphere":
            res = bmesh.ops.create_uvsphere(bm, u_segments=p.get("segments", 10),
                                            v_segments=p.get("rings", 6), radius=1.0, matrix=matrix)
            verts = res["verts"]
            faces = list({f for v in verts for f in v.link_faces})
            for f in faces:
                f.smooth = smooth
            return verts, faces

        if shape in ("rounded_box", "limb"):
            n = p.get("segments", 10 if shape == "rounded_box" else 8)
            power = p.get("power", 0.68 if shape == "rounded_box" else 0.95)
            bx, by = p.get("bottom", (1.0, 1.0))
            tx, ty = p.get("top", (1.0, 1.0))
            mx, my = p.get("mid", ((bx + tx) * 0.5, (by + ty) * 0.5))
            bev = p.get("bevel", 0.16 if shape == "rounded_box" else 0.10)
            bend_x, bend_y = p.get("bend", (0.0, 0.0))
            profile = [
                (-0.50, bx * (1.0 - bev * 0.9), by * (1.0 - bev * 0.9), 0.0, 0.0),
                (-0.50 + bev * 0.7, bx, by, bend_x * 0.2, bend_y * 0.2),
                (0.00, mx, my, bend_x, bend_y),
                (0.50 - bev * 0.7, tx, ty, bend_x * 0.2, bend_y * 0.2),
                (0.50, tx * (1.0 - bev * 0.9), ty * (1.0 - bev * 0.9), 0.0, 0.0),
            ]
            rings = []
            for z, sx, sy, ox, oy in profile:
                ring = []
                for i in range(n):
                    a = 2.0 * pi * i / n + pi / n
                    ca, sa = cos(a), sin(a)
                    x = 0.5 * sx * math.copysign(abs(ca) ** power, ca) + ox
                    y = 0.5 * sy * math.copysign(abs(sa) ** power, sa) + oy
                    ring.append((x, y, z))
                rings.append(ring)
            return cls._ring_prism(bm, rings, matrix, smooth=smooth)

        if shape == "dome":
            n = p.get("segments", 10)
            power = p.get("power", 0.85)
            flare = p.get("flare", 1.0)
            profile = [
                (-0.50, 0.92 * flare, 0.92 * flare),
                (-0.20, 1.00 * flare, 1.00 * flare),
                (0.15, 0.86, 0.86),
                (0.40, 0.58, 0.58),
                (0.50, 0.22, 0.22),
            ]
            rings = []
            for z, sx, sy in profile:
                ring = []
                for i in range(n):
                    a = 2.0 * pi * i / n + pi / n
                    ca, sa = cos(a), sin(a)
                    x = 0.5 * sx * math.copysign(abs(ca) ** power, ca)
                    y = 0.5 * sy * math.copysign(abs(sa) ** power, sa)
                    ring.append((x, y, z))
                rings.append(ring)
            return cls._ring_prism(bm, rings, matrix, smooth=smooth)

        if shape == "blade":
            # Lame en losange le long de +Y, large et biseautée jusqu'à la pointe
            sections = [
                (-0.50, 0.36, 0.42),
                (-0.15, 0.46, 0.48),
                (0.22, 0.50, 0.42),
                (0.40, 0.26, 0.25),
            ]
            verts = []
            ring_verts = []
            for y, w, t in sections:
                pts = [(-w, y, 0.0), (0.0, y, t), (w, y, 0.0), (0.0, y, -t)]
                rv = [bm.verts.new(matrix @ Vector(pt)) for pt in pts]
                verts.extend(rv)
                ring_verts.append(rv)
            tip = bm.verts.new(matrix @ Vector((0.0, 0.50, 0.0)))
            base = bm.verts.new(matrix @ Vector((0.0, -0.50, 0.0)))
            verts.extend([tip, base])
            faces = []
            for r0, r1 in zip(ring_verts[:-1], ring_verts[1:]):
                for i in range(4):
                    j = (i + 1) % 4
                    faces.append(bm.faces.new((r0[i], r1[i], r1[j], r0[j])))
            for i in range(4):
                j = (i + 1) % 4
                faces.append(bm.faces.new((ring_verts[-1][i], tip, ring_verts[-1][j])))
                faces.append(bm.faces.new((ring_verts[0][j], base, ring_verts[0][i])))
            for f in faces:
                f.smooth = False
            return verts, faces

        if shape == "shield":
            # Écu incurvé (face vers -X sur l'avant-bras gauche), large en haut et pointu en bas
            profile = [
                (-0.50, 0.08, 0.06),
                (-0.32, 0.56, -0.10),
                (-0.05, 0.92, -0.16),
                (0.28, 1.00, -0.14),
                (0.50, 0.86, 0.00),
            ]
            rings = []
            for z, wy, arch_x in profile:
                hw = 0.5 * wy
                rings.append([
                    (-0.50 + arch_x, 0.0, z),
                    (-0.22 + arch_x * 0.5, hw * 0.65, z),
                    (0.15, hw, z),
                    (0.45, hw * 0.75, z),
                    (0.50, 0.0, z),
                    (0.45, -hw * 0.75, z),
                    (0.15, -hw, z),
                    (-0.22 + arch_x * 0.5, -hw * 0.65, z),
                ])
            return cls._ring_prism(bm, rings, matrix, smooth=False)

        if shape == "cape":
            # Cape trapézoïdale plissée, évasée vers le bas et courbée
            profile = [
                (-0.50, 1.15, -0.25),
                (-0.20, 1.02, -0.12),
                (0.15, 0.86, 0.0),
                (0.50, 0.68, 0.08),
            ]
            rings = []
            for z, wx, cy in profile:
                hw = 0.5 * wx
                rings.append([
                    (-hw, cy + 0.18, z),
                    (-hw * 0.5, cy - 0.35, z),
                    (0.0, cy - 0.50, z),
                    (hw * 0.5, cy - 0.35, z),
                    (hw, cy + 0.18, z),
                    (hw * 0.5, cy + 0.45, z),
                    (0.0, cy + 0.30, z),
                    (-hw * 0.5, cy + 0.45, z),
                ])
            return cls._ring_prism(bm, rings, matrix, smooth=True)

        res = bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)
        verts = res["verts"]
        faces = list({f for v in verts for f in v.link_faces})
        return verts, faces

    def build_mesh(self, parts, mesh_name=None):
        """parts : dicts {shape, size, center, mat, bone | weights(co)->{os: poids}, rot?, ...}"""
        mname = mesh_name or (self.arm.name + "_Mesh")
        me = bpy.data.meshes.new(mname)
        body = bpy.data.objects.new(mname, me)
        bpy.context.scene.collection.objects.link(body)
        mat_index = {}
        for p in parts:
            if p["mat"] not in mat_index:
                me.materials.append(bpy.data.materials[p["mat"]])
                mat_index[p["mat"]] = len(me.materials) - 1
        groups = {n: body.vertex_groups.new(name=n).index for n in self.bone_names}

        bm = bmesh.new()
        deform = bm.verts.layers.deform.verify()
        for p in parts:
            rot = Euler([radians(a) for a in p.get("rot", (0, 0, 0))]).to_quaternion()
            m = Matrix.LocRotScale(Vector(p["center"]), rot, Vector(p["size"]))
            verts, faces = self._create_shape(bm, p, m)
            for v in verts:
                weights = p["weights"](v.co) if "weights" in p else {p["bone"]: 1.0}
                for b, w in weights.items():
                    if w > 0.0:
                        v[deform][groups[b]] = w
            for f in faces:
                f.material_index = mat_index[p["mat"]]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        body.parent = self.arm
        body.modifiers.new("Armature", "ARMATURE").object = self.arm
        self.body = body
        self.bodies.append(body)
        return body

    # ------------------------------------------------------------------ poses
    def _local_scale(self, name, s):
        m = self.rest[name].to_matrix()
        out = []
        for i in range(3):
            axis = m.col[i]
            j = max(range(3), key=lambda k: abs(axis[k]))
            out.append(s[j])
        return out

    def key(self, frame, rots, locs=None, scales=None):
        """Pose complète à `frame` : rotations (degrés), translations (m), échelles — axes de l'armature."""
        locs, scales = locs or {}, scales or {}
        for pb in self.pb:
            x, y, z = rots.get(pb.name, (0, 0, 0))
            rest = self.rest[pb.name]
            q = rest.inverted() @ Euler((radians(x), radians(y), radians(z)), "XYZ").to_quaternion() @ rest
            prev = self._last.get(pb.name)
            if prev is not None and prev.dot(q) < 0.0:
                q.negate()                       # continuité : pas de rotation « par le chemin long »
            self._last[pb.name] = q.copy()
            pb.rotation_quaternion = q
            pb.location = rest.inverted() @ Vector(locs.get(pb.name, (0, 0, 0)))
            pb.scale = self._local_scale(pb.name, scales[pb.name]) if pb.name in scales else (1, 1, 1)
            for prop in ("rotation_quaternion", "location", "scale"):
                pb.keyframe_insert(prop, frame=frame)

    def action(self, name, keys):
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        self.arm.animation_data_create()
        self.arm.animation_data.action = act
        self._last.clear()
        for k in keys:
            self.key(*k)
        self.arm.animation_data.action = None
        self.actions = getattr(self, "actions", []) + [name]
        return act

    def reset_pose(self):
        self.arm.animation_data_create()
        self.arm.animation_data.action = None
        for pb in self.pb:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)


# ---------------------------------------------------------------------- planche de contrôle
def render_rows(rig, spec, cell=72, target_z=0.62, yaw_deg=-90.0):
    """Rend les animations `spec` = [(action, pas), ...] ; renvoie une liste de lignes d'images."""
    scene = bpy.context.scene
    hidden = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o is not rig.body and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    cam = scene.camera
    cam.data.ortho_scale = cell / PIXELS_PER_METER
    fwd = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    cam.location = Vector((0, 0, target_z)) - fwd * 30.0
    scene.render.resolution_x = scene.render.resolution_y = cell
    rig.arm.rotation_euler = (0, 0, radians(yaw_deg))
    tmp = os.path.join(bpy.app.tempdir, "frame_rig.png")
    rows = []
    for name, step in spec:
        act = bpy.data.actions[name]
        rig.arm.animation_data.action = act
        start, end = (int(v) for v in act.frame_range)
        cells = []
        for f in range(start, end + 1, step):
            scene.frame_set(f)
            scene.render.filepath = tmp
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(tmp, check_existing=False)
            px = np.empty(cell * cell * 4, dtype=np.float32)
            img.pixels.foreach_get(px)
            bpy.data.images.remove(img)
            cells.append(px.reshape(cell, cell, 4))
        rows.append(cells)
    rig.arm.animation_data.action = None
    rig.arm.rotation_euler = (0, 0, 0)
    for o in hidden:
        o.hide_render = False
    return rows


def save_sheet(rows, path, cell=72, upscale=3):
    cols = max(len(r) for r in rows)
    sheet = np.zeros((len(rows) * cell, cols * cell, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    for ri, cells in enumerate(rows):
        y0 = (len(rows) - 1 - ri) * cell                       # les pixels Blender partent du bas
        for ci, c in enumerate(cells):
            sheet[y0:y0 + cell, ci * cell:(ci + 1) * cell] = c
    big = sheet.repeat(upscale, 0).repeat(upscale, 1)
    out = bpy.data.images.new("planche", big.shape[1], big.shape[0], alpha=True)
    out.pixels.foreach_set(big.ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
