"""Hand-inked, pencil-hatched renderer: paper, ink strokes, hatching, non-photo-blue construction lines."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

SS = 2
FONT_DIR = ROOT + '/fonts/'
PAL = dict(paper='#F1ECE0', ink='#1E1B2C', blue='#86B6E6', speck='#CBBFAC',
           night='#15142A', nightink='#EDE7DA', glow='#F4A63A', glow2='#FFD27A',
           lens='#9DB3C8', meta='#2F6BFF', red='#E4553B', green='#3FA66B')

def hexa(c, a=255):
    c = c.lstrip('#'); return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)

class Page:
    def __init__(self, w=1080, h=1080, dark=False, seed=0):
        self.w, self.h, self.dark = w, h, dark
        W, H = w*SS, h*SS
        rng = np.random.default_rng(seed)
        base = np.array(hexa(PAL['night'] if dark else PAL['paper'])[:3], float)
        low = rng.standard_normal((H//64 + 2, W//64 + 2))
        low = np.array(Image.fromarray(((low*20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) - 128
        fine = rng.standard_normal((H, W))*2.2
        arr = base[None, None, :] + (low*0.045 + fine)[:, :, None]
        self.im = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')
        d = ImageDraw.Draw(self.im)
        sp = hexa('#3A375A' if dark else PAL['speck'], 150)
        for _ in range(int(w*h/2600)):
            x, y = rng.uniform(0, W), rng.uniform(0, H); r = rng.uniform(0.6, 2.0)
            d.ellipse([x - r, y - r, x + r, y + r], fill=sp)
        # fine diagonal fibre scratches, like the reference's toothy paper
        fib = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fib)
        fc = hexa('#2B2950' if dark else '#DDD4C4', 70)
        for _ in range(int(w*h/1500)):
            x, y = rng.uniform(0, W), rng.uniform(0, H); L = rng.uniform(6, 20)
            fd.line([(x, y), (x + L*0.5, y - L)], fill=fc, width=1)
        self.im.alpha_composite(fib)
        self.layer = None

    def new_layer(self): return Image.new('RGBA', self.im.size, (0, 0, 0, 0))
    def add(self, layer): self.im.alpha_composite(layer)
    def result(self): return self.im.convert('RGB').resize((self.w, self.h), Image.LANCZOS)

def _sn(rng, n, sd, k):
    x = rng.normal(0, sd, n + 2*k)
    return np.convolve(x, np.ones(k)/k, 'same')[k:k + n]

def _jit(pts, amt, rng):
    P = np.array(pts, float)
    return P + rng.normal(0, amt, P.shape)

def smooth(pts, n=12, closed=False):
    P = np.array(pts, float)
    if closed: P = np.vstack([P[-1], P, P[0], P[1]])
    else: P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t*t, t*t*t
            out.append(0.5*((2*p1) + (-p0 + p2)*t + (2*p0 - 5*p1 + 4*p2 - p3)*t2 + (-p0 + 3*p1 - 3*p2 + p3)*t3))
    if not closed: out.append(P[-2])
    return np.array(out)

def stroke(layer, pts, width=3.0, color=None, seed=0, jitter=0.6, taper=True, reveal=1.0, alpha=255):
    """Ink line with pressure variation. pts in 1x coords. reveal<1 draws only the first part (draw-on)."""
    color = color or PAL['ink']
    rng = np.random.default_rng(seed)
    P = np.array(pts, float)
    if len(P) < 2: return
    seglen = np.hypot(*np.diff(P, axis=0).T); total = seglen.sum()
    if total <= 0: return
    # resample
    n = max(2, int(total/2.5))
    s = np.r_[0, np.cumsum(seglen)]; u = np.linspace(0, total*reveal, n)
    X = np.interp(u, s, P[:, 0]); Y = np.interp(u, s, P[:, 1])
    Q = np.stack([X, Y], 1)
    Q = Q + np.stack([_sn(rng, n, jitter, 9), _sn(rng, n, jitter, 9)], 1)
    k = np.linspace(0, 1, n)
    pres = 0.8 + 0.35*_sn(rng, n, 1.0, 15)
    if taper: pres *= np.clip(np.minimum(k*total/10, (reveal*total - k*total*reveal)/10 + 0.35), 0.35, 1)
    d = ImageDraw.Draw(layer)
    c = hexa(color, alpha)
    for i in range(n - 1):
        w = max(1.0, width*pres[i]*SS)
        a, b = Q[i]*SS, Q[i+1]*SS
        d.line([tuple(a), tuple(b)], fill=c, width=int(round(w)))
        r = w/2; d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=c)

def poly_mask(size, pts):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).polygon([(float(x*SS), float(y*SS)) for x, y in pts], fill=255)
    return m

def fill(layer, mask, color, alpha=255):
    solid = Image.new('RGBA', layer.size, hexa(color, alpha))
    layer.paste(solid, (0, 0), mask) if alpha == 255 else layer.alpha_composite(Image.composite(solid, Image.new('RGBA', layer.size, (0, 0, 0, 0)), mask))

def hatch(layer, mask, color, angle=55, spacing=7.0, width=1.4, seed=0, alpha=200, jitter=0.35, broken=0.15):
    """Coloured-pencil hatching clipped to mask. spacing/width in 1x px."""
    rng = np.random.default_rng(seed)
    bbox = mask.getbbox()
    if not bbox: return
    tmp = Image.new('RGBA', layer.size, (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1)/2, (y0 + y1)/2
    R = math.hypot(x1 - x0, y1 - y0)/2 + 10
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    t = -R
    c = hexa(color, alpha)
    while t < R:
        off = t + rng.normal(0, spacing*SS*jitter*0.3)
        ang = a + rng.normal(0, 0.02)
        ux2, uy2 = math.cos(ang), math.sin(ang)
        px, py = cx + nx*off, cy + ny*off
        L = R
        # occasional breaks, like pencil lifting
        segs = [(-L, L)]
        if rng.random() < broken:
            m = rng.uniform(-L*0.6, L*0.6); segs = [(-L, m - rng.uniform(4, 14)*SS), (m, L)]
        for s0, s1 in segs:
            d.line([(px + ux2*s0, py + uy2*s0), (px + ux2*s1, py + uy2*s1)], fill=c, width=max(1, int(width*SS*rng.uniform(0.75, 1.15))))
        t += spacing*SS*rng.uniform(0.8, 1.2)
    clipped = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    clipped.paste(tmp, (0, 0), ImageChops.multiply(tmp.getchannel('A'), mask))
    layer.alpha_composite(clipped)

def dashed_circle(layer, cx, cy, r, color=None, width=1.3, dash=10, gap=8, seed=0, reveal=1.0, alpha=200):
    color = color or PAL['blue']
    circ = 2*math.pi*r; n = int(circ*reveal/(dash + gap))
    d = ImageDraw.Draw(layer); c = hexa(color, alpha)
    for k in range(n):
        a0 = (k*(dash + gap))/r; a1 = a0 + dash/r
        pts = [((cx + r*math.cos(a))*SS, (cy + r*math.sin(a))*SS) for a in np.linspace(a0, a1, 5)]
        d.line(pts, fill=c, width=max(1, int(width*SS)))

def construction_line(layer, p0, p1, color=None, width=1.1, reveal=1.0, alpha=170):
    color = color or PAL['blue']
    x = p0[0] + (p1[0] - p0[0])*reveal; y = p0[1] + (p1[1] - p0[1])*reveal
    ImageDraw.Draw(layer).line([(p0[0]*SS, p0[1]*SS), (x*SS, y*SS)], fill=hexa(color, alpha), width=max(1, int(width*SS)))

def text(layer, xy, s, size=40, font='Kalam-700.ttf', color=None, anchor='la', reveal=1.0, alpha=255):
    color = color or PAL['ink']
    f = ImageFont.truetype(FONT_DIR + font, int(size*SS))
    n = int(round(len(s)*reveal))
    if n <= 0: return
    ImageDraw.Draw(layer).text((xy[0]*SS, xy[1]*SS), s[:n], font=f, fill=hexa(color, alpha), anchor=anchor)

def glow(layer, cx, cy, r, color, strength=0.55):
    a = Image.new('L', layer.size, 0)
    ImageDraw.Draw(a).ellipse([(cx - r)*SS, (cy - r)*SS, (cx + r)*SS, (cy + r)*SS], fill=int(255*strength))
    a = a.filter(ImageFilter.GaussianBlur(r*SS*0.45))
    g = Image.new('RGBA', layer.size, hexa(color, 255)); g.putalpha(a)
    layer.alpha_composite(g)

def circle_pts(cx, cy, rx, ry=None, n=48, a0=0.0):
    ry = rx if ry is None else ry
    return [(cx + rx*math.cos(a0 + 2*math.pi*k/n), cy + ry*math.sin(a0 + 2*math.pi*k/n)) for k in range(n + 1)]
