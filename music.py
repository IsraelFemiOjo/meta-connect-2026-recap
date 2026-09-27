"""Original launch track: 122 bpm electronic groove, F#m D A E, drop on the VR explosion."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__))))
import sys, math, numpy as np
sys.path.insert(0, ROOT)
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
import timeline as T

SR = 48000
DUR = T.TOTAL/24 + 2.5
N = int(DUR*SR)
rng = np.random.default_rng(11)
BPM = 122; BEAT = 60/BPM; BAR = 4*BEAT; S16 = BEAT/4
DROP = T.at('V', 1.8)
G0 = DROP - 2*BAR                        # grid origin: the drop lands on a downbeat
def grid(bar, six=0): return G0 + bar*BAR + six*S16

def lp(x, f, o=2): return sosfilt(butter(o, min(f, SR*0.45), 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def mtof(m): return 440*2**((m - 69)/12)
def tt(n): return np.arange(n)/SR

def saw(f, n, phase=0.0):
    """polyBLEP saw"""
    dt = f/SR; p = (phase + dt*np.arange(n)) % 1.0
    y = 2*p - 1
    m1 = p < dt; x = p[m1]/dt; y[m1] -= x + x - x*x - 1
    m2 = p > 1 - dt; x = (p[m2] - 1)/dt; y[m2] -= x*x + x + x + 1
    return y

# ---------------- instruments ----------------
def kick():
    n = int(0.45*SR); t = tt(n)
    f = 48 + 110*np.exp(-t/0.035)
    s = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.28)
    s[:int(0.004*SR)] += hp(rng.standard_normal(int(0.004*SR)), 2000)*0.5
    return np.tanh(1.8*s)
def clap():
    n = int(0.35*SR); t = tt(n); s = np.zeros(n)
    for k, d in enumerate((0.0, 0.011, 0.022)):
        i = int(d*SR); b = bp(rng.standard_normal(int(0.012*SR)), 900, 5000)*np.exp(-np.arange(int(0.012*SR))/SR/0.004)
        s[i:i+len(b)] += b*(0.8 if k < 2 else 1.0)
    tail = bp(rng.standard_normal(n), 1000, 6000)*np.exp(-t/0.12)
    body = np.sin(2*np.pi*190*t)*np.exp(-t/0.05)*0.5
    return s + tail*0.7 + body
def hat(open_=False):
    d = 0.22 if open_ else 0.045; n = int(d*SR); t = tt(n)
    return hp(rng.standard_normal(n), 7000, 4)*np.exp(-t/(0.07 if open_ else 0.012))
def crash():
    n = int(2.2*SR); t = tt(n)
    s = hp(rng.standard_normal(n), 4000)*np.exp(-t/0.8)
    for r in (1, 1.41, 1.83, 2.37): s += 0.05*np.sin(2*np.pi*3100*r*t)*np.exp(-t/0.5)
    return s
def bass(m, d):
    n = int(d*SR); t = tt(n); f = mtof(m)
    s = saw(f, n)*0.7 + np.sin(2*np.pi*f*t)*0.8
    s = lp(s, 900)
    env = np.minimum(1, t/0.004)*np.exp(-t/0.35)*np.minimum(1, (d - t)/0.01)
    return np.tanh(1.5*s*env)
def pad(ms, d, bright=1.0):
    n = int(d*SR); t = tt(n); L = np.zeros(n); R = np.zeros(n)
    for m in ms:
        f = mtof(m)
        for k, det in enumerate((-0.14, -0.06, 0.0, 0.07, 0.15)):
            o = saw(f*2**(det/12), n, rng.random())
            if k % 2: L += o
            else: R += o
            if k == 2: L += o*0.5; R += o*0.5
    cut = 1400*bright + 400
    L = lp(L, cut); R = lp(R, cut)
    env = np.minimum(1, t/0.03)*np.minimum(1, (d - t)/0.05)
    g = 1/(len(ms)*3)
    return L*env*g, R*env*g
def pluck(m, d=0.3):
    n = int(d*SR); t = tt(n); f = mtof(m)
    s = saw(f, n)*0.6 + saw(f*2.003, n)*0.25 + np.sin(2*np.pi*f*t)*0.4
    # filter sweep down, done in two bands for speed
    hi = lp(s, 4500)*np.exp(-t/0.05); lo = lp(s, 1200)
    return (hi*0.6 + lo*0.5)*np.exp(-t/0.16)*np.minimum(1, t/0.002)

# ---------------- buses ----------------
DR = np.zeros(N); BS = np.zeros(N); PL = np.zeros(N); PR = np.zeros(N); AL = np.zeros(N); AR = np.zeros(N); FX = np.zeros(N)
def put(bus, sig, t, g=1.0):
    i = int(t*SR)
    if i < 0: sig = sig[-i:]; i = 0
    if i >= N: return
    s = sig[:N - i]; bus[i:i+len(s)] += s*g

PROG = [('F#m', 42, [57, 61, 66]), ('D', 38, [57, 62, 66]), ('A', 45, [57, 61, 64]), ('E', 40, [56, 59, 64])]
ARP = [0, 1, 2, 1, 2, 0, 1, 2]
KICKS = [0, 7, 9]            # "dum . . . ka . . dum . dum . . ka . . ."
SNARES = [4, 12]
BASS16 = [0, 3, 6, 8, 10, 11, 14]

C_POV0, C_POV1 = T.at('C', 4.05), T.at('C', 10.5)
D0, D_ON = T.at('D', 0.0), T.at('D', 3.0)
IMPL0, IMPL1 = T.at('V', 7.35), T.at('V', 7.88)
_tgt = T.TOTAL/24 - 1.0
F_HIT = min((G0 + k*BEAT*2 for k in range(400)), key=lambda x: abs(x - _tgt))   # a half bar grid point near the end
END = F_HIT
def section(t):
    if t < DROP: return 'intro'
    if IMPL0 <= t < IMPL1: return 'break'
    if C_POV0 <= t < C_POV1: return 'night'
    if t >= END: return 'end'
    return 'full'

kicks_at = []
nb = int((END - G0)/BAR) + 1
for b in range(nb):
    name, root, ch = PROG[b % 4]
    tb = grid(b)
    sec = section(tb + 0.01)
    # chords: every bar
    if tb < END:
        bright = 0.35 + 0.65*min(1, max(0, (tb - G0)/(DROP - G0))) if sec == 'intro' else (0.55 if sec == 'night' else 1.0)
        l, r = pad(ch, BAR + 0.02, bright)
        put(PL, l, tb, 1.0); put(PR, r, tb, 1.0)
    for s16 in range(16):
        t = grid(b, s16)
        if t >= END: break
        sec = section(t + 1e-3)
        if sec in ('full',):
            if s16 in KICKS: put(DR, kick(), t, 1.0); kicks_at.append(t)
            if s16 in SNARES: put(DR, clap(), t, 0.55)
            if s16 % 2 == 0: put(DR, hat(), t, 0.16 if s16 % 4 else 0.12)
            else: put(DR, hat(), t, 0.09)
            if s16 in (6, 14): put(DR, hat(True), t, 0.09)
            if s16 in BASS16: put(BS, bass(root + (12 if s16 in (6, 14) else 0), S16*1.8), t, 0.55)
        elif sec == 'night':
            if s16 % 2 == 0: put(DR, hat(), t, 0.10)
            if s16 in (0, 8): put(DR, kick(), t, 0.45); kicks_at.append(t)
            if s16 in (0, 10): put(BS, bass(root, BEAT*1.6), t, 0.4)
        elif sec == 'intro':
            if t >= DROP - BAR and s16 % 2 == 0: put(DR, hat(), t, 0.05 + 0.1*(t - (DROP - BAR))/BAR)
        # plucked arpeggio on top
        if sec in ('full', 'night') and not (sec == 'full' and b % 8 in (6, 7) and s16 >= 12):
            note = ch[ARP[s16 % 8]] + 12 + (12 if (b % 4 == 2 and s16 % 8 == 4) else 0)
            g = 0.22 if sec == 'full' else 0.28
            p = pluck(note, 0.35)
            put(AL, p, t, g*(0.9 if s16 % 2 else 1.0)); put(AR, p, t, g*(1.0 if s16 % 2 else 0.9))
    # small fill before some bars: 16th claps
    if section(grid(b, 12)) == 'full' and b % 8 == 7:
        for s16 in (13, 14, 15): put(DR, clap(), grid(b, s16), 0.25 + 0.08*(s16 - 13))

# drop, section and ending hits
put(DR, crash(), DROP, 0.35); put(DR, kick(), DROP, 1.0)
put(DR, crash(), IMPL1, 0.3); put(DR, kick(), IMPL1, 0.9); kicks_at.append(IMPL1)
put(DR, crash(), C_POV1, 0.28)
put(DR, crash(), D_ON, 0.3)
# the final chord rings out under the end card
name, root, ch = PROG[0]
l, r = pad(ch + [69, 73], 3.4, 1.0); fade = np.linspace(1, 0, len(l))**0.7
put(PL, l*fade, F_HIT, 1.1); put(PR, r*fade, F_HIT, 1.1)
put(BS, bass(root, 2.0), F_HIT, 0.7); put(DR, kick(), F_HIT, 1.0); put(DR, crash(), F_HIT, 0.4)
for k, m in enumerate(ch + [ch[0] + 12, ch[1] + 12]):
    p = pluck(m + 12, 0.8); put(AL, p, F_HIT + 0.06*k, 0.2); put(AR, p, F_HIT + 0.06*k + 0.02, 0.2)

# ---------------- mix ----------------
t = np.arange(N)/SR
# sidechain pump from every kick on the chords and bass
duck = np.ones(N)
for k in kicks_at:
    i0 = int(k*SR); n = int(0.3*SR)
    if i0 >= N: continue
    e = 1 - 0.65*np.exp(-np.arange(min(n, N - i0))/SR/0.09)
    duck[i0:i0+len(e)] = np.minimum(duck[i0:i0+len(e)], e)
PL *= duck; PR *= duck; BS *= (0.4 + 0.6*duck)
# delay on the arp (dotted eighth, ping pong)
dly = int(S16*3*SR)
AL2 = AL.copy(); AR2 = AR.copy()
for k in range(1, 4):
    g = 0.3**k; s = lp((AL if k % 2 else AR)[:-dly*k], 2800)*g
    (AR2 if k % 2 else AL2)[dly*k:] += s
AL, AR = AL2, AR2
# a short plate style reverb on chords and arp
ir_n = int(1.1*SR); ir_t = tt(ir_n)
irL = rng.standard_normal(ir_n)*np.exp(-ir_t/0.35); irR = rng.standard_normal(ir_n)*np.exp(-ir_t/0.35)
irL = lp(irL, 5000)/np.sqrt(np.sum(irL**2)); irR = lp(irR, 5000)/np.sqrt(np.sum(irR**2))
sendL = PL*0.25 + AL*0.35; sendR = PR*0.25 + AR*0.35
revL = fftconvolve(sendL, irL)[:N]*0.35; revR = fftconvolve(sendR, irR)[:N]*0.35
DR = np.tanh(DR*1.1)/1.1
L = DR*0.9 + BS*0.8 + PL*0.55 + AL*0.7 + revL
R = DR*0.9 + BS*0.8 + PR*0.55 + AR*0.7 + revR
L = hp(L, 30); R = hp(R, 30)
# café: behind glass until Hearing Enhancement switches on
w = np.clip((t - D0)/0.25, 0, 1)*np.clip((D_ON - t)/0.2, 0, 1)
L = L*(1 - w) + lp(L, 450, 2)*w*0.85; R = R*(1 - w) + lp(R, 450, 2)*w*0.85
# intro: the whole track sits behind a filter that opens into the drop
wi = np.clip((DROP - t)/(DROP + 0.01), 0, 1)
L = L*(1 - wi) + lp(L, 700, 2)*wi*1.2; R = R*(1 - wi) + lp(R, 700, 2)*wi*1.2
# fade in / out
fi = int(0.3*SR); L[:fi] *= np.linspace(0, 1, fi); R[:fi] *= np.linspace(0, 1, fi)
end_i = int((T.TOTAL/24)*SR)
L = L[:end_i]; R = R[:end_i]
fo = int(0.5*SR); L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
pk = max(np.abs(L).max(), np.abs(R).max()); L /= pk; R /= pk
wavfile.write(ROOT + '/music.wav', SR, (np.stack([L, R], 1)*0.9*32767).astype(np.int16))
print('music', len(L)/SR, 'drop at', DROP, 'kicks', len(kicks_at))
