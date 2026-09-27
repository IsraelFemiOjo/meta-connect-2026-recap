import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, math, numpy as np
sys.path.insert(0, ROOT + '/shared')
from sfx import *
from scipy.io import wavfile

sys.path.insert(0, ROOT)
import timeline as T
DUR = T.TOTAL/24
N = int(DUR*SR)
L = np.zeros(N); R = np.zeros(N)

def add(sig, t, g=1.0, pan=0.0):
    i = int(t*SR)
    if i >= N or i + len(sig) <= 0: return
    s = sig[:N - i]*g
    a = (pan + 1)*math.pi/4
    L[i:i+len(s)] += s*math.cos(a)*1.2; R[i:i+len(s)] += s*math.sin(a)*1.2
def fade(sig, fi=0.1, fo=0.2):
    n = len(sig); e = np.ones(n)
    a, b = int(fi*SR), int(fo*SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if b: e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return sig*e
def px(x): return max(-0.7, min(0.7, (x - 540)/540*0.7))

# ---- new sounds for this piece ----
def scratch(d, rate=9):
    """pencil on paper: bandpassed grain with stroke rhythm"""
    t = t_(d)
    g = bp(noise(d), 2500, 7500)*(0.45 + 0.55*np.abs(np.sin(np.pi*rate*t + rng.uniform(0, 3))))
    g += 0.3*bp(noise(d), 900, 2000)
    return norm(g*np.minimum(1, t/0.03)*np.minimum(1, (d - t)/0.05))
def rub(d, rate=7):
    """eraser rubbing"""
    t = t_(d)
    g = bp(noise(d), 500, 2400)*(0.3 + 0.7*np.abs(np.sin(np.pi*rate*t)))**1.5
    return norm(g*np.minimum(1, t/0.04)*np.minimum(1, (d - t)/0.08))
def shutter():
    out = np.zeros(int(0.2*SR))
    for tt, f, a in ((0.0, 2600, 1.0), (0.055, 1800, 0.8)):
        c = click(f)*a; i = int(tt*SR); out[i:i+len(c)] += c
        n = bp(noise(0.03), 1200, 5000)*env_ad(int(0.03*SR), 0.0005, 0.008)*0.6; out[i:i+len(n)] += n
    th = thud(200, 120, 0.06)*0.3; out[:len(th)] += th
    return norm(out)
def murmur(d, lo=250, hi=1400, syl=4.5, seed=0):
    """speech-like: formant band noise with syllable envelope"""
    r = np.random.default_rng(seed); t = t_(d)
    env = np.zeros_like(t); tt = 0.0
    while tt < d:
        ln = r.uniform(0.08, 0.22); i0 = int(tt*SR); i1 = min(len(t), int((tt + ln)*SR))
        env[i0:i1] = np.sin(np.linspace(0, np.pi, i1 - i0))*r.uniform(0.5, 1.0)
        tt += ln + r.uniform(0.02, 0.12)
    f0 = 140 + 25*np.sin(2*np.pi*0.7*t)
    buzz = np.sign(np.sin(2*np.pi*np.cumsum(f0)/SR))
    s = bp(buzz*0.6 + noise(d)*0.4, lo, hi)
    s = s*0.6 + 0.4*bp(buzz, 700, 2600)*(0.5 + 0.5*np.sin(2*np.pi*syl*t))
    return norm(s*env)
def chatter(d):
    s = np.zeros(int(d*SR))
    for k in range(6): s += murmur(d, 200, 1800, seed=10 + k)*rng.uniform(0.5, 1.0)
    tt = 0.2
    while tt < d - 0.4:
        c = metal(rng.uniform(1800, 3200), 0.3, 0.05)*rng.uniform(0.2, 0.5); i = int(tt*SR); s[i:i+len(c)] += c[:len(s) - i]
        tt += rng.uniform(0.35, 0.9)
    return norm(s)
def pop():
    d = 0.07; t = t_(d)
    return norm(np.sin(2*np.pi*np.cumsum(300 + 900*(t/d))/SR)*np.sin(np.pi*t/d)**2)
SH = 'V'
def sa(sig, t, g=1.0, pan=0.0): add(sig, T.at(SH, t), g, pan)
def cap(t, g=0.16, p=-0.3): sa(pop(), t, g, p)


def riser(d=0.6, f0=200, f1=1800):
    """a short tension riser: filtered noise and a sine sweeping up"""
    t = t_(d); x = t/d
    n = np.zeros_like(t); seg_ = 480; nz = noise(d)
    for i in range(0, len(t), seg_):
        fc = f0*(f1/f0)**(i/len(t)); n[i:i+seg_] = bp(nz[max(0, i-4096):i+seg_], fc*0.6, min(fc*1.6, 20000))[-len(nz[i:i+seg_]):]
    s = n*x**1.5 + 0.35*chirp(f0*0.5, f1*0.5, d, 1.5)*x**2
    return norm(s)
def boom():
    d = 1.6; t = t_(d); out = np.zeros_like(t)
    sub = np.sin(2*np.pi*np.cumsum(38 + 60*np.exp(-t/0.12))/SR)*np.exp(-t/0.45)
    out += sub*1.0
    th = thud(90, 35, 0.4); out[:len(th)] += th*0.8
    cr = crack(); out[:len(cr)] += cr*0.6
    rb = lp(noise(d), 180)*np.exp(-t/0.5); out += rb*0.6
    return norm(out)
def debris(d=0.9):
    s = np.zeros(int(d*SR)); tt = 0.05
    while tt < d - 0.1:
        c = metal(rng.uniform(900, 3200), 0.2, 0.03)*rng.uniform(0.2, 0.6); i = int(tt*SR); s[i:i+len(c)] += c[:len(s) - i]
        tt += rng.exponential(0.07)
    return norm(s)
def snap():
    out = np.zeros(int(0.3*SR))
    a = kachunk(); out[:len(a)] += a[:len(out)]*0.8
    c = click(3000); out[:len(c)] += c*0.6
    return norm(out)

# ================= V: VR Glasses, the exploded view =================
SH = 'V'
sa(scratch(0.3), 0.0, 0.08, 0.0); sa(scratch(0.75, 12), 0.2, 0.13, 0.1)
sa(whoosh(0.6, 300, 1600), 0.95, 0.12, 0.2)
cap(0.35)
sa(plink(1568), 0.9, 0.1, 0.0)
sa(riser(0.5, 180, 2400), 1.3, 0.26)                       # everything pulls in...
sa(boom(), 1.8, 0.9); sa(fwoomp(0.8, 150, 3000), 1.8, 0.35); sa(debris(0.9), 1.85, 0.12, 0.2)
for k, p in enumerate((-0.6, -0.2, 0.3, 0.6)): sa(whoosh(0.45, 500 + 200*k, 2800), 1.82 + 0.04*k, 0.16, p)
cap(1.85)
sa(patter(), 2.55, 0.2, 0.55)
CALL = [(2.6, -0.5), (3.3, -0.5), (4.0, 0.0), (4.7, 0.0), (5.4, 0.5), (6.1, 0.5)]
for t0, p in CALL:
    sa(scratch(0.2, 18), t0 - 0.12, 0.10, p); sa(click(2600), t0, 0.28, p); sa(pop(), t0 + 0.02, 0.12, p)
sa(zip_(0.12, up=False), 7.3, 0.14)
sa(riser(0.45, 300, 2600), 7.45, 0.2)
sa(snap(), 7.88, 0.6); sa(thud(160, 70, 0.15), 7.88, 0.3)
sa(patter(), 7.5, 0.14, 0.4); sa(patter(), 8.3, 0.18, 0.0)
cap(8.45)
sa(zip_(0.12, up=False), 9.05, 0.1)

# ================= A: Gen 3 =================
SH = 'A'
sa(thud(), 2.0, 0.45); sa(bwong(98, 1.0), 2.0, 0.18); sa(shimmer(0.7), 2.02, 0.10)
cap(2.25); cap(2.5, 0.12)
sa(boing(), 2.55, 0.16, 0.0); sa(plink(1568), 2.7, 0.12)
cap(4.45); cap(4.7, 0.12)
sa(boing(), 5.6, 0.14, 0.2); sa(patter(), 6.72, 0.2, 0.3)
sa(whoosh(0.65, 250, 2200), 6.8, 0.24, 0.2)
sa(shutter(), 7.5, 0.55, 0.25); sa(fwoomp(0.35, 500, 3000), 7.5, 0.12, 0.25)
cap(7.85); cap(8.1, 0.12)
sa(whoosh(0.7, 2000, 300), 9.2, 0.2, -0.1)
for k, tt in enumerate((10.0, 10.35, 10.7)): sa(zip_(), tt, 0.2, (0.5, -0.5, 0.3)[k])
sa(rub(0.9), 10.6, 0.14, 0.4)
sa(ticks(1.0, 6, 16, 2400), 10.8, 0.12, -0.4); sa(chime(1318.5, 0.6, 0.5), 11.8, 0.08, -0.4)
sa(click(2200), 11.45, 0.4, 0.3); sa(chime(1568, 1.0), 11.5, 0.14, 0.3); sa(shimmer(0.5), 11.52, 0.08, 0.3)
for tt in (12.6, 12.65, 12.7): sa(zip_(0.1, up=False), tt, 0.1)
sa(boing(), 13.3, 0.14, 0.2); sa(patter(), 14.5, 0.18, 0.0)

# ================= B: Audio =================
SH = 'B'
sa(rub(1.4, 6), 0.05, 0.22, 0.0)
cap(1.55); cap(1.8, 0.12)
sa(whoosh(0.65, 250, 2200), 2.6, 0.22, 0.2)
sa(scratch(0.4), 3.3, 0.12, 0.25)
sa(zip_(0.1, False), 3.7, 0.2, 0.25); sa(zip_(0.1, False), 3.8, 0.2, 0.3)
cap(3.95); cap(4.2, 0.12)
sa(whoosh(0.7, 2000, 300), 5.0, 0.2, -0.1)
for k, f in enumerate((1318.5, 1568, 1760, 2093)): sa(plink(f), 6.0 + k*0.4, 0.07, 0.4 - 0.1*k)
for k, tt in enumerate((6.8, 7.2, 7.6)): sa(zip_(), tt, 0.2, (0.5, -0.5, 0.3)[k])
sa(ticks(0.8, 6, 16, 2400), 7.6, 0.12, -0.4)
for k in range(4): sa(blip(880 + 110*k), 7.9 + k*0.25, 0.1, 0.3)
for tt in (10.2, 10.25, 10.3): sa(zip_(0.1, up=False), tt, 0.1)

# B -> C panel wipe
add(whoosh(0.6, 400, 2400), T.START['C']/24 - 0.05, 0.22, -0.3); add(cardboard(), T.START['C']/24 + 0.45, 0.3)

# ================= C: Display =================
SH = 'C'
cap(0.3); cap(0.55, 0.12)
sa(scratch(0.4), 1.0, 0.1, -0.3); sa(beep(1318.5, 0.12), 1.4, 0.1, -0.3); cap(1.7)
sa(boing(), 2.55, 0.14)
sa(fade(whoosh(1.2, 200, 3000), 0.1, 0.2), 2.8, 0.3, -0.2)
sa(fwoomp(0.6, 300, 3000), 3.8, 0.24); sa(shimmer(0.8), 3.85, 0.12)
sa(fade(lp(noise(6.45), 300), 0.5, 0.6), 4.05, 0.05, 0.0)    # night air
for tt in (4.2, 6.3, 8.3): sa(beep(1318.5, 0.08), tt, 0.08, 0.4); sa(beep(1760, 0.08), tt + 0.09, 0.07, 0.4)
sa(zip_(0.3), 4.5, 0.12, 0.4)
cap(4.25); cap(4.6, 0.12); cap(6.55, 0.12); cap(8.55, 0.12); cap(8.8, 0.1)
for k in range(3): sa(click(2600), 6.6 + k*0.18, 0.12, 0.4)
sa(shimmer(0.7), 8.3, 0.1, 0.4)
sa(fade(murmur(1.5 + 0.8, seed=3), 0.3, 0.3), 9.0, 0.12, 0.2)    # the caller's voice, carries over the cut

# ================= D: Hearing Enhancement =================
SH = 'D'
sa(fade(chatter(3.3), 0.5, 0.4), 0.0, 0.20, 0.35)
sa(fade(chatter(4.0), 0.3, 1.0), 3.0, 0.035, 0.35)     # the room is still there, just pushed back
cap(1.0); sa(beep(988, 0.08), 1.9, 0.08); sa(beep(1318.5, 0.1), 1.99, 0.08)
sa(whoosh(0.65, 250, 2200), 2.1, 0.22, -0.2)
sa(hiss(0.6), 3.0, 0.14, 0.2); sa(chime(1568, 1.2), 3.0, 0.14); sa(chime(2093, 1.2), 3.05, 0.08)
sa(fade(murmur(2.4, 300, 2200, seed=4), 0.2, 0.3), 3.0, 0.16, -0.3)
cap(3.1); cap(3.4, 0.12); cap(3.7, 0.12)
sa(plink(2093), 5.2, 0.14); sa(boing(), 5.25, 0.12)
sa(fade(zip_(1.4), 0.05, 0.3), 5.5, 0.14, 0.4)

# ================= E: Muse =================
SH = 'E'
sa(patter(), 0.55, 0.18, -0.4)
sa(whoosh(0.35, 300, 1500), 0.1, 0.14); sa(cardboard(), 0.45, 0.25)
cap(0.35); cap(0.6, 0.12)
for k, t0 in enumerate((1.3, 2.0, 2.7)):
    sa(scratch(0.3, 14), t0 - 0.35, 0.10, 0.1)
    sa(scratch(0.18, 20), t0 + 0.05, 0.16, -0.2); sa(plink((1046.5, 1318.5, 1568)[k]), t0 + 0.12, 0.14, -0.2)
cap(3.25)
sa(whoosh(0.45, 300, 2600), 3.98, 0.3)
sa(blip(1046.5), 4.7, 0.2, 0.2); sa(shimmer(0.7), 4.72, 0.12, 0.2)
cap(4.85); cap(5.1, 0.12); cap(5.35, 0.12)
sa(boing(), 5.2, 0.14, 0.5); sa(patter(), 5.9, 0.2, 0.3)

# ================= F: end card =================
SH = 'F'
sa(whoosh(0.5, 400, 2400), -0.2, 0.2)
for k in range(5): sa(thud(120, 55, 0.2), 0.15*k, 0.32, (-0.5, 0.0, 0.5, -0.3, 0.3)[k]); sa(cardboard(), 0.15*k, 0.28, (-0.5, 0.0, 0.5, -0.3, 0.3)[k])
sa(chime(1046.5, 1.6), 0.8, 0.12); sa(chime(1568, 1.6), 0.83, 0.1)
cap(1.15)
sfxL, sfxR = L.copy(), R.copy()

_sr, _m = wavfile.read(ROOT + '/music.wav')
_m = _m.astype(np.float64)/32767
MUS_L = np.zeros(N); MUS_R = np.zeros(N); n_ = min(N, len(_m))
MUS_L[:n_] = _m[:n_, 0]; MUS_R[:n_] = _m[:n_, 1]
M = (MUS_L + MUS_R)/2
music_rms = np.sqrt(np.mean(M**2))
mg = (10**(-21/20))/max(music_rms, 1e-9)
L = sfxL + MUS_L*mg; R = sfxR + MUS_R*mg
def soft(x, th=0.6):
    y = np.copy(x); m = np.abs(x) > th
    y[m] = np.sign(x[m])*(th + (1 - th)*np.tanh((np.abs(x[m]) - th)/(1 - th)))
    return y
L, R = soft(L), soft(R)
peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
target = 10**(-1.5/20); L *= target/peak; R *= target/peak
fo = int(0.5*SR); L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
wavfile.write(ROOT + '/mix.wav', SR, (np.stack([L, R], 1)*32767).astype(np.int16))
print('dur', DUR, T.START)
