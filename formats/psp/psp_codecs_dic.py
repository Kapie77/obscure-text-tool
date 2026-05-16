from PIL import Image


# ========================================
#            SHARED HELPERS
# ========================================

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


def nearest_palette_index(r, g, b, a, palette):

    best = 0
    best_d = 999999999

    for i, (pr, pg, pb, pa) in enumerate(palette):

        dr = r - pr
        dg = g - pg
        db = b - pb
        da = a - pa

        d = (
            dr * dr +
            dg * dg +
            db * db +
            da * da * 2
        )

        if d < best_d:
            best_d = d
            best = i

    return best


# ========================================
#               SWIZZLE
# ========================================

def swizzle_psp(linear, w, h, bpp):

    stride = w * bpp // 8

    padded_stride = (stride + 15) & ~15
    padded_height = (h + 7) & ~7

    row_blocks = padded_stride // 16

    swizzled = bytearray(padded_stride * padded_height)

    for y in range(h):
        for x in range(stride):

            block_x = x // 16
            block_y = y // 8

            block_index = block_x + block_y * row_blocks

            dst = (
                block_index * 16 * 8
                + (x % 16)
                + (y % 8) * 16
            )

            src = y * stride + x

            if src < len(linear) and dst < len(swizzled):
                swizzled[dst] = linear[src]

    expected_size = stride * h

    return bytes(swizzled[:expected_size])


# ========================================
#              UNSWIZZLE
# ========================================

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


# ========================================
#               PALETTES
# ========================================

def decode_psp_palette(palette_data, color_count):

    palette = []

    for i in range(color_count):

        r = palette_data[i*4 + 0]
        g = palette_data[i*4 + 1]
        b = palette_data[i*4 + 2]
        a = palette_data[i*4 + 3]

        palette.append((r, g, b, a))

    return palette


# ========================================
#              ENCODERS
# ========================================
# ========================================
#         NEAREST PALETTE INDEX
# ========================================
def nearest_palette_index(r, g, b, a, palette):

    best = 0
    best_dist = 999999999

    for i, (pr, pg, pb, pa) in enumerate(palette):

        dr = r - pr
        dg = g - pg
        db = b - pb
        da = a - pa

        dist = (
            dr * dr +
            dg * dg +
            db * db +
            da * da
        )

        if dist < best_dist:
            best_dist = dist
            best = i

    return best


# ========================================
#              PACK 4BPP
# ========================================
def pack_4bpp(indices):

    out = bytearray((len(indices) + 1) // 2)

    for i in range(0, len(indices), 2):

        a = indices[i] & 0x0F

        b = 0

        if i + 1 < len(indices):
            b = indices[i + 1] & 0x0F

        out[i // 2] = a | (b << 4)

    return bytes(out)


# ========================================
#           ENCODE PSP PAL4
# ========================================
def encode_psp_4bpp(img, width, height, palette_data):

    img = img.convert("RGBA")

    src = img.load()

    palette = decode_psp_palette(
        palette_data,
        16
    )

    indices = bytearray(width * height)

    for y in range(height):
        for x in range(width):

            r, g, b, a = src[x, y]

            indices[y * width + x] = nearest_palette_index(
                r,
                g,
                b,
                a,
                palette
            )

    packed = pack_4bpp(indices)

    return swizzle_psp(
        packed,
        width,
        height,
        4
    )


# ========================================
#           ENCODE PSP PAL8
# ========================================
def encode_psp_8bpp(img, width, height, palette_data):

    img = img.convert("RGBA")

    src = img.load()

    palette = decode_psp_palette(
        palette_data,
        256
    )

    indices = bytearray(width * height)

    for y in range(height):
        for x in range(width):

            r, g, b, a = src[x, y]

            indices[y * width + x] = nearest_palette_index(
                r,
                g,
                b,
                a,
                palette
            )

    return swizzle_psp(
        indices,
        width,
        height,
        8
    )


# ========================================
#         ENCODE PSP RGBA8888
# ========================================
def encode_psp_rgba8888(img):

    rgba = img.convert("RGBA")

    width, height = rgba.size

    raw = rgba.tobytes()

    linear = bytearray(width * height * 4)

    for i in range(width * height):

        linear[i*4 + 0] = raw[i*4 + 0]
        linear[i*4 + 1] = raw[i*4 + 1]
        linear[i*4 + 2] = raw[i*4 + 2]
        linear[i*4 + 3] = raw[i*4 + 3]

    return swizzle_psp(
        bytes(linear),
        width,
        height,
        32
    )


# ========================================
#              DECODERS
# ========================================

# ===== PAL4 =====
def decode_psp_4bpp(pixel_data, palette_data, width, height):

    img = Image.new("RGBA", (width, height))

    pixels = img.load()

    linear_packed = unswizzle_psp(
        pixel_data,
        width,
        height,
        4
    )

    indices = unpack_4bpp(
        linear_packed,
        width * height
    )

    palette = decode_psp_palette(
        palette_data,
        16
    )

    for y in range(height):
        for x in range(width):

            idx = indices[y * width + x]

            pixels[x, y] = palette[idx]

    return img


# ===== PAL8 =====
def decode_psp_8bpp(pixel_data, palette_data, width, height):

    img = Image.new("RGBA", (width, height))

    pixels = img.load()

    indices = unswizzle_psp(
        pixel_data,
        width,
        height,
        8
    )

    palette = decode_psp_palette(
        palette_data,
        256
    )

    for y in range(height):
        for x in range(width):

            idx = indices[y * width + x]

            pixels[x, y] = palette[idx]

    return img


# ===== RGBA8888 =====
def decode_psp_rgba8888(pixel_data, width, height):

    linear = unswizzle_psp(
        pixel_data,
        width,
        height,
        32
    )

    return Image.frombytes(
        "RGBA",
        (width, height),
        linear
    )