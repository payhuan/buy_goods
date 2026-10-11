"""Register actual portable assets for Blender skill v2 validation."""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
artifacts=[
    {'id':'blend','role':'blend','path':'assets/editable/supermarket.blend'},
    {'id':'glb','role':'glb','path':'assets/models/supermarket.glb'},
    {'id':'source','role':'source','path':'source/build_models.py'},
    {'id':'finalizer','role':'source','path':'source/finalize_catalog.py'},
    {'id':'check_script','role':'check_script','path':'source/checks.py'},
    {'id':'render_config','role':'render_config','path':'assets/build-info.json'},
    {'id':'catalog','role':'source','path':'assets/catalog.json'},
]
for directory in ('images','diagnostics'):
    for path in sorted((root/'assets'/directory).glob('*.png')):
        texture=path.stem=='apple-skin'
        artifacts.append({'id':('texture.' if texture else 'preview.')+path.stem,'role':'texture' if texture else 'preview','path':path.relative_to(root).as_posix()})
for path in sorted((root/'source/tools').glob('*.py')):
    artifacts.append({'id':'tool.'+path.stem,'role':'validator','path':path.relative_to(root).as_posix()})
artifacts.append({'id':'texture.carton_atlas','role':'texture','path':'resources/toothpaste-atlas-chinese.png'})
artifacts.append({'id':'rolls.resource','role':'resource','path':'resources/rolls-supplied.glb'})
artifacts.append({'id':'pencil.resource','role':'resource','path':'resources/pencil-original.glb'})
artifacts.append({'id':'entrance.resource','role':'resource','path':'resources/entrance-background.jpg'})
for key, filename in [('battery','battery.png'),('department','department-transition.png'),('food','food-transition.png'),('candy','candy.png'),('toothpaste_real','toothpaste-real.png'),('rolls_real','rolls-real.png'),('apple_real','apple-real.png'),('brush_real','brush-real.png'),('water_real','water-real.png'),('toothpaste_atlas','toothpaste-atlas-original.png'),('rolls_handle','rolls-handle.png')]:
    artifacts.append({'id':'reference.'+key,'role':'reference','path':'resources/references/'+filename})
for key, filename in [('department','百货过渡页预览.jpg'),('food','食品过渡页预览.jpg')]:
    artifacts.append({'id':'preview.transition.'+key,'role':'preview','path':'verification/'+filename})
manifest={
    'schema_version':2,'quality':{'purpose':'teaching','completion':'final'},
    'requirements':{'description':'Twelve supermarket products with exact countable quantities, realistic product forms and unobstructed labels.',
                    'deliverables':['source','blend','glb','preview'],
                    'units':'metres','reference_relation':'Four user-provided screenshots inform the entrance, department racks and ending; webpage not scraped.',
                    'simplifications':['Transparent bags expose every unit; eggs and yogurt retain low trays.','GLB omits procedural micro-bump.'],
                    'reference':{'mode':'adapt','artifact_ids':['reference.battery','reference.department','reference.food','reference.candy','reference.toothpaste_real','reference.rolls_real','reference.apple_real','reference.brush_real','reference.water_real','reference.toothpaste_atlas','reference.rolls_handle'],
                        'allowed_changes':[{'quote':'牙刷手柄的朝向错了，应该朝相机，现在是朝左，弯曲角度没问题；用这个贴图；给卷纸的包装袋的一端增加提手','source':'User request, 2026-10-11'},{'quote':'牙刷本体按这张参考图重新建模，包装和数量不变；矿泉水按这个参考图重新建模；整体标签只保留物品名、价格','source':'User request, 2026-10-11'},{'quote':'电池重新建模，参考图三','source':'User request, 2026-10-11'},
                                           {'quote':'两个购物页面之前各加上一个过渡页，参考我给出的图一图二两张图片','source':'User request, 2026-10-11'},
                                           {'quote':'彩虹糖参考这张图片建模','source':'User request, 2026-10-11'},
                                           {'quote':'增加彩虹糖每包的厚度，增加彩虹糖红色的饱和度，减少透明袋宽度，使其左右两边更靠近彩虹糖左右两边','source':'User request, 2026-10-11'}],
                        'constraints':[
                            {'id':'toothpaste_atlas','target':'Supplied red-green carton atlas with Chinese toothpaste title replacing English, mapped onto four carton faces and ends.', 'basis':'User unfolded toothpaste texture','knowledge':'visible','method':'visual'},
                            {'id':'rolls_handle','target':'Latest supplied model.glb supersedes previous roll geometry: retain its left-end two-hole handle and transparent packaging.', 'basis':'User paper-bag handle photo','knowledge':'visible','method':'visual'},
                            {'id':'toothpaste_real','target':'Four slim retail cartons and folded edges; latest supplied red-green texture supersedes the earlier cyan brand print.', 'basis':'User toothpaste photo','knowledge':'visible','method':'visual'},
                            {'id':'rolls_real','target':'Two rows of five ivory paper ends, hollow cardboard cores, fine winding lines and clear wrinkled film.', 'basis':'User paper photo','knowledge':'visible','method':'visual'},
                            {'id':'apple_real','target':'Broad shoulders, recessed stem, uneven red and golden skin, lenticels and a natural leaf.', 'basis':'User apple photo; source watermark excluded from original texture','knowledge':'visible','method':'visual'},
                            {'id':'brush_real','target':'White curved handle with long blue, lilac or green grip insert, narrow coloured neck, oval head and dense white tuft rows. Two six-brush boards preserved.', 'basis':'User toothbrush photo','knowledge':'visible','method':'visual'},
                            {'id':'water_real','target':'Twelve clear ribbed bottles with red caps, white upper labels and red lower labels inside fitted shrink film; Chinese print.', 'basis':'User mineral water photo','knowledge':'visible','method':'visual'},
                            {'id':'battery_card','target':'Narrow rounded white retail card, hanger hole, orange corner marker and Chinese quantity above cells.', 'basis':'User image three','knowledge':'visible','method':'visual'},
                            {'id':'battery_rows','target':'Ten vertical cells in two rows of five, dark bodies and orange upper bands.', 'basis':'User image three','knowledge':'visible','method':'visual'},
                            {'id':'battery_blister','target':'Transparent fitted blister exposes all ten cells.', 'basis':'User image three','knowledge':'visible','method':'visual'},
                            {'id':'department_transition','target':'Dark full-page background, centered white department title and muted Chinese task lines.', 'basis':'User image two','knowledge':'visible','method':'visual'},
                            {'id':'food_transition','target':'Dark full-page background, centered white food title and muted Chinese task lines.', 'basis':'User image one','knowledge':'visible','method':'visual'},
                            {'id':'candy_layout','target':'Ten distinct packets in two columns and five rows with visible gaps.', 'basis':'User candy image','knowledge':'visible','method':'visual'},
                            {'id':'candy_wrappers','target':'Horizontal red packets with Chinese yellow title, heat sealed rims and multicoloured candy graphics.', 'basis':'User candy image','knowledge':'visible','method':'visual'},
                            {'id':'candy_sign','target':'Separate blue 彩虹糖 header with a yellow circular 10小包 badge above the ten packets.', 'basis':'User candy image','knowledge':'visible','method':'visual'}]}},
    'parameters':{'samples':20,'layout':'unobstructed repeated units','seed':0},
    'budgets':{},'collection':'MODEL','blend':'assets/editable/supermarket.blend',
    'glb':'assets/models/supermarket.glb','frames':[1],'tolerance':.0002,
    'resources':[{'artifact_id':'pencil.resource','source':'User-provided local pencil GLB','license':'User-provided; no third-party redistribution rights inferred.',
                  'attribution':'User-provided Pencil_Box_10支.glb','redistribution':'For this user project; additional redistribution rights are not established.'}],
    'artifacts':artifacts,
    'acceptance':[{'id':'task.product_counts','method':'task','required':True,
                   'rule':'User product inventory, 2026-10-11','check_deps':['blend','glb','source','check_script','rolls.resource'],'config':{}},
                  {'id':'task.packaging','method':'task','required':True,
                   'rule':'User transparent bags and battery card request, 2026-10-11','check_deps':['blend','glb','source','check_script','rolls.resource'],'config':{}},
                  {'id':'task.real_forms','method':'task','required':True,'rule':'User reference shapes with unchanged package quantities','check_deps':['blend','glb','source','check_script','rolls.resource'],'config':{}},
                  {'id':'task.current_repairs','method':'task','required':True,'rule':'User front-facing handles, carton texture and paper-bag grip','check_deps':['blend','glb','source','check_script','rolls.resource'],'config':{}},
                  {'id':'task.carton_uv_orientation','method':'task','required':True,'rule':'No mirrored toothpaste text on outward carton faces','check_deps':['blend','glb','source','check_script','rolls.resource'],'config':{}}],
}
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
