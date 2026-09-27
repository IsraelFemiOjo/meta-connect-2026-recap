"""One place that says which source frames of each shot are used, and where each shot sits in the cut."""
FPS = 24
def keep(n, start=0, drops=()):
    fr = []
    for f in range(start, n):
        t = f/FPS
        if any(a <= t < b for a, b in drops): continue
        fr.append(f)
    return fr

SRC = {
    'V': keep(228),
    'A': keep(350, start=48, drops=[(11.9, 12.4)]),
    'B': keep(260, drops=[(9.2, 9.7)]),
    'C': keep(252, drops=[(5.5, 5.8), (7.5, 7.8)]),
    'D': keep(168, drops=[(4.3, 4.7)]),
    'E': keep(197),
    'F': keep(84),
}
ORDER = ['V', 'A', 'B', 'C', 'D', 'E', 'F']
OVERLAP = {('B', 'C'): 14, ('E', 'F'): 10}     # comic panel wipes
WIPE_DIR = {('B', 'C'): 1, ('E', 'F'): -1}
START = {}
g = 0
for i, s in enumerate(ORDER):
    if i: g -= OVERLAP.get((ORDER[i - 1], s), 0)
    START[s] = g; g += len(SRC[s])
TOTAL = g

def at(shot, t):
    src = SRC[shot]; f = t*FPS
    if f <= src[0]: return (START[shot] + (f - src[0]))/FPS
    # position = index of the last kept frame <= f, plus the fraction into it
    lo = 0
    for i, x in enumerate(src):
        if x <= f: lo = i
        else: break
    frac = min(1.0, f - src[lo])
    return (START[shot] + lo + frac)/FPS
