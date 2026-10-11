"""Shared Blender-side path preflight. It is not a sandbox."""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract import safe_path


def roots_for(base, manifest=None):
    base = Path(base).resolve()
    environment = json.loads(os.environ.get('BLENDER_MODELING_READ_ROOTS', '[]'))
    if environment:
        safe_path(base, environment)
    roots = [base, Path(__file__).resolve().parents[1]]
    if manifest:
        roots.extend(base / p for p in manifest.get('read_roots', []))
        if environment:
            for root in roots[2:]:
                safe_path(root, environment)
    return roots + [Path(p).resolve() for p in environment]


def resource_preflight(roots):
    import bpy
    runtime = Path(bpy.app.binary_path).resolve().parent
    roots = list(roots) + [runtime]
    missing = []
    for data_list in (bpy.data.images, bpy.data.fonts, bpy.data.libraries, bpy.data.movieclips, bpy.data.sounds):
        for item in data_list:
            filepath = getattr(item, 'filepath', '')
            if filepath and filepath != '<builtin>' and not getattr(item, 'packed_file', None):
                path = safe_path(bpy.path.abspath(filepath), roots)
                if not path.is_file():
                    missing.append(str(path))
    return missing


def autoexec_blocked():
    import bpy
    return bool(getattr(bpy.app, 'autoexec_fail', False))
