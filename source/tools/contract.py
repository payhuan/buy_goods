"""v2 contracts, quality mapping and revision-aware acceptance. Standard library only."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import uuid

STATES = ['pass', 'fail', 'incomplete', 'not_applicable', 'waived', 'blocked']
METHODS = ['automatic', 'visual', 'task', 'documentary']
PURPOSES = ['schematic', 'teaching', 'presentation', 'production']
COMPLETIONS = ['draft', 'refined', 'final']
VISUAL = ['silhouette', 'proportion', 'structure', 'composition', 'material',
          'normals', 'shadows', 'occlusion', 'surface_closeup']
BASE = ['asset.readable', 'geometry.non_empty', 'geometry.finite_coords', 'resource.exists']
SCHEMATIC = ['visual.silhouette', 'visual.proportion', 'visual.structure', 'schematic.simplification']
PRESENTATION = SCHEMATIC + ['visual.' + x for x in VISUAL[3:]]
PURPOSE_CHECKS = {
    'schematic': SCHEMATIC,
    'teaching': SCHEMATIC + ['teaching.parts', 'teaching.relationships', 'teaching.labels', 'teaching.sources'],
    'presentation': PRESENTATION,
    'production': PRESENTATION + ['production.target', 'production.contract', 'asset.organization',
                                   'topology.profile', 'uv.profile', 'material.pbr', 'license.resource_manifest'],
}
COMPLETION_CHECKS = {
    'draft': ['visual.' + x for x in VISUAL[:3]],
    'refined': ['visual.' + x for x in VISUAL[:8]],
    'final': ['visual.' + x for x in VISUAL] + ['license.resource_manifest', 'delivery.complete'],
}
AUTOMATIC = BASE + ['dimension.spec', 'budget.triangles', 'budget.texture_resolution', 'budget.file_bytes',
                    'export.roundtrip', 'delivery.complete']
TASK = ['animation.behavior', 'animation.loop', 'teaching.parts', 'teaching.relationships',
        'asset.organization', 'topology.profile']
REGISTRY = set(AUTOMATIC + TASK + [x for xs in PURPOSE_CHECKS.values() for x in xs]
               + ['production.budgets'] + ['visual.' + x for x in VISUAL])
REGISTRY.add('visual.reference_fidelity')
CONDITIONAL = ['dimension.spec', 'budget.triangles', 'budget.texture_resolution', 'budget.file_bytes',
               'export.roundtrip', 'animation.behavior', 'animation.loop']


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    if not Path(path).is_file():
        return None
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f'Nonfinite JSON value: {value}')
    value = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=invalid)
    canonical(value)
    return value


def safe_path(path, roots):
    resolved = Path(path).expanduser().resolve()
    if not any(resolved.is_relative_to(Path(root).expanduser().resolve()) for root in roots):
        raise ValueError(f'Path outside registered roots: {resolved}')
    return resolved


def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def schema_check(value, schema, where='$'):
    """Validate the explicit JSON Schema subset used by the published contracts."""
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'number': (int, float),
             'boolean': bool, 'null': type(None)}
    expected = schema.get('type')
    if expected:
        kinds = expected if isinstance(expected, list) else [expected]
        if not any(isinstance(value, types[k]) and not (k in ('integer', 'number') and isinstance(value, bool)) for k in kinds):
            raise ValueError(f'{where}: expected {expected}')
    if 'const' in schema and value != schema['const']:
        raise ValueError(f'{where}: invalid constant')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{where}: unknown enum value {value}')
    if isinstance(value, str) and len(value) < schema.get('minLength', 0):
        raise ValueError(f'{where}: empty string')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value) or value < schema.get('minimum', -math.inf):
            raise ValueError(f'{where}: invalid numeric value')
    if isinstance(value, dict):
        for name in schema.get('required', []):
            if name not in value:
                raise ValueError(f'{where}: missing {name}')
        props = schema.get('properties', {})
        for name, item in value.items():
            if name in props:
                schema_check(item, props[name], where + '.' + name)
            elif schema.get('additionalProperties') is False:
                raise ValueError(f'{where}: unknown field {name}')
            elif isinstance(schema.get('additionalProperties'), dict):
                schema_check(item, schema['additionalProperties'], where + '.' + name)
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            raise ValueError(f'{where}: too few items')
        if 'maxItems' in schema and len(value) > schema['maxItems']:
            raise ValueError(f'{where}: too many items')
        if schema.get('uniqueItems') and len({canonical(x) for x in value}) != len(value):
            raise ValueError(f'{where}: duplicate array item')
        for index, item in enumerate(value):
            schema_check(item, schema.get('items', {}), f'{where}[{index}]')


def obj(properties, required=None, additional=False):
    return {'type': 'object', 'properties': properties, 'required': list(properties) if required is None else required,
            'additionalProperties': additional}


STRING = {'type': 'string', 'minLength': 1}
STRINGS = {'type': 'array', 'items': STRING, 'uniqueItems': True}
NUMBER = {'type': 'number', 'minimum': 0}
JSON_OBJECT = {'type': 'object'}
REFERENCE_CONSTRAINT = obj({'id': STRING, 'target': STRING, 'basis': STRING,
                           'knowledge': {'enum': ['visible', 'estimated', 'unknown']},
                           'method': {'enum': ['visual', 'task']}, 'tolerance': JSON_OBJECT},
                          required=['id', 'target', 'basis', 'knowledge', 'method'])
REFERENCE = obj({'artifact_ids': dict(STRINGS, minItems=1),
                 'mode': {'enum': ['reconstruct', 'adapt', 'inspiration']},
                 'constraints': {'type': 'array', 'items': REFERENCE_CONSTRAINT},
                 'allowed_changes': {'type': 'array', 'items': obj({'quote': STRING, 'source': STRING})}})
REQUIREMENTS = obj({'description': STRING, 'style': STRING, 'parts': STRINGS, 'prohibited': STRINGS,
                    'target_platform': {'type': ['string', 'null']}, 'deliverables': STRINGS,
                    'required_budgets': {'type': 'array', 'items': {'enum': ['triangles', 'texture_resolution', 'file_bytes']}, 'uniqueItems': True},
                    'dimensions': obj({'xyz': {'type': 'array', 'items': NUMBER, 'minItems': 3, 'maxItems': 3},
                                       'tolerance': {'type': 'number', 'minimum': 1e-15}}, required=['xyz']),
                    'scientific': {'type': 'boolean'}, 'labels_required': {'type': 'boolean'},
                    'uv_required': {'type': 'boolean'}, 'pbr_required': {'type': 'boolean'}, 'topology': JSON_OBJECT,
                    'reference': REFERENCE},
                   required=[], additional=True)
ARTIFACT = obj({'id': STRING, 'role': STRING, 'path': STRING})
ACCEPTANCE = obj({'id': STRING, 'method': {'enum': METHODS}, 'required': {'type': 'boolean'},
                  'rule': STRING, 'check_deps': STRINGS, 'config': JSON_OBJECT})
EVIDENCE = obj({'artifact_id': STRING, 'sha256': STRING, 'observation': STRING})
CONFIRMATION = obj({'quote': STRING, 'source': STRING})
WAIVER = obj({'check_id': STRING, 'reason': STRING, 'confirmation': CONFIRMATION,
              'params_hash': STRING, 'dependency_hashes': JSON_OBJECT, 'active': {'type': 'boolean'}})
CHECK = obj({'id': STRING, 'status': {'enum': STATES}, 'required': {'type': 'boolean'},
             'reason': {'type': 'string'}, 'measured': {}, 'evidence': {'type': 'array', 'items': EVIDENCE},
             'dependency_hashes': JSON_OBJECT, 'origin': STRING})
MANIFEST_SCHEMA = obj({
    'schema_version': {'type': 'integer', 'const': 2},
    'quality': obj({'purpose': {'enum': PURPOSES}, 'completion': {'enum': COMPLETIONS}}),
    'requirements': REQUIREMENTS, 'parameters': JSON_OBJECT,
    'budgets': obj({'triangles': NUMBER, 'texture_resolution': NUMBER, 'file_bytes': NUMBER}, required=[]),
    'artifacts': {'type': 'array', 'items': ARTIFACT, 'minItems': 1},
    'acceptance': {'type': 'array', 'items': ACCEPTANCE},
    'resources': {'type': 'array', 'items': obj({'artifact_id': STRING, 'source': STRING,
                    'license': STRING, 'attribution': {'type': 'string'}, 'redistribution': STRING})},
    'read_roots': STRINGS, 'collection': STRING, 'blend': STRING, 'glb': STRING, 'preview': STRING,
    'frames': {'type': 'array', 'items': {'type': 'integer'}, 'minItems': 1, 'uniqueItems': True},
    'animation': {'type': 'boolean'}, 'loop': {'type': 'boolean'},
    'tolerance': {'type': 'number', 'minimum': 1e-15},
    'units': STRING, 'coordinates': STRING, 'scientific_claims': {'type': 'array'}, 'tested_blender': STRING,
}, required=['schema_version', 'quality', 'requirements', 'parameters', 'budgets', 'artifacts',
             'acceptance', 'resources', 'collection', 'blend'])
REPORT_SCHEMA = obj({
    'schema_version': {'type': 'integer', 'const': 2},
    'revision': obj({'id': STRING, 'manifest_hash': STRING, 'params_hash': STRING}),
    'artifacts': {'type': 'array', 'items': obj({'id': STRING, 'role': STRING, 'path': STRING,
                  'sha256': {'type': ['string', 'null']}, 'missing': {'type': 'boolean'}})},
    'checks': {'type': 'array', 'items': CHECK, 'minItems': 1},
    'waivers': {'type': 'array', 'items': WAIVER}, 'history': {'type': 'array', 'items': JSON_OBJECT},
    'status': {'enum': STATES}, 'summary_reason': {'type': 'string'},
})
for schema in (MANIFEST_SCHEMA, REPORT_SCHEMA):
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'


def unique(items, label):
    ids = [x['id'] for x in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f'Duplicate {label} ID')


def validate_manifest(manifest):
    schema_check(manifest, MANIFEST_SCHEMA)
    canonical(manifest)
    unique(manifest['artifacts'], 'artifact')
    unique(manifest['acceptance'], 'acceptance')
    ids = {x['id'] for x in manifest['artifacts']}
    reference = manifest['requirements'].get('reference')
    if reference:
        unique(reference['constraints'], 'reference constraint')
        references = {a['id'] for a in manifest['artifacts'] if a['role'] == 'reference'}
        if not set(reference['artifact_ids']).issubset(references):
            raise ValueError('Reference images must be registered reference artifacts')
        if (reference['mode'] != 'inspiration' or any(a['id'] == 'visual.reference_fidelity' for a in manifest['acceptance'])) and not reference['constraints']:
            raise ValueError('Reference reconstruction/adaptation requires constraints')
        if any(a['id'] == 'visual.reference_fidelity' and not a['required'] for a in manifest['acceptance']) and reference['mode'] != 'inspiration':
            raise ValueError('Cannot downgrade required reference fidelity')
    elif any(a['id'] == 'visual.reference_fidelity' for a in manifest['acceptance']):
        raise ValueError('Reference fidelity requires requirements.reference')
    if manifest.get('loop') and not manifest.get('animation'):
        raise ValueError('loop requires animation')
    for check in manifest['acceptance']:
        if check['id'] not in REGISTRY and not check['id'].startswith('task.'):
            raise ValueError('Unknown check ID: ' + check['id'])
        if check['id'] == 'task.':
            raise ValueError('Task check ID requires a name')
        if not set(check['check_deps']).issubset(ids):
            raise ValueError('Unknown dependency: ' + check['id'])
        expected_method = ('visual' if check['id'].startswith('visual.') or check['id'] == 'teaching.labels' else
                           'automatic' if check['id'] in AUTOMATIC else
                           'task' if check['id'] in TASK or check['id'].startswith('task.') else 'documentary')
        if check['method'] != expected_method:
            raise ValueError('Check method conflicts with stable ID: ' + check['id'])
    if not any(x['role'] == 'blend' and x['path'] == manifest['blend'] for x in manifest['artifacts']):
        raise ValueError('blend must be registered as an artifact')
    if manifest.get('glb') and not any(x['role'] == 'glb' and x['path'] == manifest['glb'] for x in manifest['artifacts']):
        raise ValueError('glb must be registered as an artifact')
    for resource in manifest['resources']:
        if resource['artifact_id'] not in ids:
            raise ValueError('Unknown resource artifact')


def applicable(check_id, manifest):
    req, budgets = manifest['requirements'], manifest['budgets']
    predicates = {
        'dimension.spec': bool(req.get('dimensions')),
        'budget.triangles': 'triangles' in budgets,
        'budget.texture_resolution': 'texture_resolution' in budgets,
        'budget.file_bytes': 'file_bytes' in budgets,
        'export.roundtrip': bool(manifest.get('glb')),
        'animation.behavior': manifest.get('animation', False),
        'animation.loop': manifest.get('loop', False),
        'uv.profile': bool(req.get('uv_required')),
        'material.pbr': bool(req.get('pbr_required')),
        'topology.profile': bool(req.get('topology')),
        'teaching.sources': bool(req.get('scientific', False)),
        'teaching.labels': bool(req.get('labels_required', False)),
        'license.resource_manifest': bool(manifest['resources']),
    }
    # Explicit acceptance entries are requirements and cannot be auto-excluded.
    if any(x['id'] == check_id for x in manifest['acceptance']):
        return True
    return predicates.get(check_id, True)


def generate_checks(manifest):
    validate_manifest(manifest)
    quality = manifest['quality']
    chosen = set(BASE + PURPOSE_CHECKS[quality['purpose']] + COMPLETION_CHECKS[quality['completion']] + CONDITIONAL)
    if quality == {'purpose': 'production', 'completion': 'final'}:
        chosen.add('production.budgets')
    # Keep the complete visual rubric visible; unselected entries are optional diagnostics.
    chosen.update('visual.' + x for x in VISUAL)
    reference = manifest['requirements'].get('reference')
    if reference and reference['mode'] != 'inspiration':
        chosen.add('visual.reference_fidelity')
    explicit = {x['id']: x for x in manifest['acceptance']}
    result = []
    for check_id in sorted(chosen | set(explicit)):
        method = ('visual' if check_id.startswith('visual.') or check_id == 'teaching.labels' else
                  'automatic' if check_id in AUTOMATIC else 'task' if check_id in TASK else 'documentary')
        required = check_id in set(BASE + PURPOSE_CHECKS[quality['purpose']] + COMPLETION_CHECKS[quality['completion']] + CONDITIONAL)
        if check_id == 'production.budgets':
            required = True
        if check_id == 'visual.reference_fidelity':
            required = reference['mode'] != 'inspiration'
        roles = {'blend', 'source', 'check_script', 'validator'}
        if method == 'visual':
            roles |= {'preview', 'render_config', 'preview_script'}
        if check_id == 'visual.reference_fidelity':
            roles.add('reference')
        if check_id in {'export.roundtrip', 'budget.file_bytes', 'delivery.complete'} or check_id.startswith('animation.'):
            roles |= {'glb', 'source'}
        if check_id in {'resource.exists', 'license.resource_manifest', 'budget.texture_resolution', 'material.pbr', 'uv.profile'}:
            roles |= {'texture', 'font', 'resource', 'plugin'}
        default = {'id': check_id, 'method': method, 'required': required,
                   'rule': 'profile.' + check_id, 'check_deps': [a['id'] for a in manifest['artifacts'] if a['role'] in roles],
                   'config': {'depth': quality['completion']}}
        if check_id in explicit:
            user = explicit[check_id]
            if check_id in BASE and not user['required']:
                raise ValueError('Cannot remove universal safety checks')
            default.update(copy.deepcopy(user))
            default['config'] = {'depth': quality['completion'], **user['config']}
            # User entries may strengthen or change semantics but cannot remove actual dependencies.
            default['check_deps'] = sorted(set(default['check_deps']) | {a['id'] for a in manifest['artifacts'] if a['role'] in roles})
        result.append(default)
    return result


def artifact_snapshot(manifest, manifest_path):
    base = Path(manifest_path).resolve().parent
    roots = [base] + [base / r for r in manifest.get('read_roots', [])]
    result = []
    for item in manifest['artifacts']:
        path = safe_path(base / item['path'], roots)
        sha = file_hash(path)
        result.append(dict(item, sha256=sha, missing=sha is None))
    return result


def params_hash(manifest):
    return digest({k: manifest[k] for k in ('parameters', 'requirements', 'budgets', 'quality', 'acceptance')})


def dependencies(spec, artifacts):
    hashes = {x['id']: x['sha256'] for x in artifacts}
    return {name: hashes[name] for name in spec['check_deps']}


def initial_check(spec, manifest, artifacts):
    check = {'id': spec['id'], 'status': 'incomplete', 'required': spec['required'], 'reason': '',
             'measured': None, 'evidence': [], 'dependency_hashes': dependencies(spec, artifacts), 'origin': 'profile'}
    if not applicable(spec['id'], manifest):
        check.update(status='not_applicable', reason='Rule ' + spec['rule'] + ': feature not requested')
    req = manifest['requirements']
    if spec['id'] == 'visual.reference_fidelity' and any(
            a['missing'] for a in artifacts if a['id'] in req['reference']['artifact_ids']):
        check.update(status='blocked', reason='Provide missing reference images and sync')
    if manifest['quality'] == {'purpose': 'production', 'completion': 'final'}:
        missing = {'production.target': not req.get('target_platform'),
                   'production.contract': not req.get('deliverables'),
                   'production.budgets': 'required_budgets' not in req or any(x not in manifest['budgets'] for x in req.get('required_budgets', []))}
        if missing.get(spec['id']):
            check.update(status='blocked', reason='Provide target_platform, deliverables and explicit required_budgets (empty list allowed only when none are needed)')
    return check


def aggregate(checks):
    required = [x for x in checks if x['required'] and x['status'] != 'not_applicable']
    if not required:
        return 'incomplete', 'No applicable required checks; acceptance is invalid'
    for state in ('fail', 'blocked', 'incomplete', 'waived'):
        if any(x['status'] == state for x in required):
            return state, ''
    return 'pass', ''


def refresh_status(report):
    report['status'], report['summary_reason'] = aggregate(report['checks'])


def validate_report(report):
    schema_check(report, REPORT_SCHEMA)
    canonical(report)
    unique(report['checks'], 'check')
    unique(report['artifacts'], 'artifact')
    ids = {x['id'] for x in report['artifacts']}
    for check in report['checks']:
        if not set(check['dependency_hashes']).issubset(ids):
            raise ValueError('Unknown report dependency')
        if check['status'] in {'fail', 'blocked', 'not_applicable', 'waived'} and not check['reason']:
            raise ValueError('State requires reason')
        for evidence in check['evidence']:
            if evidence['artifact_id'] not in ids:
                raise ValueError('Unknown evidence artifact')
        if check['status'] == 'waived' and not any(
                w['active'] and w['check_id'] == check['id'] and
                w['dependency_hashes'] == check['dependency_hashes'] and
                w['params_hash'] == report['revision']['params_hash'] for w in report['waivers']):
            raise ValueError('Waived check lacks current user-confirmation record')
    if report['status'] != aggregate(report['checks'])[0]:
        raise ValueError('Report status does not match required checks')


def init_report(manifest, manifest_path):
    specs = generate_checks(manifest)
    artifacts = artifact_snapshot(manifest, manifest_path)
    report = {'schema_version': 2, 'revision': {'id': uuid.uuid4().hex,
                'manifest_hash': digest(manifest), 'params_hash': params_hash(manifest)},
              'artifacts': artifacts, 'checks': [initial_check(s, manifest, artifacts) for s in specs],
              'waivers': [], 'history': [], 'status': 'incomplete', 'summary_reason': ''}
    refresh_status(report)
    return report


def sync_report(report, manifest, manifest_path):
    validate_report(report)
    current = init_report(manifest, manifest_path)
    old = {x['id']: x for x in report['checks']}
    global_change = report['revision']['params_hash'] != current['revision']['params_hash']
    changed = report['revision']['manifest_hash'] != current['revision']['manifest_hash'] or report['artifacts'] != current['artifacts']
    history = copy.deepcopy(report['history'])
    invalidated = set()
    for index, check in enumerate(current['checks']):
        previous = old.get(check['id'])
        stale = previous and (global_change or previous['required'] != check['required'] or
                              previous['dependency_hashes'] != check['dependency_hashes'])
        if previous and not stale:
            current['checks'][index] = copy.deepcopy(previous)
        elif previous:
            invalidated.add(check['id'])
            history.append({'event': 'invalidated', 'revision': report['revision']['id'], 'check': copy.deepcopy(previous),
                            'reason': 'params/requirements changed' if global_change else 'artifact dependency changed'})
            # Never carry manual N/A or a waiver into changed dependencies.
            if previous['origin'] != 'profile' and check['status'] == 'not_applicable':
                check.update(status='incomplete', reason='Prior conclusion invalidated', origin='sync')
    for name, previous in old.items():
        if name not in {x['id'] for x in current['checks']}:
            history.append({'event': 'removed_by_requirement_change', 'check': previous})
            invalidated.add(name)
    current['history'] = history
    current['waivers'] = copy.deepcopy(report['waivers'])
    for waiver in current['waivers']:
        if waiver['check_id'] in invalidated:
            waiver['active'] = False
    if not changed and not global_change:
        current['revision'] = report['revision']
    refresh_status(current)
    return current


def assert_current(report, manifest, manifest_path):
    validate_report(report)
    specs = {x['id']: x for x in generate_checks(manifest)}
    if set(specs) != {x['id'] for x in report['checks']}:
        raise ValueError('Report does not match generated acceptance IDs; run sync')
    for check in report['checks']:
        spec = specs[check['id']]
        if check['required'] != spec['required'] or set(check['dependency_hashes']) != set(spec['check_deps']):
            raise ValueError('Report requirement/dependency metadata was changed; run sync')
    if (report['revision']['manifest_hash'] != digest(manifest) or
            report['revision']['params_hash'] != params_hash(manifest) or
            report['artifacts'] != artifact_snapshot(manifest, manifest_path)):
        raise ValueError('Revision changed; run sync before recording')


def validate_reference_result(manifest, status, measured, evidence, artifacts):
    reference = manifest['requirements']['reference']
    missing = any(artifacts[x]['missing'] for x in reference['artifact_ids'])
    if missing:
        if status != 'blocked':
            raise ValueError('Missing reference images require blocked')
        return
    if status == 'blocked':
        return
    if status not in {'pass', 'fail', 'incomplete'}:
        raise ValueError('Reference requirement cannot be marked not applicable')
    schema = obj({'criteria': {'type': 'array', 'items': obj({
        'id': STRING, 'status': {'enum': ['pass', 'fail', 'incomplete']},
        'observation': STRING, 'reference_evidence': dict(STRINGS, minItems=1),
        'preview_evidence': STRINGS})}})
    schema_check(measured, schema)
    criteria = measured['criteria']
    unique(criteria, 'criterion result')
    if {x['id'] for x in criteria} != {x['id'] for x in reference['constraints']}:
        raise ValueError('Criterion results must cover exactly all reference constraints')
    evidence_ids = {x['artifact_id'] for x in evidence}
    if len(evidence_ids) != len(evidence):
        raise ValueError('Duplicate reference evidence')
    for item in criteria:
        if not set(item['reference_evidence']).issubset(set(reference['artifact_ids']) & evidence_ids):
            raise ValueError('Criterion requires current registered reference evidence')
        if not set(item['preview_evidence']).issubset(evidence_ids) or any(
                artifacts[x]['role'] != 'preview' for x in item['preview_evidence']):
            raise ValueError('Criterion requires registered preview evidence')
        if item['status'] != 'incomplete' and not item['preview_evidence']:
            raise ValueError('Executed criterion requires a rendered comparison')
    states = {x['status'] for x in criteria}
    expected = 'fail' if 'fail' in states else 'incomplete' if 'incomplete' in states else 'pass'
    if status != expected:
        raise ValueError('Reference status conflicts with criterion results')


def record(report, manifest, manifest_path, check_id, status, origin, reason='', measured=None, evidence=None, rule_source=None):
    assert_current(report, manifest, manifest_path)
    schema_check(origin, STRING)
    if status not in STATES or status == 'waived':
        raise ValueError('Use waive for user-authorized waivers')
    spec = next((x for x in generate_checks(manifest) if x['id'] == check_id), None)
    if not spec:
        raise ValueError('Unknown check ID')
    if status in {'fail', 'blocked', 'not_applicable'} and not reason:
        raise ValueError('A reason is required')
    if status == 'not_applicable':
        if applicable(check_id, manifest) or rule_source != spec['rule']:
            raise ValueError('N/A contradicts an applicable requirement or has an unknown rule source')
    previous = next(x for x in report['checks'] if x['id'] == check_id)
    if previous['status'] == 'blocked' and previous['origin'] == 'profile' and status == 'pass':
        raise ValueError('Resolve missing requirements/resources and sync first')
    evidence = evidence or []
    artifacts = {x['id']: x for x in report['artifacts']}
    for item in evidence:
        schema_check(item, EVIDENCE)
        artifact = artifacts.get(item['artifact_id'])
        if not artifact or not artifact['sha256'] or item['sha256'] != artifact['sha256']:
            raise ValueError('Evidence hash does not match current artifact')
        if item['artifact_id'] not in spec['check_deps']:
            raise ValueError('Evidence must be a declared dependency')
        allowed_roles = {'preview', 'reference'} if check_id == 'visual.reference_fidelity' else {'preview'}
        if spec['method'] == 'visual' and artifact['role'] not in allowed_roles:
            raise ValueError('Visual evidence must reference a preview')
    if check_id == 'visual.reference_fidelity':
        validate_reference_result(manifest, status, measured, evidence, artifacts)
    if status in {'pass', 'fail'} and spec['method'] == 'visual' and not evidence:
        raise ValueError('Visual decisions require image evidence and observations')
    if status == 'pass' and spec['method'] in {'automatic', 'task'} and measured is None:
        raise ValueError('Mechanical pass requires measured values')
    if status == 'pass' and spec['method'] == 'documentary' and not reason:
        raise ValueError('Documentary pass requires a factual explanation')
    if status == 'pass' and any(value is None for value in previous['dependency_hashes'].values()):
        raise ValueError('A required dependency is missing')
    canonical(measured)
    updated = dict(previous, status=status, origin=origin, reason=reason, measured=measured, evidence=evidence)
    report['history'].append({'event': 'record', 'revision': report['revision']['id'], 'previous': copy.deepcopy(previous)})
    previous.update(updated)
    for waiver in report['waivers']:
        if waiver['check_id'] == check_id:
            waiver['active'] = False
    refresh_status(report)
    validate_report(report)


def waive(report, manifest, manifest_path, check_id, reason, confirmation):
    assert_current(report, manifest, manifest_path)
    schema_check(confirmation, CONFIRMATION)
    if not reason:
        raise ValueError('Waiver reason required')
    check = next((x for x in report['checks'] if x['id'] == check_id), None)
    if not check:
        raise ValueError('Unknown check')
    report['history'].append({'event': 'waive', 'previous': copy.deepcopy(check), 'revision': report['revision']['id']})
    for previous in report['waivers']:
        if previous['check_id'] == check_id:
            previous['active'] = False
    report['waivers'].append({'check_id': check_id, 'reason': reason, 'confirmation': confirmation,
                             'params_hash': report['revision']['params_hash'],
                             'dependency_hashes': copy.deepcopy(check['dependency_hashes']), 'active': True})
    check.update(status='waived', reason=reason, origin='user-confirmation', evidence=[])
    refresh_status(report)


def exit_code(status, allow_waived=False):
    return {'pass': 0, 'fail': 1, 'incomplete': 3, 'blocked': 3, 'waived': 0 if allow_waived else 4,
            'not_applicable': 3}[status]
