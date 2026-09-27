import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, os, math
sys.path.insert(0, ROOT)
from common import *

DUR = 3.5
BGA = to_arr(make_bg(seed=12))
PLAIN = to_arr(make_bg(seed=13, field=False))

def still3d(path, pad=0.12, aspect=None):
    P = fast3d.load(path)
    img = fast3d.stylize(P, PLAIN)
    ys, xs = np.nonzero(P['I'] > 0)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    if aspect:   # grow the box so nothing gets cropped away by the panel
        w_, h_ = x1 - x0, y1 - y0
        if w_/h_ > aspect: c = (y0 + y1)/2; h_ = w_/aspect; y0, y1 = int(c - h_/2), int(c + h_/2)
        else: c = (x0 + x1)/2; w_ = h_*aspect; x0, x1 = int(c - w_/2), int(c + w_/2)
    ph, pw = (y1 - y0)*pad, (x1 - x0)*pad
    y0, y1 = int(max(0, y0 - ph)), int(min(H, y1 + ph)); x0, x1 = int(max(0, x0 - pw)), int(min(W, x1 + pw))
    return Image.fromarray(img[y0:y1, x0:x1])

def still2d(path, box):
    return Image.open(path).convert('RGB').crop(box)

PW, PH = 330, 270
def fit(im, w, h):
    """cover fit"""
    s = max(w/im.width, h/im.height)
    im = im.resize((max(1, int(im.width*s)), max(1, int(im.height*s))), Image.LANCZOS)
    x = (im.width - w)//2; y = (im.height - h)//2
    return im.crop((x, y, x + w, y + h))

def build_panel(im, name, price, seed, fill_col='#FBF8EF'):
    """one comic panel at SS resolution, with its product still and a price tag"""
    pad = 40
    L = Image.new('RGBA', ((PW + 2*pad)*SS, (PH + 2*pad)*SS), (0, 0, 0, 0))
    box = [(pad, pad), (pad + PW, pad + 3), (pad + PW - 2, pad + PH), (pad + 2, pad + PH - 3)]
    fill(L, poly_mask(L.size, [(x + 9, y + 10) for x, y in box]), '#1E1B2C')
    fill(L, poly_mask(L.size, box), fill_col)
    pic = fit(im, (PW - 20)*SS, (PH - 70)*SS)
    L.paste(pic, ((pad + 10)*SS, (pad + 10)*SS))
    stroke(L, [(pad + 10, pad + 10), (pad + PW - 10, pad + 10), (pad + PW - 10, pad + PH - 60), (pad + 10, pad + PH - 60), (pad + 10, pad + 10)], 1.8, PAL['ink'], seed=seed + 1, taper=False)
    stroke(L, box + [box[0]], 3.0, PAL['ink'], seed=seed, taper=False, jitter=0.3)
    text(L, (pad + 16, pad + PH - 52), name, 28, 'Kalam-700.ttf', PAL['ink'])
    tw = 30 + 19*len(price)
    tag = [(pad + PW - tw, pad - 16), (pad + PW + 14, pad - 22), (pad + PW + 18, pad + 34), (pad + PW - tw + 4, pad + 38)]
    fill(L, poly_mask(L.size, [(x + 5, y + 6) for x, y in tag]), '#1E1B2C')
    fill(L, poly_mask(L.size, tag), '#FFE36E'); stroke(L, tag + [tag[0]], 2.2, PAL['ink'], seed=seed + 2, taper=False)
    text(L, (pad + PW - tw/2 + 8, pad + 8), price, 32, 'Kalam-700.ttf', PAL['ink'], anchor='mm')
    return L, pad

import shotD_comp
PANELS = None
def panels():
    global PANELS
    if PANELS is None:
        d = shotD_comp.render(92)          # the glowing arm by the ear, before any caption appears
        PANELS = [
            (build_panel(still3d('r3d/V/0121.exr', pad=0.04, aspect=310/200), 'Meta VR Glasses', '$1,299.99', 50), (30, 165), -0.015, 0.0),
            (build_panel(still3d('r3d/A/0373.exr'), 'Ray-Ban Meta Gen 3', '$449', 10), (375, 177), 0.012, 0.15),
            (build_panel(still3d('r3d/B/0261.exr'), 'Ray-Ban Meta Audio', '$349', 20), (720, 165), -0.01, 0.3),
            (build_panel(still3d('r3d/C/0001.exr'), 'Meta Ray-Ban Display', '$799', 30), (200, 505), 0.012, 0.45),
            (build_panel(d.crop((100, 180, 1000, 760)), 'Hearing Enhancement', '$149', 40), (550, 497), -0.015, 0.6),
        ]
    return PANELS

def render(fi):
    t = fi/24; tt = twos(t)
    out = Image.fromarray(BGA).convert('RGBA')
    for (L, pad), (x, y), rot, t0 in panels():
        s = pop_scale(tt, t0)
        if s <= 0: continue
        im = L.rotate(math.degrees(-rot), resample=Image.BICUBIC, expand=False)
        if s != 1: im = im.resize((int(im.width*s), int(im.height*s)), Image.LANCZOS)
        cx, cy = (x + PW/2)*SS, (y + PH/2)*SS
        out.alpha_composite(im, (int(cx - im.width/2), int(cy - im.height/2)))
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    caption(L, 250, 30, 580, 92, [('META CONNECT 2026', 'Kalam-700.ttf', 52, PAL['ink'])], tt, 0.8, seed=90)
    caption(L, 260, 840, 540, 80, [('Made with Claude Opus 5.5', 'Kalam-700.ttf', 42, PAL['ink'])], tt, 1.15, '#FFFFFF', seed=91, rot=-0.01)
    if tt >= 1.3:
        hop = abs(math.sin(twos(tt)*math.pi*1.4))*10
        spark2d(None, L, 872, 864 - hop, 40, t=tt*3, look=(-0.3, 0.05), seed=92, happy=True)
        # a little wave of the tuft: two motion ticks
        if int(tt*6) % 2 == 0:
            for k in range(2): stroke(L, [(914 + k*10, 802 - k*8), (926 + k*12, 788 - k*10)], 2.2, PAL['ink'], seed=93 + k, taper=False)
    out.alpha_composite(L)
    return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('fr/F', exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'fr/F/{fi:04d}.png')
