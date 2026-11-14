import glob, struct, sys, os
import numpy as np
from storm_extract import extract
BS = chr(92)
DD = r'<CLIENT_DIR>\Data'
NS = 'wow-88d5e8ef05ec5a8446cdec93d142d7c6'
PACKS = sorted(glob.glob(DD + BS + 'Patch-*Pack-*.MPQ'))
os.makedirs('survey', exist_ok=True)


def get(fid):
    f = 'survey/%d.bin' % fid
    if os.path.exists(f):
        return open(f, 'rb').read()
    key = BS.join(['EsteriaRetail', NS, '2', '%d.bin' % fid])
    for p in PACKS:
        d = extract(p, key)
        if d:
            open(f, 'wb').write(d)
            return d
    return None


def chunks(d):
    p = 0
    out = {}
    while p + 8 <= len(d):
        tag = d[p:p + 4]
        sz = struct.unpack_from('<I', d, p + 4)[0]
        out.setdefault(tag, []).append((p + 8, sz))
        p += 8 + sz
    return out


def bones_of(skb_off):
    cnt, ofs = struct.unpack_from('<II', d_skel, skb_off)
    res = []
    for i in range(cnt):
        o = skb_off + ofs + i * 88
        key, flags, par = struct.unpack_from('<iIh', d_skel, o)
        piv = struct.unpack_from('<3f', d_skel, o + 76)
        res.append((key, par, piv))
    return res


u16 = lambda x, i: struct.unpack_from('<H', x, i)[0]
MODELS = {'Human F': 1000764, 'BloodElf F': 1100258, 'NightElf F': 921844, 'Draenei F': 1022598, 'Nightborne F': 1593999, 'VoidElf F': 5548259, 'Dracthyr F': 7478494}
for name, fid in MODELS.items():
    d = get(fid)
    if not d:
        print(name, fid, 'NOT FOUND')
        continue
    ch = chunks(d)
    skid = struct.unpack_from('<I', d, ch[b'SKID'][0][0])[0] if b'SKID' in ch else None
    sfid = struct.unpack_from('<I', d, ch[b'SFID'][0][0])[0] if b'SFID' in ch else None
    line = '%s %d skid=%s skin=%s' % (name, fid, skid, sfid)
    if skid:
        d_skel = get(skid)
        if d_skel:
            sc = chunks(d_skel)
            bl = bones_of(sc[b'SKB1'][0][0]) if b'SKB1' in sc else []
            cape = [(i, b[0], b[1], tuple(round(x, 2) for x in b[2])) for i, b in enumerate(bl) if 36 <= b[0] <= 40]
            back = [i for i, b in enumerate(bl) if b[0] == 190]
            line += ' bones=%d cape=%s backcloak=%s' % (len(bl), cape, back)
        else:
            line += ' skel NOT FOUND'
    if sfid:
        sk = get(sfid)
        if sk:
            from_wot = None
            sys.path[:0] = ['<WOTLKCONV_DIR>']
            from wotlkconv.m2 import parse_skin
            s = parse_skin(sk)
            gs = sorted({u16(x, 0) for x in s.submeshes if 1500 <= u16(x, 0) < 1600})
            hair = sorted({u16(x, 0) for x in s.submeshes if 1 <= u16(x, 0) < 100})
            line += ' cloakgeosets=%s hairgeosets=%s' % (gs, hair)
    print(line)
