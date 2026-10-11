"""One-time upgrade of the first catalogue; source/build_models.py includes it."""
from pathlib import Path
import bpy

root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'assets/editable/supermarket.blend'))
scene=bpy.context.scene
model=bpy.data.collections.get('MODEL')
if model is None:
    model=bpy.data.collections.new('MODEL')
    scene.collection.children.link(model)
for material in bpy.data.materials:
    if material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type=='BSDF_PRINCIPLED':
                color=node.inputs['Base Color'].default_value
                color[3]=1
for collection in list(scene.collection.children):
    if collection.name not in ('MODEL','STUDIO'):
        model.children.link(collection)
        scene.collection.children.unlink(collection)
bpy.ops.object.select_all(action='DESELECT')
for obj in model.all_objects:
    obj.select_set(True)
for slug in ('rolls','candy'):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.collections[slug].objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(root/'assets/models'/f'{slug}.glb'),export_format='GLB',
                             use_selection=True,export_cameras=False,export_lights=False)
bpy.ops.object.select_all(action='DESELECT')
for obj in model.all_objects:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(root/'assets/models/supermarket.glb'),export_format='GLB',
                         use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'assets/editable/supermarket.blend'))
