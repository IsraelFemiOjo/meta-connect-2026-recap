import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, os, json, math
sys.path.insert(0, ROOT)
from common import *

A = json.load(open('r3d/A/anchors_1_373.json'))
BG = make_bg(seed=4)
BGL = BG.new_layer()
dashed_circle(BGL, 540, 560, 430, seed=1)
BGARR0 = to_arr(BG)          # paper + dot field (no guides)
BG.add(BGL); BGARR = to_arr(BG)

def anchor(f, k):
    a = A[str(f)][k]; return a[0]*1080, a[1]*1080, a[2]

def spark_px(f):
    x, y, z = anchor(f, 'spark'); s = A[str(f)]['sparkscale'][0]
    return x, y, 0.14*max(s, 0.001)/max(z, 0.1)*2.0*1080

def render(fi):
    t = fi/24; f3 = fi - fi % 2 + 1; tt = twos(t)
    P = fast3d.load(f'r3d/A/{f3:04d}.exr')
    # ---- background: guides draw on, glow behind Spark, burst lines ----
    if t < 0.9:
        g = BG.new_layer(); g.paste(Image.fromarray(BGARR0).convert('RGBA'))
        dashed_circle(g, 540, 560, 430, seed=1, reveal=ease(seg(tt, 0.0, 0.8)))
        bg = np.array(g)[..., :3]
    else:
        bg = BGARR.copy()
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if 2.0 <= tt < 4.0:
        grow = ease(seg(tt, 2.0, 2.3))*(1 - ease(seg(tt, 3.5, 4.0)))
        cx, cy, _ = anchor(f3, 'center')
        burst(L, cx, cy, 330, 560, 44, 3, grow=grow)
    sx, sy, sr = spark_px(f3)
    if tt >= 2.6 and sr > 2: glow_at(L, sx, sy, sr*2.4, 0.5)
    if 6.8 <= tt < 7.45 or 9.2 <= tt < 9.9:
        zoom_lines(L, 540, 540, int(tt*12))
    base = Image.fromarray(bg).convert('RGBA'); base.alpha_composite(L); bg = np.array(base)[..., :3]
    # ---- 3D: ink draws on, then the print fills in ----
    yy, xx = fast3d._grid(H, W)
    if t < 0.45:
        img = bg
    elif t < 1.3:
        img = fast3d.edges_only(P, bg, reveal_mask=xx < W*ease(seg(tt, 0.45, 1.25)))
    else:
        full = fast3d.stylize(P, bg)
        if t < 2.15:
            lines = fast3d.edges_only(P, bg)
            m = (xx + yy*0.6) < (W*1.6)*ease(seg(tt, 1.3, 1.95))
            img = np.where(m[..., None], full, lines)
        else:
            img = full
    # panels scene: the 3D steps back out of focus (offset print instead of blur)
    if 9.9 <= tt < 13.0:
        k = ease(seg(tt, 9.9, 10.2))*(1 - ease(seg(tt, 12.6, 13.0)))
        if k > 0:
            img = fast3d.misregister(img, int(8*k), int(-4*k))
            img = (img.astype(np.float32)*(1 - 0.12*k) + 245*0.12*k).astype(np.uint8)
    out = Image.fromarray(img).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # ---- captions ----
    caption(L, 56, 56, 470, 92, [('Ray-Ban Meta Gen 3', 'Kalam-700.ttf', 48, PAL['ink'])], tt, 2.25, seed=3, out_t=14.35)
    caption(L, 60, 160, 330, 64, [('$449 · on sale now', 'ArchitectsDaughter.ttf', 30, PAL['ink'])], tt, 2.5, '#FFFFFF', seed=4, out_t=14.35)
    # ---- the camera close-up ----
    cx, cy, _ = anchor(f3, 'cam')
    if 7.5 <= tt < 7.65:
        for k in range(16):
            a = 2*math.pi*k/16 + 0.2
            stroke(L, [(cx + 30*math.cos(a), cy + 30*math.sin(a)), (cx + 190*math.cos(a), cy + 190*math.sin(a))], 7, '#FFFFFF', seed=k, alpha=235)
        glow(L, cx, cy, 120, '#FFFFFF', 0.85)
    if 7.75 <= tt < 9.3:
        stroke(L, [(cx + 26, cy + 18), (cx + 90, cy + 150), (650, 845)], 2.2, PAL['ink'], seed=40, taper=False, reveal=ease(seg(tt, 7.75, 7.95)))
    caption(L, 650, 800, 330, 80, [('12 MP camera', 'Kalam-700.ttf', 46, PAL['ink'])], tt, 7.85, '#FFFFFF', out_t=9.25, seed=5, rot=-0.02)
    caption(L, 690, 900, 250, 68, [('3K video', 'Kalam-700.ttf', 40, PAL['ink'])], tt, 8.1, '#FFE36E', out_t=9.25, seed=6, rot=0.02)
    out.alpha_composite(L)
    sfx_word(out, 'CLICK!', cx + 170, cy - 170, 110, tt, 7.5, dur=0.9)
    # ---- feature panels ----
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    def slide(t0, t1, dx, dy):
        p = seg(tt, t0, t0 + 0.34); q = seg(tt, t1, t1 + 0.34)
        if p <= 0 or q >= 1: return None
        k = 1 - ease_out(p) + ease(q)
        return dx*k, dy*k
    o = slide(10.0, 12.6, 700, 0)
    if o:
        x0, y0 = 548 + o[0], 60 + o[1]
        panel(L, x0, y0, 480, 330, seed=10, rot=0.012)
        wave = [(x0 + 40 + k*8, y0 + 150 + 38*math.sin(k*0.45)*math.sin(k*0.09)) for k in range(51)]
        stroke(L, wave, 4.0, PAL['meta'], seed=11, taper=False)
        erase = ease(seg(tt, 10.6, 11.5))
        rng = np.random.default_rng(12)
        for k in range(18):
            if rng.random() < erase: rng.random(); continue
            px, py = x0 + rng.uniform(40, 440), y0 + rng.uniform(60, 240)
            sc = [(px + 22*math.cos(a*2.3) + rng.normal(0, 4), py + 14*math.sin(a*3.1) + rng.normal(0, 4)) for a in np.linspace(0, 6, 12)]
            stroke(L, sc, 1.8, '#7A7390', seed=13 + k, taper=False)
        text(L, (x0 + 24, y0 + 238), '6 mics', 44, 'Kalam-700.ttf', PAL['ink'])
        text(L, (x0 + 24, y0 + 286), 'cut 90%+ of background noise', 25, 'ArchitectsDaughter.ttf', '#4A4560')
    o = slide(10.35, 12.65, -700, 0)
    if o:
        x0, y0 = 52 + o[0], 640 + o[1]
        panel(L, x0, y0, 470, 340, seed=20, rot=-0.01)
        bx, by = x0 + 60, y0 + 70
        stroke(L, [(bx, by), (bx + 250, by), (bx + 250, by + 110), (bx, by + 110), (bx, by)], 3.4, PAL['ink'], seed=21, taper=False)
        stroke(L, [(bx + 254, by + 34), (bx + 272, by + 34), (bx + 272, by + 76), (bx + 254, by + 76)], 3.0, PAL['ink'], seed=22, taper=False)
        lvl = ease(seg(tt, 10.8, 11.8))
        if lvl > 0.02:
            m = poly_mask(L.size, [(bx + 8, by + 8), (bx + 8 + 234*lvl, by + 8), (bx + 8 + 234*lvl, by + 102), (bx + 8, by + 102)])
            fill(L, m, '#BFE5C9'); hatch(L, m, PAL['green'], angle=60, spacing=5, width=1.6, seed=23, alpha=230)
        text(L, (x0 + 24, y0 + 206), 'up to 9 hours', 44, 'Kalam-700.ttf', PAL['ink'])
        text(L, (x0 + 24, y0 + 256), 'one more hour than Gen 2', 25, 'ArchitectsDaughter.ttf', '#4A4560')
    o = slide(10.7, 12.7, 0, 700)
    if o:
        x0, y0 = 552 + o[0], 640 + o[1]
        panel(L, x0, y0, 476, 340, seed=30, rot=0.01)
        # a temple arm with a round button (generic: exact button position not published)
        stroke(L, [(x0 + 30, y0 + 120), (x0 + 330, y0 + 98)], 26, '#2A2740', seed=31, taper=False, jitter=0.2)
        bxc, byc = x0 + 200, y0 + 108
        press = 1 if 11.45 <= tt < 11.7 else 0
        fill(L, poly_mask(L.size, circle_pts(bxc, byc - 4 + press*3, 15, n=24)), PAL['glow'])
        stroke(L, circle_pts(bxc, byc - 4 + press*3, 15, n=24), 2.2, PAL['ink'], seed=32, taper=False)
        pk = ease(seg(tt, 11.1, 11.45)) - ease(seg(tt, 11.7, 12.0))*0.6
        spark2d(None, L, bxc + 110 - 70*pk, byc - 70 + 20*pk, 30, t=tt*3, look=(-0.2, 0.1), seed=33, happy=tt >= 11.5)
        if tt >= 11.5:
            burst(L, bxc, byc, 26, 70, 10, 34, grow=ease(seg(tt, 11.5, 11.7)), width=(1.5, 3), color=PAL['glow'], alpha=220)
            text(L, (x0 + 320, y0 + 34), 'Meta AI', 36, 'Kalam-700.ttf', PAL['meta'], reveal=seg(tt, 11.55, 11.9))
        text(L, (x0 + 24, y0 + 206), 'new action button', 44, 'Kalam-700.ttf', PAL['ink'])
        text(L, (x0 + 24, y0 + 256), 'one press for Meta AI', 25, 'ArchitectsDaughter.ttf', '#4A4560')
    out.alpha_composite(L)
    return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('fr/A', exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'fr/A/{fi:04d}.png')
