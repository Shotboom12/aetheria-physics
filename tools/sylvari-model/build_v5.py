"""Claude 2026-11-13: Sylvari female v5 = shape model + Draenei boot shells (unchanged from v2-v4) + a retail cape bone chain (5 bones, keys 36-40)
+ the RETAIL cloak shells 1502-1510 (from the retail Draenei female 1022598), skinned to that chain. Cloaks are rigid until the client spring physics
drives the cape bones (flag 0x80 procedural transform).
usage: python build_v5.py OUTSET COUT OUTDIR"""
import sys, struct, hashlib, os
from pathlib import Path
import numpy as np
T = Path('<WORK_DIR>')
sys.path[:0] = ['<WOTLKCONV_DIR>']
from wotlkconv.m2 import parse_m2, parse_skin
from wotlkconv.m2.skin import write_skin
from m2lib import verts

u16 = lambda x, i: struct.unpack_from('<H', x, i)[0]
BOOTS = [502, 503, 504, 505]
CLOAKS = list(range(1502, 1511))
CAPE = [29, 39, 48, 56, 108]          # retail skeleton bone ids (keys 36..40)
OUTSET = float(sys.argv[1]) if len(sys.argv) > 1 else 0.010
COUT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.012
OUTDIR = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('out/v5')
base_raw = open('out/faunfemale-shape100.m2', 'rb').read()
sk_raw = open(T / 'scratch-release1-stage-20261110/race_assets/patch-ZZZZ/custom/vorkai/fnf00/faunfemale00.skin', 'rb').read()
sm = parse_m2(base_raw); ss = parse_skin(sk_raw); sv = verts(base_raw)
dm = parse_m2(open('legacy/DraeneiFemale.M2', 'rb').read()); ds = parse_skin(open('legacy/DraeneiFemale00.skin', 'rb').read()); dv = verts(open('legacy/DraeneiFemale.M2', 'rb').read())
rraw = open('retail/1022598.bin', 'rb').read()
rmd = rraw[8:8 + struct.unpack_from('<I', rraw, 4)[0]]
rs = parse_skin(open('retail/1022770.skin', 'rb').read()); rv = verts(rmd)
skel = np.load('retail_skel_bones.npy')   # rows: key, parent, px, py, pz
H = lambda o: struct.unpack_from('<II', base_raw, o)
assert H(0x3C)[0] == 29889 and H(0x50)[0] == 9 and H(0x80)[0] == 10 and H(0x78)[0] == 404 and H(0x68)[0] == 16 and H(0x2C)[0] == 185

spiv = np.array([b['pivot'] for b in sm.bones]); dpiv = np.array([b['pivot'] for b in dm.bones]); rpiv = skel[:, 2:5]
NB0 = len(spiv)
# new cape bones: index NB0 + k, pivot from retail, parent = previous (first: Sylvari chest 151 = retail chest 19, pivot checked below)
assert np.linalg.norm(spiv[151] - rpiv[19]) < 0.005
newpiv = [rpiv[b] for b in CAPE]
allpiv = np.vstack([spiv, np.array(newpiv)])
cape_new = {b: NB0 + k for k, b in enumerate(CAPE)}
TAIL = {7, 15, 21}


def map_bone(pivot_set, wb):
    p = pivot_set[wb]
    cand = np.arange(len(spiv))     # only original bones for non-cape bones
    cand = np.array([c for c in cand if c not in TAIL])
    if abs(p[1]) > 0.02:
        cand = cand[np.sign(spiv[cand, 1]) == np.sign(p[1])]
    d = np.linalg.norm(spiv[cand] - p, axis=1)
    j = d.argmin()
    return int(cand[j]), float(d[j])


S = sv['pos'].astype(np.float64); N = sv['nrm'].astype(np.float64)
leg = np.where(S[:, 2] < 0.95)[0]
Sl, Nl = S[leg], N[leg]
g0 = []
for sec_ in ss.submeshes:
    if u16(sec_, 0) == 0:
        g0 += list(ss.vertices[u16(sec_, 4):u16(sec_, 4) + u16(sec_, 6)])
g0 = np.unique(g0)
Sb, Nb = S[g0], N[g0]
sections = []
PUSH_OFF = 0
CP_OFF = 0
report = {}
for gid in BOOTS + CLOAKS:
    boot = gid in BOOTS
    if boot:
        skn, vv, piv = ds, dv, dpiv
    else:
        skn, vv, piv = rs, rv, rpiv
    sec = next(x for x in skn.submeshes if u16(x, 0) == gid)
    v0, vc, i0, ic = u16(sec, 4), u16(sec, 6), u16(sec, 8) + (u16(sec, 2) << 16), u16(sec, 10)
    lookup = skn.vertices[v0:v0 + vc]
    tri = np.array(skn.indices[i0:i0 + ic]).reshape(-1, 3) - v0
    P = vv['pos'][lookup].astype(np.float64).copy()
    Nn = vv['nrm'][lookup].astype(np.float64)
    RefS, RefN, out_ = (Sl, Nl, OUTSET) if boot else (Sb, Nb, COUT)
    for a in range(len(P)):
        d = np.linalg.norm(RefS - P[a], axis=1)
        j = d.argmin()
        sgn = (P[a] - RefS[j]) @ RefN[j]
        if sgn < out_ and d[j] < 0.08:
            P[a] += RefN[j] * (out_ - sgn)
    if boot:
        if os.path.exists('pushes.npy'):
            P = P + np.load('pushes.npy')[PUSH_OFF:PUSH_OFF + len(P)]
        PUSH_OFF += len(P)
    if (not boot) and os.environ.get('CLOAK_PUSHES') and os.path.exists(os.environ['CLOAK_PUSHES']):
        P = P + np.load(os.environ['CLOAK_PUSHES'])[CP_OFF:CP_OFF + len(P)]
        CP_OFF += len(P)
    w = vv['w'][lookup].copy()
    bi = vv['bi'][lookup]
    bmap = {}
    newbi = np.zeros_like(bi)
    for a in range(len(P)):
        if boot:
            d = np.linalg.norm(Sl - P[a], axis=1)
            j = d.argmin()
            if d[j] < 0.15:
                w[a] = sv['w'][leg[j]]
                newbi[a] = sv['bi'][leg[j]]
                continue
        for q in range(4):
            if w[a][q] == 0:
                continue
            wb = int(bi[a][q])
            if wb not in bmap:
                if (not boot) and wb in cape_new:
                    bmap[wb] = (cape_new[wb], 0.0)
                else:
                    bmap[wb] = map_bone(piv, wb)
            newbi[a][q] = bmap[wb][0]
    if not boot:
        report[gid] = {wb: (m[0], round(m[1] * 1000, 1)) for wb, m in bmap.items()}
    sections.append(dict(gid=gid, tex=(1 if boot else 2), P=P, N=Nn, w=w, bi=newbi, uv=vv['uv1'][lookup], tri=tri))
for g, r in report.items():
    print('cloak', g, 'retail bone -> sylvari bone (pivot error mm):', r)

vdt = np.dtype([('pos', '<f4', 3), ('w', 'u1', 4), ('bi', 'u1', 4), ('nrm', '<f4', 3), ('uv1', '<f4', 2), ('uv2', '<f4', 2)])
nv0 = len(sv); lk0 = len(ss.vertices); idx0 = len(ss.indices); bc0 = len(sm.bone_combos)
new_vertices = []; add_lookup = []; add_indices = []; add_bones = []; add_secs = []; add_batches = []; add_bone_combos = []
tex1 = len(sm.textures); tex2 = tex1 + 1
combo1 = len(sm.texture_combos); combo2 = combo1 + 1
tmpl = ss.batches[0]
nvtotal = 0
for k, sec in enumerate(sections):
    n = len(sec['P'])
    arr = np.zeros(n, vdt)
    arr['pos'] = sec['P'].astype(np.float32); arr['nrm'] = sec['N'].astype(np.float32)
    arr['w'] = sec['w']; arr['bi'] = sec['bi']; arr['uv1'] = sec['uv']; arr['uv2'] = sec['uv']
    used = sorted({int(sec['bi'][a][j]) for a in range(n) for j in range(4) if sec['w'][a][j]})
    assert len(used) <= 75, (sec['gid'], len(used))
    local = {b: i for i, b in enumerate(used)}
    bstart = bc0 + len(add_bone_combos)
    add_bone_combos += used
    for a in range(n):
        add_bones.append(bytes(local[int(sec['bi'][a][j])] if sec['w'][a][j] else 0 for j in range(4)))
    gv0 = nv0 + nvtotal
    nvtotal += n
    new_vertices.append(arr)
    vstart = lk0 + len(add_lookup)
    add_lookup += [gv0 + a for a in range(n)]
    istart = idx0 + len(add_indices)
    add_indices += [int(vstart + t) for t in sec['tri'].reshape(-1)]
    cen = sec['P'].mean(0)
    rad = float(np.linalg.norm(sec['P'] - cen, axis=1).max())
    assert (istart & 0xFFFF) + len(sec['tri']) * 3 < 65536 * 2
    blob = struct.pack('<10H', sec['gid'], istart >> 16, vstart, n, istart & 0xFFFF, len(sec['tri']) * 3, len(used), bstart, 4, used[0]) + struct.pack('<3f3ff', *cen, *cen, rad)
    assert len(blob) == 48
    add_secs.append(blob)
    secidx = len(ss.submeshes) + k
    b = list(struct.unpack('<BB' + 'H' * 11, tmpl))
    b[2] = 0; b[3] = secidx; b[4] = secidx; b[5] = 65535; b[6] = 0; b[7] = 0; b[8] = 1
    b[9] = combo2 if sec['tex'] == 2 else combo1
    add_batches.append(struct.pack('<BB' + 'H' * 11, *b))
nvb = np.concatenate(new_vertices)
print('new vertices', len(nvb), 'indices', len(add_indices), 'bone_combos +', len(add_bone_combos), 'skin lookup', lk0 + len(add_lookup), 'index total', idx0 + len(add_indices))
assert lk0 + len(add_lookup) < 65536 and nv0 + len(nvb) < 65536

raw = bytearray(base_raw)


def align():
    while len(raw) % 4:
        raw.append(0)


def reloc(count_off, extra, item_size, new_count):
    cnt, ofs = struct.unpack_from('<II', raw, count_off)
    old = bytes(raw[ofs:ofs + cnt * item_size])
    align()
    pos = len(raw)
    raw.extend(old + extra)
    struct.pack_into('<II', raw, count_off, new_count, pos)


# cape bones: key 36..40, flags 0, no tracks (bone matrix = parent's until the client drives it), parent chain
def bone_rec(key, parent, pivot):
    empty = struct.pack('<HhIIII', 0, -1, 0, 0, 0, 0)
    return struct.pack('<iIhHI', key, 0, parent, 0, 0) + empty * 3 + struct.pack('<3f', *[float(x) for x in pivot])


bones_extra = b''
for k, rb in enumerate(CAPE):
    parent = 151 if k == 0 else NB0 + k - 1
    bones_extra += bone_rec(36 + k, parent, rpiv[rb])
assert len(bones_extra) == 88 * len(CAPE)
reloc(0x2C, bones_extra, 88, NB0 + len(CAPE))
reloc(0x3C, nvb.tobytes(), 48, nv0 + len(nvb))
reloc(0x50, struct.pack('<IIII', 1, 0, 0, 0) + struct.pack('<IIII', 2, 0, 0, 0), 16, len(sm.textures) + 2)
reloc(0x80, struct.pack('<HH', tex1, tex2), 2, len(sm.texture_combos) + 2)
reloc(0x78, struct.pack('<%dH' % len(add_bone_combos), *add_bone_combos), 2, bc0 + len(add_bone_combos))
_, rofs = struct.unpack_from('<II', raw, 0x68)
assert struct.unpack_from('<H', raw, rofs + 2)[0] == 65535 and struct.unpack_from('<H', raw, rofs + 4)[0] == 65535
struct.pack_into('<H', raw, rofs + 2, tex1)
struct.pack_into('<H', raw, rofs + 4, tex2)

ss.vertices = list(ss.vertices) + add_lookup
ss.indices = list(ss.indices) + add_indices
ss.bones = ss.bones + b''.join(add_bones)
ss.submeshes = list(ss.submeshes) + add_secs
ss.batches = list(ss.batches) + add_batches
skin_out = write_skin(ss)
OUTDIR.mkdir(parents=True, exist_ok=True)
(OUTDIR / 'faunfemale.m2').write_bytes(bytes(raw))
(OUTDIR / 'faunfemale00.skin').write_bytes(skin_out)

m2 = parse_m2(bytes(raw)); s2 = parse_skin(skin_out)
print('reparse: bones', len(m2.bones), [(i, b['key_bone_id'], b['parent_bone']) for i, b in enumerate(m2.bones) if i >= NB0],
      'verts', m2.vertex_count, 'textures', [t['type'] for t in m2.textures], 'replacable[1,2]', m2.replacable_texture_lookup[1:3], 'submeshes', len(s2.submeshes), 'batches', len(s2.batches))
for n_, bb in (('m2', bytes(raw)), ('skin', skin_out)):
    print(n_, len(bb), hashlib.sha256(bb).hexdigest())
