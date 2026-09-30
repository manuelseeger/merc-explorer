import struct, zlib
SLF = r"D:\SteamLibrary\steamapps\common\Jagged Alliance 2 Gold\Data\Faces.slf"
def slf_entries(path=SLF):
    b = open(path, "rb").read(); n = struct.unpack_from("<i", b, 512)[0]; r = {}
    for i in range(n):
        o = len(b) - (n - i) * 280
        name = b[o:o+256].split(b"\0")[0].decode("latin1").upper().replace("\\", "/")
        off, ln, st = struct.unpack_from("<IIB", b, o + 256)
        if st == 0: r[name] = b[off:off+ln]
    return r
def png(w, h, rgba):
    raw = b"".join(b"\0" + bytes(rgba[y*w*4:(y+1)*w*4]) for y in range(h))
    def ch(t, d): c = struct.pack(">I", len(d)) + t + d; return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def decode(d, frame=0):
    assert d[:4] == b"STCI"
    flags = struct.unpack_from("<I", d, 16)[0]; assert flags & 8
    ncol, nsub = struct.unpack_from("<IH", d, 24)
    pal = d[64:64+768]; p = 64 + 768
    subs = []
    for i in range(nsub):
        subs.append(struct.unpack_from("<IIhhHH", d, p)); p += 16
    off, ln, ox, oy, h, w = subs[frame]
    data = d[p+off:p+off+ln]; px = bytearray(w*h*4); x = y = 0; i = 0
    while i < len(data) and y < h:
        b = data[i]; i += 1
        if b == 0: y += 1; x = 0
        elif b & 0x80: x += b & 0x7f
        else:
            for c in data[i:i+b]:
                if x < w:
                    o = (y*w + x)*4; px[o:o+4] = bytes((pal[c*3], pal[c*3+1], pal[c*3+2], 255))
                x += 1
            i += b
    return w, h, px, nsub
if __name__ == "__main__":
    E = slf_entries()
    for k in ("00.STI", "BIGFACES/00.STI", "BIGFACES/DEBUG.TXT"):
        if k in E and k.endswith("STI"):
            w, h, px, n = decode(E[k]); print(k, w, h, n); open(k.replace("/", "_") + ".png", "wb").write(png(w, h, px))
    print(sorted(k for k in E if k.startswith("BIGFACES/"))[:80])
