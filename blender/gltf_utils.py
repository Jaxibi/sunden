"""Outils communs d'export glTF vers Godot (utilisés par export_godot.py et rig_hero.py)."""
import bpy


def color_of(mat):
    """Retrouve la couleur d'un matériau généré par generate_example.py : (rgba, émissif)."""
    for n in mat.node_tree.nodes:
        if n.type == "VECT_MATH":
            return tuple(n.inputs[1].default_value) + (1.0,), False
    for n in mat.node_tree.nodes:
        if n.type == "EMISSION":
            return tuple(n.inputs["Color"].default_value), True
    return tuple(mat.diffuse_color), False


def to_principled():
    """Remplace les matériaux toon (nœuds EEVEE, non exportables) par un Principled BSDF de même couleur.
    Godot les reconvertit en shader toon au chargement (scripts/toon_materials.gd)."""
    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        col, emissive = color_of(mat)
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = col
        bsdf.inputs["Roughness"].default_value = 1.0
        if emissive:
            bsdf.inputs["Emission Color"].default_value = col
            bsdf.inputs["Emission Strength"].default_value = 1.0
        nt.links.new(bsdf.outputs[0], out.inputs["Surface"])


def export_glb(path, objects, animations=False):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_apply=not animations,          # ne pas appliquer le modificateur Armature
        export_yup=True, export_lights=False, export_cameras=False,
        export_animations=animations, export_animation_mode="ACTIONS",
        export_force_sampling=True,
    )
