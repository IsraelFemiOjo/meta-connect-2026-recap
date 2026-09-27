import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, os, math
sys.path.insert(0, ROOT)
from common import *

DUR = 7.0
BG = make_bg(seed=8)
BGARR = to_arr(BG)

# ---- world drawing (1x world coords), shown through a zooming camera T ----
PROFILE = [(300, 820), (272, 700), (244, 575), (250, 440), (298, 350), (380, 302), (470, 304), (540, 348), (576, 420),
           (586, 468), (580, 492), (626, 560), (592, 582), (600, 604), (590, 622), (598, 640), (572, 690), (530, 712),
           (492, 732), (488, 830)]
HAIR = [(566, 405), (544, 344), (472, 296), (380, 292), (296, 342), (248, 440), (242, 575), (270, 690), (300, 700),
        (322, 640), (345, 570), (372, 505), (420, 452), (480, 424), (540, 418)]
FRONT = (596, 482)
ARM = [(588, 470), (520, 476), (440, 494), (400, 500), (380, 520), (376, 548)]
EAR = (408, 540)
SPEAKER = (440, 500)
MOUTH = (604, 612)

def cam(tt):
    """camera: wide, push along the arm to the ear, then pan to follow Spark out"""
    z = lerp(1.0, 2.25, ease(seg(tt, 2.1, 2.8)))
    fx = lerp(540, 500, ease(seg(tt, 2.1, 2.8))); fy = lerp(540, 520, ease(seg(tt, 2.1, 2.8)))
    p = ease(seg(tt, 5.5, 7.0))
    fx += 420*p; z = lerp(z, 1.6, p)
    return z, fx, fy

def make_T(tt):
    z, fx, fy = cam(tt)
    def T(p): return ((p[0] - fx)*z + 540, (p[1] - fy)*z + 540)
    return T, z

def voice_path(tt, T, clean):
    """the friend's voice: from off screen right into the speaker near the ear"""
    m = ease(seg(tt, 0.0, 0.6))
    a0 = (lerp(830, 1250, m), lerp(900, 640, m)); a1 = (lerp(250, FRONT[0] + 8, m), lerp(900, FRONT[1], m))
    n = 110; pts = []
    dx, dy = a1[0] - a0[0], a1[1] - a0[1]; ln = math.hypot(dx, dy); nx, ny = -dy/ln, dx/ln
    amp = lerp(46, 26, m)
    for k in range(n + 1):
        u = k/n; env = math.sin(math.pi*u)**1.2
        messy = (1 - clean)*(0.5*math.sin(u*170 + tt*31) + 0.4*math.sin(u*83 - tt*17))
        off = amp*env*(0.65*math.sin(u*38 + tt*14) + 0.35*math.sin(u*91 - tt*9) + messy)
        pts.append(T((lerp(a0[0], a1[0], u) + nx*off, lerp(a0[1], a1[1], u) + ny*off)))
    return pts

NOISE = []
rng = np.random.default_rng(3)
for k in range(16):
    NOISE.append(dict(x=rng.uniform(620, 1060), y=rng.uniform(260, 860), s=rng.uniform(0.7, 1.2), kind=k % 4, t_off=2.95 + rng.uniform(0, 0.7), seed=100 + k))
NOISE += [dict(x=150, y=240, s=1.0, kind=1, t_off=3.1, seed=140), dict(x=180, y=900, s=1.1, kind=0, t_off=3.3, seed=141),
          dict(x=720, y=180, s=1.0, kind=3, t_off=3.0, seed=142)]
WORDS = ['chatter', 'clink!', 'hum', 'ha ha', 'bzz']

def noise_item(L, n, T, z, tt):
    if tt >= n['t_off'] + 0.25: return
    k = 1.0 if tt < n['t_off'] else 1 - seg(tt, n['t_off'], n['t_off'] + 0.25)   # shrinks out on twos
    x, y = T((n['x'], n['y'])); s = n['s']*z*k
    col = '#7A7390'; jit = 3*math.sin(tt*30 + n['seed'])
    if n['kind'] == 0:
        sc = [(x + 26*s*math.cos(a*2.3) + jit, y + 16*s*math.sin(a*3.1)) for a in np.linspace(0, 6, 14)]
        stroke(L, sc, 1.8*z, col, seed=n['seed'], taper=False)
    elif n['kind'] == 1:
        text(L, (x + jit, y), WORDS[n['seed'] % 5], 26*s, 'Caveat-700.ttf', col, anchor='mm')
    elif n['kind'] == 2:
        for j in range(3):
            stroke(L, [(x - 14*s + j*14*s, y - 16*s), (x - 10*s + j*14*s + jit, y + 16*s)], 1.6*z, col, seed=n['seed'] + j, taper=False)
    else:
        stroke(L, smooth([(x - 26*s, y), (x - 13*s, y - 12*s + jit), (x, y), (x + 13*s, y + 12*s), (x + 26*s, y)], 6), 1.8*z, col, seed=n['seed'], taper=False)
    if k < 1:   # eraser crumbs
        for j in range(4):
            a = j*1.7 + n['seed']; r = 22*z*(1 - k) + 6
            fill(L, poly_mask(L.size, circle_pts(x + r*math.cos(a), y + r*math.sin(a), 3*z, n=8)), '#F29CB0')

def head(L, T, z, reveal):
    skin = poly_mask(L.size, [T(p) for p in PROFILE + [(300, 820)]])
    fill(L, skin, '#F4E0C8', alpha=int(255*reveal))
    sh = poly_mask(L.size, [T(p) for p in [(300, 820), (300, 700), (360, 690), (440, 700), (492, 732), (488, 830)]])
    hatch(L, sh, '#C98E62', angle=-35, spacing=6*z, width=1.1*z, seed=22, alpha=int(170*reveal))
    hair = [T(p) for p in HAIR]
    m = poly_mask(L.size, hair)
    fill(L, m, '#3A3550', alpha=int(245*reveal))
    hatch(L, m, '#1E1B2C', angle=60, spacing=5*z, width=1.3*z, seed=21, alpha=int(200*reveal))
    stroke(L, smooth(hair[8:], 6), 2.2*z, PAL['ink'], seed=27, reveal=reveal)
    stroke(L, smooth([T(p) for p in PROFILE], 8), 3.0*z, PAL['ink'], seed=23, reveal=reveal)
    # eye
    ex, ey = T((552, 490))
    stroke(L, [(ex - 12*z, ey), (ex, ey - 5*z), (ex + 10*z, ey + 1*z)], 2.2*z, PAL['ink'], seed=24, taper=False, reveal=reveal)
    # ear
    ear = [T((EAR[0] + 26*math.cos(a), EAR[1] + 44*math.sin(a))) for a in np.linspace(-2.1, 2.4, 20)]
    fill(L, poly_mask(L.size, ear), '#F2CFA8', alpha=int(255*reveal))
    stroke(L, ear, 2.6*z, PAL['ink'], seed=25, reveal=reveal)
    inner = [T((EAR[0] + 12*math.cos(a) + 4, EAR[1] + 24*math.sin(a))) for a in np.linspace(-1.8, 1.9, 14)]
    stroke(L, inner, 1.8*z, PAL['ink'], seed=26, reveal=reveal)

def glasses_side(L, T, z, reveal, tt):
    # front of the frame seen edge on, then the arm running back over the ear
    fr = [T((582, 444)), T((598, 446)), T((600, 528)), T((584, 530))]
    fill(L, poly_mask(L.size, fr), '#2A2740', alpha=int(255*reveal))
    stroke(L, fr + [fr[0]], 2.6*z, PAL['ink'], seed=30, taper=False, reveal=reveal)
    arm = [T(p) for p in ARM]
    stroke(L, arm, 13*z, '#2A2740', seed=31, taper=False, jitter=0.15, reveal=reveal)
    stroke(L, arm, 2.0*z, PAL['ink'], seed=32, taper=False, reveal=reveal, alpha=160)
    # open ear speaker, a slot on the arm just in front of the ear
    sx, sy = T(SPEAKER)
    for j in range(3):
        stroke(L, [(sx - 12*z + j*9*z, sy - 3*z), (sx - 12*z + j*9*z, sy + 3*z)], 1.6*z, '#8FA2D6', seed=33 + j, taper=False, alpha=int(255*reveal))

def render(fi):
    t = fi/24; tt = twos(t)
    T, z = make_T(tt)
    out = Image.fromarray(BGARR).convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if 2.1 <= tt < 2.8: zoom_lines(L, 540, 540, int(tt*12))
    reveal = ease(seg(tt, 0.15, 0.95))
    # the café: a cup on a table edge
    tb = [T((0, 900)), T((1400, 880))]
    stroke(L, tb, 2.6*z, PAL['ink'], seed=40, taper=False, reveal=reveal)
    cx, cy = T((820, 840))
    cup = [(cx - 40*z, cy - 60*z), (cx + 40*z, cy - 60*z), (cx + 32*z, cy + 20*z), (cx - 32*z, cy + 20*z)]
    fill(L, poly_mask(L.size, cup), '#FFFFFF', alpha=int(255*reveal)); stroke(L, cup + [cup[0]], 2.4*z, PAL['ink'], seed=41, taper=False, reveal=reveal)
    stroke(L, circle_pts(cx + 50*z, cy - 22*z, 16*z, n=20)[-8:] + circle_pts(cx + 50*z, cy - 22*z, 16*z, n=20)[:8], 2.2*z, PAL['ink'], seed=42, taper=False, reveal=reveal)
    for j in range(2):
        stroke(L, smooth([(cx - 12*z + j*22*z, cy - 70*z), (cx - 20*z + j*22*z, cy - 95*z + 4*math.sin(tt*8 + j)), (cx - 8*z + j*22*z, cy - 120*z)], 6), 1.6*z, '#7A7390', seed=43 + j, taper=False)
    head(L, T, z, reveal)
    glasses_side(L, T, z, reveal, tt)
    # noise everywhere until Hearing Enhancement switches on
    for n in NOISE:
        if reveal > 0.6: noise_item(L, n, T, z, tt)
    clean = ease(seg(tt, 3.0, 3.6))
    col = '#7A7390' if clean < 0.5 else PAL['meta']
    wv = voice_path(tt, T, clean)
    if tt < 5.4 or True:
        stroke(L, wv, lerp(2.6, 4.6, clean)*min(z, 1.8), col if tt >= 0.6 else '#FFD27A', seed=50, taper=False, jitter=0.15)
    if clean > 0:
        # the mics pick the voice up at the front; it travels down the arm to the speaker
        seglen = [math.hypot(ARM[i+1][0] - ARM[i][0], ARM[i+1][1] - ARM[i][1]) for i in range(3)]
        for k in range(4):
            u = ((tt*1.4 + k/4) % 1.0)*sum(seglen); i = 0
            while i < 2 and u > seglen[i]: u -= seglen[i]; i += 1
            f = min(1, u/seglen[i]); p = T((lerp(ARM[i][0], ARM[i+1][0], f), lerp(ARM[i][1], ARM[i+1][1], f)))
            glow(L, p[0], p[1], 18*z, '#86B6E6', 0.8*clean)
            fill(L, poly_mask(L.size, circle_pts(p[0], p[1], 3.5*z, n=10)), '#FFFFFF', alpha=int(255*clean))
        sx, sy = T(SPEAKER)
        glow(L, sx, sy, 80*z*clean, '#86B6E6', 0.6*clean)
        for j in range(3):   # sound arcs into the ear
            r = (18 + j*16 + (tt*60 % 16))*z*0.6
            stroke(L, [(sx - r*math.cos(a), sy + r*math.sin(a)) for a in np.linspace(-0.5, 0.9, 8)], 2.2*z*0.6, PAL['meta'], seed=60 + j, taper=False, alpha=int(220*clean))
    # the wake phrase
    if 0.95 <= tt < 2.2:
        mx, my = T(MOUTH)
        caption(L, mx + 40, my - 250, 420, 116, [('"Hey Meta, start', 'Kalam-700.ttf', 38, PAL['ink']), ('Hearing Enhancement"', 'Kalam-700.ttf', 38, PAL['ink'])],
                tt, 1.0, '#FFFFFF', out_t=2.05, seed=70, rot=-0.02)
        if tt >= 1.1 and tt < 2.05:
            stroke(L, [(mx + 70, my - 128), (mx + 18, my - 18)], 3, PAL['ink'], seed=71, taper=False)
    caption(L, 56, 56, 530, 92, [('Hearing Enhancement', 'Kalam-700.ttf', 48, PAL['ink'])], tt, 3.1, seed=72, out_t=5.5)
    caption(L, 60, 790, 560, 64, [('FDA-cleared · $149 · later this year', 'ArchitectsDaughter.ttf', 29, PAL['ink'])], tt, 3.4, '#FFFFFF', out_t=5.5, seed=73, rot=0.01)
    caption(L, 60, 880, 470, 64, [('for mild to moderate hearing loss', 'ArchitectsDaughter.ttf', 27, PAL['ink'])], tt, 3.7, '#FFE36E', out_t=5.5, seed=74, rot=-0.015)
    # Spark pops out of the speaker and surfs the voice wave out of frame
    if tt >= 5.2:
        p = seg(tt, 5.5, 7.0)**1.3
        idx = int(lerp(len(wv) - 1, 0, p))
        x, y = wv[idx]
        pop = pop_scale(tt, 5.2)
        spark2d(None, L, x, y - 34*min(z, 1.8)*0.8, 30*min(z, 1.8)*pop, t=tt*3, look=(0.3, -0.05), seed=80, happy=p > 0.1)
    out.alpha_composite(L)
    sfx_word(out, 'SHHH', 820, 330, 92, tt, 3.0, dur=0.7, fill_col='#BFD3FF', rot=8)
    sfx_word(out, 'WHEE!', 760, 250, 96, tt, 5.8, dur=0.8, rot=-8)
    return out.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('fr/D', exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'fr/D/{fi:04d}.png')
