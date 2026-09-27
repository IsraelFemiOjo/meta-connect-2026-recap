import sys, os, numpy as np
from PIL import Image
import timeline as T
yy, xx = np.mgrid[0:1080, 0:1080]
def load(d, i): return np.array(Image.open(f'fr/{d}/{i:04d}.png').convert('RGB'))
def wipe(a, b, p, direction):
    s = xx + 0.42*(yy - 540) if direction > 0 else (1080 - xx) + 0.42*(yy - 540)
    edge = -320 + p*(1080 + 640)
    out = np.where((s < edge)[..., None], b, a)
    band = np.abs(s - edge)
    out[band < 9] = (250, 247, 238)
    out[(band >= 9) & (band < 13)] = (30, 27, 44)
    return out
def frame(g):
    live = [(s, g - T.START[s]) for s in T.ORDER if T.START[s] <= g < T.START[s] + len(T.SRC[s])]
    if len(live) == 1:
        s, k = live[0]; return load(s, T.SRC[s][k])
    (s1, k1), (s2, k2) = live
    ov = T.OVERLAP[(s1, s2)]
    p = (k2 + 1)/(ov + 1); p = p*p*(3 - 2*p)
    return wipe(load(s1, T.SRC[s1][k1]), load(s2, T.SRC[s2][k2]), p, T.WIPE_DIR[(s1, s2)])
if __name__ == '__main__':
    os.makedirs('fr/ALL', exist_ok=True)
    for f in os.listdir('fr/ALL'): os.remove(f'fr/ALL/{f}')
    for g in range(T.TOTAL): Image.fromarray(frame(g)).save(f'fr/ALL/{g:04d}.png')
