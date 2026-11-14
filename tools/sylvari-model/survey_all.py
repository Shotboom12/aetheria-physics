import struct, sys, io, contextlib
sys.path.insert(0,'.')
sys.path[:0] = ['<WOTLKCONV_DIR>']
with contextlib.redirect_stdout(io.StringIO()):
    import survey_cape as sc
from wotlkconv.m2 import parse_skin
u16=lambda x,i: struct.unpack_from('<H',x,i)[0]
ids=[(1,0,1011653),(1,1,1000764),(2,0,917116),(2,1,949470),(3,0,878772),(3,1,950080),(4,0,974343),(4,1,921844),(5,0,959310),(5,1,997378),(6,0,968705),(6,1,986648),(7,0,900914),(7,1,940356),(8,0,1022938),(8,1,1018060),(9,0,119376),(10,0,1100087),(10,1,1100258),(11,0,1005887),(11,1,1022598),(12,0,307454),(12,1,307453),(13,0,1734034),(13,1,1733758),(16,0,1890765),(16,1,1890763),(19,0,535052),(19,1,589715),(22,0,1630447),(22,1,1662187),(25,0,1721003),(25,1,1886724),(26,0,1814471),(26,1,1810676),(27,0,1620605),(27,1,1593999),(29,0,5548261),(29,1,5548259),(46,0,1630218),(46,1,1630402),(47,0,2622502),(47,1,2564806),(50,0,5422149),(50,1,5422147),(52,0,7478487),(52,1,7478494),(66,0,4395382),(66,1,4220448),(74,0,4036647),(74,1,4081379),(75,0,3490792),(77,0,5926159),(77,1,6152557)]
for race,sex,fid in ids:
    d=sc.get(fid)
    if not d: print('race',race,'sex',sex,fid,'NOT IN PACKS'); continue
    ch=sc.chunks(d); line='race %d sex %d %d:'%(race,sex,fid)
    skid=struct.unpack_from('<I',d,ch[b'SKID'][0][0])[0] if b'SKID' in ch else None
    cape='?'
    if skid:
        sc.d_skel=sc.get(skid)
        if sc.d_skel:
            bl=sc.bones_of(sc.chunks(sc.d_skel)[b'SKB1'][0][0])
            keys=sorted(b[0] for b in bl if 36<=b[0]<=40)
            cape='cape keys %s of %d bones'%(keys,len(bl))
        else: cape='skel %d missing'%skid
    else: cape='embedded skeleton (no SKID)'
    skin=None
    if b'SFID' in ch: skin=struct.unpack_from('<I',d,ch[b'SFID'][0][0])[0]
    cg='?'
    if skin:
        sk=sc.get(skin)
        if sk:
            s=parse_skin(sk); cg=sorted({u16(x,0) for x in s.submeshes if 1500<=u16(x,0)<1600})
            cg='cloak geosets %d (%s..%s)'%(len(cg),cg[0] if cg else '-',cg[-1] if cg else '-')
    print(line,cape,'|',cg,flush=True)
