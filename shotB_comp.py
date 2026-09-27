import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, os, json, math
sys.path.insert(0, ROOT)
from common import *
A = json.load(open('r3d/B/anchors_1_261.json'))
BG = make_bg(seed=5)
L0 = BG.new_layer(); dashed_circle(L0, 540, 560, 430, seed=1); BG.add(L0)
BGARR = to_arr(BG)

def anchor(f, k):
    a = A[str(f)][k]; return a[0]*1080, a[1]*1080, a[2]
def spark_px(f):
    x, y, z = anchor(f, 'spark'); s = A[str(f)]['sparkscale'][0]
    return x, y, 0.14*max(s, 0.001)/max(z, 0.1)*2.0*1080

# eraser path: three passes across the glasses, drawn like someone scrubbing
ERASE = [(120, 360), (960, 330), (180, 520), (980, 500), (140, 700), (940, 690), (560, 560)]
def erase_mask(p):
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    P = np.array(ERASE, float); seglen = np.hypot(*np.diff(P, axis=0).T); tot = seglen.sum()
    s = np.r_[0, np.cumsum(seglen)]; u = np.linspace(0, tot*p, max(2, int(200*p)))
    X = np.interp(u, s, P[:, 0]); Y = np.interp(u, s, P[:, 1])
    pts = [(x*SS, y*SS) for x, y in zip(X, Y)]
    if len(pts) > 1: d.line(pts, fill=255, width=int(210*SS), joint='curve')
    for x, y in pts[::6]: d.ellipse([x - 105*SS, y - 105*SS, x + 105*SS, y + 105*SS], fill=255)
    return np.array(m) > 0, (X[-1], Y[-1])

def pencil(L, x, y, ang=-0.6):
    """Comic pencil with a pink eraser, eraser end at (x, y)."""
    c, s = math.cos(ang), math.sin(ang)
    def R(px, py): return (x + px*c - py*s, y + px*s + py*c)
    er = [R(0, -22), R(60, -22), R(60, 22), R(0, 22)]
    fe = [R(60, -24), R(96, -24), R(96, 24), R(60, 24)]
    bd = [R(96, -24), R(420, -24), R(420, 24), R(96, 24)]
    fill(L, poly_mask(L.size, bd), '#FFC93C'); hatch(L, poly_mask(L.size, [R(96, 6), R(420, 6), R(420, 24), R(96, 24)]), '#D99A1C', 30, 5, 1.4, seed=3)
    fill(L, poly_mask(L.size, fe), '#B9BCC8'); fill(L, poly_mask(L.size, er), '#F29CB0')
    hatch(L, poly_mask(L.size, [R(0, 6), R(60, 6), R(60, 22), R(0, 22)]), '#D66F8A', 30, 4, 1.3, seed=4)
    for poly in (er, fe, bd): stroke(L, poly + [poly[0]], 2.6, PAL['ink'], seed=5, taper=False, jitter=0.2)
    for k in (70, 80, 88): stroke(L, [R(k, -24), R(k, 24)], 1.6, PAL['ink'], seed=k, taper=False)

def note(L, x, y, s, seed, rot=0.0):
    c, sn = math.cos(rot), math.sin(rot)
    def R(px, py): return (x + (px*c - py*sn)*s, y + (px*sn + py*c)*s)
    head = [R(12*math.cos(a), 8*math.sin(a) + 30) for a in np.linspace(0, 2*math.pi, 18)]
    fill(L, poly_mask(L.size, head), PAL['ink'])
    stroke(L, [R(11, 28), R(11, -26)], 3*s, PAL['ink'], seed=seed, taper=False)
    stroke(L, [R(11, -26), R(28, -16), R(26, -4)], 3*s, PAL['ink'], seed=seed + 1, taper=False)

def render(fi):
    t = fi/24; f3 = fi - fi % 2 + 1; tt = twos(t)
    P = fast3d.load(f'r3d/B/{f3:04d}.exr')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sx, sy, sr = spark_px(f3)
    if sr > 2: glow_at(L, sx, sy, sr*2.4, 0.5)
    if 2.6 <= tt < 3.25 or 5.0 <= tt < 5.7: zoom_lines(L, 540, 540, int(tt*12))
    base = Image.fromarray(BGARR).convert('RGBA'); base.alpha_composite(L); bg = np.array(base)[..., :3]
    img = fast3d.stylize(P, bg)
    if tt < 1.5:
        g3 = fast3d.stylize(fast3d.load(f'r3d/B/g3_{min(f3, 37):04d}.exr'), bg)
        m, tip = erase_mask(ease(seg(tt, 0.05, 1.45)))
        img = np.where(m[..., None], img, g3)
    if 6.6 <= tt < 10.6:
        k = ease(seg(tt, 6.6, 6.9))*(1 - ease(seg(tt, 10.2, 10.6)))
        if k > 0:
            img = fast3d.misregister(img, int(8*k), int(-4*k))
            img = (img.astype(np.float32)*(1 - 0.12*k) + 245*0.12*k).astype(np.uint8)
    out = Image.fromarray(img).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if tt < 1.5:
        _, tip = erase_mask(ease(seg(tt, 0.05, 1.45)))
        wob = 10*math.sin(tt*40)
        pencil(L, tip[0] + wob, tip[1], ang=-0.7)
    caption(L, 56, 56, 470, 92, [('Ray-Ban Meta Audio', 'Kalam-700.ttf', 48, PAL['ink'])], tt, 1.55, seed=3, out_t=10.4)
    caption(L, 60, 160, 360, 64, [('$349 · ships Oct 13', 'ArchitectsDaughter.ttf', 30, PAL['ink'])], tt, 1.8, '#FFFFFF', seed=4, out_t=10.4)
    cx, cy, _ = anchor(f3, 'cam')
    if 3.3 <= tt < 5.05:
        dashed_circle(L, cx, cy, 70, color=PAL['blue'], width=3, dash=14, gap=8, reveal=ease(seg(tt, 3.3, 3.7)), alpha=255)
        r = ease(seg(tt, 3.7, 3.9))
        if r > 0:
            stroke(L, [(cx - 44, cy - 44), (cx + 44, cy + 44)], 7, PAL['red'], seed=81, reveal=r, taper=False)
            stroke(L, [(cx + 44, cy - 44), (cx - 44, cy + 44)], 7, PAL['red'], seed=82, reveal=seg(tt, 3.8, 4.0), taper=False)
    caption(L, 640, 800, 330, 80, [('no camera', 'Kalam-700.ttf', 50, PAL['ink'])], tt, 3.95, '#FFFFFF', out_t=5.0, seed=5, rot=-0.02)
    caption(L, 680, 900, 290, 64, [('by design', 'Kalam-700.ttf', 38, PAL['ink'])], tt, 4.2, '#FFE36E', out_t=5.0, seed=6, rot=0.02)
    # music drifting out from the arms
    if tt >= 6.0:
        tx, ty, _ = anchor(f3, 'temple')
        for k in range(6):
            ph = ((tt - 6.0)*0.55 + k/6) % 1.0
            x = tx - 40 - ph*260 + 30*math.sin(ph*9 + k); y = ty - 60 - ph*300
            if ph < 0.9: note(L, x, y, 1.1 - 0.3*ph, 90 + k, rot=0.3*math.sin(ph*6 + k))
    def slide(t0, t1, dx, dy):
        p = seg(tt, t0, t0 + 0.34); q = seg(tt, t1, t1 + 0.34)
        if p <= 0 or q >= 1: return None
        k = 1 - ease_out(p) + ease(q); return dx*k, dy*k
    o = slide(6.8, 10.2, 700, 0)
    if o:
        x0, y0 = 600 + o[0], 250 + o[1]
        panel(L, x0, y0, 420, 290, seed=10, rot=0.015)
        tag = [(x0 + 70, y0 + 80), (x0 + 230, y0 + 70), (x0 + 250, y0 + 150), (x0 + 90, y0 + 165)]
        fill(L, poly_mask(L.size, tag), '#FFE36E'); stroke(L, tag + [tag[0]], 2.4, PAL['ink'], seed=11, taper=False)
        stroke(L, [(x0 + 60, y0 + 40), (x0 + 88, y0 + 100)], 2.0, PAL['ink'], seed=12, taper=False)
        text(L, (x0 + 104, y0 + 88), '43 g', 50, 'Kalam-700.ttf', PAL['ink'])
        text(L, (x0 + 24, y0 + 196), 'light as a feather', 38, 'Kalam-700.ttf', PAL['ink'])
    o = slide(7.2, 10.25, -700, 0)
    if o:
        x0, y0 = 52 + o[0], 640 + o[1]
        panel(L, x0, y0, 470, 340, seed=20, rot=-0.01)
        bx, by = x0 + 40, y0 + 70
        stroke(L, [(bx, by), (bx + 200, by), (bx + 200, by + 100), (bx, by + 100), (bx, by)], 3.2, PAL['ink'], seed=21, taper=False)
        lvl = ease(seg(tt, 7.6, 8.4))
        if lvl > 0.02:
            m = poly_mask(L.size, [(bx + 8, by + 8), (bx + 8 + 184*lvl, by + 8), (bx + 8 + 184*lvl, by + 92), (bx + 8, by + 92)])
            fill(L, m, '#BFE5C9'); hatch(L, m, PAL['green'], 60, 5, 1.6, seed=23, alpha=230)
        text(L, (bx + 214, by + 20), '+', 56, 'Kalam-700.ttf', PAL['ink'])
        case = [(bx + 262, by + 10), (bx + 380, by + 10), (bx + 390, by + 92), (bx + 252, by + 92)]
        fill(L, poly_mask(L.size, case), '#D9CDB8'); stroke(L, case + [case[0]], 3, PAL['ink'], seed=24, taper=False)
        text(L, (bx + 282, by + 30), 'case', 30, 'Kalam-700.ttf', PAL['ink'])
        text(L, (x0 + 24, y0 + 200), '12 hours', 44, 'Kalam-700.ttf', PAL['ink'])
        text(L, (x0 + 24, y0 + 250), 'plus 48 more from the case', 25, 'ArchitectsDaughter.ttf', '#4A4560')
    o = slide(7.6, 10.3, 0, 700)
    if o:
        x0, y0 = 552 + o[0], 640 + o[1]
        panel(L, x0, y0, 476, 340, seed=30, rot=0.01)
        for i, item in enumerate(['music', 'podcasts', 'calls', 'Meta AI']):
            r = seg(tt, 7.9 + i*0.25, 8.1 + i*0.25)
            if r > 0:
                text(L, (x0 + 40, y0 + 34 + i*66), '• ' + item, 42, 'Kalam-700.ttf', PAL['meta'] if item == 'Meta AI' else PAL['ink'], reveal=r)
    out.alpha_composite(L)
    return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('fr/B', exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'fr/B/{fi:04d}.png')
