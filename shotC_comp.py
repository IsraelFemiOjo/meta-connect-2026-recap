import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, os, json, math
sys.path.insert(0, ROOT)
from common import *

DUR = 10.5
A = json.load(open('r3d/C/anchors_1_97.json')) if os.path.exists('r3d/C/anchors_1_97.json') else {}
BG = make_bg(seed=6)
L0 = BG.new_layer(); dashed_circle(L0, 540, 560, 430, seed=2); BG.add(L0)
BGARR = to_arr(BG)
NI = PAL['nightink']

def anchor(f, k):
    a = A[str(f)][k]; return a[0]*1080, a[1]*1080, a[2]
def spark_px(f):
    x, y, z = anchor(f, 'spark'); s = A[str(f)]['sparkscale'][0]
    return x, y, 0.14*max(s, 0.001)/max(z, 0.1)*2.0*1080

# ------------------------------------------------------------------ the night street, seen through the glasses
V = (540, 500)
def fpt(side, d, y_near):
    """point on a facade plane. side -1 left, +1 right. d 0 near .. 1 at the vanishing point"""
    xn = 30 if side < 0 else 1050
    return (lerp(xn, V[0], d), lerp(y_near, V[1], d))

def street(seed):
    pg = Page(1080, 1080, dark=True, seed=30 + seed)
    L = pg.new_layer()
    rng = np.random.default_rng(seed)
    for _ in range(40):   # stars
        x, y = rng.uniform(260, 820), rng.uniform(20, 300)
        fill(L, poly_mask(L.size, circle_pts(x, y, rng.uniform(1, 2.2), n=8)), NI, alpha=int(rng.uniform(90, 200)))
    # road + kerbs
    for x0 in (170, 910): stroke(L, [(x0, 1080), V], 2.6, NI, seed=seed + 1, taper=False)
    for x0 in (-60, 1140): stroke(L, [(x0, 1000), V], 2.0, NI, seed=seed + 2, taper=False, alpha=200)
    for k in range(7):
        d0 = 1 - 0.62**k; d1 = 1 - 0.62**(k + 0.45)
        stroke(L, [(540, lerp(1080, V[1], d0)), (540, lerp(1080, V[1], d1))], 5*(1 - d0) + 1, '#FFD27A', seed=seed + 3 + k, taper=False)
    road = poly_mask(L.size, [(170, 1080), V, (910, 1080)])
    hatch(L, road, '#3A3868', angle=8, spacing=9, width=1.2, seed=seed + 4, alpha=150)
    # buildings on both sides, converging to V
    for side in (-1, 1):
        cuts = [0.0, 0.28, 0.46, 0.6, 0.7, 0.78]
        tops = [60, 190, 120, 260, 220]
        for b in range(5):
            d0, d1 = cuts[b], cuts[b + 1]; yt = tops[b] + (40 if side > 0 else 0); yb = 960
            q = [fpt(side, d0, yt), fpt(side, d1, yt), fpt(side, d1, yb), fpt(side, d0, yb)]
            m = poly_mask(L.size, q)
            fill(L, m, '#1D1C3A')
            hatch(L, m, '#2E2C5A', angle=70 if side < 0 else 110, spacing=7, width=1.1, seed=seed + 10 + b, alpha=200)
            stroke(L, q + [q[0]], 2.4, NI, seed=seed + 20 + b + side, taper=False, jitter=0.4)
            # windows
            nx, ny = 3, 6
            for i in range(nx):
                for j in range(ny):
                    u0 = lerp(d0, d1, (i + 0.25)/nx); u1 = lerp(d0, d1, (i + 0.75)/nx)
                    h0 = lerp(yt + 40, yb - 80, j/ny); h1 = h0 + (yb - yt - 120)/ny*0.55
                    w = [fpt(side, u0, h0), fpt(side, u1, h0), fpt(side, u1, h1), fpt(side, u0, h1)]
                    lit = ((i*7 + j*3 + b*5 + (side > 0)) % 4) == 0
                    if lit: fill(L, poly_mask(L.size, w), '#FFD27A', alpha=230)
                    stroke(L, w + [w[0]], 1.2, NI, seed=seed + i*31 + j, taper=False, alpha=150)
        # lamp posts
        for d in (0.18, 0.5):
            x, yb = fpt(side, d, 1010); x = lerp(x, 540, 0.22)
            h = 420*(1 - d)
            stroke(L, [(x, yb), (x, yb - h), (x - side*40*(1 - d), yb - h - 16*(1 - d))], 4*(1 - d) + 1.5, NI, seed=seed + 60, taper=False)
            glow(L, x - side*40*(1 - d), yb - h - 8*(1 - d), 90*(1 - d) + 20, '#FFD27A', 0.55)
    pg.add(L)
    return np.array(pg.im)[..., :3]

STREETS = [street(s) for s in range(3)]

# ------------------------------------------------------------------ HUD pieces (1x coords)
HX, HY, HW, HH = 590, 300, 380, 330
def hud_frame(L, a=1.0):
    box = [(HX, HY), (HX + HW, HY), (HX + HW, HY + HH), (HX, HY + HH)]
    glow(L, HX + HW/2, HY + HH/2, HW*0.75, '#5E8BFF', 0.30*a)
    fill(L, poly_mask(L.size, box), '#0C1434', alpha=int(185*a))
    stroke(L, box + [box[0]], 2.6, '#A9C6FF', seed=5, taper=False, jitter=0.2, alpha=int(255*a))

def bike(L, x, y, s=1.0, col='#FFFFFF'):
    for dx in (-26, 26): stroke(L, circle_pts(x + dx*s, y, 17*s, n=24) + [circle_pts(x + dx*s, y, 17*s, n=24)[0]], 2.4, col, seed=7, taper=False)
    stroke(L, [(x - 26*s, y), (x - 6*s, y - 26*s), (x + 16*s, y - 26*s), (x + 26*s, y), (x + 2*s, y), (x - 6*s, y - 26*s)], 2.4, col, seed=8, taper=False)
    stroke(L, [(x + 16*s, y - 26*s), (x + 20*s, y - 36*s)], 2.4, col, seed=9, taper=False)

def bus(L, x, y, col='#FFFFFF'):
    b = [(x, y), (x + 70, y), (x + 70, y + 56), (x, y + 56)]
    stroke(L, b + [b[0]], 2.6, col, seed=11, taper=False)
    for k in range(3):
        w = [(x + 6 + k*21, y + 8), (x + 22 + k*21, y + 8), (x + 22 + k*21, y + 26), (x + 6 + k*21, y + 26)]
        stroke(L, w + [w[0]], 1.8, col, seed=12 + k, taper=False)
    for dx in (14, 56): fill(L, poly_mask(L.size, circle_pts(x + dx, y + 58, 7, n=12)), col)

def face(L, x, y, t, a=1.0):
    col = '#9FD0FF'
    fl = 0.8 + 0.2*math.sin(t*37)
    glow(L, x, y + 10, 110, '#6FB2FF', 0.35*a*fl)
    head = circle_pts(x, y, 44, 54, n=36)
    fill(L, poly_mask(L.size, head), '#2A5A9A', alpha=int(120*a))
    stroke(L, head + [head[0]], 2.4, col, seed=13, taper=False, alpha=int(255*a*fl))
    stroke(L, smooth([(x - 46, y - 8), (x - 30, y - 50), (x + 10, y - 58), (x + 44, y - 30), (x + 46, y - 8)], 8), 2.4, col, seed=14, taper=False, alpha=int(255*a))
    for s in (-1, 1): fill(L, poly_mask(L.size, circle_pts(x + s*16, y + 2, 4, 6, n=10)), col, alpha=int(255*a))
    stroke(L, smooth([(x - 14, y + 24), (x, y + 32), (x + 14, y + 24)], 6), 2.2, col, seed=15, taper=False, alpha=int(255*a))
    stroke(L, smooth([(x - 70, y + 118), (x - 50, y + 70), (x, y + 62), (x + 50, y + 70), (x + 70, y + 118)], 8), 2.4, col, seed=16, taper=False, alpha=int(255*a))
    # scan lines, the hologram tell
    for k in range(-60, 120, 9):
        ImageDraw.Draw(L).line([((x - 80)*SS, (y + k)*SS), ((x + 80)*SS, (y + k)*SS)], fill=hexa('#9FD0FF', int(40*a)), width=SS)

def wave(L, t, amp, x0=250, x1=830, y=900, col='#FFD27A', seed=70, width=4.0):
    n = 90
    pts = []
    for k in range(n + 1):
        u = k/n; env = math.sin(math.pi*u)**1.5
        pts.append((lerp(x0, x1, u), y + amp*env*(0.65*math.sin(u*38 + t*14) + 0.35*math.sin(u*91 - t*9))))
    stroke(L, pts, width, col, seed=seed, taper=False, jitter=0.2)

def card_in(tt, t0, t1):
    """HUD cards slide up and fade in on twos, then out"""
    a = seg(tt, t0, t0 + 0.25)*(1 - seg(tt, t1 - 0.2, t1))
    return a, 30*(1 - ease_out(seg(tt, t0, t0 + 0.25)))

def pov(fi, tt):
    img = STREETS[(fi//2) % 3].copy()
    bob = int(round(3*math.sin(tt*2*math.pi*1.6)))*SS
    img = np.roll(img, bob, axis=0)
    out = Image.fromarray(img).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hud_frame(L, seg(tt, 4.2, 4.45))
    # 1. cycling directions
    a, dy = card_in(tt, 4.35, 6.3)
    if a > 0:
        bike(L, HX + 60, HY + 70 + dy, 0.9, '#FFFFFF')
        text(L, (HX + 120, HY + 44 + dy), 'cycling', 30, 'Kalam-700.ttf', '#A9C6FF', alpha=int(255*a))
        r = ease(seg(tt, 4.5, 5.0))
        arrow = [(HX + 110, HY + 290 + dy), (HX + 110, HY + 190 + dy), (HX + 130, HY + 150 + dy), (HX + 250, HY + 150 + dy)]
        stroke(L, smooth(arrow, 8), 14, '#FFFFFF', seed=17, taper=False, reveal=r, alpha=int(255*a))
        if r > 0.95:
            fill(L, poly_mask(L.size, [(HX + 250, HY + 122 + dy), (HX + 296, HY + 150 + dy), (HX + 250, HY + 178 + dy)]), '#FFFFFF', alpha=int(255*a))
        text(L, (HX + 170, HY + 210 + dy), 'turn right', 40, 'Kalam-700.ttf', '#FFFFFF', alpha=int(255*a), reveal=seg(tt, 4.9, 5.2))
    # 2. transit
    a, dy = card_in(tt, 6.3, 8.3)
    if a > 0:
        bus(L, HX + 30, HY + 40 + dy)
        text(L, (HX + 120, HY + 44 + dy), 'next departures', 32, 'Kalam-700.ttf', '#FFFFFF', alpha=int(255*a))
        for k in range(3):
            r = seg(tt, 6.6 + k*0.18, 6.85 + k*0.18)
            if r <= 0: continue
            yy = HY + 140 + k*60 + dy
            badge = [(HX + 30, yy), (HX + 78, yy), (HX + 78, yy + 38), (HX + 30, yy + 38)]
            fill(L, poly_mask(L.size, badge), ['#2F6BFF', '#3FA66B', '#E4553B'][k], alpha=int(255*a*r))
            stroke(L, [(HX + 100, yy + 12), (HX + 100 + 180*r, yy + 12)], 7, '#FFFFFF', seed=20 + k, taper=False, alpha=int(200*a))
            stroke(L, [(HX + 100, yy + 30), (HX + 100 + 110*r, yy + 30)], 4, '#A9C6FF', seed=24 + k, taper=False, alpha=int(170*a))
    # 3. hologram call
    a, dy = card_in(tt, 8.3, 10.45)
    if a > 0:
        face(L, HX + HW/2, HY + 150 + dy, tt, a)
        text(L, (HX + 24, HY + 22 + dy), 'call', 28, 'Kalam-700.ttf', '#A9C6FF', alpha=int(255*a))
        for k in range(3):
            if (int(tt*6) + k) % 3 == 0: fill(L, poly_mask(L.size, circle_pts(HX + 84 + k*14, HY + 38 + dy, 3.5, n=8)), '#A9C6FF', alpha=int(255*a))
        fill(L, poly_mask(L.size, circle_pts(HX + HW/2, HY + HH - 34 + dy, 18, n=20)), '#E4553B', alpha=int(255*a))
    # Spark perched on the HUD corner, watching
    hop = abs(math.sin(twos(tt)*math.pi*1.2))*8 if tt < 9.9 else 0
    look = (0.25, -0.1) if tt < 8.3 else (0.3, -0.2)
    spark2d(None, L, HX - 34, HY + HH - 30 - hop, 34, t=tt*3, look=look, seed=31, happy=(8.6 < tt < 9.2), blink=(int(tt*24) % 70 == 0))
    # captions for each HUD beat
    caption(L, 56, 56, 500, 92, [('Meta Ray-Ban Display', 'Kalam-700.ttf', 48, PAL['ink'])], tt, 4.25, seed=40, out_t=10.35)
    caption(L, 60, 700, 380, 70, [('cycling directions', 'Kalam-700.ttf', 42, PAL['ink'])], tt, 4.6, '#FFFFFF', out_t=6.25, seed=41, rot=-0.02)
    caption(L, 60, 700, 390, 70, [('transit departures', 'Kalam-700.ttf', 42, PAL['ink'])], tt, 6.55, '#FFFFFF', out_t=8.25, seed=42, rot=0.015)
    caption(L, 50, 680, 530, 70, [('hologram calls on WhatsApp', 'Kalam-700.ttf', 38, PAL['ink'])], tt, 8.55, '#FFFFFF', out_t=10.35, seed=43, rot=-0.015)
    caption(L, 80, 782, 220, 58, [('early access', 'ArchitectsDaughter.ttf', 30, PAL['ink'])], tt, 8.8, '#FFE36E', out_t=10.35, seed=44, rot=0.03)
    # the caller's voice becomes the waveform we match cut on
    amp = 46*ease(seg(tt, 9.0, 9.6)) if tt < 10.2 else 46
    if tt >= 9.0: wave(L, tt, amp)
    out.alpha_composite(L)
    return out

def render(fi):
    t = fi/24; tt = twos(t)
    if tt >= 4.05:
        out = pov(fi, tt)
        # iris: the POV opens as a lens shaped window from the centre
        k = ease(seg(tt, 4.05, 4.35))
        if k < 1:
            m = Image.new('L', (W, H), 0)
            ImageDraw.Draw(m).rounded_rectangle([(540 - 600*k)*SS, (540 - 420*k)*SS, (540 + 600*k)*SS, (540 + 420*k)*SS], radius=int(260*k*SS) + 1, fill=255)
            white = Image.new('RGBA', (W, H), (255, 252, 240, 255))
            out = Image.composite(out, white, m)
        return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)
    f3 = min(fi - fi % 2 + 1, 97)
    P = fast3d.load(f'r3d/C/{f3:04d}.exr')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sx, sy, sr = spark_px(f3)
    if sr > 2 and tt < 3.7: glow_at(L, sx, sy, sr*2.4, 0.5)
    if 2.9 <= tt < 3.95: zoom_lines(L, 540, 540, int(tt*12))
    base = Image.fromarray(BGARR).convert('RGBA'); base.alpha_composite(L); bg = np.array(base)[..., :3]
    img = fast3d.stylize(P, bg)
    out = Image.fromarray(img).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lx, ly, _ = anchor(f3, 'lens'); cx, cy, _ = anchor(f3, 'center')
    lr = 0.72*math.hypot(lx - cx, ly - cy)
    if 1.0 <= tt < 2.55:
        a = 1 - seg(tt, 2.35, 2.55)
        dashed_circle(L, lx, ly, lr, color=PAL['blue'], width=3, dash=14, gap=8, reveal=ease(seg(tt, 1.0, 1.4)), alpha=int(255*a))
        g = ease(seg(tt, 1.4, 1.7))*a
        if g > 0:
            pulse = 0.85 + 0.15*math.sin(tt*9)
            glow(L, lx + lr*0.1, ly + lr*0.15, lr*0.55, '#5E8BFF', 0.5*g*pulse)
            q = [(lx - lr*0.2, ly - lr*0.05), (lx + lr*0.4, ly - lr*0.05), (lx + lr*0.4, ly + lr*0.35), (lx - lr*0.2, ly + lr*0.35)]
            fill(L, poly_mask(L.size, q), '#2F6BFF', alpha=int(170*g))
            stroke(L, q + [q[0]], 2.2, '#FFFFFF', seed=51, taper=False, alpha=int(255*g))
        stroke(L, [(lx - lr*0.5, ly + lr*0.8), (lx - lr*0.55, 820), (300, 830)], 2.2, PAL['ink'], seed=52, taper=False, reveal=ease(seg(tt, 1.5, 1.75))*a)
    caption(L, 56, 56, 500, 92, [('Meta Ray-Ban Display', 'Kalam-700.ttf', 48, PAL['ink'])], tt, 0.3, seed=3, out_t=2.7)
    caption(L, 60, 160, 160, 64, [('$799', 'Kalam-700.ttf', 40, PAL['ink'])], tt, 0.55, '#FFFFFF', seed=4, out_t=2.7)
    caption(L, 300, 790, 420, 80, [('a screen in the right lens', 'Kalam-700.ttf', 38, PAL['ink'])], tt, 1.7, '#FFFFFF', out_t=2.5, seed=5, rot=-0.02)
    out.alpha_composite(L)
    if tt >= 3.8:   # flash as we go through the lens
        k = seg(tt, 3.8, 4.0)
        out = Image.blend(out, Image.new('RGBA', (W, H), (255, 252, 240, 255)), k)
    sfx_word(out, 'WHOOSH', 760, 250, 96, tt, 3.05, dur=0.7, rot=-10)
    return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('fr/C', exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'fr/C/{fi:04d}.png')
