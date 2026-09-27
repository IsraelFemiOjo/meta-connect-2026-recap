import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys; sys.path.insert(0, ROOT)
from props import *
pg = Page(1080, 1080, seed=3)
L = pg.new_layer()
cx, cy = 540, 580
# construction first (non-photo blue, like an animator's rough)
dashed_circle(L, cx, cy, 420, seed=1)
dashed_circle(L, cx, cy, 300, dash=4, gap=10, seed=2, alpha=150)
for a in range(0, 360, 15):
    ra = math.radians(a)
    construction_line(L, (cx + 450*math.cos(ra), cy + 450*math.sin(ra)), (cx + 470*math.cos(ra), cy + 470*math.sin(ra)), width=1.4)
construction_line(L, (40, cy - 100*0.95), (1040, cy - 100*0.95), alpha=110)
construction_line(L, (cx, 150), (cx, 990), alpha=110)
pg.add(L); L = pg.new_layer()
g = glasses(pg, L, cx, cy, 0.95, seed=5)
# radial lines from the camera
cam = g['cam']
for k in range(14):
    a = math.radians(-70 + k*10)
    construction_line(L, (cam[0] + 26*math.cos(a), cam[1] + 26*math.sin(a)), (cam[0] + (90 + 30*(k % 3))*math.cos(a), cam[1] + (90 + 30*(k % 3))*math.sin(a)), color=PAL['ink'], width=1.0, alpha=130)
pg.add(L); L = pg.new_layer()
callout(L, (cam[0] + 4, cam[1] - 12), (880, 250), [('12 MP camera', 'Kalam-700.ttf', 36, PAL['ink']), ('3K video', 'ArchitectsDaughter.ttf', 27, '#4A4560')], seed=11, align='ra')
callout(L, (g['led'][0] - 4, g['led'][1] - 8), (86, 330), [('capture light', 'Kalam-700.ttf', 30, PAL['ink'])], seed=12)
# spec strip, drawn like a notebook margin
y0 = 850
items = [('9 hrs', 'battery, +1 hr vs Gen 2'), ('6 mics', 'cut 90%+ of noise'), ('action button', 'instant Meta AI')]
for i, (a, b) in enumerate(items):
    x = 70 + i*330
    if i == 0:
        stroke(L, [(x, y0 + 8), (x + 56, y0 + 8), (x + 56, y0 + 40), (x, y0 + 40), (x, y0 + 8)], 2.2, PAL['ink'], seed=60, taper=False)
        stroke(L, [(x + 58, y0 + 18), (x + 64, y0 + 18), (x + 64, y0 + 30), (x + 58, y0 + 30)], 2.0, PAL['ink'], seed=61, taper=False)
        hatch(L, poly_mask(L.size, [(x + 4, y0 + 12), (x + 46, y0 + 12), (x + 46, y0 + 36), (x + 4, y0 + 36)]), PAL['green'], angle=60, spacing=4, width=1.4, seed=62, alpha=230)
    elif i == 1:
        for k, h in enumerate((10, 22, 34, 22, 10)):
            stroke(L, [(x + 8 + k*12, y0 + 24 - h/2), (x + 8 + k*12, y0 + 24 + h/2)], 3.0, PAL['meta'], seed=63 + k, taper=False)
    else:
        stroke(L, circle_pts(x + 28, y0 + 24, 18, n=24), 2.2, PAL['ink'], seed=70, taper=False)
        fill(L, poly_mask(L.size, circle_pts(x + 28, y0 + 24, 10, n=20)), PAL['glow'])
    text(L, (x + 84, y0 - 2), a, 32, 'Kalam-700.ttf', PAL['ink'])
    text(L, (x + 84, y0 + 38), b, 22, 'ArchitectsDaughter.ttf', '#4A4560')
# title block
text(L, (64, 90), 'Ray-Ban Meta', 64, 'Kalam-700.ttf', PAL['ink'])
text(L, (64, 160), 'Gen 3', 44, 'Kalam-700.ttf', PAL['meta'])
text(L, (190, 170), '$449 · on sale now', 28, 'ArchitectsDaughter.ttf', '#4A4560')
stroke(L, [(64, 212), (420, 206)], 2.2, PAL['ink'], seed=90)
pg.add(L); L = pg.new_layer()
muse(pg, L, cx, cy - 175, 46, t=0.3, look=(0.18, 0.06), seed=7)
pg.add(L)
pg.result().save(ROOT + '/styleframe_v1.png')
print('ok')
