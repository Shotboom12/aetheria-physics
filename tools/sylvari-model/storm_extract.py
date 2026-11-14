import ctypes, sys, os, glob
DLL = r'<STORMLIB_DLL>'
S = ctypes.WinDLL(DLL)
S.SFileOpenArchive.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(ctypes.c_void_p)]
S.SFileOpenFileEx.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_void_p)]
S.SFileGetFileSize.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]; S.SFileGetFileSize.restype=ctypes.c_uint32
S.SFileReadFile.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.c_void_p]
def extract(mpq, key):
    h=ctypes.c_void_p()
    if not S.SFileOpenArchive(mpq,0,0x100,ctypes.byref(h)): return None  # read-only
    f=ctypes.c_void_p(); data=None
    if S.SFileOpenFileEx(h,key.encode(),0,ctypes.byref(f)):
        hi=ctypes.c_uint32(); sz=S.SFileGetFileSize(f,ctypes.byref(hi)); buf=ctypes.create_string_buffer(sz); rd=ctypes.c_uint32()
        S.SFileReadFile(f,buf,sz,ctypes.byref(rd),None); data=buf.raw[:rd.value]; S.SFileCloseFile(f)
    S.SFileCloseArchive(h); return data
if __name__=='__main__':
    data_dir=r'<CLIENT_DIR>\Data'; BS=chr(92)
    key=BS.join(['EsteriaRetail','wow-88d5e8ef05ec5a8446cdec93d142d7c6','2',sys.argv[1]+'.bin'])
    for p in sorted(glob.glob(data_dir+BS+'Patch-Retail-Pack-*.MPQ')):
        d=extract(p,key)
        if d is not None:
            os.makedirs('retail',exist_ok=True); open('retail/'+sys.argv[1]+'.bin','wb').write(d); print(sys.argv[1],'found in',os.path.basename(p),len(d)); break
    else: print('not found')
