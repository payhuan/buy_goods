"""Blender v2 mechanical checks; never awards visual/documentary passes."""
import copy
from pathlib import Path
import runpy

import bpy

from blender_io import roots_for, resource_preflight, autoexec_blocked
from contract import (atomic_write, init_report, load, record, safe_path, sync_report,
                      generate_checks, validate_report, assert_current)


def validate(args, snapshot, close, json_safe):
    manifest_path = args.manifest.resolve()
    manifest = load(manifest_path)
    roots = roots_for(manifest_path.parent, manifest)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / 'validation.json'
    if report_path.exists() and not args.overwrite:
        raise FileExistsError(report_path)
    report = sync_report(load(report_path), manifest, manifest_path) if report_path.exists() else init_report(manifest, manifest_path)
    results = []
    specs = {x['id']: x for x in generate_checks(manifest)}

    def emit(name, status, measured=None, reason=''):
        if name not in specs:
            return
        current = next(x for x in report['checks'] if x['id'] == name)
        if current['status'] == 'not_applicable':
            return
        previous = next((x for x in results if x['id'] == name), None)
        item = {'id': name, 'status': status, 'origin': 'validate_v2',
                'measured': json_safe(measured), 'reason': reason}
        if previous:
            stages = previous['measured'] if isinstance(previous['measured'], list) else [previous['measured']]
            item['measured'] = stages + [item['measured']]
            if previous['status'] == 'fail':
                item['status'], item['reason'] = 'fail', previous['reason']
            results.remove(previous)
        results.append(item)

    def hook(stage, objects):
        if not args.checks:
            return
        script = safe_path(args.checks, roots)
        if not any(a['role'] == 'check_script' and (manifest_path.parent / a['path']).resolve() == script for a in report['artifacts']):
            raise ValueError('Task check script must be registered as check_script artifact')
        function = runpy.run_path(str(script))['check']
        names = {'animation_behavior': 'animation.behavior', 'loop_behavior': 'animation.loop'}
        for result in function(stage, objects, manifest):
            name = result.get('id') or names.get(result.get('name'), 'task.' + result.get('name', ''))
            if name not in specs or specs[name]['method'] != 'task':
                raise ValueError('Task result must match declared task-method acceptance: ' + name)
            if name.startswith('animation.') and stage != 'glb' and manifest.get('glb'):
                continue
            status = {'passed': 'pass', 'failed': 'fail', 'not_executed': 'incomplete'}.get(result['status'], result['status'])
            if status not in ('pass', 'fail', 'incomplete', 'blocked'):
                raise ValueError('Task executor may not award waivers or N/A')
            emit(name, status, {'stage': stage, 'value': result.get('measured')},
                 result.get('reason', '') or ('Task check did not pass' if status in ('fail', 'blocked') else ''))

    try:
        blend = safe_path(manifest_path.parent / manifest['blend'], roots)
        bpy.ops.wm.open_mainfile(filepath=str(blend))
        scene = bpy.context.scene
        fps, fps_base = scene.render.fps, scene.render.fps_base
        collection = bpy.data.collections.get(manifest['collection'])
        if collection is None:
            raise ValueError('Model collection missing')
        objects = [o for o in collection.all_objects if not o.get('validation_helper', False)]
        frames = manifest.get('frames', [1])
        tolerance = manifest.get('tolerance', 0.0001)
        samples = []
        for frame in frames:
            scene.frame_set(frame)
            samples.append(snapshot(objects))
        emit('asset.readable', 'pass', {'blend': str(blend), 'blender': bpy.app.version_string})
        valid = all(s['triangles'] > 0 and not s['empty_objects'] for s in samples)
        emit('geometry.non_empty', 'pass' if valid else 'fail', samples, 'Empty model geometry' if not valid else '')
        valid = all(s['finite'] for s in samples)
        emit('geometry.finite_coords', 'pass' if valid else 'fail', samples, 'Nonfinite geometry' if not valid else '')
        missing = resource_preflight(roots)
        emit('resource.exists', 'fail' if missing else 'pass', missing, 'Missing external resources' if missing else '')
        dims = manifest['requirements'].get('dimensions')
        if dims:
            actual = [samples[0]['bounds'][i+3] - samples[0]['bounds'][i] for i in range(3)] if samples[0]['bounds'] else None
            expected = dims.get('xyz')
            valid = close(actual, expected, dims.get('tolerance', tolerance))
            emit('dimension.spec', 'pass' if valid else 'fail', {'actual': actual, 'expected': expected}, 'Dimension mismatch' if not valid else '')
        budgets = manifest['budgets']
        if 'triangles' in budgets:
            actual = max(s['triangles'] for s in samples)
            emit('budget.triangles', 'pass' if actual <= budgets['triangles'] else 'fail',
                 {'actual': actual, 'limit': budgets['triangles']}, 'Triangle budget exceeded' if actual > budgets['triangles'] else '')
        if 'texture_resolution' in budgets:
            images = [image for image in bpy.data.images if image.type == 'IMAGE' and image.source != 'VIEWER']
            actual = max([max(image.size) for image in images] or [0])
            emit('budget.texture_resolution', 'pass' if actual <= budgets['texture_resolution'] else 'fail',
                 {'actual': actual, 'limit': budgets['texture_resolution']}, 'Texture resolution budget exceeded' if actual > budgets['texture_resolution'] else '')
        if 'file_bytes' in budgets:
            sizes = {a['id']: (manifest_path.parent / a['path']).stat().st_size for a in report['artifacts']
                     if a['role'] in ('blend', 'glb') and not a['missing']}
            actual = max(sizes.values(), default=0)
            emit('budget.file_bytes', 'pass' if actual <= budgets['file_bytes'] else 'fail',
                 {'actual_max_file_bytes': actual, 'files': sizes, 'limit': budgets['file_bytes']},
                 'Per-file budget exceeded' if actual > budgets['file_bytes'] else '')
        hook('blend', objects)
        driver_block = autoexec_blocked()
        if manifest.get('glb'):
            glb = safe_path(manifest_path.parent / manifest['glb'], roots)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = fps, fps_base
            bpy.ops.import_scene.gltf(filepath=str(glb))
            objects = [o for o in bpy.context.scene.objects if not any(c.name.startswith('glTF_not_exported') for c in o.users_collection)]
            imported = []
            for frame in frames:
                bpy.context.scene.frame_set(frame)
                imported.append(snapshot(objects))
            valid = all(b['finite'] and b['triangles'] > 0 and not b['empty_objects'] and
                        close(a['bounds'], b['bounds'], tolerance) and
                        (not a['base_colors'] or a['base_colors'] == b['base_colors'])
                        for a, b in zip(samples, imported))
            emit('export.roundtrip', 'pass' if valid else 'fail', {'source': samples, 'glb': imported},
                 'GLB geometry/bounds/constant color mismatch' if not valid else '')
            hook('glb', objects)
        if driver_block:
            emit('asset.readable', 'blocked', {'autoexec_disabled': True}, 'Python drivers require execution; bake in an authorized trusted workflow instead')
        if 'delivery.complete' in specs:
            deliverables = manifest['requirements'].get('deliverables', ['blend', 'source', 'glb', 'preview'])
            missing = [role for role in deliverables if not any(a['role'] == role and not a['missing'] for a in report['artifacts'])]
            emit('delivery.complete', 'fail' if missing else 'pass', {'missing_roles': missing}, 'Missing deliverables' if missing else '')
    except Exception as exc:
        emit('asset.readable', 'fail', {'exception': type(exc).__name__}, str(exc))
    # Verify unchanged dependencies before accepting any executor result.
    assert_current(report, manifest, manifest_path)
    staged = copy.deepcopy(report)
    for item in results:
        try:
            record(staged, manifest, manifest_path, item['id'], item['status'], item['origin'],
                   item['reason'], item['measured'])
        except ValueError as exc:
            record(staged, manifest, manifest_path, item['id'], 'blocked', item['origin'], str(exc))
    validate_report(staged)
    atomic_write(output / 'mechanical-results.json', results)
    atomic_write(report_path, staged)
    print('VALIDATION_V2:', staged['status'], report_path, flush=True)
    if staged['status'] == 'fail':
        raise RuntimeError('Required v2 validation failed')
