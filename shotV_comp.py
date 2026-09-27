import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, os, json, math
sys.path.insert(0, ROOT)
from common import *

DUR = 9.5
R3 = os.environ.get('R3', 'r3d/V')
A = json.load(open(f'{R3}/anchors_1_229.json')) if os.path.exists(f'{R3}/anchors_1_229.json') else {}
BG = make_bg(seed=21)
BGL = BG.new_layer(); dashed_circle(BGL, 540, 560, 440, seed=4)
BGARR0 = to_arr(BG); BG.add(BGL); BGARR = to_arr(BG)
BLUE = PAL['blue']

def near(f):
    """nearest rendered frame (on twos, or sparser when testing)"""
    ks = sorted(int(k) for k in A)
    return min(ks, key=lambda k: abs(k - f))
def anc(f, k):
    a = A[str(f)][k]; return a[0]*1080, a[1]*1080, a[2]
def spark_px(f):
    x, y, z = anc(f, 'spark'); s = A[str(f)]['sparkscale'][0]
    lens = 36 if 2.6 <= (f - 1)/24 <= 7.35 else 50
    return x, y, 0.14*max(s, 0.001)/max(z, 0.1)*lens/36*1.4*1080

CALLOUTS = [   # part, time in, label box (x, y, w), title, detail
    ('shell', 2.6, (40, 830, 320), '6 cameras', 'color passthrough'),
    ('disp', 3.3, (40, 175, 330), '5K micro OLED', 'up to 120 Hz'),
    ('lens', 4.0, (385, 880, 330), 'pancake lenses', 'eye tracking built in'),
    ('frame', 4.7, (400, 160, 330), 'magnesium frame', 'about 100 g'),
    ('arm', 5.4, (752, 185, 300), 'arms, no strap', 'open ear speakers'),
    ('puck', 6.1, (730, 840, 320), 'compute puck', '3+ hours · 12 GB RAM'),
]
C_OUT = 7.3

def label(L, x, y, w, title, detail, tt, t0, seed):
    s = pop_scale(tt, t0)
    if s <= 0: return
    if tt >= C_OUT:
        k = int((tt - C_OUT)*12)
        if k >= 3: return
        s = [1.06, 0.7, 0.3][k]
    h = 100; cx, cy = x + w/2, y + h/2
    def P(px, py): return (cx + (px - cx)*s, cy + (py - cy)*s)
    box = [P(x, y), P(x + w, y - 3), P(x + w + 2, y + h), P(x - 2, y + h + 2)]
    fill(L, poly_mask(L.size, [(px + 7, py + 8) for px, py in box]), PAL['ink'])
    fill(L, poly_mask(L.size, box), '#FFFFFF')
    band = [P(x, y), P(x + 12, y), P(x + 12, y + h), P(x, y + h)]
    fill(L, poly_mask(L.size, band), PAL['meta'])
    stroke(L, box + [box[0]], 2.6, PAL['ink'], seed=seed, taper=False, jitter=0.25)
    tx, ty = P(x + 28, y + 14); text(L, (tx, ty), title, 35*s, 'Kalam-700.ttf', PAL['ink'])
    tx, ty = P(x + 28, y + 60); text(L, (tx, ty), detail, 25*s, 'ArchitectsDaughter.ttf', '#4A4560')

def leader(L, ax, ay, x, y, w, tt, t0, seed):
    r = ease(seg(tt, t0 - 0.12, t0 + 0.12))
    if r <= 0 or tt >= C_OUT + 0.08: return
    ex = x + w/2 if abs((x + w/2) - ax) < 160 else (x + w if ax > x + w else x)
    ey = y + 100 if ay > y + 100 else y
    elbow = (ax + (ex - ax)*0.25, ey)
    stroke(L, [(ax, ay), elbow, (ex, ey)], 2.2, PAL['ink'], seed=seed, taper=False, jitter=0.2, reveal=r)
    fill(L, poly_mask(L.size, circle_pts(ax, ay, 7, n=16)), '#FFFFFF')
    stroke(L, circle_pts(ax, ay, 7, n=16) + [circle_pts(ax, ay, 7, n=16)[0]], 2.4, PAL['ink'], seed=seed + 1, taper=False)
    fill(L, poly_mask(L.size, circle_pts(ax, ay, 3, n=10)), PAL['ink'])
    # a quick highlight ring as the part is named
    hk = seg(tt, t0, t0 + 0.7)
    if 0 < hk < 1:
        rr = 40 + 40*ease_out(hk)
        dashed_circle(L, ax, ay, rr, color=PAL['meta'], width=3, dash=12, gap=8, reveal=min(1, hk*3), alpha=int(255*(1 - hk)))

def gloss(img, P, gx, gy, tt, strength=1.0):
    """comic gloss: two diagonal white streaks across the front glass"""
    m = P['I'] == 28
    if not m.any(): return img
    yy, xx = fast3d._grid(H, W)
    u = (xx - gx*SS) + (yy - gy*SS)*0.55
    o = 40*SS*math.sin(tt*0.9)
    band = ((np.abs(u - o) < 26*SS) | (np.abs(u - o - 70*SS) < 9*SS)) & m
    img = img.astype(np.float32)
    img[band] = img[band]*(1 - 0.55*strength) + 255*0.55*strength
    return img.clip(0, 255).astype(np.uint8)

def panels_glow(img, P, tt):
    m = P['I'] == 21
    if not m.any(): return img, None
    ys, xs = np.nonzero(m)
    y0, y1 = ys.min(), ys.max()
    g = (ys - y0)/max(1, y1 - y0)
    c0, c1 = fast3d.hexrgb('#EAF2FF'), fast3d.hexrgb('#6F95FF')
    col = c0[None]*(1 - g[:, None]) + c1[None]*g[:, None]
    grid = ((xs//(6*SS)) % 2 == 0) & ((ys//(6*SS)) % 2 == 0)    # a hint of pixels
    col[grid] *= 0.9
    img = img.astype(np.float32); img[ys, xs] = col
    return img.clip(0, 255).astype(np.uint8), (xs.mean()/SS, ys.mean()/SS)

def grill(img, P):
    m = P['I'] == 26
    if not m.any(): return img
    d = fast3d.halftone((H, W), np.full((H, W), 0.35), cell=9, angle=0) & m
    img = img.copy(); img[d] = (30, 27, 44)
    return img

def render(fi):
    t = fi/24; tt = twos(t)
    f3 = near(fi - fi % 2 + 1)
    P = fast3d.load(f'{R3}/{f3:04d}.exr')
    if P['I'].shape[0] != H:      # low res test renders
        from PIL import Image as _I
        P = {k: (np.array(_I.fromarray(v.astype(np.float32)).resize((W, H), _I.NEAREST)) if v.ndim == 2 else
                 np.stack([np.array(_I.fromarray(v[..., c]).resize((W, H), _I.NEAREST)) for c in range(3)], -1)) for k, v in P.items()}
        P['I'] = P['I'].astype(np.int16)
    # ---------------- background ----------------
    if tt < 0.35:
        g = BG.new_layer(); g.paste(Image.fromarray(BGARR0).convert('RGBA'))
        dashed_circle(g, 540, 560, 440, seed=4, reveal=ease(seg(tt, 0.0, 0.3)))
        bg = np.array(g)[..., :3]
    else:
        bg = BGARR.copy()
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cx, cy, _ = anc(f3, 'center')
    # drafting: the two optical axes, dashed, once the stack is apart
    ax_k = seg(tt, 2.35, 2.75)*(1 - seg(tt, 7.25, 7.45))
    if ax_k > 0:
        for s in ('L', 'R'):
            p0 = anc(f3, 'ax%s0' % s); p1 = anc(f3, 'ax%s1' % s)
            n = 34
            for k in range(n):
                if k % 2: continue
                u0, u1 = k/n, (k + 0.6)/n
                if u0 > ax_k: break
                construction_line(L, (lerp(p0[0], p1[0], u0), lerp(p0[1], p1[1], u0)), (lerp(p0[0], p1[0], u1), lerp(p0[1], p1[1], u1)), color=BLUE, width=2.2, alpha=235)
    # explosion: shock ring, burst, speed streaks behind the flying parts
    if 1.78 <= tt < 2.7:
        k = seg(tt, 1.78, 2.5)
        burst(L, cx, cy, 120 + 300*k, 260 + 520*k, 60, 7, grow=1 - k*0.7, width=(1.5, 4.5), alpha=int(200*(1 - k)))
        ring = circle_pts(cx, cy, 90 + 520*ease_out(k), n=72)
        stroke(L, ring + [ring[0]], 10*(1 - k) + 1, PAL['ink'], seed=int(tt*12), taper=False, jitter=0.8, alpha=int(230*(1 - k)))
        if tt < 2.45:
            for part in ('shell', 'disp', 'lens', 'frame', 'arm', 'puck'):
                px, py, _ = anc(f3, part)
                dx, dy = px - cx, py - cy; ln = math.hypot(dx, dy) + 1e-3
                for j in range(4):
                    off = (j - 1.5)*14
                    ox, oy = -dy/ln*off, dx/ln*off
                    stroke(L, [(px - dx*0.9 + ox, py - dy*0.9 + oy), (px - dx*0.35 + ox, py - dy*0.35 + oy)], 2.5, PAL['ink'], seed=j, alpha=150)
    if 7.45 <= tt < 7.95:   # implode: streaks point inward
        k = seg(tt, 7.45, 7.95)
        zoom_lines(L, cx, cy, int(tt*12), n=50, alpha=int(150*(1 - k)))
    sx, sy, sr = spark_px(f3)
    if sr > 2 and tt >= 0.9: glow_at(L, sx, sy, sr*2.2, 0.5)
    base = Image.fromarray(bg).convert('RGBA'); base.alpha_composite(L); bg = np.array(base)[..., :3]
    # ---------------- 3D: ink draws on, then the print fills ----------------
    yy, xx = fast3d._grid(H, W)
    if tt < 0.2:
        img = bg
    elif tt < 0.95:
        img = fast3d.edges_only(P, bg, reveal_mask=xx < W*ease(seg(tt, 0.2, 0.9)))
    else:
        full = fast3d.stylize(P, bg)
        img, _ = panels_glow(full, P, tt)
        img = grill(img, P)
        gx, gy, _ = anc(f3, 'glass')
        img = gloss(img, P, gx, gy, tt)
        if tt < 1.5:
            lines = fast3d.edges_only(P, bg)
            m = (xx + yy*0.6) < (W*1.6)*ease(seg(tt, 0.95, 1.45))
            img = np.where(m[..., None], img, lines)
    out = Image.fromarray(img).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # white hot flash at the moment of the burst
    if 1.8 <= tt < 1.96:
        glow(L, cx, cy, 300, '#FFFFFF', 0.9)
        for k in range(18):
            a = 2*math.pi*k/18 + 0.1
            stroke(L, [(cx + 60*math.cos(a), cy + 60*math.sin(a)), (cx + 330*math.cos(a), cy + 330*math.sin(a))], 8, '#FFFFFF', seed=k, alpha=235)
    # ---------------- captions ----------------
    caption(L, 56, 56, 560, 92, [('META CONNECT 2026', 'Kalam-700.ttf', 52, PAL['ink'])], tt, 0.35, seed=1, out_t=1.75)
    caption(L, 56, 56, 420, 92, [('Meta VR Glasses', 'Kalam-700.ttf', 50, PAL['ink'])], tt, 1.85, seed=2, out_t=9.3)
    caption(L, 60, 160, 470, 64, [('$1,299.99 · ships spring 2027', 'ArchitectsDaughter.ttf', 29, PAL['ink'])], tt, 8.45, '#FFFFFF', seed=3, out_t=9.3, rot=0.01)
    if 2.5 <= tt < 7.3:
        text(L, (540, 1046), 'fig. 1  ·  exploded view', 30, 'Caveat-700.ttf', BLUE, anchor='mm', reveal=seg(tt, 2.5, 2.9))
    for i, (part, t0, (bx, by, bw), title, detail) in enumerate(CALLOUTS):
        ax, ay, _ = anc(f3, part)
        leader(L, ax, ay, bx, by, bw, tt, t0, 40 + i*3)
    for i, (part, t0, (bx, by, bw), title, detail) in enumerate(CALLOUTS):
        label(L, bx, by, bw, title, detail, tt, t0, 60 + i)
    out.alpha_composite(L)
    sfx_word(out, 'BOOM!', cx + 250, cy - 250, 150, tt, 1.82, dur=0.75, rot=-9)
    sfx_word(out, 'CLICK!', cx + 170, cy - 170, 96, tt, 7.9, dur=0.6, fill_col='#FFFFFF', rot=7)
    return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('fr/V', exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'fr/V/{fi:04d}.png')
