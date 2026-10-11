"""Package a standalone HTML with all runtime modules and binary assets embedded."""
import base64
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root/'publish'
output.mkdir(exist_ok=True)
modules = {
    'market-three-core':'vendor/three.core.js',
    'market-three':'vendor/three.module.js',
    'market-buffer-utils':'vendor/BufferGeometryUtils.js',
    'market-gltf-loader':'vendor/GLTFLoader.js',
    'market-scene':'scene.js',
    'market-meshopt':'vendor/meshopt_decoder.mjs',
}
aliases = {
    'three':'market-three', './three.core.js':'market-three-core',
    './BufferGeometryUtils.js':'market-buffer-utils',
    './vendor/meshopt_decoder.mjs':'market-meshopt',
    './vendor/three.module.js':'market-three', './vendor/GLTFLoader.js':'market-gltf-loader',
}
module_sources = {}
for key, path in modules.items():
    source = (root/path).read_text(encoding='utf-8-sig')
    for alias, target in aliases.items():
        source = re.sub(r'(\bfrom\s*)([\x27\x22])'+re.escape(alias)+r'\2', lambda m:m[1]+m[2]+target+m[2], source)
    module_sources[key] = source

catalog = json.loads((root/'assets/catalog.json').read_text(encoding='utf-8'))
assets, inventory = {}, []
for item in catalog:
    paths = [f"assets/models/{item['id']}.glb", f"assets/images/{item['id']}.png"]
    for path in paths:
        content = (root/path).read_bytes()
        mime = 'model/gltf-binary' if path.endswith('.glb') else 'image/png'
        assets[path] = f'data:{mime};base64,'+base64.b64encode(content).decode('ascii')
        inventory.append({'path':path,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})

background_path = 'assets/images/entrance-background.jpg'
content = (root/background_path).read_bytes()
assets[background_path] = 'data:image/jpeg;base64,'+base64.b64encode(content).decode('ascii')
inventory.append({'path':background_path,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})

def safe_json(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')

bootstrap = '<script>\n/* All models, images and modules are embedded; no CDN or local server dependency. */\n'
bootstrap += 'globalThis.MARKET_EMBEDDED_ASSETS='+safe_json(assets)+';\n'
bootstrap += 'const embeddedModules='+safe_json(module_sources)+';\n'
bootstrap += "const embeddedImports={imports:{}}; for(const [name,source] of Object.entries(embeddedModules)) embeddedImports.imports[name]=URL.createObjectURL(new Blob([source],{type:'text/javascript'}));\n"
bootstrap += "const importMap=document.createElement('script'); importMap.type='importmap'; importMap.textContent=JSON.stringify(embeddedImports); document.head.append(importMap);\n</script>"
html = (root/'index.html').read_text(encoding='utf-8-sig')
html = re.sub(r'<script type="importmap">.*?</script>',lambda m:bootstrap,html,flags=re.S)
css = (root/'styles.css').read_text(encoding='utf-8-sig')
html = re.sub(r'<link rel="stylesheet" href="[^"]+">',lambda m:'<style>'+css+'</style>',html)
def inline_script(match):
    source = (root/match[1].split('?')[0]).read_text(encoding='utf-8-sig')
    source = re.sub(r"import\('\./scene\.js[^']*'\)","import('market-scene')",source)
    assert '</script' not in source.lower()
    return '<script>\n'+source+'\n</script>'
html = re.sub(r'<script src="([^"]+)"></script>',inline_script,html)
target = output/'逛超市_超喵单文件版.html'
target.write_text(html,encoding='utf-8')
report = {'format':'standalone HTML','models':12,'images':13,'embedded_modules':list(modules),
          'external_runtime_files':0,'html_bytes':target.stat().st_size,'assets':inventory,
          'runtime':'Modern browser with WebGL, import maps and Blob modules; audio synthesized locally.'}
(output/'资源依赖清单.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(output/'THREE-LICENSE.txt').write_text((root/'vendor/THREE-LICENSE.txt').read_text(encoding='utf-8'),encoding='utf-8')
print(f'{target.name}: {target.stat().st_size/1024/1024:.1f} MB, 12 models + 13 images embedded')
