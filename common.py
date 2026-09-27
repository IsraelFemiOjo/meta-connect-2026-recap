import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, math, json, numpy as np
sys.path.insert(0, ROOT)
from ink import *
from props import muse as spark2d
import fast3d
from PIL import Image, ImageDraw, ImageFont

W = H = 2160
def clamp(x, a=0, b=1): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a)/(b - a))
def ease(x): return x*x*(3 - 2*x)
def ease_out(x): return 1 - (1 - x)**3
def lerp(a, b, x): return a + (b - a)*x
def twos(t): return math.floor(t*12)/12

def pop_scale(t, t0):
    """Comic 'pop' on twos: 0 -> 1.14 -> 0.95 -> 1."""
    if t < t0: return 0.0
    k = int((t - t0)*12)
    return [0.6, 1.14, 0.95, 1.0][min(k, 3)]

def make_bg(seed=4, field_color='#8FB2F5', guides=True, dark=False, field=True):
    pg = Page(1080, 1080, dark=dark, seed=seed)
    arr = np.array(pg.im).astype(np.float32)
    if field:
        yy, xx = fast3d._grid(H, W)
        amt = np.clip((xx*0.6 + (H - yy)*0.5)/W - 0.55, 0, 1)*0.55
        dots = fast3d.halftone((H, W), amt, cell=22, angle=15)
        col = fast3d.hexrgb(field_color)
        arr[..., :3] = np.where(dots[..., None], arr[..., :3]*0.35 + col*0.65, arr[..., :3])
    pg.im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    return pg

def caption(L, x, y, w, h, lines, t, t0, fill_col='#FFE36E', out_t=None, rot=0.0, seed=0):
    s = pop_scale(t, t0)
    if s <= 0: return
    if out_t is not None and t >= out_t:
        k = int((t - out_t)*12)
        if k >= 3: return
        s = [1.06, 0.7, 0.3][k]
    cx, cy = x + w/2, y + h/2
    def P(px, py):
        dx, dy = (px - cx)*s, (py - cy)*s
        c, sn = math.cos(rot), math.sin(rot)
        return (cx + dx*c - dy*sn, cy + dx*sn + dy*c)
    box = [P(x, y), P(x + w, y - 4), P(x + w + 3, y + h), P(x - 2, y + h + 3)]
    shadow = [(px + 7, py + 8) for px, py in box]
    fill(L, poly_mask(L.size, shadow), '#1E1B2C')
    fill(L, poly_mask(L.size, box), fill_col)
    stroke(L, box + [box[0]], 2.6, PAL['ink'], seed=seed, taper=False, jitter=0.25)
    yy = y + 12
    for (txt, fnt, sz, col) in lines:
        px, py = P(x + 18, yy)
        text(L, (px, py), txt, sz*s, fnt, col)
        yy += sz*1.22

def sfx_word(img, word, cx, cy, size, t, t0, dur=0.8, fill_col='#FFE36E', rot=-8):
    """Hand-lettered sound effect: Bangers, thick ink outline, pops on twos."""
    s = pop_scale(t, t0)
    if s <= 0 or t > t0 + dur: return
    f = ImageFont.truetype(FONT_DIR + 'Bangers.ttf', int(size*s*SS))
    tmp = Image.new('RGBA', (int(size*len(word)*1.2*SS) + 200, int(size*1.8*SS) + 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((tmp.size[0]//2 + 10, tmp.size[1]//2 + 12), word, font=f, fill=hexa('#1E1B2C'), anchor='mm', stroke_width=int(10*SS*s), stroke_fill=hexa('#1E1B2C'))
    d.text((tmp.size[0]//2, tmp.size[1]//2), word, font=f, fill=hexa(fill_col), anchor='mm', stroke_width=int(7*SS*s), stroke_fill=hexa('#1E1B2C'))
    tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(tmp, (int(cx*SS - tmp.size[0]/2), int(cy*SS - tmp.size[1]/2)))

def burst(L, cx, cy, r0, r1, n, seed, grow=1.0, width=(1.2, 3.2), color=None, alpha=170):
    rng = np.random.default_rng(seed)
    for k in range(n):
        a = rng.uniform(0, 2*math.pi); a0 = rng.uniform(r0, r0*1.2); a1 = a0 + rng.uniform(0.3, 1.0)*(r1 - r0)*grow
        stroke(L, [(cx + a0*math.cos(a), cy + a0*math.sin(a)), (cx + a1*math.cos(a), cy + a1*math.sin(a))], rng.uniform(*width), color or PAL['ink'], seed=seed + k, alpha=alpha)

def zoom_lines(L, cx, cy, seed, n=70, alpha=120):
    rng = np.random.default_rng(seed)
    for k in range(n):
        a = rng.uniform(0, 2*math.pi); r0 = rng.uniform(360, 520); r1 = r0 + rng.uniform(160, 420)
        ImageDraw.Draw(L).line([((cx + r0*math.cos(a))*SS, (cy + r0*math.sin(a))*SS), ((cx + r1*math.cos(a))*SS, (cy + r1*math.sin(a))*SS)],
                               fill=hexa(PAL['ink'], alpha), width=int(rng.uniform(1, 3.5)*SS))

def panel(L, x, y, w, h, seed=0, fill_col='#F7F2E6', rot=0.0):
    box = [(x, y), (x + w, y + 3), (x + w - 2, y + h), (x + 2, y + h - 3)]
    c, sn = math.cos(rot), math.sin(rot); cx, cy = x + w/2, y + h/2
    box = [(cx + (px - cx)*c - (py - cy)*sn, cy + (px - cx)*sn + (py - cy)*c) for px, py in box]
    fill(L, poly_mask(L.size, [(px + 10, py + 12) for px, py in box]), '#1E1B2C')
    fill(L, poly_mask(L.size, box), fill_col)
    stroke(L, box + [box[0]], 3.2, PAL['ink'], seed=seed, taper=False, jitter=0.3)

def glow_at(L, x, y, r, strength=0.5): glow(L, x, y, r, PAL['glow2'], strength)

def to_arr(pg): return np.array(pg.im)[..., :3]
