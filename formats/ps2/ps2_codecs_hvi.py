from PIL import Image

# ==============================
#         PS2 SWIZZLE
# ==============================
def ps2_swizzle_id(x, y, w):
    block = (y & ~0xF) * w + (x & ~0xF) * 2
    swap  = (((y + 2) >> 2) & 1) * 4
    posY  = (((y & ~3) >> 1) + (y & 1)) & 7
    column = posY * w * 2 + ((x + swap) & 7) * 4
    byte = ((y >> 1) & 1) + ((x >> 2) & 2)
    return block + column + byte

# ==============================
#           HELPERS
# ==============================
def remap_clut_index(i):
    return (i & 0xE7) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)

def pack_4bpp(indices):
    raw = bytearray((len(indices) + 1) // 2)
    for i in range(0, len(indices), 2):
        lo = indices[i] & 0x0F
        hi = indices[i + 1] & 0x0F if i + 1 < len(indices) else 0
        raw[i // 2] = lo | (hi << 4)
    return bytes(raw)

def unpack_4bpp(raw, pixel_count):
    out = bytearray(pixel_count)
    di = 0
    for b in raw:
        if di < pixel_count:
            out[di] = b & 0x0F
            di += 1
        if di < pixel_count:
            out[di] = (b >> 4) & 0x0F
            di += 1
    return out

# ==============================
#       PALETTE / HELPERS
# ==============================
def decode_ps2_palette(pal, color_count=256):
    """Converte paleta BGRA do HVI em RGBA tuples"""
    colors = [(0, 0, 0, 0)] * color_count
    scale_alpha = max(pal[i] for i in range(3, len(pal), 4)) <= 0x90

    for i in range(color_count):
        b, g, r, a = pal[i*4:i*4+4]
        if scale_alpha:
            a = min(255, a*2)
        colors[i] = (r, g, b, a)
    return colors

def nearest_palette_index(r, g, b, a, palette):
    """Retorna índice exato se houver match, senão o mais próximo"""
    for i, (pr, pg, pb, pa) in enumerate(palette):
        if (r, g, b, a) == (pr, pg, pb, pa):
            return i
    # fallback nearest
    best = 0
    best_d = 1_000_000
    for i, (pr, pg, pb, pa) in enumerate(palette):
        dr, dg, db, da = r-pr, g-pg, b-pb, a-pa
        d = dr*dr + dg*dg + db*db + da*da
        if d < best_d:
            best_d = d
            best = i
    return best

# ==============================
#       DECODERS (HVI)
# ==============================
def decode_ps2_hvi(pixel_data, palette_data, width, height):
    """Decode PS2 8bpp HVI linear"""
    img = Image.new("RGBA", (width, height))
    pixels = img.load()
    palette = decode_ps2_palette(palette_data, 256)

    for y in range(height):
        for x in range(width):
            idx = pixel_data[y*width + x]
            pixels[x, y] = palette[idx] if idx < 256 else (0,0,0,0)

    return img

def decode_psp_hvi(pixels, palette, width, height):
    """Decode PSP 8bpp HVI linear (unswizzle)"""
    out = bytearray(width * height * 4)
    for i, idx in enumerate(pixels):
        p = idx*4
        d = i*4
        r, g, b, a = palette[p:p+4]
        out[d:d+4] = bytes([r, g, b, a])
    return Image.frombytes("RGBA", (width, height), bytes(out))

# ==============================
#       ENCODERS (HVI)
# ==============================
def encode_ps2_8bpp_hvi(img, width, height, palette_data):
    """HVI 8bpp linear (sem swizzle)"""
    img = img.convert("RGBA")
    src = img.load()
    palette = decode_ps2_palette(palette_data, 256)
    indices = bytearray(width*height)
    for y in range(height):
        for x in range(width):
            r, g, b, a = src[x, y]
            indices[y*width + x] = nearest_palette_index(r, g, b, a, palette)
    return bytes(indices), palette_data

def encode_ps2_4bpp_hvi(img, width, height, palette_data):
    """HVI 4bpp linear (sem swizzle)"""
    img = img.convert("RGBA")
    src = img.load()
    palette = decode_ps2_palette(palette_data, 16)
    indices = bytearray(width*height)
    for y in range(height):
        for x in range(width):
            r, g, b, a = src[x, y]
            indices[y*width + x] = nearest_palette_index(r, g, b, a, palette) & 0x0F
    packed = pack_4bpp(indices)
    return packed, palette_data

def encode_ps2_hvi(img, width, height, palette_data, pixel_data):
    """Rebuild HVI 8bpp PS2 linear (sem swizzle), preservando pixels idênticos"""
    img = img.convert("RGBA")
    src = img.load()
    palette = decode_ps2_palette(palette_data, 256)
    linear_indices = bytearray(width*height)

    for y in range(height):
        for x in range(width):
            r, g, b, a = src[x, y]
            idx = pixel_data[y*width + x]
            pr, pg, pb, pa = palette[idx]
            if (r, g, b, a) == (pr, pg, pb, pa):
                linear_indices[y*width + x] = idx
            else:
                linear_indices[y*width + x] = nearest_palette_index(r, g, b, a, palette)

    return bytes(linear_indices), palette_data