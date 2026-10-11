"""Run in a separate Blender process. Visual review remains manual."""
import argparse
import json
import math
from pathlib import Path
import runpy
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))


def snapshot(objects):
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    points, triangles, degenerate = [], 0, 0
    colors = []
    empty_objects = []
    for obj in objects:
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
            continue
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        try:
            if mesh is None:
                continue
            points.extend(tuple(evaluated.matrix_world @ v.co) for v in mesh.vertices)
            mesh.calc_loop_triangles()
            if not mesh.vertices or not mesh.loop_triangles:
                empty_objects.append(obj.name)
            triangles += len(mesh.loop_triangles)
            degenerate += sum(t.area <= 1e-12 for t in mesh.loop_triangles)
            for material in mesh.materials:
                if material and material.use_nodes:
                    nodes = [n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
                    for node in nodes:
                        socket = node.inputs['Base Color']
                        if not socket.is_linked:
                            colors.append(tuple(round(v, 5) for v in socket.default_value))
        finally:
            evaluated.to_mesh_clear()
    finite = all(math.isfinite(x) for point in points for x in point)
    bounds = ([min(p[i] for p in points) for i in range(3)] +
              [max(p[i] for p in points) for i in range(3)]) if points and finite else None
    return {'vertices': len(points), 'triangles': triangles, 'degenerate_triangles': degenerate,
            'finite': finite, 'bounds': bounds, 'base_colors': sorted(set(colors)), 'empty_objects': empty_objects}


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def close(a, b, tolerance):
    return a is not None and b is not None and len(a) == len(b) and all(abs(x-y) <= tolerance for x, y in zip(a, b))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--checks', type=Path, help='Task script defining check(stage, objects, manifest) -> check list')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    from contract import load
    if load(args.manifest).get('schema_version') == 2:
        from validate_v2 import validate
        validate(args, snapshot, close, json_safe)
        return
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / 'validation.json'
    if report_path.exists() and not args.overwrite:
        raise FileExistsError(report_path)
    report = {'blender': bpy.app.version_string, 'checks': []}

    def add(name, passed, measured=None, required=True, status=None):
        report['checks'].append({'name': name, 'status': status or ('passed' if passed else 'failed'),
                                 'required': required, 'measured': measured})

    def hook(stage, objects, manifest):
        if args.checks:
            function = runpy.run_path(str(args.checks.resolve()))['check']
            for item in function(stage, objects, manifest):
                if item['status'] not in {'passed', 'failed', 'not_executed'}:
                    raise ValueError('Invalid task check status')
                json.dumps(item, allow_nan=False)
                add(stage + ':' + item['name'], False, item.get('measured'),
                    item.get('required', True), item['status'])

    try:
        manifest_path = args.manifest.resolve()
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        base = manifest_path.parent
        frames = manifest.get('frames', [1])
        tolerance = float(manifest.get('tolerance', 0.0001))
        if not frames or not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError('Nonempty frames and finite positive tolerance required')
        bpy.ops.wm.open_mainfile(filepath=str(base / manifest['blend']))
        fps = bpy.context.scene.render.fps
        fps_base = bpy.context.scene.render.fps_base
        collection = bpy.data.collections.get(manifest['collection'])
        if collection is None:
            raise ValueError('Model collection missing')
        objects = [o for o in collection.all_objects if not o.get('validation_helper', False)]
        source = []
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            sample = snapshot(objects)
            source.append(sample)
            add(f'source_geometry_frame_{frame}', sample['triangles'] > 0 and sample['finite'] and not sample['empty_objects'], sample)
            add(f'degenerate_geometry_frame_{frame}', sample['degenerate_triangles'] == 0,
                sample['degenerate_triangles'], required=False)
        missing = []
        for datablocks in (bpy.data.images, bpy.data.fonts, bpy.data.libraries, bpy.data.movieclips, bpy.data.sounds):
            for data in datablocks:
                path = getattr(data, 'filepath', '')
                if path and path != '<builtin>' and not getattr(data, 'packed_file', None):
                    if not Path(bpy.path.abspath(path)).exists():
                        missing.append(path)
        add('external_resources', not missing, missing)
        hook('blend', objects, manifest)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.render.fps = fps
        bpy.context.scene.render.fps_base = fps_base
        bpy.ops.import_scene.gltf(filepath=str(base / manifest['glb']))
        objects = [o for o in bpy.context.scene.objects
                   if not any(c.name.startswith('glTF_not_exported') for c in o.users_collection)]
        imported = []
        for frame, original in zip(frames, source):
            bpy.context.scene.frame_set(frame)
            sample = snapshot(objects)
            imported.append(sample)
            add(f'glb_geometry_frame_{frame}', sample['triangles'] > 0 and sample['finite'] and not sample['empty_objects'], sample)
            add(f'roundtrip_bounds_frame_{frame}', close(original['bounds'], sample['bounds'], tolerance),
                {'source': original['bounds'], 'imported': sample['bounds'], 'tolerance': tolerance})
            simple = bool(original['base_colors'])
            add(f'constant_base_colors_frame_{frame}', original['base_colors'] == sample['base_colors'],
                {'source': original['base_colors'], 'imported': sample['base_colors']},
                required=simple, status=None if simple else 'not_executed')
        if manifest.get('animation'):
            changed = len(frames) > 1 and any(not close(imported[0]['bounds'], x['bounds'], tolerance) for x in imported[1:])
            add('animation_bounds_change', changed, [s['bounds'] for s in imported], required=False)
            # Bounds cannot prove internal motion; a task hook must check that behavior.
            if manifest.get('loop'):
                add('loop_bounds', close(imported[0]['bounds'], imported[-1]['bounds'], tolerance),
                    {'first': imported[0]['bounds'], 'last': imported[-1]['bounds']})
        hook('glb', objects, manifest)
        if manifest.get('animation') and not any(x['name'] == 'glb:animation_behavior' and x['required'] for x in report['checks']):
            add('animation_behavior', False, 'Supply a glb animation_behavior task check', status='not_executed')
        if manifest.get('loop') and not any(x['name'] == 'glb:loop_behavior' and x['required'] for x in report['checks']):
            add('loop_behavior', False, 'Supply a glb loop_behavior pose check', status='not_executed')
        preview = base / manifest.get('preview', 'preview.png')
        add('preview_file', preview.is_file() and preview.stat().st_size > 0, manifest.get('preview', 'preview.png'))
        add('visual_review', False, 'Inspect preview and record reviewer findings before final delivery', status='not_executed')
    except Exception as exc:
        add('validation_exception', False, f'{type(exc).__name__}: {exc}')
    required = [x for x in report['checks'] if x['required']]
    report['status'] = ('failed' if any(x['status'] == 'failed' for x in required) else
                        'incomplete' if any(x['status'] == 'not_executed' for x in required) else 'passed')
    report_path.write_text(json.dumps(json_safe(report), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print('VALIDATION:', report['status'], str(report_path), flush=True)
    if report['status'] == 'failed':
        raise RuntimeError('Required validation failed; see validation.json')
    # Incomplete is a recorded review state, not a Blender execution error.


if __name__ == '__main__':
    main()
