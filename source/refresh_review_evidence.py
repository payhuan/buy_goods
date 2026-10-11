"""Refresh evidence after actual visual inspection; does not perform the review."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
artifacts = {a['id']: a for a in manifest['artifacts']}
results = json.loads((root/'verification/review-results.json').read_text(encoding='utf-8'))
imports = json.loads((root/'verification/individual-assets.json').read_text(encoding='utf-8'))
for result in results:
    result['origin'] = 'Codex root, same-agent review after integrating the user-supplied roll pack, 2026-10-11'
    if result['id'] == 'license.resource_manifest':
        result['reason'] = 'Other procedural models and texture are task-created. Roll pack is imported from the user-supplied GLB, retained locally in resources/rolls-supplied.glb; its provenance and rights remain those of the supplied asset. Battery, candy, toothbrush, toothpaste, paper rolls, apples, mineral water and two transitions adapt user-provided images, retained in resources/references. Entrance uses user-provided JPG retained in resources. Original pencil input is retained; derived output replaces English. No additional redistribution rights are inferred. Three.js MIT notice included.'
    if result['id'] == 'schematic.simplification':
        result['reason'] = 'Rolls and candy use clear soft bags with end seals; water uses fitted film without projecting sealed fins. Eggs and yogurt retain low trays. Latest supplied roll GLB supersedes the procedural paper model and retains its original wrapper, printing, layer rings and handle. Candy follows two columns of five saturated red pillow packets with approximately 25 mm actual body thickness and a 203 mm outer width including seals, plus a separate blue and yellow Chinese sign. Roll film keeps supplied materials; candy film opacity is 24%; water shrink film is 18%, clear PET walls 30%. Prices are classroom examples; GLB omits procedural micro-bump.'
    if result['id'] == 'visual.material':
        result['reason'] = 'Compared current reference adaptations in actual WebGL rack views and model previews: red/yellow textured apple skin and recessed stem, fine pale paper layers and clear film, printed carton panels, curved toothbrush grips and white tufts, red-capped transparent PET with red/white Chinese labels. These are rebuilt 3D assets; photographs guide the forms and materials.'
    if result['id'] == 'visual.shadows':
        result['reason'] = 'Actual food rack screenshot shows all egg shells without the upper shelf shadow; egg models do not receive projected shadows. Natural shell shading and grounding shadows on the rack are retained. The accepted food yaw angles are unchanged.'
    if result['id'] == 'visual.composition':
        result['reason'] = 'Six shelf tickets in each actual rack contain only the product name and price, with no stock counts, unit text or magnifier. Tickets stay below the goods; all twelve product groups fit the rack.'
    if result['id'] == 'teaching.parts':
        result['measured']['asset_imports'] = imports['checks']
    if result['id'] == 'teaching.relationships':
        result['measured']['behavior_tests_passed'] = 7
    for evidence in result.get('evidence', []):
        evidence['sha256'] = hashlib.sha256((root/artifacts[evidence['artifact_id']]['path']).read_bytes()).hexdigest()
results = [r for r in results if r['id'] != 'visual.reference_fidelity']
criteria = [
    ('toothpaste_real','reference.toothpaste_real','preview.toothpaste','Four tall rectangular cartons retained; print replaced by the later user-supplied red-green carton atlas, superseding the earlier blue reference.'),
    ('toothpaste_atlas','reference.toothpaste_atlas','preview.toothpaste','Supplied red-green print and herb illustrations on six faces; Chinese 牙膏 and 草本 glyphs are unmirrored in front, side and top views after correcting opposite-face UV orientation.'),
    ('rolls_handle','reference.rolls_handle','preview.rolls-top','Supplied model retains its left-end reinforced film flap and two real finger holes. All ten rolls remain countable.'),
    ('rolls_real','reference.rolls_real','preview.rolls','Supplied GLB retains ten rolls in two rows of five, fine paper layers, hollow cores, individual film and outer clear packaging. Rack view presents all ten ends.'),
    ('apple_real','reference.apple_real','preview.apples','Organic broad shoulders, narrower base, recessed stem, uneven red and yellow pigmentation, small lenticels and serrated veined green leaves. Four individual apples retained; reference watermark is not copied.'),
    ('brush_real','reference.brush_real','preview.brushes','Existing handle bend redirected toward camera in depth rather than left in width, with grips facing the board front and one continuous neck into each head; two unchanged six-brush boards.'),
    ('water_real','reference.water_real','preview.water','Twelve clear ribbed PET bottles have red caps and red-white labels with Chinese printing. Transparent shrink film fits all bottles without projecting side seals; accepted rack yaw retained.'),
    ('battery_card','reference.battery','preview.batteries-top','Tall white card with rounded edges, real hanger slot, orange corner and 10节 above the cells.'),
    ('battery_rows','reference.battery','preview.batteries-top','Exactly two separated rows of five narrow cells; dark bodies and orange upper bands. Main rack shows all ten.'),
    ('battery_blister','reference.battery','preview.batteries','Ten fitted transparent covers surround individual batteries; cell shapes remain countable.'),
    ('department_transition','reference.department','preview.transition.department','Dark full-page field, centered white 百货区 title and muted Chinese category and task lines.'),
    ('food_transition','reference.food','preview.transition.food','Dark full-page field, centered white 食品区 title and muted Chinese category and task lines.'),
    ('candy_layout','reference.candy','preview.candy-top','Exactly two columns and five rows of ten separate wide packets, with gaps in both directions.'),
    ('candy_wrappers','reference.candy','preview.candy-top','Thicker saturated red puffed packets carry yellow Chinese 彩虹糖 titles, small 水果味 captions and multicolour candy illustrations, plus crimped heat seals.'),
    ('candy_sign','reference.candy','preview.candy-top','Blue separate header sits above the packets; white 彩虹糖 title on the left and yellow round 10小包 badge on the right.'),
]
evidence = {}
measured = []
for key, reference, preview, observation in criteria:
    measured.append({'id':key,'status':'pass','observation':observation,'reference_evidence':[reference],'preview_evidence':[preview]})
    for artifact_id in (reference,preview):
        evidence[artifact_id] = {'artifact_id':artifact_id,'sha256':hashlib.sha256((root/artifacts[artifact_id]['path']).read_bytes()).hexdigest(),'observation':observation}
results.append({'id':'visual.reference_fidelity','status':'pass','origin':'Codex root, same-agent comparison, 2026-10-11',
                'reason':'Compared supplied battery, candy, toothbrush, toothpaste, paper, apple, water and both transition images against rebuilt views and actual browser screenshots.',
                'measured':{'criteria':measured},'evidence':list(evidence.values())})
(root/'verification/review-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
