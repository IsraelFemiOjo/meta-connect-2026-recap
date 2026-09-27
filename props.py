import math, numpy as np
from ink import *
from PIL import ImageChops

# Wayfarer-style rim for the viewer's-right lens, local coords (lens centre at 0,0)
WAY_OUT = [(-168, -104), (-60, -112), (90, -112), (176, -124), (192, -100), (177, -40), (150, 40), (96, 90), (0, 100), (-96, 88), (-148, 46), (-170, -20)]
WAY_IN = [(-148, -78), (-50, -86), (100, -84), (160, -92), (154, -40), (132, 32), (86, 72), (0, 82), (-84, 70), (-130, 34), (-150, -12)]

def _xf(pts, cx, cy, s, mirror=False, dx=0):
    return [(cx + (-(x) if mirror else x)*s + dx*s*(-1 if mirror else 1), cy + y*s) for x, y in pts]

def glasses(page, layer, cx, cy, s=1.0, seed=0, camera=True, led=True, style='wayfarer', lens_color=None,
            reveal=1.0, frame_color=None, display=False):
    """Front view. Viewer's right = wearer's left (camera side, per Meta's layout). reveal draws lines on."""
    frame_color = frame_color or PAL['ink']
    size = layer.size
    off = 196
    outs = [smooth(_xf(WAY_OUT, cx, cy, s, m, off), 8, True) for m in (False, True)]
    ins = [smooth(_xf(WAY_IN, cx, cy, s, m, off), 8, True) for m in (False, True)]
    if style == 'clubmaster':
        # browline: acetate brow on top, thin wire below
        brow = [(-172, -120), (-60, -128), (90, -128), (180, -138), (194, -110), (178, -62), (120, -76), (0, -80), (-120, -74), (-168, -56)]
        outs_b = [smooth(_xf(brow, cx, cy, s, m, off), 8, True) for m in (False, True)]
    bridge = [(cx - 40*s, cy - 106*s), (cx + 40*s, cy - 106*s), (cx + 34*s, cy - 62*s), (cx, cy - 70*s), (cx - 34*s, cy - 62*s)]
    if reveal >= 0.55:
        f = min(1, (reveal - 0.55)/0.45)
        # lenses
        lc = lens_color or PAL['lens']
        for k, inn in enumerate(ins):
            m = poly_mask(size, inn)
            hatch(layer, m, lc, angle=62, spacing=8, width=1.3, seed=seed + 10 + k, alpha=int(150*f))
        # frame body
        if style == 'clubmaster':
            fm = Image.new('L', size, 0)
            for ob in outs_b: fm = ImageChops.lighter(fm, poly_mask(size, ob))
            fm = ImageChops.lighter(fm, poly_mask(size, bridge))
            for inn in ins: fm = ImageChops.subtract(fm, poly_mask(size, inn))
        else:
            fm = Image.new('L', size, 0)
            for o in outs: fm = ImageChops.lighter(fm, poly_mask(size, o))
            fm = ImageChops.lighter(fm, poly_mask(size, bridge))
            for inn in ins: fm = ImageChops.subtract(fm, poly_mask(size, inn))
        fm = fm.point(lambda v: int(v*f))
        fill(layer, fm, '#27233B' if frame_color == PAL['ink'] else frame_color)
        hatch(layer, fm, '#6C6690', angle=-32, spacing=5, width=1.1, seed=seed + 3, alpha=int(150*f))
        # highlight along the brow
        for m in (False, True):
            hl = _xf([(-120, -98), (0, -102), (120, -106)], cx, cy, s, m, off)
            stroke(layer, smooth(hl, 8), 2.2*s, '#F1ECE0', seed=seed + 7 + m, alpha=int(150*f), jitter=0.3)
    # ink outlines draw on first
    rv = min(1, reveal/0.55)
    for k, o in enumerate(outs if style != 'clubmaster' else outs_b):
        stroke(layer, o, 2.6*s, PAL['ink'], seed=seed + 20 + k, reveal=rv)
    for k, inn in enumerate(ins):
        stroke(layer, inn, 2.0*s if style != 'clubmaster' else 1.6*s, PAL['ink'], seed=seed + 30 + k, reveal=rv)
    if reveal >= 0.8:
        for k, (m, xs) in enumerate(((False, 1), (True, -1))):
            # glare on each lens
            g = _xf([(-80, -60), (-30, -76)], cx, cy, s, m, off)
            stroke(layer, g, 3.2*s, '#FFFFFF', seed=seed + 40 + k, alpha=170, jitter=0.2)
            g = _xf([(-96, -30), (-70, -40)], cx, cy, s, m, off)
            stroke(layer, g, 2.2*s, '#FFFFFF', seed=seed + 44 + k, alpha=150, jitter=0.2)
    cam_xy = (cx + (off + 170)*s, cy - 100*s)
    led_xy = (cx - (off + 170)*s, cy - 100*s)
    if reveal >= 0.85:
        if camera:
            for rr, col in ((13, '#2B2842'), (9, '#0F0E1A'), (4, '#6E86B8')):
                fill(layer, poly_mask(size, circle_pts(cam_xy[0], cam_xy[1], rr*s, n=24)), col)
            stroke(layer, circle_pts(cam_xy[0], cam_xy[1], 13*s, n=24), 1.4*s, '#8A84A8', seed=seed + 50, alpha=200)
            fill(layer, poly_mask(size, circle_pts(cam_xy[0] - 3*s, cam_xy[1] - 3*s, 2*s, n=12)), '#FFFFFF')
        if led:
            fill(layer, poly_mask(size, circle_pts(led_xy[0], led_xy[1], 5*s, n=16)), '#3A3656')
    return dict(cam=cam_xy, led=led_xy, lensR=(cx + off*s, cy), lensL=(cx - off*s, cy), outs=outs, ins=ins)

def muse(page, layer, cx, cy, r=34, t=0.0, look=(0, 0), blink=False, seed=0, happy=False, glow_amt=1.0, squash=1.0):
    """Muse: an original little spark-creature. Warm core, ink outline, a four-point star tuft."""
    size = layer.size
    glow(layer, cx, cy, r*2.3, PAL['glow2'], 0.45*glow_amt)
    ry = r*squash; rx = r/squash**0.5
    body = circle_pts(cx, cy, rx, ry, n=40, a0=t)
    m = poly_mask(size, body)
    fill(layer, m, '#FFD27A')
    # shade: hatch on the lower-left
    sh = poly_mask(size, circle_pts(cx + r*0.35, cy - r*0.35, rx*1.05, ry*1.05, n=40))
    hatch(layer, ImageChops.subtract(m, sh), '#EE8A24', angle=40, spacing=4.5, width=1.3, seed=seed + 1, alpha=230)
    hatch(layer, m, '#F6B24A', angle=-35, spacing=7, width=1.0, seed=seed + 2, alpha=110)
    stroke(layer, body, 2.4, PAL['ink'], seed=seed + 3, jitter=0.35)
    # star tuft
    sx, sy = cx + r*0.15, cy - ry - r*0.55
    star = []
    for k in range(8):
        a = -math.pi/2 + k*math.pi/4 + 0.12*math.sin(t*3)
        rr = r*0.42 if k % 2 == 0 else r*0.14
        star.append((sx + rr*math.cos(a), sy + rr*math.sin(a)))
    star.append(star[0])
    stroke(layer, [(cx + r*0.05, cy - ry*0.92), (sx, sy + r*0.12)], 2.0, PAL['ink'], seed=seed + 4)
    fill(layer, poly_mask(size, star), '#FFE3A1')
    stroke(layer, star, 1.8, PAL['ink'], seed=seed + 5, taper=False, jitter=0.2)
    # face
    ex = r*0.33; ey = cy - r*0.02 + look[1]*r
    for s_ in (-1, 1):
        x = cx + s_*ex + look[0]*r
        if blink or happy:
            stroke(layer, [(x - r*0.12, ey + r*0.03), (x, ey - r*0.08), (x + r*0.12, ey + r*0.03)], 2.4, PAL['ink'], seed=seed + 6 + s_, taper=False)
        else:
            fill(layer, poly_mask(size, circle_pts(x, ey, r*0.09, r*0.15, n=20)), PAL['ink'])
            fill(layer, poly_mask(size, circle_pts(x - r*0.03, ey - r*0.06, r*0.035, n=10)), '#FFFFFF')
    mx = cx + look[0]*r
    if happy:
        mouth = circle_pts(mx, ey + r*0.28, r*0.13, r*0.10, n=16)
        fill(layer, poly_mask(size, [p for p in mouth if p[1] >= ey + r*0.27] + [(mx - r*0.13, ey + r*0.28)]), PAL['ink'])
    else:
        stroke(layer, smooth([(mx - r*0.1, ey + r*0.24), (mx, ey + r*0.31), (mx + r*0.1, ey + r*0.24)], 6), 2.0, PAL['ink'], seed=seed + 9, taper=False)
    # blush
    for s_ in (-1, 1):
        hatch(layer, poly_mask(size, circle_pts(cx + s_*r*0.55 + look[0]*r, ey + r*0.2, r*0.12, r*0.07, n=14)), PAL['red'], angle=30, spacing=3, width=1.0, seed=seed + 11 + s_, alpha=160)

def callout(layer, anchor, label_xy, lines, seed=0, reveal=1.0, size=30, color=None, align='la'):
    """Draftsman-style leader line with a dot and hand-lettered label."""
    color = color or PAL['ink']
    ax, ay = anchor; lx, ly = label_xy
    endx = lx - 14 if align in ('la', 'ls') else lx + 14
    elbow = (endx - (26 if align == 'la' else -26), ly + size*0.62) if align == 'la' else (endx + 26, ly + size*0.62)
    r1 = min(1, reveal*2)
    stroke(layer, [anchor, elbow, (endx, ly + size*0.62)], 1.6, color, seed=seed, reveal=r1, taper=False, jitter=0.25)
    fill(layer, poly_mask(layer.size, circle_pts(ax, ay, 4, n=12)), color)
    r2 = max(0, (reveal - 0.4)/0.6)
    for i, (txt, fnt, sz, col) in enumerate(lines):
        text(layer, (lx, ly + i*sz*1.15 - (0 if i == 0 else sz*0.1)), txt, sz, fnt, col, anchor=align, reveal=r2)
