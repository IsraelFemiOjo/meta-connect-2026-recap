import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, json, math
sys.path.insert(0, ROOT)
import bpy
from mathutils import Vector
from scene3d import *
from vr3d import *
F = lambda t: int(round(t*24)) + 1
bpy.ops.wm.read_factory_settings(use_empty=True)
P = build_vr()
spark = build_spark()
cam, tgt = tracked_camera((0, 0.3, 0.0), lens=50)

def kl(f, lens): cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
# ---- camera: front 3/4 -> orbit -> pull up and back for the exploded view -> slow drift -> home to the front
key(cam, F(0), loc=(1.3, -8.7, 1.0)); key(tgt, F(0), loc=(0, 0.35, 0.0)); kl(F(0), 50)
key(cam, F(1.7), loc=(3.4, -7.7, 1.8)); key(tgt, F(1.7), loc=(0, 0.4, -0.1)); kl(F(1.7), 52)
key(cam, F(2.6), loc=(6.1, -5.6, 4.3)); key(tgt, F(2.6), loc=(0.55, 0.65, -0.45)); kl(F(2.6), 36)
key(cam, F(7.35), loc=(5.4, -6.3, 3.9)); key(tgt, F(7.35), loc=(0.5, 0.6, -0.45)); kl(F(7.35), 37)
key(cam, F(8.35), loc=(0.35, -8.3, 0.75)); key(tgt, F(8.35), loc=(0, 0.35, 0.0)); kl(F(8.35), 52)
key(cam, F(9.6), loc=(0.3, -7.9, 0.7)); key(tgt, F(9.6), loc=(0, 0.35, 0.0)); kl(F(9.6), 53)

# ---- the explode ----
EX = {'shell': (0, -2.1, 0), 'disp': (0, -0.95, 0), 'lens': (0, 0.25, 0), 'frame': (0, 1.45, 0)}
home = {k: P[k].location.copy() for k in ('shell', 'disp', 'lens', 'frame', 'armL', 'armR')}
def put(k, f, amt, bob=0.0, squeeze=0.0):
    h = home[k]
    if k in EX:
        d = EX[k]; key(P[k], f, loc=(h.x + d[0]*amt, h.y + d[1]*amt + squeeze, h.z + bob))
    else:
        s = 1 if k == 'armL' else -1
        key(P[k], f, loc=(h.x + s*0.5*amt, h.y + 1.45*amt + squeeze, h.z + bob), rot=(0, 0, -s*math.radians(16)*amt))
SQ = {'shell': 0.06, 'disp': 0.03, 'lens': -0.01, 'frame': -0.04, 'armL': -0.04, 'armR': -0.04}
for k in home:
    put(k, F(0), 0); put(k, F(1.5), 0)
    put(k, F(1.78), 0, squeeze=SQ[k])                   # anticipation: everything pulls in
    put(k, F(2.12), 1.12); put(k, F(2.4), 1.0)          # burst, overshoot, settle
    ph = list(home).index(k)
    for j, tt in enumerate((3.4, 4.6, 5.8, 7.0)):       # a slow float while exploded
        put(k, F(tt + ph*0.05), 1.0, bob=0.035*(1 if (j + ph) % 2 else -1))
    put(k, F(7.4), 1.0); put(k, F(7.74), -0.035); put(k, F(7.9), 0)   # snap back together, tiny overshoot
PK_OUT = (2.95, 3.4, -5.6); PK_IN = (2.95, 3.4, -1.45)
key(P['puck'], F(0), loc=PK_OUT, rot=(0, 0, math.radians(-12))); key(P['puck'], F(1.8), loc=PK_OUT)
key(P['puck'], F(2.2), loc=(2.95, 3.4, -1.3)); key(P['puck'], F(2.42), loc=PK_IN)
key(P['puck'], F(5.0), loc=(2.95, 3.4, -1.40), rot=(0, 0, math.radians(-8)))
key(P['puck'], F(7.4), loc=PK_IN, rot=(0, 0, math.radians(-12))); key(P['puck'], F(7.85), loc=PK_OUT)

# ---- Spark: sits on the visor, gets flung by the burst onto the puck, rides it, hops home, ducks out ----
TOP = (0.2, 0.05, 0.62)
PUCK_TOP = (PK_IN[0] - 0.3, PK_IN[1], PK_IN[2] + 0.9)
face = lambda deg: (0, 0, math.radians(deg))
key(spark, F(0), loc=(0.2, 0.3, 0.2), scale=0.001, rot=face(8)); key(spark, F(0.85), loc=(0.2, 0.3, 0.2), scale=0.001)
key(spark, F(1.1), loc=(0.2, 0.05, 0.7), scale=(0.9, 0.9, 1.25)); key(spark, F(1.28), loc=TOP, scale=(1.12, 1.12, 0.88)); key(spark, F(1.45), loc=TOP, scale=1.0)
key(spark, F(1.8), loc=TOP, scale=(1.15, 1.15, 0.8), rot=face(10))
key(spark, F(2.15), loc=(1.6, 1.6, 1.5), scale=(0.9, 0.9, 1.2), rot=face(200))
key(spark, F(2.55), loc=PUCK_TOP, scale=(1.2, 1.2, 0.8), rot=face(382)); key(spark, F(2.72), loc=PUCK_TOP, scale=1.0, rot=face(382))
key(spark, F(7.4), loc=PUCK_TOP, scale=1.0, rot=face(380)); key(spark, F(7.5), loc=(PUCK_TOP[0], PUCK_TOP[1], PUCK_TOP[2] - 0.03), scale=(1.14, 1.14, 0.84))
key(spark, F(7.95), loc=(1.3, 1.2, 1.7), scale=(0.9, 0.9, 1.2), rot=face(370))
key(spark, F(8.3), loc=TOP, scale=(1.14, 1.14, 0.84), rot=face(368)); key(spark, F(8.45), loc=TOP, scale=1.0, rot=face(368))
key(spark, F(9.05), loc=TOP, scale=1.0); key(spark, F(9.35), loc=(0.2, 0.35, 0.3), scale=0.001)

# callout anchors, carried by each part
def anchor(name, parent, co):
    e = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(e); e.parent = parent; e.location = co; return e
AN = {
    'shell': anchor('a_shell', P['shell'], (1.05, -0.14 + wrap_y(1.05), 0.12)),
    'disp': anchor('a_disp', P['disp'], (0.8, 0.12 + wrap_y(0.8), 0.18)),
    'lens': anchor('a_lens', P['lens'], (EYE_X + 0.18, 0.27 + wrap_y(EYE_X), 0.22)),
    'frame': anchor('a_frame', P['frame'], (1.35, 0.46 + wrap_y(1.35), 0.3)),
    'arm': anchor('a_arm', P['armL'], (0, 1.75, -0.02)),
    'puck': anchor('a_puck', P['puck'], (0.25, -0.15, 0.2)),
    'center': anchor('a_center', P['root'], (0.4, 0.5, -0.2)),
    'axL0': anchor('axL0', P['root'], (EYE_X, -2.8, 0)), 'axL1': anchor('axL1', P['root'], (EYE_X, 2.1, 0)),
    'axR0': anchor('axR0', P['root'], (-EYE_X, -2.8, 0)), 'axR1': anchor('axR1', P['root'], (-EYE_X, 2.1, 0)),
}
import os
render_setup(int(os.environ.get('RES', 2160)))
sc = bpy.context.scene
out = sys.argv[sys.argv.index('--') + 1]
first, last = int(sys.argv[sys.argv.index('--') + 2]), int(sys.argv[sys.argv.index('--') + 3])
anchors = {}
STEP = int(os.environ.get('STEP', 2))
for f in range(first, last + 1, STEP):
    sc.frame_set(f); update_tether(P); bpy.context.view_layer.update()
    a = {k: project(o, cam) for k, o in AN.items()}
    a['spark'] = project(spark, cam); a['sparkscale'] = list(spark.scale)
    a['glass'] = project(P['shell'].matrix_world @ Vector((0.3, -0.13, 0.1)), cam)
    anchors[f] = a
    sc.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump(anchors, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
