"""Independent Blender process: import each delivered GLB and inspect actual meshes."""
from pathlib import Path
import json
import math
import re
import bpy
from mathutils import Vector

root=Path(__file__).resolve().parents[1]
patterns={
    'rolls':r'^Roll_\d+$','mugs':r'^Mug \d+ hollow ceramic body',
    'toothpaste':r'^Toothpaste box \d+','brushes':r'^Brush \d+\.\d+ rounded handle',
    'batteries':r'^Battery \d+ AA body','pencils':r'^Pencil \d+ hexagonal yellow barrel',
    'water':r'^Water bottle \d+ PET body','chips':r'^Chips can \d+$',
    'candy':r'^Candy mini pouch \d+$','yogurt':r'^Yogurt cup \d+$',
    'eggs':r'^Egg \d+$','apples':r'^Apple \d+ organic lobed skin',
}
results=[]
for item in json.loads((root/'assets/catalog.json').read_text(encoding='utf-8')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(root/'assets'/item['model']))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    counted=[o for o in meshes if re.search(patterns[item['id']],o.name)]
    finite=all(math.isfinite(value) for o in meshes for v in o.data.vertices for value in v.co)
    bpy.context.view_layer.update()
    points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    dimensions=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
    dims_ok=all(abs(a-b)<.0002 for a,b in zip(dimensions,item['dimensions']))
    textures_ok=all(image.packed_file or image.source=='GENERATED' for image in bpy.data.images if image.type=='IMAGE')
    # Packed UV image is embedded in the apple GLB, then reconstructed by importer.
    passed=len(counted)==item['countableUnits'] and finite and dims_ok and textures_ok
    results.append({'product':item['id'],'status':'pass' if passed else 'fail',
                    'actual_count':len(counted),'expected_count':item['countableUnits'],
                    'dimensions':dimensions,'finite':finite,'embedded_resources':textures_ok})
report={'blender':bpy.app.version_string,'method':'Fresh scene for each GLB; count principal meshes and measure imported bounding boxes.',
        'status':'pass' if all(r['status']=='pass' for r in results) else 'fail','checks':results}
(root/'verification').mkdir(exist_ok=True)
(root/'verification/individual-assets.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if report['status']!='pass':
    raise RuntimeError('Individual assets failed; inspect report')
print('ALL 12 INDIVIDUAL GLBS PASS',flush=True)
