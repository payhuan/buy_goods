"""Original teaching assets, metres, Blender 5.x. Run from any working directory.

Rebuild: blender --background --factory-startup --disable-autoexec --python
source/build_models.py -- --output-dir <NEW DIRECTORY>
The supplied pencil GLB is retained as input; visible English is replaced.
"""
import argparse
import json
import math
import sys
import shutil
import random
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', type=Path, default=ROOT / 'assets')
parser.add_argument('--samples', type=int, default=20)
parser.add_argument('--changed-products', nargs='+', default=['rolls','toothpaste','brushes','water','apples'])
parser.add_argument('--reuse-previews', type=Path, help='Reuse unchanged product previews from a previous output directory')
parser.add_argument('--font', type=Path, default=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc')
parser.add_argument('--bold-font', type=Path, default=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyhbd.ttc')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
OUT = args.output_dir.resolve()
for folder in ('models', 'images', 'editable', 'diagnostics'):
    (OUT / folder).mkdir(parents=True, exist_ok=True)
if (OUT / 'catalog.json').exists():
    raise FileExistsError('Use a new output directory; existing successful assets are preserved.')
if not args.font.is_file():
    raise FileNotFoundError('Provide a Chinese font using --font; no font is installed automatically.')
if not args.bold_font.is_file():
    raise FileNotFoundError('Provide a Chinese bold font using --bold-font; no font is installed automatically.')
shutil.copy2(ROOT/'resources/entrance-background.jpg',OUT/'images/entrance-background.jpg')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = args.samples
scene.cycles.use_denoising = True
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = True
scene.render.resolution_percentage = 100
scene.world.color = (.36, .36, .36)
scene.view_settings.view_transform = 'AgX'
chinese_font=bpy.data.fonts.load(str(args.font))
chinese_bold_font=bpy.data.fonts.load(str(args.bold_font))
bold_labels={'10节','牙膏','柔软牙刷','彩虹糖','薯片','矿泉水','酸奶','原味酸奶'}
printed_labels=[]

def material(name, color, rough=.4, metal=0, alpha=1):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, alpha)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    # Principled opacity belongs in its Alpha socket, not Base Color's alpha.
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        m.surface_render_method = 'DITHERED'
    return m

white = material('Ivory paper', (.87, .83, .74), .85)
paperedge = material('Visible paper winding grooves', (.78, .75, .68), .92)
candyred = material('Candy raspberry red wrapper', (.95, .015, .035), .42)
milk = material('Porcelain glaze', (.90, .92, .88), .21)
blue = material('Cobalt blue', (.035, .23, .57), .25)
mint = material('Mint ceramic', (.18, .56, .43), .22)
pink = material('Coral ceramic', (.83, .29, .20), .23)
red = material('Printed vermilion', (.71, .032, .035), .38)
yellow = material('Printed sunshine', (.94, .57, .035), .34)
green = material('Printed emerald', (.025, .35, .17), .38)
ink = material('Dark printing', (.035, .07, .065), .55)
silver = material('Brushed aluminium', (.67, .70, .73), .28, .88)
black = material('Battery charcoal', (.028, .034, .040), .3)
gold = material('Battery gold jacket', (.80, .44, .08), .32, .65)
orange = material('Battery orange copper jacket', (.93, .25, .035), .30, .42)
card = material('Kraft paper fibres', (.52, .35, .20), .91)
plastic = material('Transparent side film', (.82, .93, 1), .12, alpha=.16)
bagfilm = material('Clear flexible bag film', (.80, .91, .98), .18, alpha=.24)
bagseal = material('Transparent heat sealed folds', (.68, .83, .93), .25, alpha=.55)
blisterfilm = material('Clear fitted battery blister', (.88, .95, 1), .12, alpha=.065)
water = material('Clear PET bottle wall', (.78, .88, .90), .12, alpha=.30)
waterfilm = material('Water fitted shrink film', (.90, .95, .97), .16, alpha=.18)
waterlabel = material('Mineral water red label', (.66, .012, .025), .40)
leafmat = material('Natural apple leaf', (.20,.32,.018), .68)
eggmat = material('Natural eggshell', (.79, .58, .36), .89)
applemat = material('Apple wax skin', (.46, .018, .022), .43)
stemmat = material('Apple stem wood', (.16, .075, .028), .8)

# Original UV texture: uneven red/yellow pigmentation and small lenticels.
# Packed in blend and embedded in GLB, so both viewers retain the same skin.
skin=bpy.data.images.new('Original apple skin pigmentation',width=1024,height=512)
rng=random.Random(39)
spots={(rng.randrange(1024),rng.randrange(512)) for _ in range(2200)}
pixels=[]
for py in range(512):
    v=py/512
    for px in range(1024):
        u=px/1024
        patch=math.sin(u*math.tau+1.3)*.62+math.cos(u*19+v*9)*.20+math.sin(u*35-v*11)*.12
        yellowpatch=max(0,patch-.05)*(.30+.45*abs(2*v-1)**2)
        streak=(.5+.5*math.sin(u*290+math.sin(v*15)*.8))**5
        grain=rng.uniform(-.022,.022)
        color=[.56+.24*yellowpatch+.05*streak+grain,.035+.64*yellowpatch+.025*streak+grain*.4,.019+.15*yellowpatch+grain*.2]
        if (px,py) in spots:
            color=[.73,.46,.21]
        pixels.extend((*color,1))
skin.pixels=pixels
skin.filepath_raw=str(OUT/'images'/'apple-skin.png')
skin.file_format='PNG'
skin.save()
skin.pack()
tex=applemat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image=skin
applemat.node_tree.links.new(tex.outputs['Color'],applemat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

# Subtle procedural surfaces become geometry/material colours in GLB; nodes
# remain editable in .blend. No external images or fonts are required.
for m, scale, strength in [(white, 120, .11), (card, 85, .16), (eggmat, 65, .08), (applemat, 110, .025)]:
    p = m.node_tree.nodes.get('Principled BSDF')
    noise = m.node_tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    bump = m.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = .0003
    m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    m.node_tree.links.new(bump.outputs['Normal'], p.inputs['Normal'])

current = None
def finish(o, name, mat, smooth=False):
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    current.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    if smooth and o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
    return o

def box(name, loc, size, mat, bevel=.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(o, name, mat)
    if bevel:
        mod = o.modifiers.new('Manufactured edge rounding', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return o

def cylinder(name, loc, radius, depth, mat, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=loc)
    o = finish(bpy.context.object, name, mat, True)
    if rotation:
        o.rotation_euler = rotation
    mod = o.modifiers.new('Rolled edge', 'BEVEL')
    mod.width = min(.001, radius / 8, depth / 6)
    mod.segments = 2
    o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return o

def sphere(name, loc, size, mat, segments=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    o = finish(bpy.context.object, name, mat, True)
    o.scale = size
    return o

def pouch(name, x, y, mat, width=.045, height=.070, puff=.025):
    # Two curved faces meet at a real, thin sealed perimeter.
    nx,ny=16,24
    vertices=[]
    for side in (0,1):
        for j in range(ny+1):
            v=j/ny*2-1
            for i in range(nx+1):
                u=i/nx*2-1
                dome=max(0,(1-u*u)*(1-v*v))**.6
                crease=.0015*math.cos(u*28+v*9)*max(0,abs(v)-.5)*dome
                z=.006+(puff*dome+crease if side else -.002*dome)
                vertices.append((x+u*width/2,y+v*height/2,z))
    stride=nx+1; count=stride*(ny+1); faces=[]
    for side in (0,1):
        for j in range(ny):
            for i in range(nx):
                a=side*count+j*stride+i
                face=(a,a+1,a+1+stride,a+stride)
                faces.append(face if side else tuple(reversed(face)))
    boundary=list(range(stride))+[j*stride+nx for j in range(1,ny+1)]+[ny*stride+i for i in range(nx-1,-1,-1)]+[j*stride for j in range(ny-1,0,-1)]
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):
        faces.append((a,b,b+count,a+count))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh);current.objects.link(o)
    o.data.materials.append(mat)
    for face in mesh.polygons: face.use_smooth=True
    return o

def lathe(name, loc, profile, mat, segments=64):
    # Closed cross section allows hollow cups and physical roll cores.
    vertices = [(loc[0]+r*math.cos(2*math.pi*i/segments), loc[1]+r*math.sin(2*math.pi*i/segments), loc[2]+z)
                for r,z in profile for i in range(segments)]
    faces = []
    for j in range(len(profile)):
        k = (j+1) % len(profile)
        for i in range(segments):
            a = j*segments+i
            b = j*segments+(i+1)%segments
            c = k*segments+(i+1)%segments
            d = k*segments+i
            faces.append((a,b,c,d))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    current.objects.link(o)
    o.data.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    return o

def torus(name, loc, major, minor, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                   major_segments=48, minor_segments=12, location=loc)
    o = finish(bpy.context.object, name, mat, True)
    if rotation:
        o.rotation_euler = rotation
    return o

def text(name, body, loc, size, mat, top=False):
    bpy.ops.object.text_add(location=loc)
    o = bpy.context.object
    o.data.body = body
    o.data.font = chinese_bold_font if body in bold_labels else chinese_font
    printed_labels.append({'object':name,'text':body,'font_weight':'bold' if body in bold_labels else 'regular'})
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    o.data.size = size
    o.data.extrude = .00008
    if not top:
        o.rotation_euler = (math.pi/2, 0, 0)
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object, name, mat)

def tray(w, d, h=.015, mat=card):
    box('Packaging base', (0,0,.002), (w,d,.004), mat, .001)
    for x in (-w/2,w/2):
        box('Packaging side', (x,0,h/2), (.003,d,h), mat, .001)
    for y in (-d/2,d/2):
        box('Packaging end', (0,y,h/2), (w,.003,h), mat, .001)

def grid(cols, rows, dx, dy):
    for row in range(rows):
        for col in range(cols):
            yield row*cols+col+1, (col-(cols-1)/2)*dx, (row-(rows-1)/2)*dy

def marker(index, loc, package=1):
    o = bpy.data.objects.new(f'UNIT_{package:02}_{index:02}', None)
    o.location = loc
    o['countable_unit'] = True
    o['package'] = package
    o['index'] = index
    current.objects.link(o)
    return o

def rolls():
    # Keep the supplied model intact; its paper ends already face Blender -Y.
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'resources/rolls-supplied.glb'))
    for obj in set(bpy.data.objects)-before:
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        current.objects.link(obj)

def transparent_bag(name, w, d, h, sealed_ends=True, seal_extension=.018, seal_width=.009):
    # Puffed continuous film tube with rounded shoulders and flattened end seals.
    vertices, faces = [], []
    length_segments, ring_segments = 40, 64
    def signed_power(value):
        return math.copysign(abs(value)**(1/3),value)
    for j in range(length_segments+1):
        x = (j/length_segments*2-1)*(w/2+(seal_extension if sealed_ends else 0))
        pinch = max(0,(abs(x)-w/2)/seal_extension) if sealed_ends else 0
        for i in range(ring_segments):
            angle = i/ring_segments*math.tau
            wrinkle = .0012*math.sin(x*180+angle*9)*(1-pinch)
            y = signed_power(math.cos(angle))*(d/2+wrinkle)
            z = h/2 + signed_power(math.sin(angle))*(h/2+.002+wrinkle)*(1-.97*pinch)
            vertices.append((x,y,z))
    for j in range(length_segments):
        for i in range(ring_segments):
            a=j*ring_segments+i; b=j*ring_segments+(i+1)%ring_segments
            faces.append((a,b,b+ring_segments,a+ring_segments))
    faces.append(tuple(reversed(range(ring_segments))))
    faces.append(tuple(length_segments*ring_segments+i for i in range(ring_segments)))
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(vertices,[],faces); mesh.update()
    obj = bpy.data.objects.new(name,mesh); current.objects.link(obj); mesh.materials.append(bagfilm)
    for face in mesh.polygons: face.use_smooth = True
    for sign in ((-1,1) if sealed_ends else ()):
        box(name+' end seal',(sign*(w/2+seal_extension+.002),0,h/2),(seal_width,d,.0012),bagseal,.0004)
        for i in range(18):
            box(name+' seal crimp',(sign*(w/2+seal_extension+.002),(i-8.5)*d/19,h/2+.001),(seal_width,.0007,.0005),bagseal,.0002)

def mugs():
    for i,x,y in grid(3,1,.13,0):
        mat = (mint,milk,pink)[i-1]
        marker(i,(x,y,0))
        lathe(f'Mug {i} hollow ceramic body',(x,y,0),[(.030,0),(.038,.003),(.040,.083),(.039,.088),(.034,.088),(.033,.010),(.030,.010)],mat)
        torus(f'Mug {i} handle',(x+.051,y,.046),.027,.006,mat,(math.pi/2,0,0))
        cylinder(f'Mug {i} inner bottom',(x,y,.008),.033,.006,mat)

def toothpastes():
    atlas=bpy.data.images.load(str(ROOT/'resources/toothpaste-atlas-chinese.png'),check_existing=True)
    atlas.pack()
    printed=material('User toothpaste carton atlas',(.95,.95,.95),.43)
    node=printed.node_tree.nodes.new('ShaderNodeTexImage');node.image=atlas
    printed.node_tree.links.new(node.outputs['Color'],printed.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    # Panel rectangles in normalised coordinates of the supplied unfolded carton.
    panels={'front':(192/1052,171/646,868/1052,293/646),
            'back':(192/1052,441/646,868/1052,605/646),
            'left':(192/1052,38/646,868/1052,138/646),
            'right':(192/1052,315/646,868/1052,438/646),
            'end':(22/1052,154/646,178/1052,309/646)}
    for i,x,y in grid(4,1,.054,0):
        marker(i,(x,y,0))
        body=box(f'Toothpaste box {i}',(x,0,.093),(.042,.032,.186),printed,.00045)
        uv=body.data.uv_layers.active
        for face in body.data.polygons:
            n=face.normal
            panel='front' if n.y<-.5 else 'back' if n.y>.5 else 'left' if n.x<-.5 else 'right' if n.x>.5 else 'end'
            u0,v0,u1,v1=panels[panel]
            for idx in face.loop_indices:
                co=body.data.vertices[body.data.loops[idx].vertex_index].co
                if panel=='end':a=(co.x+.021)/.042;b=(co.y+.016)/.032
                else:
                    a=(.093-co.z)/.186
                    b=(co.x+.021)/.042 if panel in ('front','back') else (co.y+.016)/.032
                # Opposite outward faces have opposite transverse axes.
                # Keep UV winding positive to rotate print without mirroring it.
                if panel in ('front','right') or (panel=='end' and n.z>0):b=1-b
                uv.data[idx].uv=(u0+a*(u1-u0),1-(v0+b*(v1-v0)))
        for z in (.002,.183):
            box(f'Toothpaste folded carton seam {i}',(x,-.0165,z),(.039,.0003,.0005),milk,.0001)

def organic_sweep(name, x, sections, mat):
    verts=[]; faces=[]; n=16
    for y,offset,z,w,t in sections:
        for k in range(n):
            angle=k*math.tau/n
            verts.append((x+offset+w*math.cos(angle),y,z+t*math.sin(angle)))
    for j in range(len(sections)-1):
        for k in range(n):
            a=j*n+k; b=j*n+(k+1)%n
            faces.append((a,b,b+n,a+n))
    faces.extend([tuple(reversed(range(n))),tuple((len(sections)-1)*n+k for k in range(n))])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);current.objects.link(o);mesh.materials.append(mat)
    for f in mesh.polygons:f.use_smooth=True
    mod=o.modifiers.new('Smooth moulded contour','SUBSURF');mod.levels=1;mod.render_levels=1
    return o

def brushes():
    brushpurple=material('Toothbrush lilac silicone',(.47,.19,.61),.35)
    brushgreen=material('Toothbrush spring green silicone',(.12,.58,.22),.35)
    brushwhite=material('Toothbrush ivory moulding',(.91,.92,.89),.32)
    for package,center in enumerate((-.115,.115),1):
        box(f'Board {package} backing',(center,.0,.003),(.212,.225,.006),milk,.007)
        box(f'Board {package} header',(center,.088,.008),(.212,.042,.004),blue,.001)
        text(f'Board {package} title','柔软牙刷',(center,.087,.011),.022,milk,True)
        for i in range(6):
            x=center+(i-2.5)*.033; name=f'Brush {package}.{i+1}'
            marker(i+1,(x,0,.014),package)
            color=(blue,brushpurple,brushgreen)[i%3]
            sections=[]
            for j in range(25):
                t=j/24; y=-.098+t*.143
                w=.0065*(.72+.27*math.sin(t*math.pi)) if t<.67 else .0065*(1-(t-.67)*1.9)
                if j in (0,24): w*=.65
                sections.append((y,0,.015+.0015*math.sin(t*math.pi)+.0027*math.sin(t*math.tau),w,.004))
            # Keep the existing bend but turn its plane toward the camera (+Z),
            # continuing the same body into the head so there is no forked neck.
            sections.extend([(.050,0,.018,.0031,.0028),(.057,0,.019,.004,.0027)])
            body=organic_sweep(name+' rounded handle',x,sections,brushwhite)
            body.data.materials.append(color)
            for face in body.data.polygons:
                if sum(body.data.vertices[v].co.y for v in face.vertices)/len(face.vertices)>.014:face.material_index=1
            insert=[(y,offset-.0004,z+.0035,w*.55,.0009) for y,offset,z,w,th in sections[:19]]
            organic_sweep(name+' coloured curved silicone grip',x,insert,color)
            sphere(name+' thumb grip button',(x,.004,.021),(.0024,.003,.001),color)
            box(name+' head',(x,.059,.019),(.015,.029,.008),color,.006)
            box(name+' white bristle base',(x,.059,.024),(.014,.027,.003),brushwhite,.005)
            for col in range(3):
                for row in range(6):
                    bx=x+(col-1)*.0037; by=.048+row*.0043
                    sphere(name+f' bristle tuft {col}.{row}',(bx,by,.029),(.0018,.0020,.005),brushwhite,segments=12,rings=8)
                    for fibre in (-1,0,1):
                        box(name+' fine bristle',(bx+fibre*.00065,by,.031),(.00035,.0028,.006),brushwhite,.0001)

def batteries():
    backing = box('Battery retail backing card',(0,.02,.003),(.148,.215,.006),milk,.009)
    cutter = box('Hanger slot cutter',(0,.105,.003),(.038,.007,.02),milk,.003)
    slot = backing.modifiers.new('Real hanger hole','BOOLEAN'); slot.operation='DIFFERENCE'; slot.object=cutter
    bpy.context.view_layer.objects.active=backing; bpy.ops.object.modifier_apply(modifier=slot.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    box('Battery card orange corner',(.058,.107,.007),(.012,.012,.001),orange,.005)
    text('Battery pack quantity','10节',(0,.077,.0072),.018,red,True)
    # An outlined hanging tab and clear fitted blister match the supplied card.
    for i,x,y in grid(5,2,.026,.066):
        y -= .014
        marker(i,(x,y,.012))
        cylinder(f'Battery {i} AA body',(x,y,.016),.007,.048,black,(math.pi/2,0,0))
        cylinder(f'Battery {i} gold band',(x,y+.017,.016),.0072,.012,orange,(math.pi/2,0,0))
        cylinder(f'Battery {i} positive terminal',(x,y+.025,.018),.004,.003,silver,(math.pi/2,0,0))
        cylinder(f'Battery {i} negative terminal',(x,y-.024,.018),.007,.0015,silver,(math.pi/2,0,0))
        text(f'Battery {i} AA print','电池',(x,y-.004,.0232),.005,milk,True)
        box(f'Battery {i} fitted clear blister',(x,y,.016),(.019,.055,.023),blisterfilm,.005)

def bottles():
    transparent_bag('Water sealed transparent bag',.312,.232,.185,sealed_ends=False)
    current.objects.get('Water sealed transparent bag').data.materials[0]=waterfilm
    for i,x,y in grid(4,3,.074,.074):
        marker(i,(x,y,.006))
        lathe(f'Water bottle {i} PET body',(x,y,.006),[(.001,0),(.026,0),(.030,.008),(.031,.022),(.030,.09),(.029,.116),(.025,.131),(.015,.148),(.012,.158),(.010,.158),(.013,.146),(.024,.129),(.027,.114),(.028,.015),(.002,.003)],water)
        for z in (.016,.025,.036,.106,.113):
            torus(f'Water bottle {i} moulded rib',(x,y,z+.006),.0301,.00065,water)
        cylinder(f'Water bottle {i} red cap',(x,y,.168),.014,.018,red)
        torus(f'Water bottle {i} tamper band',(x,y,.159),.0134,.001,red)
        cylinder(f'Water bottle {i} printed wrap',(x,y,.071),.0312,.062,milk)
        cylinder(f'Water bottle {i} red lower label',(x,y,.055),.03145,.031,waterlabel)
        text(f'Water bottle {i} label','矿泉水',(x,y-.0319,.057),.011,milk)
        text(f'Water bottle {i} volume','净含量500毫升',(x,y-.0319,.046),.0047,milk)
        # Chinese mountain emblem in the upper white label, with fine legal-print rules.
        for k in range(3):
            mountain=box(f'Water bottle {i} mountain emblem',(x+(k-1)*.004,y-.0318,.087),(.006,.0004,.012-k*.002),green,.0002)
            mountain.rotation_euler.y=.25*(k-1)
        for k in range(4):box(f'Water bottle {i} fine label rule',(x-.021,y-.0235,.077+k*.003),(.010,.0003,.00045),red,.0001)
        for k in range(24):
            a=k*math.tau/24
            box(f'Cap {i} grip',(x+.014*math.cos(a),y+.014*math.sin(a),.168),(.0007,.0007,.014),red,.00015)

def chips():
    for i,x,y in grid(3,2,.09,.10):
        marker(i,(x,y,0))
        cylinder(f'Chips can {i}',(x,y,.108),.037,.214,red)
        cylinder(f'Chips can {i} metal base',(x,y,.006),.0375,.009,silver)
        cylinder(f'Chips can {i} lid',(x,y,.219),.038,.008,milk)
        torus(f'Chips can {i} lid rim',(x,y,.224),.0365,.0016,silver)
        text(f'Chips can {i} title','薯片',(x,y-.0374,.152),.025,milk)
        text(f'Chips can {i} subtitle','原味',(x,y-.0374,.125),.012,yellow)
        sphere(f'Chips can {i} potato illustration',(x,y-.036,.075),(.020,.002,.024),yellow)

def candy():
    transparent_bag('Candy sealed transparent outer bag',.190,.315,.040,seal_extension=.003,seal_width=.003)
    colors=(red,blue,yellow,green,pink)
    box('Candy blue quantity sign',(0,.207,.008),(.194,.049,.007),blue,.004)
    text('Candy sign title','彩虹糖',(-.034,.207,.012),.032,milk,True)
    cylinder('Candy yellow quantity badge',(.062,.207,.014),.029,.003,yellow)
    text('Candy sign quantity','10小包',(.062,.207,.016),.016,ink,True)
    for i,x,y in grid(2,5,.097,.062):
        marker(i,(x,y,.005))
        pouch(f'Candy mini pouch {i}',x,y,candyred,width=.088,height=.054,puff=.023)
        for dy in (-.0255,.0255):
            box(f'Candy pouch {i} heat seal',(x,y+dy,.006),(.086,.003,.002),candyred,.0006)
            for n in range(13):
                box(f'Candy pouch {i} crimp',(x+(n-6)*.006,y+dy,.0072),(.0007,.0025,.0005),candyred,.0002)
        text(f'Candy pouch {i} printed title','彩虹糖',(x,y+.009,.0285),.012,yellow,True)
        text(f'Candy pouch {i} bottom caption','水果味',(x,y-.019,.0212),.0045,milk,True)
        for n in range(6):
            angle=math.pi*.1+n*math.pi*.16
            sphere(f'Candy pouch {i} rainbow print {n+1}',(x+math.cos(angle)*.014,y-.009+math.sin(angle)*.006,.030),(.0038,.0028,.0008),colors[n%5])

def yogurts():
    tray(.365,.164,.016,blue)
    for i,x,y in grid(5,2,.071,.076):
        marker(i,(x,y,.006))
        lathe(f'Yogurt cup {i}',(x,y,.006),[(.001,0),(.023,0),(.030,.055),(.032,.058),(.001,.058)],milk)
        cylinder(f'Yogurt cup {i} foil seal',(x,y,.065),.033,.0025,blue)
        torus(f'Yogurt cup {i} rim',(x,y,.065),.032,.001,silver)
        text(f'Yogurt cup {i} lid print','酸奶',(x,y,.0668),.018,milk,True)
        box(f'Yogurt cup {i} pull tab',(x+.031,y,.065),(.012,.014,.0016),silver,.004)
        text(f'Yogurt cup {i} front print','原味酸奶',(x,y-.028,.039),.008,blue)

def eggs():
    tray(.318,.142,.023)
    for i,x,y in grid(5,2,.062,.064):
        marker(i,(x,y,.009))
        lathe(f'Egg carton {i} molded socket',(x,y,.006),[(.021,0),(.028,.010),(.029,.018),(.024,.017),(.018,.006)],card,32)
        o = sphere(f'Egg {i}',(x,y,.038),(.023,.023,.032),eggmat)
        # Eggs narrow smoothly toward the upper pole.
        for v in o.data.vertices:
            taper = 1-.12*max(0,v.co.z)
            v.co.x *= taper
            v.co.y *= taper

def apples():
    for i,x,y in grid(4,1,.096,0):
        marker(i,(x,y,0))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=36, radius=1, location=(x,y,.039))
        o = finish(bpy.context.object,f'Apple {i} organic lobed skin',applemat,True)
        for uv in o.data.uv_layers.active.data:
            uv.uv.x+=(i-1)*.17
        for v in o.data.vertices:
            z = v.co.z
            angle = math.atan2(v.co.y,v.co.x)
            lobe = 1+.045*math.cos(5*angle+.15*i)*(abs(z)**3)
            v.co.x *= .042*lobe*(1+.13*z)
            v.co.y *= .041*lobe*(1+.12*z)
            v.co.z = .041*z - .009*max(0,z)**16 + .004*max(0,-z)**8 + .0013*math.cos(5*angle)*abs(z)**5
        cylinder(f'Apple {i} stem',(x+.002,y,.078),.0022,.018,stemmat,(0,.2,.1))
        vertices=[];faces=[]
        for j in range(17):
            t=j/16; ly=y+t*.016; lx=x+.002+t*.037
            width=.009*math.sin(math.pi*t)*(1+.07*(-1)**j)
            for side in (-1,0,1):vertices.append((lx,ly+side*width,.082+.004*math.sin(t*math.pi)-.004*side*side))
        for j in range(16):
            for k in range(2):a=j*3+k;faces.append((a,a+1,a+4,a+3))
        mesh=bpy.data.meshes.new(f'Apple {i} serrated leaf');mesh.from_pydata(vertices,[],faces);mesh.update()
        leaf=bpy.data.objects.new(f'Apple {i} veined natural leaf',mesh);current.objects.link(leaf);mesh.materials.append(leafmat)
        for face in mesh.polygons:face.use_smooth=True
        for j in range(8):
            t=(j+.5)/8
            vein=sphere(f'Apple {i} leaf midrib',(x+.002+t*.037,y+t*.016,.0824+.004*math.sin(t*math.pi)),(.003,.00045,.0003),leafmat,segments=12,rings=6)
            vein.rotation_euler.z=.4
        # Small transparent beads follow the skin rather than a regular dot pattern.
        for k in range(4):
            a=3.6+((i*13+k*7)%19)*.073;z=.008+((i*11+k*3)%13)*.0014
            radius=.041*math.sqrt(max(0,1-(z/.043)**2))*(1+.13*z/.04)
            sphere(f'Apple {i} dew bead {k}',(x+radius*math.cos(a),y+radius*math.sin(a),.039+z),(.00045,.00045,.00075),plastic,segments=12,rings=8)

catalog = [
    ('rolls','卷纸','百货区',10,1,'袋',19.9,rolls),
    ('mugs','水杯','百货区',1,3,'个',12.9,mugs),
    ('toothpaste','牙膏','百货区',1,4,'盒',8.9,toothpastes),
    ('brushes','牙刷','百货区',6,2,'板',15.9,brushes),
    ('batteries','电池','百货区',10,1,'板',19.9,batteries),
    ('pencils','铅笔','百货区',10,1,'盒',9.9,None),
    ('water','矿泉水','食品区',12,1,'件',18.0,bottles),
    ('chips','筒装薯片','食品区',1,6,'筒',8.9,chips),
    ('candy','彩虹糖','食品区',10,1,'袋',12.9,candy),
    ('yogurt','酸奶','食品区',10,1,'件',24.9,yogurts),
    ('eggs','鸡蛋','食品区',10,1,'盒',12.0,eggs),
    ('apples','苹果','食品区',1,4,'个',4.0,apples),
]

def bounds(objects):
    bpy.context.view_layer.update()
    points=[o.matrix_world @ Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
    lo=Vector([min(v[i] for v in points) for i in range(3)])
    hi=Vector([max(v[i] for v in points) for i in range(3)])
    return lo,hi

# Studio lighting is intentionally broad to reveal contours and countable gaps.
studio = bpy.data.collections.new('STUDIO')
scene.collection.children.link(studio)
current = studio
bpy.ops.object.camera_add()
camera=bpy.context.object
finish(camera,'Camera',None)
scene.camera=camera
camera.data.type='ORTHO'
for name,loc,power,size in [('Key',(-1,-1,1.7),85,1.3),('Fill',(1,-.3,1),50,1.0),('Rim',(0,1,1.3),70,.9)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector((0,0,.05))-obj.location).to_track_quat('-Z','Y').to_euler()

records=[]
for slug,name,zone,per,stock,unit,price,build in catalog:
    print('BUILD',slug,flush=True)
    for c in scene.collection.children:
        if c != studio:
            c.hide_render=True
            c.hide_viewport=True
    current=bpy.data.collections.new(slug)
    scene.collection.children.link(current)
    if build:
        build()
    else:
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(ROOT/'resources/pencil-original.glb'))
        imported=set(bpy.data.objects)-before
        for obj in imported:
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            current.objects.link(obj)
        # Preserve all ten pencil bodies; only replace English printed meshes.
        remove_names={'Label grade','Label grade subtitle','Label bottom title','Lower carton caption'}
        for obj in list(current.objects):
            if obj.name in remove_names or 'HB imprint' in obj.name:
                bpy.data.objects.remove(obj,do_unlink=True)
        text('Pencil Chinese brand','铅笔',(0,-.242*.08,1.071*.08),.009,ink)
        text('Pencil Chinese grade','学生用',(.285*.08,-.242*.08,1.35*.08),.005,ink)
        text('Pencil Chinese subtitle','书写顺滑',(.285*.08,-.242*.08,1.235*.08),.0035,ink)
        text('Pencil Chinese caption','学生铅笔',(0,-.214*.08,.166*.08),.006,ink)
    lo,hi=bounds(current.objects)
    center=(lo+hi)/2
    scene.render.resolution_x=800
    scene.render.resolution_y=600
    # High viewing elevation separates all rows, especially bottles and cans.
    for view,direction in [('main',(.30,-.65,.88)),('top',(0,-.015,1)),('front',(.12,-1,.26)),('side',(1,-.18,.40))]:
        camera.location=center+Vector(direction).normalized()*1.6
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        q=camera.rotation_euler.to_quaternion().inverted()
        local=[q@(Vector(p)-center) for o in current.objects if o.type=='MESH' for p in [o.matrix_world@Vector(c) for c in o.bound_box]]
        width=max(v.x for v in local)-min(v.x for v in local)
        height=max(v.y for v in local)-min(v.y for v in local)
        camera.data.ortho_scale=max(width,height*(4/3))*1.25
        if view=='main':
            scene.cycles.samples=args.samples
            path=OUT/'images'/f'{slug}.png'
        else:
            scene.cycles.samples=8
            scene.render.resolution_x=480
            scene.render.resolution_y=360
            path=OUT/'diagnostics'/f'{slug}-{view}.png'
        scene.render.filepath=str(path)
        if args.reuse_previews and slug not in args.changed_products:
            shutil.copy2(args.reuse_previews/path.relative_to(OUT),path)
        else:
            bpy.ops.render.render(write_still=True)
    # GLB export is limited to this product; scene cameras/lights are excluded.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in current.objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'models'/f'{slug}.glb'), export_format='GLB',
                              use_selection=True, export_cameras=False, export_lights=False)
    if slug=='rolls':
        shutil.copy2(ROOT/'resources/rolls-supplied.glb',OUT/'models/rolls.glb')
    # Keep all asset collections in a single editable catalogue blend.
    records.append(dict(id=slug,name=name,zone=zone,perPackage=per,stock=stock,unit=unit,price=price,
                        correct=per==10,dimensions=[round(v,5) for v in hi-lo],
                        model=f'models/{slug}.glb',image=f'images/{slug}.png',
                        countableUnits=per*stock))
    print('COMPLETE',slug,flush=True)

for c in scene.collection.children:
    c.hide_render=False
    c.hide_viewport=False
# In the editable scene, arrange the products separately rather than overlay.
for i,rec in enumerate(records):
    col=bpy.data.collections[rec['id']]
    delta=Vector(((i%4)*.70,(i//4)*.50,0))
    for obj in col.objects:
        if obj.parent is None:
            obj.location+=delta
scene.cycles.samples=args.samples
model_collection=bpy.data.collections.new('MODEL')
scene.collection.children.link(model_collection)
for rec in records:
    col=bpy.data.collections[rec['id']]
    model_collection.children.link(col)
    scene.collection.children.unlink(col)
bpy.ops.object.select_all(action='DESELECT')
for obj in model_collection.all_objects:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'models'/'supermarket.glb'),export_format='GLB',
                         use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'editable'/'supermarket.blend'))
(OUT/'catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'printed-labels.json').write_text(json.dumps(printed_labels,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'build-info.json').write_text(json.dumps({'blender':bpy.app.version_string,'engine':'Cycles CPU',
    'samples':args.samples,'units':'metres','renderViews':['main','top','front','side'],
    'simplifications':['Transparent bags expose rolls, water and candy; yogurt and eggs retain low trays.','PET body is tinted for legibility.',
                       'Procedural micro-bump stays in blend; GLB uses plain PBR colours.'],
    'source':'Task-created models; battery and candy adapted from user references. Pencil GLB supplied by user; no source webpage scraped.'},indent=2),encoding='utf-8')
print('ALL MODELS COMPLETE',flush=True)
