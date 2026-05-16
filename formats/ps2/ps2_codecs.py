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

        hi = (
            (indices[i + 1] & 0x0F)
            if i + 1 < len(indices)
            else 0
        )

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
#         UNSWIZZLE (PS2)
# ==============================
def unswizzle_8bpp(data, width, height):
    out = bytearray(width * height)

    for y in range(height):
        for x in range(width):
            sid = ps2_swizzle_id(x, y, width)
            if sid < len(data):
                out[y * width + x] = data[sid]

    return out

# ==============================
#         UNSWIZZLE (PSP)
# ==============================
def unswizzle_psp(raw, w, h, bpp):

    stride = w * bpp // 8

    padded_stride = (stride + 15) & ~15

    row_blocks = padded_stride // 16

    linear = bytearray(stride * h)

    dst = 0

    for y in range(h):
        for x in range(stride):

            block_x = x // 16
            block_y = y // 8

            block_index = block_x + block_y * row_blocks

            src = (
                block_index * 16 * 8
                + (x % 16)
                + (y % 8) * 16
            )

            if src < len(raw):
                linear[dst] = raw[src]

            dst += 1

    return bytes(linear)

# ==============================
#        DECODERS (PS2)
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

# ========================
#   DECODE 8BPP (.DIC)
# ========================
def decode_ps2_8bpp(pixel_data, palette_data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    # UNSWIZZLE (PS2 DIC)
    indices = unswizzle_8bpp(pixel_data, width, height)

    # PALETTE (com remap)
    palette = decode_ps2_palette(palette_data)

    for y in range(height):
        for x in range(width):
            idx = indices[y * width + x]
            if idx < 256:
                pixels[x, y] = palette[idx]

    return img

# ========================
#   DECODE 4BPP (.DIC)
# ========================
def decode_ps2_4bpp(pixel_data, palette_data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    packed = unpack_4bpp(pixel_data, width * height)

    indices = bytearray(width * height)

    for y in range(height):
        for x in range(width):

            sid = ps2_swizzle_id(x, y, width)

            if sid < len(packed):
                indices[y * width + x] = packed[sid]

    palette = decode_ps2_palette(palette_data, 16)

    for y in range(height):
        for x in range(width):

            idx = indices[y * width + x] & 0x0F

            pixels[x, y] = palette[idx]

    return img

# ============================
#   DECODE RGBA8888 (.DIC)
# ============================
def decode_ps2_rgba8888(pixel_data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for y in range(height):
        for x in range(width):

            if pos + 3 >= len(pixel_data):
                break

            r = pixel_data[pos + 0]
            g = pixel_data[pos + 1]
            b = pixel_data[pos + 2]
            a = pixel_data[pos + 3]

            # PS2 alpha range
            a = min(255, a * 2)

            pixels[x, y] = (r, g, b, a)

            pos += 4

    return img

# ==========================
#   DECODE RGBA5551 (.DIC)
# ==========================
def decode_ps2_rgb5551(pixel_data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for y in range(height):
        for x in range(width):

            if pos + 1 >= len(pixel_data):
                break

            v = pixel_data[pos] | (pixel_data[pos + 1] << 8)

            r = (v & 0x1F) * 255 // 31
            g = ((v >> 5) & 0x1F) * 255 // 31
            b = ((v >> 10) & 0x1F) * 255 // 31
            a = 255 if (v & 0x8000) else 0

            pixels[x, y] = (r, g, b, a)

            pos += 2

    return img

# ============================
#           .HVI
# ============================
# ============ PS2 (.hvi) ================ #
def decode_ps2_hvi(pixel_data, palette_data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    # ✔ pixels já são lineares
    indices = pixel_data

    # ✔ detectar se precisa escalar alpha
    max_alpha = max(palette_data[i] for i in range(3, len(palette_data), 4))
    scale_alpha = max_alpha <= 0x90

    # ✔ palette é BGRA
    palette = []
    for i in range(256):
        b = palette_data[i*4 + 0]
        g = palette_data[i*4 + 1]
        r = palette_data[i*4 + 2]
        a = palette_data[i*4 + 3]

        if scale_alpha:
            a = min(255, a * 2)

        palette.append((r, g, b, a))

    # ✔ aplicar direto
    for y in range(height):
        for x in range(width):
            idx = indices[y * width + x]
            if idx < 256:
                pixels[x, y] = palette[idx]

    return img

# ============ PSP (.hvi) ================ #
def decode_psp_hvi(pixels, palette, width, height):

    indices = unswizzle_psp(
        pixels,
        width,
        height,
        8
    )

    out = bytearray(width * height * 4)

    for i, idx in enumerate(indices):

        p = idx * 4
        d = i * 4

        r = palette[p + 0]
        g = palette[p + 1]
        b = palette[p + 2]
        a = palette[p + 3]

        out[d + 0] = r
        out[d + 1] = g
        out[d + 2] = b
        out[d + 3] = a

    return Image.frombytes(
        "RGBA",
        (width, height),
        bytes(out)
    )


# ==============================
#        ENCODERS (PS2)
# ==============================

# ===== RGBA8888 (.DIC) ===== #
def encode_ps2_rgba8888(img, width, height):

    pixels = img.convert("RGBA").tobytes()

    out = bytearray()

    for i in range(0, len(pixels), 4):

        r = pixels[i]
        g = pixels[i + 1]
        b = pixels[i + 2]
        a = pixels[i + 3]

        # PS2 usa alpha 0-128 normalmente
        a = a // 2

        out += bytes([r, g, b, a])

    return bytes(out)

# ====== RGB5551 (.DIC) ====== #
def encode_ps2_rgb5551(img, width, height):

    pixels = img.convert("RGBA").load()

    out = bytearray()

    for y in range(height):
        for x in range(width):

            r, g, b, a = pixels[x, y]

            r5 = r >> 3
            g5 = g >> 3
            b5 = b >> 3

            a1 = 1 if a >= 128 else 0

            value = (
                r5 |
                (g5 << 5) |
                (b5 << 10) |
                (a1 << 15)
            )

            out += value.to_bytes(2, "little")

    return bytes(out)

# ==============================
#      PALETTE MATCHING
# ==============================
def nearest_palette_index(r, g, b, a, palette):

    best = 0
    best_d = 999999999

    for i, (pr, pg, pb, pa) in enumerate(palette):

        dr = r - pr
        dg = g - pg
        db = b - pb
        da = a - pa

        # alpha com peso maior
        d = (
            dr * dr +
            dg * dg +
            db * db +
            da * da * 2
        )

        if d < best_d:

            best_d = d
            best = i

            # match perfeito
            if d == 0:
                break

    return best


# ==============================
#          8BPP (.DIC)
# ==============================
def encode_ps2_8bpp(
    img,
    width,
    height,
    palette_data
):

    img = img.convert("RGBA")

    src = img.load()

    # usa palette ORIGINAL
    palette = decode_ps2_palette(
        palette_data,
        256
    )

    indices = bytearray(width * height)

    # =========================
    # mapear pixels -> palette
    # =========================
    for y in range(height):

        row = y * width

        for x in range(width):

            r, g, b, a = src[x, y]

            indices[row + x] = (
                nearest_palette_index(
                    r,
                    g,
                    b,
                    a,
                    palette
                )
            )

    # =========================
    # swizzle PS2
    # =========================
    swizzled = bytearray(width * height)

    for y in range(height):

        row = y * width

        for x in range(width):

            sid = ps2_swizzle_id(
                x,
                y,
                width
            )

            if sid < len(swizzled):

                swizzled[sid] = (
                    indices[row + x]
                )

    return bytes(swizzled), palette_data


# ==============================
#          4BPP (.DIC)
# ==============================
def encode_ps2_4bpp(
    img,
    width,
    height,
    palette_data
):

    img = img.convert("RGBA")

    src = img.load()

    # usa palette ORIGINAL
    palette = decode_ps2_palette(
        palette_data,
        16
    )

    indices = bytearray(width * height)

    # =========================
    # mapear pixels -> palette
    # =========================
    for y in range(height):

        row = y * width

        for x in range(width):

            r, g, b, a = src[x, y]

            indices[row + x] = (
                nearest_palette_index(
                    r,
                    g,
                    b,
                    a,
                    palette
                ) & 0x0F
            )

    # =========================
    # swizzle PS2
    # =========================
    swizzled = bytearray(width * height)

    for y in range(height):

        row = y * width

        for x in range(width):

            sid = ps2_swizzle_id(
                x,
                y,
                width
            )

            if sid < len(swizzled):

                swizzled[sid] = (
                    indices[row + x]
                )

    # =========================
    # pack 4bpp
    # =========================
    packed = pack_4bpp(swizzled)

    return packed, palette_data