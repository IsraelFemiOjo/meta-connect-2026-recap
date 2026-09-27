import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, json, math
sys.path.insert(0, ROOT)
import bpy
from mathutils import Vector
from scene3d import *
F = lambda t: int(round(t*24)) + 1
bpy.ops.wm.read_factory_settings(use_empty=True)
charm = build_charm()
spark = build_spark()
cam, tgt = tracked_camera((0, 0, 0.35), lens=60)
key(cam, F(0), loc=(1.4, -5.2, 1.0)); key(cam, F(5.0), loc=(-0.6, -5.3, 0.9))
key(charm, F(0), loc=(0.0, 0, 0.0), rot=(0, 0, math.radians(-25))); key(charm, F(0.6), loc=(0.0, 0, 0.0), rot=(0, 0, math.radians(8)))
key(charm, F(1.0), rot=(0, 0, math.radians(-4))); key(charm, F(1.4), rot=(0, 0, math.radians(0)))
key(charm, F(5.0), loc=(0.0, 0, 0.05), rot=(0, 0, math.radians(6)))
S0 = (0.98, -0.1, -0.52)
key(spark, F(0), loc=(2.4, -0.1, -0.52), scale=1.2, rot=(0, 0, math.radians(-20)))
key(spark, F(0.9), loc=(2.4, -0.1, -0.52), scale=1.2); key(spark, F(1.25), loc=(1.7, -0.1, 0.2), scale=(1.1, 1.1, 1.35))
key(spark, F(1.6), loc=S0, scale=(1.35, 1.35, 1.0)); key(spark, F(1.8), loc=S0, scale=1.2)
key(spark, F(5.0), loc=S0, scale=1.2, rot=(0, 0, math.radians(-30)))
render_setup()
sc = bpy.context.scene
out = sys.argv[sys.argv.index('--') + 1]
first, last = int(sys.argv[sys.argv.index('--') + 2]), int(sys.argv[sys.argv.index('--') + 3])
anchors = {}
for f in range(first, last + 1, 2):
    sc.frame_set(f)
    anchors[f] = dict(spark=project(spark, cam), charm=project(charm, cam), sparkscale=list(spark.scale))
    sc.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump(anchors, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
