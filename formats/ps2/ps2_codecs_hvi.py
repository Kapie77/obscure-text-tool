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
#           OTHERS
# ==============================
def remap_clut_index(i):
    return (i & 0xE7) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)

def pack_4bpp(indices):
    raw = bytearray((len(indices) + 1) // 2)
    for i in range(0, len(indices), 2):
        lo = indices[i] & 0x0F
        hi = (indices[i + 1] & 0x0F) if i + 1 < len(indices) else 0
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
#       DECODERS (HVI)
# ==============================
def decode_ps2_palette(pal, color_count=256):

    colors = [(0,0,0,0)] * 256

    is_rgba8888 = len(pal) >= color_count * 4

    if is_rgba8888:

        n = min(color_count, len(pal) // 4)

        for i in range(n):

            r = pal[i*4+0]
            g = pal[i*4+1]
            b = pal[i*4+2]
            a = min(255, pal[i*4+3] * 2)

            colors[i] = (r, g, b, a)

    else:

        n = min(color_count, len(pal) // 2)

        for i in range(n):

            v = pal[i*2] | (pal[i*2+1] << 8)

            r = (v & 0x1F) * 255 // 31
            g = ((v >> 5) & 0x1F) * 255 // 31
            b = ((v >> 10) & 0x1F) * 255 // 31
            a = 255 if (v & 0x8000) else 0

            colors[i] = (r, g, b, a)

    # CLUT remap somente 8bpp
    if color_count == 256:

        fixed = [(0,0,0,0)] * 256

        for i in range(256):
            fixed[remap_clut_index(i)] = colors[i]

        return fixed

    return colors

def decode_ps2_hvi(pixel_data, palette_data, width, height):
    """Decode PS2 8bpp HVI linear"""
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    # pixels já são lineares
    indices = pixel_data

    # detectar se precisa escalar alpha
    max_alpha = max(palette_data[i] for i in range(3, len(palette_data), 4))
    scale_alpha = max_alpha <= 0x90

    # palette é BGRA
    palette = []
    for i in range(256):
        b = palette_data[i*4 + 0]
        g = palette_data[i*4 + 1]
        r = palette_data[i*4 + 2]
        a = palette_data[i*4 + 3]
        if scale_alpha:
            a = min(255, a * 2)
        palette.append((r, g, b, a))

    # aplicar pixels
    for y in range(height):
        for x in range(width):
            idx = indices[y * width + x]
            if idx < 256:
                pixels[x, y] = palette[idx]

    return img

def decode_psp_hvi(pixels, palette, width, height):
    """Decode PSP 8bpp HVI linear (unswizzle)"""
    out = bytearray(width * height * 4)
    for i, idx in enumerate(pixels):
        p = idx * 4
        d = i * 4
        r, g, b, a = palette[p+0], palette[p+1], palette[p+2], palette[p+3]
        out[d+0] = r
        out[d+1] = g
        out[d+2] = b
        out[d+3] = a
    return Image.frombytes("RGBA", (width, height), bytes(out))

# ==============================
#       PALETTE / HELPERS
# ==============================
def nearest_palette_index(r, g, b, a, palette):
    best = 0
    best_d = 999999999
    for i, (pr, pg, pb, pa) in enumerate(palette):
        dr, dg, db, da = r - pr, g - pg, b - pb, a - pa
        d = dr*dr + dg*dg + db*db + da*da*2  # alpha com peso maior
        if d < best_d:
            best_d = d
            best = i
            if d == 0:
                break
    return best

# ==============================
#        ENCODERS (HVI)
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

def encode_ps2_hvi(img, width, height, palette_data):
    """Rebuild HVI 8bpp PS2 com swizzle"""
    img = img.convert("RGBA")
    src = img.load()
    palette = decode_ps2_palette(palette_data, 256)
    indices = bytearray(width*height)
    for y in range(height):
        for x in range(width):
            r, g, b, a = src[x, y]
            indices[y*width + x] = nearest_palette_index(r, g, b, a, palette)
    # swizzle PS2
    swizzled = bytearray(width*height)
    for y in range(height):
        for x in range(width):
            sid = ps2_swizzle_id(x, y, width)
            swizzled[sid] = indices[y*width + x]
    return swizzled, palette_data