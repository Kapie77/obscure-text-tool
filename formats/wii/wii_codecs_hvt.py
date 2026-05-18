from PIL import Image

from texture_codecs.dxt_codecs_wii_dic_hvt import (
    decode_cmpr,
    encode_cmpr
)

# =========================================================
# BLOCK SIZES
# =========================================================

def block_size(bpp):

    if bpp == 4:
        return (8, 8)

    elif bpp == 8:
        return (8, 4)

    elif bpp == 16:
        return (4, 4)

    elif bpp == 32:
        return (4, 4)

    raise Exception(f"Unsupported bpp: {bpp}")

# =========================================================
# OFFSETS
# =========================================================

def offset_bpp32(x, y, w):

    blocks_x = (w + 3) >> 2

    xb = x >> 2
    yb = y >> 2

    xp = x & 3
    yp = y & 3

    return (
        ((yb * blocks_x + xb) << 6) +
        ((yp << 3) + (xp << 1))
    )

def offset_bpp16(x, y, w):

    blocks_x = (w + 3) >> 2

    xb = x >> 2
    yb = y >> 2

    xp = x & 3
    yp = y & 3

    return (
        ((yb * blocks_x + xb) << 5) +
        ((yp << 3) + (xp << 1))
    )

def offset_bpp8(x, y, w):

    blocks_x = (w + 7) >> 3

    xb = x >> 3
    yb = y >> 2

    xp = x & 7
    yp = y & 3

    return (
        ((yb * blocks_x + xb) << 5) +
        ((yp << 3) + xp)
    )

# =========================================================
# RGB565
# =========================================================

def rgb565_to_rgba(c):

    r = ((c >> 11) & 31) * 255 // 31
    g = ((c >> 5) & 63) * 255 // 63
    b = (c & 31) * 255 // 31

    return (r, g, b, 255)

def encode_rgb565(r, g, b):

    r5 = (r * 31 + 127) // 255
    g6 = (g * 63 + 127) // 255
    b5 = (b * 31 + 127) // 255

    return (
        (r5 << 11) |
        (g6 << 5) |
        b5
    )

# =========================================================
# RGB5A3
# =========================================================

def decode_rgb5a3_pixel(p):

    if p & 0x8000:

        r = ((p >> 10) & 0x1F) * 255 // 31
        g = ((p >> 5) & 0x1F) * 255 // 31
        b = (p & 0x1F) * 255 // 31

        a = 255

    else:

        a = ((p >> 12) & 0x07) * 255 // 7

        r = ((p >> 8) & 0x0F) * 255 // 15
        g = ((p >> 4) & 0x0F) * 255 // 15
        b = (p & 0x0F) * 255 // 15

    return (r, g, b, a)

def encode_rgb5a3_pixel(r, g, b, a):

    if a < 248:

        r4 = (r * 15 + 127) // 255
        g4 = (g * 15 + 127) // 255
        b4 = (b * 15 + 127) // 255

        a3 = (a * 7 + 127) // 255

        return (
            (a3 << 12) |
            (r4 << 8) |
            (g4 << 4) |
            b4
        )

    else:

        r5 = (r * 31 + 127) // 255
        g5 = (g * 31 + 127) // 255
        b5 = (b * 31 + 127) // 255

        return (
            0x8000 |
            (r5 << 10) |
            (g5 << 5) |
            b5
        )

# =========================================================
# CMPR
# =========================================================

def decode_cmpr_block(block):

    c0 = (block[0] << 8) | block[1]
    c1 = (block[2] << 8) | block[3]

    p0 = rgb565_to_rgba(c0)
    p1 = rgb565_to_rgba(c1)

    if c0 > c1:

        p2 = (
            (2*p0[0] + p1[0]) // 3,
            (2*p0[1] + p1[1]) // 3,
            (2*p0[2] + p1[2]) // 3,
            255
        )

        p3 = (
            (2*p1[0] + p0[0]) // 3,
            (2*p1[1] + p0[1]) // 3,
            (2*p1[2] + p0[2]) // 3,
            255
        )

    else:

        p2 = (
            (p0[0] + p1[0]) // 2,
            (p0[1] + p1[1]) // 2,
            (p0[2] + p1[2]) // 2,
            255
        )

        p3 = (0, 0, 0, 0)

    palette = [p0, p1, p2, p3]

    pixels = []

    offset = 4

    for row in range(4):

        bits = block[offset]
        offset += 1

        for col in range(4):

            idx = (
                bits >> (6 - col * 2)
            ) & 3

            pixels.append(
                palette[idx]
            )

    return pixels

def decode_cmpr(data, width, height):

    img = Image.new(
        "RGBA",
        (width, height)
    )

    pixels = img.load()

    sw = (width + 7) & ~7
    sh = (height + 7) & ~7

    offset = 0

    for y in range(0, sh, 8):

        for x in range(0, sw, 8):

            for sy in range(0, 8, 4):

                for sx in range(0, 8, 4):

                    block = data[
                        offset:
                        offset + 8
                    ]

                    offset += 8

                    block_pixels = decode_cmpr_block(
                        block
                    )

                    i = 0

                    for dy in range(4):

                        for dx in range(4):

                            px = x + sx + dx
                            py = y + sy + dy

                            if (
                                px < width and
                                py < height
                            ):
                                pixels[px, py] = (
                                    block_pixels[i]
                                )

                            i += 1

    return img

def encode_cmpr(img, width, height, template=None):

    pixels = img.load()

    out = bytearray()

    sw = (width + 7) & ~7
    sh = (height + 7) & ~7

    for y in range(0, sh, 8):

        for x in range(0, sw, 8):

            for sy in range(0, 8, 4):

                for sx in range(0, 8, 4):

                    block = []

                    for dy in range(4):

                        for dx in range(4):

                            px = x + sx + dx
                            py = y + sy + dy

                            if (
                                px < width and
                                py < height
                            ):
                                block.append(
                                    pixels[px, py]
                                )
                            else:
                                block.append(
                                    (0,0,0,0)
                                )

                    opaque = [
                        p for p in block
                        if p[3] >= 128
                    ]

                    alpha_mode = (
                        len(opaque) != 16
                    )

                    if not opaque:

                        c0 = 0
                        c1 = 0

                    else:

                        bright = sorted(
                            opaque,
                            key=lambda p:
                                p[0] + p[1] + p[2]
                        )

                        lo = bright[0]
                        hi = bright[-1]

                        c0 = encode_rgb565(
                            hi[0],
                            hi[1],
                            hi[2]
                        )

                        c1 = encode_rgb565(
                            lo[0],
                            lo[1],
                            lo[2]
                        )

                        if alpha_mode and c0 > c1:
                            c0, c1 = c1, c0

                        elif (
                            not alpha_mode and
                            c0 < c1
                        ):
                            c0, c1 = c1, c0

                    p0 = rgb565_to_rgba(c0)
                    p1 = rgb565_to_rgba(c1)

                    palette = [p0, p1]

                    if c0 > c1:

                        palette.append((
                            (2*p0[0] + p1[0]) // 3,
                            (2*p0[1] + p1[1]) // 3,
                            (2*p0[2] + p1[2]) // 3,
                            255
                        ))

                        palette.append((
                            (p0[0] + 2*p1[0]) // 3,
                            (p0[1] + 2*p1[1]) // 3,
                            (p0[2] + 2*p1[2]) // 3,
                            255
                        ))

                    else:

                        palette.append((
                            (p0[0] + p1[0]) // 2,
                            (p0[1] + p1[1]) // 2,
                            (p0[2] + p1[2]) // 2,
                            255
                        ))

                        palette.append(
                            (0,0,0,0)
                        )

                    bits_out = bytearray()

                    for row in range(4):

                        bits = 0

                        for col in range(4):

                            px = block[
                                row * 4 + col
                            ]

                            best = 0
                            best_d = 999999999

                            max_idx = (
                                2 if c0 <= c1
                                else 3
                            )

                            if (
                                alpha_mode and
                                px[3] < 128 and
                                c0 <= c1
                            ):
                                best = 3

                            else:

                                for k in range(max_idx + 1):

                                    pr, pg, pb, pa = palette[k]

                                    dr = px[0] - pr
                                    dg = px[1] - pg
                                    db = px[2] - pb

                                    d = (
                                        dr*dr +
                                        dg*dg +
                                        db*db
                                    )

                                    if d < best_d:

                                        best_d = d
                                        best = k

                            bits |= (
                                (best & 3)
                                << (6 - col * 2)
                            )

                        bits_out.append(bits)

                    out += c0.to_bytes(2, "big")
                    out += c1.to_bytes(2, "big")
                    out += bits_out

    return bytes(out)

# =========================================================
# RGBA32
# =========================================================

def decode_rgba32(data, width, height):

    img = Image.new(
        "RGBA",
        (width, height)
    )

    pixels = img.load()

    sw = (width + 3) & ~3
    sh = (height + 3) & ~3

    offset = 0

    for y in range(0, sh, 4):

        for x in range(0, sw, 4):

            for dy in range(4):

                for dx in range(4):

                    px = x + dx
                    py = y + dy

                    a = data[offset]
                    r = data[offset + 1]

                    g = data[offset + 32]
                    b = data[offset + 33]

                    offset += 2

                    if (
                        px < width and
                        py < height
                    ):
                        pixels[px, py] = (
                            r, g, b, a
                        )

            offset += 32

    return img

def encode_rgba32(img, width, height):

    pixels = img.load()

    sw = (width + 3) & ~3
    sh = (height + 3) & ~3

    out = bytearray(sw * sh * 4)

    offset = 0

    for y in range(0, sh, 4):

        for x in range(0, sw, 4):

            for dy in range(4):

                for dx in range(4):

                    px = x + dx
                    py = y + dy

                    if (
                        px < width and
                        py < height
                    ):
                        r, g, b, a = pixels[px, py]
                    else:
                        r = g = b = a = 0

                    out[offset] = a
                    out[offset + 1] = r

                    out[offset + 32] = g
                    out[offset + 33] = b

                    offset += 2

            offset += 32

    return bytes(out)

# =========================================================
# RGB5A3
# =========================================================

def decode_rgb5a3(data, width, height):

    img = Image.new(
        "RGBA",
        (width, height)
    )

    pixels = img.load()

    bw, bh = block_size(16)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    for y in range(sh):

        for x in range(sw):

            off = offset_bpp16(x, y, sw)

            if off + 1 >= len(data):
                continue

            p = (
                (data[off] << 8) |
                data[off + 1]
            )

            rgba = decode_rgb5a3_pixel(p)

            if x < width and y < height:
                pixels[x, y] = rgba

    return img

def encode_rgb5a3(img, width, height, template=None):

    pixels = img.load()

    bw, bh = block_size(16)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    out = bytearray(sw * sh * 2)

    for y in range(sh):

        for x in range(sw):

            if (
                x < width and
                y < height
            ):
                r, g, b, a = pixels[x, y]
            else:
                r = g = b = a = 0

            p = encode_rgb5a3_pixel(
                r, g, b, a
            )

            off = offset_bpp16(x, y, sw)

            out[off] = (p >> 8) & 0xFF
            out[off + 1] = p & 0xFF

    return bytes(out)

# =========================================================
# IA8
# =========================================================

def decode_ia8(data, width, height):

    img = Image.new(
        "RGBA",
        (width, height)
    )

    pixels = img.load()

    bw, bh = block_size(16)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    for y in range(sh):

        for x in range(sw):

            off = offset_bpp16(x, y, sw)

            if off + 1 >= len(data):
                continue

            i = data[off + 1]
            a = data[off]

            if x < width and y < height:

                pixels[x, y] = (
                    i, i, i, a
                )

    return img

def encode_ia8(img, width, height):

    pixels = img.load()

    bw, bh = block_size(16)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    out = bytearray(sw * sh * 2)

    for y in range(sh):

        for x in range(sw):

            if (
                x < width and
                y < height
            ):
                r, g, b, a = pixels[x, y]
            else:
                r = g = b = a = 0

            i = (r + g + b) // 3

            off = offset_bpp16(x, y, sw)

            out[off] = a
            out[off + 1] = i

    return bytes(out)

# =========================================================
# I8
# =========================================================

def decode_i8(data, width, height):

    img = Image.new(
        "RGBA",
        (width, height)
    )

    pixels = img.load()

    bw, bh = block_size(8)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    for y in range(sh):

        for x in range(sw):

            off = offset_bpp8(x, y, sw)

            if off >= len(data):
                continue

            v = data[off]

            if x < width and y < height:

                pixels[x, y] = (
                    v, v, v, 255
                )

    return img

def encode_i8(img, width, height):

    pixels = img.load()

    bw, bh = block_size(8)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    out = bytearray(sw * sh)

    for y in range(sh):

        for x in range(sw):

            if (
                x < width and
                y < height
            ):
                r, g, b, a = pixels[x, y]
            else:
                r = g = b = a = 0

            v = (r + g + b) // 3

            out[
                offset_bpp8(x, y, sw)
            ] = v

    return bytes(out)

# =========================================================
# C8
# =========================================================

def decode_c8(data, palette, width, height):

    pal = []

    for i in range(256):

        p = (
            (palette[i * 2] << 8) |
            palette[i * 2 + 1]
        )

        pal.append(
            decode_rgb5a3_pixel(p)
        )

    img = Image.new(
        "RGBA",
        (width, height)
    )

    pixels = img.load()

    bw, bh = block_size(8)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    for y in range(sh):

        for x in range(sw):

            off = offset_bpp8(x, y, sw)

            if off >= len(data):
                continue

            idx = data[off]

            if x < width and y < height:
                pixels[x, y] = pal[idx]

    return img

def encode_c8(
    img,
    palette,
    width,
    height,
    template=None
):

    pal = []

    for i in range(256):

        p = (
            (palette[i * 2] << 8) |
            palette[i * 2 + 1]
        )

        pal.append(
            decode_rgb5a3_pixel(p)
        )

    pixels = img.load()

    bw, bh = block_size(8)

    sw = ((width + bw - 1) // bw) * bw
    sh = ((height + bh - 1) // bh) * bh

    out = bytearray(sw * sh)

    for y in range(sh):

        for x in range(sw):

            if (
                x < width and
                y < height
            ):
                r, g, b, a = pixels[x, y]
            else:
                r = g = b = a = 0

            best = 0
            best_d = 999999999

            for i, p in enumerate(pal):

                dr = r - p[0]
                dg = g - p[1]
                db = b - p[2]
                da = a - p[3]

                d = (
                    dr*dr +
                    dg*dg +
                    db*db +
                    da*da
                )

                if d < best_d:

                    best_d = d
                    best = i

            out[
                offset_bpp8(x, y, sw)
            ] = best

    return bytes(out)