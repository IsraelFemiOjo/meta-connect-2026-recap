import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, json, math
sys.path.insert(0, ROOT)
import bpy
from mathutils import Vector
from scene3d import *
F = lambda t: int(round(t*24)) + 1
bpy.ops.wm.read_factory_settings(use_empty=True)
before = set(bpy.data.objects)
build_glasses('wayfarer')
gen3 = [o for o in bpy.data.objects if o not in before]
before = set(bpy.data.objects)
build_glasses('clubmaster', camera=False)
club = [o for o in bpy.data.objects if o not in before]
spark = build_spark()
cam, tgt = tracked_camera((0.05, 0.62, -0.1))
CP = (1.464, -0.045, 0.40)
key(cam, F(0), loc=(5.6, -3.7, 2.45)); key(cam, F(1.6), loc=(5.5, -3.9, 2.4))
key(cam, F(2.6), loc=(5.5, -3.9, 2.4)); key(cam, F(3.25), loc=(2.55, -1.25, 0.95))
key(cam, F(5.0), loc=(2.62, -1.30, 1.0)); key(cam, F(5.7), loc=(6.0, -2.2, 2.2))
key(cam, F(9.6), loc=(6.1, -1.8, 2.25)); key(cam, F(10.8), loc=(6.1, -1.8, 2.25))
key(tgt, F(0), loc=(0.05, 0.62, -0.1)); key(tgt, F(2.6), loc=(0.05, 0.62, -0.1)); key(tgt, F(3.25), loc=(CP[0] - 0.05, CP[1], CP[2] + 0.12))
key(tgt, F(5.0), loc=(CP[0] - 0.05, CP[1], CP[2] + 0.12)); key(tgt, F(5.7), loc=(0.35, 0.55, -0.05)); key(tgt, F(10.8), loc=(0.35, 0.55, -0.05))
top = (0.0, -0.05, 0.80); C = (1.40, -0.06, 0.66); T = (1.52, 1.0, 0.56)
key(spark, F(0), loc=top, scale=1.0, rot=(0, 0, math.radians(25)))
key(spark, F(1.9), loc=top, scale=1.0); key(spark, F(2.05), loc=top, scale=(1.1, 1.1, 0.85))
key(spark, F(2.45), loc=(0.8, -0.15, 1.45), scale=(0.92, 0.92, 1.15)); key(spark, F(2.85), loc=C, scale=(1.12, 1.12, 0.86)); key(spark, F(3.05), loc=C, scale=1.0, rot=(0, 0, math.radians(42)))
key(spark, F(5.05), loc=C, scale=1.0, rot=(0, 0, math.radians(42))); key(spark, F(5.2), loc=(C[0], C[1], C[2] - 0.02), scale=(1.1, 1.1, 0.86))
key(spark, F(5.65), loc=(1.6, 0.45, 1.3), scale=(0.92, 0.92, 1.15)); key(spark, F(6.05), loc=T, scale=(1.12, 1.12, 0.86)); key(spark, F(6.25), loc=T, scale=1.0, rot=(0, 0, math.radians(70)))
key(spark, F(10.8), loc=T, scale=1.0, rot=(0, 0, math.radians(70)))
render_setup()
sc = bpy.context.scene
out = sys.argv[sys.argv.index('--') + 1]
first, last = int(sys.argv[sys.argv.index('--') + 2]), int(sys.argv[sys.argv.index('--') + 3])
anchors = {}
temple_end = Vector(((196 + 186)/250.0, 1.30, 0.36))
for f in range(first, last + 1, 2):
    sc.frame_set(f)
    anchors[f] = dict(spark=project(spark, cam), cam=project(Vector(CP), cam), center=project(Vector((0, 0, 0)), cam),
                      temple=project(temple_end, cam), sparkscale=list(spark.scale))
    for o in gen3: o.hide_render = True
    for o in club: o.hide_render = False
    sc.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
    if f <= F(1.6):
        for o in gen3: o.hide_render = False
        for o in club: o.hide_render = True
        sc.render.filepath = f'{out}/g3_{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump(anchors, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
