import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, json, math
sys.path.insert(0, ROOT)
import bpy
from mathutils import Vector
from scene3d import *
F = lambda t: int(round(t*24)) + 1
bpy.ops.wm.read_factory_settings(use_empty=True)
build_glasses('wayfarer', chunky=1.45)
spark = build_spark()
LENS_R = Vector((-(196)/250.0, -0.02, 0.0))    # wearer's right lens (viewer's left): the one with the display
cam, tgt = tracked_camera((0, 0.3, 0.0))
key(cam, F(0), loc=(1.6, -7.8, 1.2)); key(cam, F(2.4), loc=(1.1, -7.9, 0.9))
key(cam, F(3.0), loc=(0.2, -5.0, 0.4)); key(cam, F(3.9), loc=(LENS_R.x + 0.02, -0.55, 0.02))
key(tgt, F(0), loc=(0, 0.3, 0.0)); key(tgt, F(2.4), loc=(-0.2, 0.3, 0.0)); key(tgt, F(3.0), loc=(LENS_R.x, 0.3, 0.0)); key(tgt, F(3.9), loc=(LENS_R.x, 0.3, 0.0))
top = (0.35, -0.05, 0.78)
key(spark, F(0), loc=top, scale=1.0, rot=(0, 0, math.radians(10)))
key(spark, F(2.4), loc=top, scale=1.0); key(spark, F(2.55), loc=(0.35, -0.05, 0.76), scale=(1.1, 1.1, 0.86))
key(spark, F(2.9), loc=(-0.2, -0.2, 1.3), scale=(0.92, 0.92, 1.15)); key(spark, F(3.3), loc=(LENS_R.x, -0.3, 0.1), scale=(0.85, 0.85, 1.25))
key(spark, F(3.9), loc=(LENS_R.x, 0.6, 0.0), scale=0.4)
render_setup()
sc = bpy.context.scene
out = sys.argv[sys.argv.index('--') + 1]
first, last = int(sys.argv[sys.argv.index('--') + 2]), int(sys.argv[sys.argv.index('--') + 3])
anchors = {}
for f in range(first, last + 1, 2):
    sc.frame_set(f)
    anchors[f] = dict(spark=project(spark, cam), lens=project(LENS_R, cam), center=project(Vector((0, 0, 0)), cam), sparkscale=list(spark.scale))
    sc.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump(anchors, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
