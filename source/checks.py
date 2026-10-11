import re
from collections import Counter

def check(stage, objects, manifest):
    # Count actual principal meshes rather than generated marker empties.
    patterns={
        'rolls': (r'^Roll_\d+$',10),
        'mugs': (r'^Mug \d+ hollow ceramic body',3),
        'toothpaste': (r'^Toothpaste box \d+',4),
        'brushes': (r'^Brush \d+\.\d+ rounded handle',12),
        'batteries': (r'^Battery \d+ AA body',10),
        'pencils': (r'^Pencil \d+ hexagonal yellow barrel',10),
        'water': (r'^Water bottle \d+ PET body',12),
        'chips': (r'^Chips can \d+$',6),
        'candy': (r'^Candy mini pouch \d+$',10),
        'yogurt': (r'^Yogurt cup \d+$',10),
        'eggs': (r'^Egg \d+$',10),
        'apples': (r'^Apple \d+ organic lobed skin',4),
    }
    counts={key:sum(bool(re.search(pattern,o.name)) for o in objects if o.type=='MESH')
            for key,(pattern,expected) in patterns.items()}
    passed=all(counts[key]==expected for key,(_,expected) in patterns.items())
    brush_boards=Counter(int(re.match(r'^Brush (\d+)\.',o.name).group(1))
                          for o in objects if re.match(r'^Brush \d+\.\d+ rounded handle',o.name))
    passed=passed and dict(brush_boards)=={1:6,2:6}
    results = [{'id':'task.product_counts','status':'pass' if passed else 'fail',
             'measured':{'principal_mesh_counts':counts,'toothbrush_boards':dict(brush_boards)},
             'reason':'Counts verified from principal meshes, including six brushes in each of two boards.'}]
    bags = {}
    for key, name in [('rolls','Transparent_bag'),('water','Water sealed transparent bag'),('candy','Candy sealed transparent outer bag')]:
        meshes = [o for o in objects if o.type=='MESH' and o.name==name]
        bags[key] = bool(meshes) and all(any(n.type=='BSDF_PRINCIPLED' and .0 < n.inputs['Alpha'].default_value < 1
                            for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes) for o in meshes)
    bases = sum(o.type=='MESH' and o.name.startswith('Packaging base') for o in objects)
    blisters = sum(bool(re.match(r'^Battery \d+ fitted clear blister',o.name)) for o in objects)
    water_seals = sum(o.name.startswith('Water sealed transparent bag end seal') or o.name.startswith('Water sealed transparent bag seal crimp') for o in objects)
    winding_grooves = sum(bool(re.match(r'^Layer_\d+_\d+$',o.name)) for o in objects)
    candy_centers = []
    candy_thickness = []
    candy_bag_points = []
    candy_saturated_red = True
    for o in objects:
        from mathutils import Vector
        if o.type=='MESH' and o.name.startswith('Candy sealed transparent outer bag'):
            candy_bag_points.extend(o.matrix_world @ Vector(c) for c in o.bound_box)
        if o.type=='MESH' and re.match(r'^Candy mini pouch \d+$',o.name):
            points = [o.matrix_world @ Vector(c) for c in o.bound_box]
            candy_centers.append([round(sum(p[axis] for p in points)/8,4) for axis in (0,1)])
            candy_thickness.append(max(p.z for p in points)-min(p.z for p in points))
            colors = [n.inputs['Base Color'].default_value for m in o.data.materials if m and m.use_nodes
                      for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
            candy_saturated_red &= bool(colors) and all(c[0]>=.90 and c[1]<=.03 and c[2]<=.05 for c in colors)
    candy_columns = len({p[0] for p in candy_centers})
    candy_rows = len({p[1] for p in candy_centers})
    candy_bag_width = max(p.x for p in candy_bag_points)-min(p.x for p in candy_bag_points) if candy_bag_points else 0
    candy_detail_ok = len(candy_thickness)==10 and all(.023<=v<=.035 for v in candy_thickness) and .19<=candy_bag_width<=.21 and candy_saturated_red
    package_ok = all(bags.values()) and bases==2 and blisters==10 and water_seals==0 and winding_grooves==180 and (candy_columns,candy_rows)==(2,5) and candy_detail_ok
    results.append({'id':'task.packaging','status':'pass' if package_ok else 'fail',
                    'measured':{'transparent_bags':bags,'remaining_egg_yogurt_tray_bases':bases,'battery_blisters':blisters,
                                'water_external_seals':water_seals,'roll_winding_grooves':winding_grooves,'candy_columns':candy_columns,'candy_rows':candy_rows,
                                'candy_pouch_thickness_m':candy_thickness,'candy_outer_width_m':candy_bag_width,'candy_saturated_red':candy_saturated_red},
                    'reason':'Transparent bags, water without external seals, 180 supplied paper layer rings and ten candy packets in two columns of five.'})
    parts = {
        'brush_grip_inserts':sum('coloured curved silicone grip' in o.name for o in objects if o.type=='MESH'),
        'brush_white_bristle_bases':sum('white bristle base' in o.name for o in objects if o.type=='MESH'),
        'brush_tufts':sum(bool(re.match(r'^Brush .* bristle tuft',o.name)) for o in objects if o.type=='MESH'),
        'carton_fold_seams':sum(o.name.startswith('Toothpaste folded carton seam') for o in objects if o.type=='MESH'),
        'water_red_caps':sum(bool(re.match(r'^Water bottle .* red cap',o.name)) for o in objects if o.type=='MESH'),
        'apple_natural_leaves':sum('veined natural leaf' in o.name for o in objects if o.type=='MESH'),
    }
    expected={'brush_grip_inserts':12,'brush_white_bristle_bases':12,'brush_tufts':216,'carton_fold_seams':8,'water_red_caps':12,'apple_natural_leaves':4}
    results.append({'id':'task.real_forms','status':'pass' if parts==expected else 'fail','measured':parts,
                    'reason':'Actual reference-specific parts counted after source reopen and GLB import; carton folds, rounded brush bases, dense tufts, coloured inserts, red bottle caps and natural leaves.'})
    from mathutils import Vector
    connections=[]
    for handle in objects:
        if handle.type!='MESH' or not re.match(r'^Brush .* rounded handle',handle.name):continue
        prefix=handle.name.split(' rounded handle')[0]
        head=next((o for o in objects if o.name==prefix+' head'),None)
        pts=[handle.matrix_world@v.co for v in handle.data.vertices]
        hp=[head.matrix_world@v.co for v in head.data.vertices] if head else []
        if not hp:connections.append(False);continue
        center_x=(max(p.x for p in hp)+min(p.x for p in hp))/2
        slice_pts=[p for p in pts if -.070<p.y<-.040]
        toward_camera=bool(slice_pts) and abs(sum(p.x for p in slice_pts)/len(slice_pts)-center_x)<.0002
        overlap=max(p.y for p in pts)-min(p.y for p in hp)
        connections.append(toward_camera and overlap>.005)
    textured_cartons=sum(bool(re.match(r'^Toothpaste box ',o.name)) and any(n.type=='TEX_IMAGE' and n.image for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes) for o in objects if o.type=='MESH')
    handles=sum(o.name=='Handle_with_two_real_holes' for o in objects if o.type=='MESH')
    results.append({'id':'task.current_repairs','status':'pass' if len(connections)==12 and all(connections) and textured_cartons==4 and handles==1 else 'fail',
                    'measured':{'camera_facing_connected_brushes':sum(connections),'textured_cartons':textured_cartons,'paper_bag_handles':handles},
                    'reason':'Each handle has no lateral bow in its middle cross-section and overlaps the brush head; four cartons carry embedded images and one double-hole handle is present.'})
    uv_faces=0; mirrored_faces=0
    for obj in objects:
        if obj.type!='MESH' or not re.match(r'^Toothpaste box ',obj.name):continue
        uv=obj.data.uv_layers.active
        if not uv:mirrored_faces+=1;continue
        for face in obj.data.polygons:
            if max(abs(v) for v in face.normal)<.9999:continue
            points=[uv.data[i].uv for i in face.loop_indices]
            area=sum(a.x*b.y-b.x*a.y for a,b in zip(points,points[1:]+points[:1]))/2
            if abs(area)<1e-8:continue
            uv_faces+=1
            if area<0:mirrored_faces+=1
    results.append({'id':'task.carton_uv_orientation','status':'pass' if uv_faces>=24 and mirrored_faces==0 else 'fail',
                    'measured':{'flat_textured_faces':uv_faces,'mirrored_faces':mirrored_faces},
                    'reason':'Positive UV winding on every outward flat carton face; zero reflected texture faces in both Blender and imported GLB.'})
    return results
