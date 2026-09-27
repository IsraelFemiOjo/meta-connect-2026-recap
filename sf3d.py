import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys; sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image
from ink import *
from stylize3d import *

P = load('r3d/test.exr')
H = W = 2160
# background: our paper, a big Ben-Day gradient field, blue-pencil construction, comic caption boxes
pg = Page(1080, 1080, seed=4)
bgl = pg.new_layer()
yy, xx = np.mgrid[0:H, 0:W]
amt = np.clip((xx*0.6 + (H - yy)*0.5)/W - 0.55, 0, 1)*0.55
dots = halftone((H, W), amt, cell=22, angle=15)
arr = np.array(pg.im).astype(float)
col = hexrgb('#8FB2F5')
arr[..., :3] = np.where(dots[..., None], arr[..., :3]*0.35 + col*0.65, arr[..., :3])
pg.im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
L = pg.new_layer()
dashed_circle(L, 540, 560, 430, seed=1)
for a in range(0, 360, 12):
    ra = math.radians(a)
    construction_line(L, (540 + 440*math.cos(ra), 560 + 440*math.sin(ra)), (540 + 462*math.cos(ra), 560 + 462*math.sin(ra)), width=1.4)
# speed burst behind the product (hand-inked, like comic action lines)
rng = np.random.default_rng(3)
for k in range(46):
    a = rng.uniform(0, 2*math.pi); r0 = rng.uniform(300, 380); r1 = r0 + rng.uniform(80, 200)
    stroke(L, [(540 + r0*math.cos(a), 560 + r0*math.sin(a)), (540 + r1*math.cos(a), 560 + r1*math.sin(a))], rng.uniform(1.2, 3.0), PAL['ink'], seed=k, alpha=150)
pg.add(L)
bg = np.array(pg.im)[..., :3]
# drop shadow: flat offset silhouette in halftone
mask = P['I'] > 0
sh = np.roll(mask, (60, -30), (0, 1))
shd = halftone((H, W), np.full((H, W), 0.5), cell=9, angle=45) & sh
bg = np.where(shd[..., None], (bg*0.5 + hexrgb('#1E1B2C')*0.5).astype(np.uint8), bg)
img, m = stylize(P, bg=bg)
out = Image.fromarray(img).convert('RGBA')
L = Image.new('RGBA', out.size, (0, 0, 0, 0))
# lens glare, drawn by hand on top
pass
# caption box (comic style)
def caption(Lyr, x, y, w, h, lines, fill_col='#FFE36E'):
    fill(Lyr, poly_mask(Lyr.size, [(x, y), (x + w, y - 4), (x + w + 3, y + h), (x - 2, y + h + 3)]), fill_col)
    stroke(Lyr, [(x, y), (x + w, y - 4), (x + w + 3, y + h), (x - 2, y + h + 3), (x, y)], 2.6, PAL['ink'], seed=int(x), taper=False, jitter=0.3)
    yy_ = y + 10
    for (t, f, s) in lines:
        text(Lyr, (x + 16, yy_), t, s, f, PAL['ink']); yy_ += s*1.25
caption(L, 60, 64, 470, 132, [('Ray-Ban Meta Gen 3', 'Kalam-700.ttf', 44), ('$449 · on sale now', 'ArchitectsDaughter.ttf', 30)])
caption(L, 690, 850, 330, 104, [('12 MP camera', 'Kalam-700.ttf', 38), ('3K video', 'ArchitectsDaughter.ttf', 28)], '#FFFFFF')
from props import muse
muse(None, L, 470, 330, 44, t=0.3, look=(0.2, 0.1), seed=7)
out.alpha_composite(L)
out.convert('RGB').resize((1080, 1080), Image.LANCZOS).save('styleframe3d_v1.png')
print('ok')
