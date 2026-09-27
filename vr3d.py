"""Meta VR Glasses, built as separate layers so they can explode apart.
Layout from published descriptions: slim wraparound visor, magnesium frame, micro OLED panels, pancake lenses with
integrated eye tracking (2 cameras per eye), nose pads, temple arms (no strap) with off ear speakers, a cable running
back from one arm to a phone sized compute puck with a clip and a mesh grill on top.
Exact external camera positions are not published, so none are modelled on the shell."""
import bpy, math
from mathutils import Vector
from shapely.geometry import Polygon, Point, box
from shapely import affinity
from scene3d import catmull

WRAP = 0.16     # y offset per x^2: how much the visor wraps back at the sides
EYE_X = 0.70

def wrap_y(x): return WRAP*x*x

def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(e); e.location = loc
    return e

def poly_mesh(name, poly, thick, bevel, index, y0, parent, wrap=True):
    """extrude a shapely polygon (x, z) into a solid, then bend it around the face"""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = thick; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    rings = [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]
    for ring in rings:
        sp = cu.splines.new('POLY'); sp.points.add(len(ring) - 1)
        for i, (x, z) in enumerate(ring): sp.points[i].co = (x, z, 0, 1)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    tot = 2*thick + 2*bevel
    rm = ob.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = min(0.012, tot/4); rm.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier='rm')
    me = ob.data
    for v in me.vertices:
        v.co.y += y0 + (wrap_y(v.co.x) if wrap else 0)
    me.update()
    bpy.ops.object.shade_smooth()
    ob.pass_index = index; ob.parent = parent
    return ob

def cyl(r, d, loc, rot, index, parent, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.active_object; o.pass_index = index; o.parent = parent
    return o

HALF = [(0.0, 0.43), (0.5, 0.455), (0.95, 0.47), (1.38, 0.46), (1.6, 0.38), (1.68, 0.15), (1.63, -0.15), (1.5, -0.4),
        (1.24, -0.55), (0.86, -0.6), (0.52, -0.54), (0.33, -0.38), (0.2, -0.2), (0.09, -0.13), (0.0, -0.12)]
def outline():
    pts = HALF + [(-x, z) for x, z in reversed(HALF[1:-1])]
    return Polygon(catmull(pts, 8)).buffer(0)

def build_vr():
    P = {}
    root = empty('vr_root'); P['root'] = root
    # 1. front shell: the dark visor
    g = empty('g_shell'); g.parent = root; P['shell'] = g
    poly_mesh('shell', outline(), 0.05, 0.03, 20, 0.0, g)
    poly_mesh('glass', outline().buffer(-0.075), 0.012, 0.01, 28, -0.118, g)
    # 2. micro OLED panels
    g = empty('g_disp'); g.parent = root; P['disp'] = g
    for s in (-1, 1):
        x = s*EYE_X
        pan = box(x - 0.24, -0.23, x + 0.24, 0.23).buffer(0.04, quad_segs=6)
        poly_mesh('panel', pan, 0.018, 0.008, 21, 0.13, g)
    bridge = box(-0.46, 0.12, 0.46, 0.19)
    poly_mesh('flex', bridge, 0.006, 0.0, 27, 0.14, g)
    # 3. pancake lenses: two thin elements per eye in a ring, with 2 eye tracking cameras per eye
    g = empty('g_lens'); g.parent = root; P['lens'] = g
    for s in (-1, 1):
        x = s*EYE_X; y = 0.30 + wrap_y(x)
        for dy in (-0.035, 0.035):
            l = cyl(0.33, 0.035, (x, y + dy, 0.0), (math.radians(90), 0, 0), 2, g, 64)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.035, location=(x, y, 0.0), rotation=(math.radians(90), 0, 0), major_segments=64, minor_segments=12)
        t = bpy.context.active_object; t.pass_index = 23; t.parent = g
        for a in (-125, -55):
            ax = x + 0.35*math.cos(math.radians(a)); az = 0.35*math.sin(math.radians(a))
            cyl(0.038, 0.05, (ax, y + 0.03, az), (math.radians(90), 0, 0), 4, g, 24)
            cyl(0.022, 0.056, (ax, y + 0.03, az), (math.radians(90), 0, 0), 7, g, 24)
    # 4. magnesium frame with nose pads
    g = empty('g_frame'); g.parent = root; P['frame'] = g
    fr = outline().buffer(-0.02)
    for s in (-1, 1):
        fr = fr.difference(box(s*EYE_X - 0.36, -0.36, s*EYE_X + 0.36, 0.36).buffer(0.05, quad_segs=8))
    poly_mesh('frame', fr, 0.03, 0.012, 23, 0.46, g)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, segments=24, ring_count=12, location=(s*0.2, 0.55, -0.3))
        n = bpy.context.active_object; n.scale = (0.55, 0.9, 1.25); n.rotation_euler = (0, 0, s*math.radians(28))
        n.pass_index = 24; n.parent = g; bpy.ops.object.shade_smooth()
    # 5. arms: pivots at the hinges so they can swing out
    for s, nm in ((-1, 'armR'), (1, 'armL')):
        hx = s*1.60
        piv = empty('p_' + nm, (hx, 0.46 + wrap_y(1.55), 0.18)); piv.parent = root; P[nm] = piv
        prof = [(-0.02, 0.0), (0.02, 0.07), (0.14, 0.088), (0.8, 0.075), (1.55, 0.06), (2.05, 0.04), (2.35, -0.05), (2.5, -0.3), (2.46, -0.36),
                (2.3, -0.14), (2.0, -0.05), (1.55, -0.07), (0.8, -0.08), (0.14, -0.08), (0.02, -0.06)]
        cu = bpy.data.curves.new('arm', 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
        cu.extrude = 0.035; cu.bevel_depth = 0.014; cu.bevel_resolution = 3
        sp = cu.splines.new('POLY'); pts = catmull(prof, 6); sp.points.add(len(pts) - 1)
        for i, (a, b) in enumerate(pts): sp.points[i].co = (a, b, 0, 1)
        sp.use_cyclic_u = True
        ob = bpy.data.objects.new('arm', cu); bpy.context.collection.objects.link(ob)
        ob.rotation_euler = (math.radians(90), 0, math.radians(90)); ob.location = (0, 0, 0)
        ob.pass_index = 3; ob.parent = piv
        # off ear speaker: a grille of slots on the underside, toward the ear
        for k in range(5):
            cyl(0.012, 0.03, (s*0.0 + 0, 1.62 + k*0.06, -0.075), (0, 0, 0), 6, piv, 12)
        tip = empty('tip_' + nm, (0, 2.46, -0.33)); tip.parent = piv; P['tip_' + nm] = tip
    # 6. compute puck
    g = empty('g_puck', (0, 0, 0)); g.parent = root; P['puck'] = g
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    b = bpy.context.active_object; b.scale = (0.72, 0.14, 1.5); b.pass_index = 25; b.parent = g
    bev = b.modifiers.new('bev', 'BEVEL'); bev.width = 0.12; bev.segments = 8; bpy.ops.object.shade_smooth()
    # mesh grill along the top for cooling
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.72))
    gr = bpy.context.active_object; gr.scale = (0.56, 0.1, 0.1); gr.pass_index = 26; gr.parent = g
    bev = gr.modifiers.new('bev', 'BEVEL'); bev.width = 0.04; bev.segments = 4
    # belt clip on the back
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.095, 0.1))
    cl = bpy.context.active_object; cl.scale = (0.3, 0.03, 1.0); cl.pass_index = 23; cl.parent = g
    bev = cl.modifiers.new('bev', 'BEVEL'); bev.width = 0.012; bev.segments = 3
    port = empty('port', (0.0, 0.0, 0.78)); port.parent = g; P['port'] = port
    # 7. the tether: a braided cable, points updated every frame
    cc = bpy.data.curves.new('tether', 'CURVE'); cc.dimensions = '3D'; cc.bevel_depth = 0.022; cc.bevel_resolution = 3
    sp = cc.splines.new('BEZIER'); sp.bezier_points.add(3)
    to = bpy.data.objects.new('tether', cc); bpy.context.collection.objects.link(to); to.pass_index = 14
    P['tether'] = to
    return P

def update_tether(P, side='armL'):
    a = P['tip_' + side].matrix_world.translation.copy(); b = P['port'].matrix_world.translation.copy()
    sp = P['tether'].data.splines[0]
    mid1 = a + Vector((0.05, 0.15, -0.6)); mid2 = b + Vector((0, 0, 0.9))
    pts = [a, a.lerp(b, 0.33) + Vector((0.15, 0.3, -0.35)), a.lerp(b, 0.66) + Vector((0.1, 0.1, 0.25)), b]
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]; bp.co = p
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
