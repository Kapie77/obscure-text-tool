from utils.binary import read_be_u32

def is_printable(b):
    return 32 <= b < 127


def is_valid_texture_entry(data, off):
    if off >= len(data):
        return False

    name_len = data[off]
    if name_len < 1 or name_len > 48:
        return False

    if off + 1 + name_len > len(data):
        return False

    for i in range(name_len):
        if not is_printable(data[off + 1 + i]):
            return False

    p = off + 1 + name_len
    if p + 28 > len(data):
        return False

    width = read_be_u32(data, p)
    height = read_be_u32(data, p + 4)
    gx = read_be_u32(data, p + 16)
    size = read_be_u32(data, p + 24)

    if not is_power_of_two(width) or width > 1024:
        return False
    if not is_power_of_two(height) or height > 1024:
        return False
    if gx not in [1,3,5,6,8,9,14]:
        return False
    if size <= 0 or size > len(data):
        return False
    if p + 28 + size > len(data):
        return False

    return True

def is_power_of_two(v):
        return v != 0 and (v & (v - 1)) == 0

# =============================================
#    DETECÇÃO DE .HVT (OBSCURE OU FINAL EXAM)
# =============================================
def is_finalexam_hvt(path):
    try:
        with open(path, "rb") as f:
            data = f.read(0x40)  # lê mais pra garantir

        magic = data[0:4]

        # PC
        if magic == b"HVI ":
            return True

        # PS3 / X360
        if magic == b" IVH":
            # heurística: Final Exam sempre tem formato ASCII em 0x14
            fmt = data[0x14:0x18]

            # formatos válidos conhecidos
            known = [
                b"DXT1", b"DXT3", b"DXT5",
                b"TXD1", b"TXD3", b"TXD5",
                b"ARGB", b"XRGB",
            ]

            return fmt in known

        return False

    except:
        return False

# ===============================
#       DETECTAR PSP .DIC
# ===============================
def looks_like_psp_dic(data):

    if len(data) < 32:
        return False

    count = int.from_bytes(data[0:4], "little")

    if count <= 0 or count > 4096:
        return False

    name_len = int.from_bytes(data[4:8], "little")

    if name_len <= 0 or name_len > 64:
        return False

    if 8 + name_len + 16 > len(data):
        return False

    name = data[8:8+name_len]

    # nome ASCII válido
    if not all(32 <= c < 127 for c in name):
        return False

    p = 8 + name_len

    if p + 16 > len(data):
        return False

    width  = int.from_bytes(data[p:p+2], "little")
    height = int.from_bytes(data[p+2:p+4], "little")

    palette_entries = int.from_bytes(data[p+4:p+6], "little")

    bpp = data[p+6]

    palette_size = int.from_bytes(data[p+12:p+16], "little")

    # dimensões plausíveis
    if width <= 0 or width > 4096:
        return False

    if height <= 0 or height > 4096:
        return False

    # formatos suportados
    if bpp not in (4, 8, 32):
        return False

    # PAL4
    if bpp == 4:
        if palette_entries != 16:
            return False

        if palette_size != 64:
            return False

    # PAL8
    elif bpp == 8:
        if palette_entries != 256:
            return False

        if palette_size != 1024:
            return False

    # RGBA8888
    elif bpp == 32:
        if palette_entries != 0:
            return False

    print("[+] PSP signature validated")

    return True