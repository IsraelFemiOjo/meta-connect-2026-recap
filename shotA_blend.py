import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, json, math
sys.path.insert(0, ROOT)
import bpy
from mathutils import Vector
from scene3d import *
F = lambda t: int(round(t*24)) + 1
bpy.ops.wm.read_factory_settings(use_empty=True)
build_glasses('wayfarer')
spark = build_spark()
cam, tgt = tracked_camera((0, 0.35, 0.0))
# camera: front -> 3/4 orbit -> push into the camera corner -> pull back -> drift
CP = (1.464, -0.045, 0.40)
key(cam, F(0), loc=(0.0, -8.3, 0.35)); key(cam, F(3.9), loc=(0.25, -8.25, 0.45))
key(cam, F(4.7), loc=(3.4, -6.9, 1.5)); key(cam, F(5.5), loc=(5.3, -4.4, 2.3))
key(cam, F(6.8), loc=(5.3, -4.4, 2.3)); key(cam, F(7.45), loc=(2.55, -1.25, 0.95))
key(cam, F(9.2), loc=(2.62, -1.30, 1.0)); key(cam, F(9.9), loc=(5.35, -4.3, 2.3))
key(cam, F(13.0), loc=(5.45, -4.0, 2.35)); key(cam, F(15.0), loc=(5.6, -3.7, 2.45))
key(tgt, F(0), loc=(0, 0.35, 0.0)); key(tgt, F(3.9), loc=(0, 0.35, 0.0)); key(tgt, F(5.5), loc=(0.05, 0.62, -0.1))
key(tgt, F(6.8), loc=(0.05, 0.62, -0.1)); key(tgt, F(7.45), loc=(CP[0] - 0.05, CP[1], CP[2] + 0.12))
key(tgt, F(9.2), loc=(CP[0] - 0.05, CP[1], CP[2] + 0.12)); key(tgt, F(9.9), loc=(0.05, 0.62, -0.1)); key(tgt, F(15.0), loc=(0.05, 0.62, -0.1))
# Spark: pops up behind the bridge, hops onto the camera corner, squashes on the click, hops back
top = (0.0, -0.05, 0.80)
C = (1.40, -0.06, 0.66)
key(spark, F(0), loc=(0, 0.25, 0.25), scale=0.001); key(spark, F(2.55), loc=(0, 0.25, 0.25), scale=0.001)
key(spark, F(2.85), loc=(0, -0.05, 0.86), scale=(0.9, 0.9, 1.25)); key(spark, F(3.05), loc=top, scale=(1.12, 1.12, 0.88)); key(spark, F(3.25), loc=top, scale=1.0)
key(spark, F(5.6), loc=top, scale=1.0); key(spark, F(5.75), loc=top, scale=(1.1, 1.1, 0.85))
key(spark, F(6.15), loc=(0.8, -0.15, 1.45), scale=(0.92, 0.92, 1.15)); key(spark, F(6.55), loc=C, scale=(1.12, 1.12, 0.86)); key(spark, F(6.75), loc=C, scale=1.0)
key(spark, F(7.45), loc=C, scale=1.0); key(spark, F(7.55), loc=(C[0], C[1], C[2] - 0.02), scale=(1.14, 1.14, 0.82)); key(spark, F(7.75), loc=C, scale=1.0)
key(spark, F(13.3), loc=C, scale=1.0); key(spark, F(13.45), loc=(C[0], C[1], C[2] - 0.02), scale=(1.1, 1.1, 0.86))
key(spark, F(13.9), loc=(0.7, -0.15, 1.45), scale=(0.92, 0.92, 1.15)); key(spark, F(14.35), loc=top, scale=(1.1, 1.1, 0.88)); key(spark, F(14.55), loc=top, scale=1.0)
key(spark, F(15.0), loc=top, scale=1.0)
key(spark, F(0), rot=(0, 0, 0)); key(spark, F(4.0), rot=(0, 0, 0)); key(spark, F(5.5), rot=(0, 0, math.radians(25)))
key(spark, F(6.75), rot=(0, 0, math.radians(35))); key(spark, F(7.45), rot=(0, 0, math.radians(42)))
key(spark, F(9.2), rot=(0, 0, math.radians(42))); key(spark, F(9.9), rot=(0, 0, math.radians(28))); key(spark, F(15.0), rot=(0, 0, math.radians(25)))
for ob in (spark, cam, tgt):
    if ob.animation_data:
        for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, 'fcurves') else []:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
render_setup()
sc = bpy.context.scene
cam_pos = Vector(((196 + 170)/250.0, -0.045, 100/250.0))
anchors = {}
out = sys.argv[sys.argv.index('--') + 1]
first, last = int(sys.argv[sys.argv.index('--') + 2]), int(sys.argv[sys.argv.index('--') + 3])
for f in range(first, last + 1, 2):   # 3D is rendered on twos
    sc.frame_set(f)
    anchors[f] = dict(spark=project(spark, cam), cam=project(cam_pos, cam), led=project(Vector((-cam_pos.x, cam_pos.y, cam_pos.z)), cam),
                      center=project(Vector((0, 0, 0)), cam), sparkscale=list(spark.scale))
    sc.render.filepath = f'{out}/{f:04d}.exr'
    bpy.ops.render.render(write_still=True)
json.dump(anchors, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
