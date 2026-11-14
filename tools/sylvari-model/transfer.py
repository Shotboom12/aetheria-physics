"""Claude 2026-11-13: shape transfer of Rwise's Draenei female body changes onto the Sylvari female (offline, scratch only).
Delta field = (Rwise vertex - retail vertex) for vertices matched by UV; applied to every Sylvari vertex by gaussian-weighted
nearest anchors (distance gated). Writes a patched M2 (same size, positions + normals only) and a delta report."""
import sys, struct, hashlib, json
from pathlib import Path
import numpy as np
from m2lib import verts
base = Path(r'<WORK_DIR>')
sys.path[:0] = ['<WOTLKCONV_DIR>']
from wotlkconv.m2 import parse_skin
STRENGTH = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
SIGMA, RADIUS = 0.02, 0.05
R = base / 'scratch-idealistic-physics-20261112/extracted/Idealistic Physics Models/character/Draenei/Female/draeneifemale_hd.m2'
SYL = base / 'scratch-release1-stage-20261110/race_assets/patch-ZZZZ/custom/vorkai/fnf00/faunfemale.m2'
SKIN = SYL.with_name('faunfemale00.skin')
vt = verts(open('retail/1022598.bin', 'rb').read()); vw = verts(open(R, 'rb').read())
idx = np.load('rw_to_retail_idx.npy'); ok = idx >= 0
P0 = vt['pos'][idx[ok]].astype(np.float64); D = (vw['pos'][ok] - vt['pos'][idx[ok]]).astype(np.float64)
dm = np.linalg.norm(D, axis=1); keep = dm < 0.12      # drop wrong UV matches (mirrored/overlapping islands)
P0, D = P0[keep], D[keep]
print('anchors', len(P0), 'moving', int((np.linalg.norm(D, axis=1) > 0.002).sum()))
raw = bytearray(SYL.read_bytes()); nv, ov = struct.unpack_from('<II', raw, 0x3C)
S = verts(bytes(raw)); pos = S['pos'].astype(np.float64)
# spatial hash on anchors
CELL = RADIUS
cells = {}
for i, p in enumerate(P0):
    cells.setdefault(tuple((p // CELL).astype(int)), []).append(i)
delta = np.zeros_like(pos); conf = np.zeros(len(pos))
for v, p in enumerate(pos):
    c = (p // CELL).astype(int); cand = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cand += cells.get((c[0]+dx, c[1]+dy, c[2]+dz), [])
    if not cand: continue
    q = P0[cand]; d = np.linalg.norm(q - p, axis=1); m = d < RADIUS
    if not m.any(): continue
    w = np.exp(-(d[m] / SIGMA) ** 2); sw = w.sum()
    delta[v] = (w[:, None] * D[cand][m]).sum(0) / sw
    conf[v] = min(1.0, sw / 1.5)
delta *= (conf * STRENGTH)[:, None]
mag = np.linalg.norm(delta, axis=1)
print('sylvari verts moved >0.002:', int((mag > 0.002).sum()), 'of', nv, 'max', mag.max(), 'mean(moved)', mag[mag > 0.002].mean())
# vertices with no anchor nearby
print('no anchor (conf 0):', int((conf == 0).sum()))

# --- smoothing + seam welding (v2) ---
s_ = parse_skin(SKIN.read_bytes()); lut_ = np.array(s_.vertices); tri_ = lut_[np.array(s_.indices).reshape(-1, 3)]
# group vertices at identical bind positions (UV seams) so they always move together
q = np.round(pos / 1e-4).astype(np.int64); _, grp = np.unique(q, axis=0, return_inverse=True); grp = grp.ravel()
ng = grp.max() + 1
def weld(dl):
    acc = np.zeros((ng, 3)); cnt = np.zeros(ng); np.add.at(acc, grp, dl); np.add.at(cnt, grp, 1); return (acc / cnt[:, None])[grp]
nb = [[] for _ in range(ng)]
for a, b, c in tri_:
    ga, gb, gc = grp[a], grp[b], grp[c]
    nb[ga] += [gb, gc]; nb[gb] += [ga, gc]; nb[gc] += [ga, gb]
nb = [np.unique(x) if x else np.array([], int) for x in nb]
gd = np.zeros((ng, 3)); np.add.at(gd, grp, delta); cnt0 = np.zeros(ng); np.add.at(cnt0, grp, 1); gd /= cnt0[:, None]
SMOOTH = int(sys.argv[2]) if len(sys.argv) > 2 else 8
for _ in range(SMOOTH):
    new = gd.copy()
    for g in range(ng):
        if len(nb[g]): new[g] = 0.5 * gd[g] + 0.5 * gd[nb[g]].mean(0)
    gd = new
delta = gd[grp]
mag = np.linalg.norm(delta, axis=1)
print('after smoothing: moved >0.002:', int((mag > 0.002).sum()), 'max', mag.max(), 'mean(moved)', mag[mag > 0.002].mean(), 'smooth iters', SMOOTH)
newpos = pos + delta
# normals: add area-weighted change of face normals
s = parse_skin(SKIN.read_bytes()); lut = np.array(s.vertices); ind = np.array(s.indices).reshape(-1, 3)
tri = lut[ind]
def fnorm(P):
    return np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
dn = fnorm(newpos) - fnorm(pos)
acc = np.zeros_like(pos)
for k in range(3): np.add.at(acc, tri[:, k], dn)
nrm = S['nrm'].astype(np.float64)
nrm2 = nrm + acc / (np.linalg.norm(acc, axis=1, keepdims=True).clip(1e-9) ) * np.minimum(np.linalg.norm(acc, axis=1, keepdims=True), 1.0) * 0.0
# conservative: rebuild only where moved a lot; blend face-normal change
for v in np.where(mag > 0.002)[0]:
    n = nrm[v] + acc[v] / max(1e-9, np.linalg.norm(acc[v])) * min(0.5, np.linalg.norm(acc[v]) * 50.0) if np.linalg.norm(acc[v]) > 0 else nrm[v]
    nrm2[v] = n
nrm2 /= np.linalg.norm(nrm2, axis=1, keepdims=True).clip(1e-9)
for v in range(nv):
    o = ov + v * 48
    struct.pack_into('<3f', raw, o, *newpos[v].astype(np.float32))
    struct.pack_into('<3f', raw, o + 20, *nrm2[v].astype(np.float32))
out = Path('out'); out.mkdir(exist_ok=True)
name = f'faunfemale-shape{int(STRENGTH*100):03d}.m2'
(out / name).write_bytes(bytes(raw)); np.save(out / f'delta{int(STRENGTH*100):03d}.npy', delta)
print(name, hashlib.sha256(bytes(raw)).hexdigest(), len(raw), 'bounds', newpos.min(0), newpos.max(0))
