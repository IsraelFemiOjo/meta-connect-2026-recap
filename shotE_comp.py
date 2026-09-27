import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, os, json, math
sys.path.insert(0, ROOT)
from common import *

DUR = 8.2
T3 = 4.3          # shot time where the 3D Charm starts
A = json.load(open('r3d/E/anchors_1_121.json')) if os.path.exists('r3d/E/anchors_1_121.json') else {}
BG2 = to_arr(make_bg(seed=9))
BG3 = make_bg(seed=10); L0 = BG3.new_layer(); dashed_circle(L0, 540, 540, 400, seed=3); BG3.add(L0); BG3 = to_arr(BG3)

def anchor(f, k):
    a = A[str(f)][k]; return a[0]*1080, a[1]*1080, a[2]

# ---------------------------------------------------------------- 2D: Muse, the agent, as a to do list that ticks itself
NX, NY, NW, NH = 250, 300, 770, 430
ITEMS = [('book appointments', 1.3), ('check flight prices', 2.0), ("buy what you're looking at", 2.7)]

def icon(L, kind, x, y):
    ink = PAL['ink']
    if kind == 0:     # calendar
        b = [(x - 22, y - 16), (x + 22, y - 16), (x + 22, y + 22), (x - 22, y + 22)]
        fill(L, poly_mask(L.size, b), '#FFFFFF'); fill(L, poly_mask(L.size, [(x - 22, y - 16), (x + 22, y - 16), (x + 22, y - 4), (x - 22, y - 4)]), PAL['red'])
        stroke(L, b + [b[0]], 2.2, ink, seed=1, taper=False)
        for dx in (-10, 10): stroke(L, [(x + dx, y - 22), (x + dx, y - 10)], 2.4, ink, seed=2, taper=False)
        for i in range(3):
            for j in range(2): fill(L, poly_mask(L.size, circle_pts(x - 12 + i*12, y + 4 + j*10, 2.2, n=8)), ink)
    elif kind == 1:   # plane
        pl = [(x - 24, y + 2), (x + 20, y - 2), (x + 26, y), (x + 20, y + 3), (x - 24, y + 4)]
        fill(L, poly_mask(L.size, pl), '#FFFFFF'); stroke(L, pl + [pl[0]], 2.0, ink, seed=3, taper=False)
        wing = [(x - 2, y + 1), (x - 14, y - 20), (x - 6, y - 20), (x + 10, y + 1)]
        fill(L, poly_mask(L.size, wing), PAL['meta']); stroke(L, wing, 2.0, ink, seed=4, taper=False)
        wing2 = [(x - 2, y + 3), (x - 12, y + 20), (x - 4, y + 20), (x + 10, y + 3)]
        fill(L, poly_mask(L.size, wing2), PAL['meta']); stroke(L, wing2, 2.0, ink, seed=5, taper=False)
        stroke(L, [(x - 22, y + 2), (x - 26, y - 10), (x - 20, y - 10), (x - 16, y + 2)], 2.0, ink, seed=6, taper=False)
    else:             # shopping bag
        b = [(x - 20, y - 10), (x + 20, y - 10), (x + 24, y + 22), (x - 24, y + 22)]
        fill(L, poly_mask(L.size, b), PAL['glow2']); stroke(L, b + [b[0]], 2.2, ink, seed=7, taper=False)
        stroke(L, smooth([(x - 10, y - 10), (x - 9, y - 24), (x, y - 28), (x + 9, y - 24), (x + 10, y - 10)], 6), 2.2, ink, seed=8, taper=False)

def notepad(L, tt, ox=0):
    x0 = NX + ox
    oy = 900*(1 - ease_out(seg(tt, 0.1, 0.45)))
    if oy > 890: return
    NYo = NY + oy
    panel(L, x0, NYo, NW, NH, seed=50, fill_col='#FBF8EF', rot=-0.012)
    for k in range(4):   # ruled lines, drafting blue
        stroke(L, [(x0 + 30, NYo + 88 + k*100), (x0 + NW - 30, NYo + 88 + k*100)], 1.0, PAL['blue'], seed=51 + k, taper=False, alpha=150)
    stroke(L, [(x0 + 104, NYo + 20), (x0 + 104, NYo + NH - 20)], 1.2, PAL['red'], seed=58, taper=False, alpha=140)
    text(L, (x0 + 130, NYo + 30), 'Muse, can you...', 34, 'Caveat-700.ttf', '#4A4560')
    for i, (label, t0) in enumerate(ITEMS):
        y = NYo + 140 + i*100
        r = ease(seg(tt, t0 - 0.35, t0))
        if r <= 0: continue
        bx = x0 + 44
        box = [(bx - 18, y - 18), (bx + 18, y - 18), (bx + 18, y + 18), (bx - 18, y + 18)]
        fill(L, poly_mask(L.size, box), '#FFFFFF'); stroke(L, box + [box[0]], 2.4, PAL['ink'], seed=60 + i, taper=False, reveal=r)
        icon(L, i, x0 + 150, y)
        text(L, (x0 + 196, y - 26), label, 42, 'Kalam-700.ttf', PAL['ink'], reveal=r)
        tk = ease(seg(tt, t0 + 0.05, t0 + 0.3))
        if tk > 0:
            stroke(L, [(bx - 14, y), (bx - 3, y + 14), (bx + 28, y - 30)], 7, PAL['green'], seed=70 + i, taper=False, reveal=tk)

def part2d(fi, tt):
    out = Image.fromarray(BG2).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    notepad(L, tt)
    caption(L, 56, 56, 200, 100, [('Muse', 'Kalam-700.ttf', 64, PAL['ink'])], tt, 0.35, seed=80)
    caption(L, 60, 172, 430, 64, [("Meta's personal AI agent", 'ArchitectsDaughter.ttf', 30, PAL['ink'])], tt, 0.6, '#FFFFFF', seed=81)
    caption(L, 330, 800, 520, 74, [('coming soon to AI glasses', 'Kalam-700.ttf', 40, PAL['ink'])], tt, 3.25, '#FFFFFF', seed=82, rot=-0.015)
    # Spark arrives from the left, still riding the tail of the voice wave, then helps with the list
    if tt < 0.7:
        p = ease_out(seg(tt, 0.0, 0.7)); x = lerp(-40, 190, p); y = 870 - 20*math.sin(p*math.pi)
        tail = [(x - 260 + k*6, 880 + 14*math.sin(k*0.5 + tt*14)) for k in range(44)]
        stroke(L, tail, 4, PAL['meta'], seed=90, taper=True, alpha=int(255*(1 - seg(tt, 0.4, 0.7))))
    else:
        # hop up next to whichever item is being ticked
        tgt_y = 870
        for i, (_, t0) in enumerate(ITEMS):
            if tt >= t0 - 0.4: tgt_y = NY + 140 + i*100
        hop = abs(math.sin(twos(tt)*math.pi*1.5))*10
        x, y = 190, tgt_y - hop
    tick_now = any(0 <= tt - (t0 + 0.05) < 0.4 for _, t0 in ITEMS)
    spark2d(None, L, x, y, 36, t=tt*3, look=(0.35, -0.05), seed=91, happy=tick_now or tt > 3.3)
    out.alpha_composite(L)
    for i, (_, t0) in enumerate(ITEMS):
        sfx_word(out, 'TICK!', NX + 60, NY + 92 + i*100, 52, tt, t0 + 0.1, dur=0.35, fill_col='#BFE5C9', rot=-6)
    return out

# ---------------------------------------------------------------- 3D: the Muse Charm
def part3d(fi, tt):
    t3 = tt - T3; f3 = min(max(1, int(round(t3*24)) + 1), 121); f3 = f3 - (f3 - 1) % 2
    P = fast3d.load(f'r3d/E/{f3:04d}.exr')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sx, sy, _ = anchor(f3, 'spark')
    if t3 > 0.9: glow_at(L, sx, sy, 110, 0.5)
    base = Image.fromarray(BG3).convert('RGBA'); base.alpha_composite(L); bg = np.array(base)[..., :3]
    img = fast3d.stylize(P, bg).astype(np.float32)
    # the screen wakes up: a soft glowing gradient, no mascot, no invented UI
    from scipy.ndimage import binary_erosion
    front = (P['I'] == 13) & (P['N'][..., 1] < -0.85)
    scr = binary_erosion(front, iterations=16) if front.any() else front
    on = ease(seg(t3, 0.35, 0.65))
    if scr.any():
        yy, xx = np.nonzero(scr)
        cy_, cx_ = yy.mean(), xx.mean(); hh = yy.max() - yy.min() + 1
        g = np.clip((yy - yy.min())/hh, 0, 1)
        c0, c1 = fast3d.hexrgb('#5E8BFF'), fast3d.hexrgb('#FFB866')
        col = c0[None]*(1 - g[:, None]) + c1[None]*g[:, None]
        shimmer = 0.9 + 0.1*math.sin(t3*6)
        img[yy, xx] = fast3d.hexrgb('#1B2140')[None]*(1 - on) + col*on*shimmer
        rim = scr & ~binary_erosion(scr, iterations=4)
        img[rim] = fast3d.hexrgb('#141221')
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if scr.any() and on > 0:
        glow(L, cx_/SS, cy_/SS, 190, '#7FA6FF', 0.35*on)
        for k in range(3):   # a listening pulse
            a = 0.5 + 0.5*math.sin(t3*8 - k*0.9)
            fill(L, poly_mask(L.size, circle_pts(cx_/SS - 34 + k*34, cy_/SS, 9 + 3*a, n=14)), '#FFFFFF', alpha=int(230*on))
    caption(L, 56, 56, 330, 92, [('Muse Charm', 'Kalam-700.ttf', 52, PAL['ink'])], tt, T3 + 0.55, seed=83, out_t=8.05)
    caption(L, 60, 164, 380, 64, [('a 2 inch touchscreen', 'ArchitectsDaughter.ttf', 30, PAL['ink'])], tt, T3 + 0.8, '#FFFFFF', seed=84, out_t=8.05)
    caption(L, 60, 244, 330, 64, [('this holiday season', 'ArchitectsDaughter.ttf', 30, PAL['ink'])], tt, T3 + 1.05, '#FFE36E', seed=85, out_t=8.05)
    out.alpha_composite(L)
    sfx_word(out, 'BLIP!', 800, 330, 84, tt, T3 + 0.4, dur=0.6, fill_col='#BFD3FF', rot=8)
    return out

def render(fi):
    t = fi/24; tt = twos(t)
    if tt < 4.0: out = part2d(fi, tt)
    elif tt >= 4.4: out = part3d(fi, tt)
    else:
        # whip pan: the list slides out left while the Charm swings in from the right
        e = ease(seg(tt, 4.0, 4.4))
        a = part2d(fi, 3.99); b = part3d(fi, max(tt, T3))
        out = Image.new('RGBA', (W, H))
        out.paste(a, (int(-W*e), 0)); out.paste(b, (int(W*(1 - e)), 0))
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        rng = np.random.default_rng(int(tt*12))
        for k in range(40):
            y = rng.uniform(0, 1080); x = rng.uniform(-200, 1080); ln = rng.uniform(200, 700)
            stroke(L, [(x, y), (x + ln, y)], rng.uniform(1, 4), PAL['ink'], seed=k, taper=True, alpha=150)
        out.alpha_composite(L)
    return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('fr/E', exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'fr/E/{fi:04d}.png')
