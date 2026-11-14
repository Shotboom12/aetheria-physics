import struct, numpy as np
def md20(b):
    if b[:4]==b'MD20': return 0
    i=0
    while i+8<=len(b):
        t=b[i:i+4]; sz=struct.unpack_from('<I',b,i+4)[0]
        if t==b'MD21': return i+8
        i+=8+sz
    raise ValueError
def verts(b, base=None):
    if base is None: base=md20(b)
    nv,ov=struct.unpack_from('<II',b,base+0x3C)
    dt=np.dtype([('pos','<f4',3),('w','u1',4),('bi','u1',4),('nrm','<f4',3),('uv1','<f4',2),('uv2','<f4',2)])
    return np.frombuffer(b,dtype=dt,count=nv,offset=base+ov).copy()
def chunks(b):
    i=0;d={}
    while i+8<=len(b):
        t=b[i:i+4].decode('latin1');sz=struct.unpack_from('<I',b,i+4)[0];d.setdefault(t,[]).append(b[i+8:i+8+sz]);i+=8+sz
    return d
