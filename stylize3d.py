"""Turn Blender data passes into a Spider-Verse-leaning hybrid look: posterised cel light, Ben-Day halftone,
pencil hatching in the deepest shadow, variable-width ink contours, flat printed colour."""
import numpy as np, OpenEXR, math
from PIL import Image, ImageFilter

def load(path):
    with OpenEXR.File(path) as f:
        ch = {}
        for p in f.parts:
            for k, v in p.channels.items(): ch[k] = v.pixels
    comb = ch['ViewLayer.Combined']
    A = comb[..., 3] if comb.ndim == 3 else None
    N = np.stack([ch['ViewLayer.Normal.X'], ch['ViewLayer.Normal.Y'], ch['ViewLayer.Normal.Z']], -1)
    Z = ch['ViewLayer.Depth.Z']; I = np.rint(ch['ViewLayer.Object Index.X']).astype(int)
    return dict(A=A, N=N, Z=Z, I=I)

def hexrgb(c): c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)

MATS = {  # index: (lit, mid, shadow, dot colour)
    1: ('#45405E', '#2A2740', '#191727', '#0C0B14'),   # black acetate frame, read in indigo so light can play on it
    2: ('#CFE0EE', '#B6CCE0', '#98B3CC', '#6E8DB0'),   # lens tint (composited translucent)
    3: ('#45405E', '#2A2740', '#191727', '#0C0B14'),   # temples
    4: ('#4A4666', '#2E2B44', '#1C1A2A', '#0C0B14'),   # camera housing
    5: ('#5B5680', '#3A3656', '#232036', '#0C0B14'),   # capture light
    6: ('#C8C4D6', '#9C98AE', '#6F6B84', '#3B3852'),   # metal wire
    7: ('#6E86B8', '#3E4F7C', '#1E2744', '#0C0B14'),   # camera glass
}

def halftone(shape, amount, cell=11, angle=45, offset=(0, 0)):
    """amount 0..1 -> dot coverage. Returns bool mask."""
    H, W = shape
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    x += offset[0]; y += offset[1]
    a = math.radians(angle)
    u = (x*math.cos(a) + y*math.sin(a))/cell; v = (-x*math.sin(a) + y*math.cos(a))/cell
    du = u - np.round(u); dv = v - np.round(v)
    d = np.sqrt(du*du + dv*dv)
    r = np.sqrt(np.clip(amount, 0, 1)/math.pi)*1.05
    return d < r

def hatch_mask(shape, amount, period=9, angle=-35, width=0.32, seed=0):
    H, W = shape
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(seed)
    a = math.radians(angle)
    t = (x*math.cos(a) + y*math.sin(a))/period
    wob = np.sin((-x*math.sin(a) + y*math.cos(a))/37.0 + rng.random()*6)*0.12
    f = np.abs((t + wob) - np.round(t + wob))
    return (f < width) & (amount > 0.05)

def edges(P, depth_rel=0.012, normal_dot=0.80, width=4, seed=0):
    I, Z, N, A = P['I'], P['Z'], P['N'], P['A']
    Z = np.where(I > 0, Z, 1e4)
    e = np.zeros(I.shape, bool)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        I2 = np.roll(I, (dy, dx), (0, 1)); Z2 = np.roll(Z, (dy, dx), (0, 1)); N2 = np.roll(N, (dy, dx), (0, 1))
        e |= (I != I2) & ((I == 2) == (I2 == 2)) | (I != I2) & (np.minimum(I, I2) == 0)
        e |= np.abs(Z - Z2)/np.minimum(Z, Z2) > depth_rel
        dot = (N*N2).sum(-1)
        e |= (dot < normal_dot) & (I > 0) & (I2 > 0)
    # lens edges are thin, silhouette thick: variable width like a brush
    img = Image.fromarray((e*255).astype(np.uint8))
    rng = np.random.default_rng(seed)
    thick = img.filter(ImageFilter.MaxFilter(width | 1))
    # break the line slightly: modulate with low-frequency noise so width breathes
    noise = rng.standard_normal((I.shape[0]//48 + 2, I.shape[1]//48 + 2))
    noise = np.array(Image.fromarray(((noise*40) + 128).clip(0, 255).astype(np.uint8)).resize(I.shape[::-1], Image.BICUBIC)) > 104
    thin = img.filter(ImageFilter.MaxFilter(3))
    out = np.where(noise, np.array(thick) > 0, np.array(thin) > 0)
    return out

def stylize(P, light=(-0.55, -0.65, 0.55), view=(0.55, -0.8, 0.25), bg=None, seed=0, glare=True):
    H, W = P['I'].shape
    L = np.array(light, float); L /= np.linalg.norm(L)
    V = np.array(view, float); V /= np.linalg.norm(V)
    N = P['N']
    ndl = (N*L).sum(-1)
    rim = np.clip(1 - np.abs((N*V).sum(-1)), 0, 1)
    out = np.zeros((H, W, 3)) if bg is None else bg.astype(float).copy()
    I = P['I']
    for idx, (lit, mid, sh, dot) in MATS.items():
        m = I == idx
        if not m.any(): continue
        col = np.where((ndl > 0.35)[..., None], hexrgb(lit), np.where((ndl > -0.05)[..., None], hexrgb(mid), hexrgb(sh)))
        shade_amt = np.clip((0.35 - ndl)/0.9, 0, 1)
        ht = halftone((H, W), shade_amt*0.55, cell=12, angle=45)
        col = np.where(ht[..., None], hexrgb(dot)*0.6 + col*0.4, col)
        hm = hatch_mask((H, W), np.clip(-ndl - 0.25, 0, 1), period=10, seed=seed + idx)
        col = np.where((hm & (ndl < -0.25))[..., None], hexrgb(dot), col)
        # rim light in print blue, hard-edged
        col = np.where(((rim > 0.72) & (ndl > -0.2))[..., None], hexrgb('#7FA6FF'), col)
        if idx == 2:
            tint = hexrgb('#BFD3E8')
            out[m] = out[m]*0.62 + tint*0.38
        else:
            out[m] = col[m]
    e = edges(P, seed=seed)
    out[e] = hexrgb('#141221')
    return out.clip(0, 255).astype(np.uint8), (I > 0)

def misregister(img, mask, dx=5, dy=-3):
    """Offset-print look: shift the cyan and magenta separations a touch (used for out-of-focus layers)."""
    a = img.astype(float)
    r = np.roll(a[..., 0], (dy, dx), (0, 1)); b = np.roll(a[..., 2], (-dy, -dx), (0, 1))
    out = a.copy(); out[..., 0] = r; out[..., 2] = b
    return out.astype(np.uint8)
