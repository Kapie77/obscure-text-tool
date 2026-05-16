from PIL import Image

# ==============================
#           SWIZZLE
# ==============================
def psp_swizzle_id(x, y, w):
    """
    PSP 8x8 tile swizzle
    """
    tile_x = x & ~7
    tile_y = y & ~7
    local_x = x & 7
    local_y = y & 7
    return (tile_y * w) + (tile_x * 8) + (local_y * 8) + local_x

# ==============================
#           HELPERS
# ==============================
def pack_4bpp(indices):
    raw = bytearray((len(indices) + 1) // 2)
    for i in range(0, len(indices), 2):
        lo = indices[i] & 0x0F
        hi = indices[i+1] & 0x0F if i+1 < len(indices) else 0
        raw[i//2] = lo | (hi << 4)
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
#           UNSWIZZLE
# ==============================
def psp_unswizzle_8bpp(data, width, height):
    """Deswizzle PSP 8bpp tiles 8x8"""
    out = bytearray(len(data))
    tile_w = 8
    tile_h = 8
    tiles_x = width // tile_w
    tiles_y = height // tile_h

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            for y in range(tile_h):
                for x in range(tile_w):
                    src_idx = (
                        ((ty * tiles_x + tx) * tile_w * tile_h) +
                        y * tile_w + x
                    )
                    dst_idx = (ty * tile_h + y) * width + (tx * tile_w + x)
                    out[dst_idx] = data[src_idx]
    return out

# ==============================
#       PALETTE
# ==============================
def decode_psp_palette(pal, color_count=256):
    """Converte paleta BGRA do PSP HVI em RGBA tuples"""
    colors = [(0,0,0,0)] * color_count
    scale_alpha = max(pal[i] for i in range(3, len(pal), 4)) <= 0x90
    for i in range(color_count):
        b = pal[i*4 + 0]
        g = pal[i*4 + 1]
        r = pal[i*4 + 2]
        a = pal[i*4 + 3]
        if scale_alpha:
            a = min(255, a*2)
        colors[i] = (r, g, b, a)
    return colors

def nearest_palette_index(r, g, b, a, palette):
    """Encontra a cor mais próxima na paleta"""
    best = 0
    best_d = 1_000_000
    for i, (pr, pg, pb, pa) in enumerate(palette):
        dr, dg, db, da = r - pr, g - pg, b - pb, a - pa
        d = dr*dr + dg*dg + db*db + da*da*2  # peso maior para alpha
        if d < best_d:
            best_d = d
            best = i
            if d == 0:
                break
    return best

# ==============================
#       DECODERS (HVI)
# ==============================
def decode_psp_hvi(pixel_data, palette_data, width, height):
    """Decode PSP 8bpp HVI linear (sem swizzle)"""
    # Converter paleta BGRA → RGBA
    palette = []
    max_alpha = max(palette_data[i] for i in range(3, len(palette_data), 4))
    scale_alpha = max_alpha <= 0x90
    for i in range(256):
        b, g, r, a = palette_data[i*4:i*4+4]
        if scale_alpha:
            a = min(255, a * 2)
        palette.append((r, g, b, a))

    # Aplicar pixels lineares
    img = Image.new("RGBA", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            idx = pixel_data[y*width + x]
            px[x, y] = palette[idx]

    return img

# ==============================
#       ENCODERS (HVI)
# ==============================
def encode_psp_hvi(img, width, height, palette_data):
    """
    Rebuild PSP HVI 8bpp linear (sem swizzle)
    img          : PIL RGBA
    width/height : dimensões da imagem
    palette_data : bytes da paleta original (256*4)
    Retorna: bytes(linear_indices), bytes(palette_data)
    """
    img = img.convert("RGBA")
    src = img.load()

    # Converte paleta BGRA -> RGBA tuples
    palette = [(palette_data[i*4 + 2], palette_data[i*4 + 1], palette_data[i*4 + 0], palette_data[i*4 + 3]) for i in range(256)]

    indices = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            r, g, b, a = src[x, y]
            # procura o índice mais próximo
            best = 0
            best_d = 1_000_000
            for i, (pr, pg, pb, pa) in enumerate(palette):
                dr, dg, db, da = r - pr, g - pg, b - pb, a - pa
                d = dr*dr + dg*dg + db*db + da*da
                if d < best_d:
                    best_d = d
                    best = i
            indices[y*width + x] = best

    return bytes(indices), palette_data