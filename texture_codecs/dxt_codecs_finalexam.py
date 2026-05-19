# ==============================
#           DECODERS
# ==============================
def decode_dxt1(raw, width, height):
    def rgb565(c):
        r = ((c >> 11) & 0x1F) * 255 // 31
        g = ((c >> 5) & 0x3F) * 255 // 63
        b = (c & 0x1F) * 255 // 31
        return b, g, r

    out = bytearray(width * height * 4)
    pos = 0

    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4

    for by in range(blocks_y):
        for bx in range(blocks_x):
            if pos + 8 > len(raw):
                return out

            c0 = raw[pos] | (raw[pos+1] << 8)
            c1 = raw[pos+2] | (raw[pos+3] << 8)

            b0,g0,r0 = rgb565(c0)
            b1,g1,r1 = rgb565(c1)

            colors = [
                (b0,g0,r0,255),
                (b1,g1,r1,255),
            ]

            if c0 > c1:
                colors.append(((2*b0+b1)//3,(2*g0+g1)//3,(2*r0+r1)//3,255))
                colors.append(((b0+2*b1)//3,(g0+2*g1)//3,(r0+2*r1)//3,255))
            else:
                colors.append(((b0+b1)//2,(g0+g1)//2,(r0+r1)//2,255))
                colors.append((0,0,0,0))

            bits = int.from_bytes(raw[pos+4:pos+8], "little")

            for y in range(4):
                for x in range(4):
                    px = bx*4 + x
                    py = by*4 + y

                    if px >= width or py >= height:
                        continue

                    idx = (bits >> (2*(y*4+x))) & 3
                    b,g,r,a = colors[idx]

                    i = (py*width + px)*4
                    out[i:i+4] = bytes([b,g,r,a])

            pos += 8

    return out

def decode_dxt3(raw, width, height):

    def rgb565(c):
        r = ((c >> 11) & 0x1F) * 255 // 31
        g = ((c >> 5) & 0x3F) * 255 // 63
        b = (c & 0x1F) * 255 // 31
        return b, g, r

    out = bytearray(width * height * 4)

    pos = 0

    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4

    for by in range(blocks_y):
        for bx in range(blocks_x):

            if pos + 16 > len(raw):
                return out

            alpha_bits = int.from_bytes(raw[pos:pos+8], "little")

            c0 = raw[pos+8] | (raw[pos+9] << 8)
            c1 = raw[pos+10] | (raw[pos+11] << 8)

            b0,g0,r0 = rgb565(c0)
            b1,g1,r1 = rgb565(c1)

            colors = [
                (b0,g0,r0),
                (b1,g1,r1),
                ((2*b0+b1)//3,(2*g0+g1)//3,(2*r0+r1)//3),
                ((b0+2*b1)//3,(g0+2*g1)//3,(r0+2*r1)//3),
            ]

            bits = int.from_bytes(raw[pos+12:pos+16], "little")

            for y in range(4):
                for x in range(4):

                    px = bx*4 + x
                    py = by*4 + y

                    if px >= width or py >= height:
                        continue

                    idx = y*4 + x

                    cidx = (bits >> (idx*2)) & 3
                    a = ((alpha_bits >> (idx*4)) & 0xF) * 17

                    b,g,r = colors[cidx]

                    dst = (py*width + px) * 4

                    out[dst:dst+4] = bytes([b,g,r,a])

            pos += 16

    return out


def decode_dxt5(raw, width, height):
    def rgb565(c):
        r = ((c >> 11) & 0x1F) * 255 // 31
        g = ((c >> 5) & 0x3F) * 255 // 63
        b = (c & 0x1F) * 255 // 31
        return b, g, r

    out = bytearray(width * height * 4)
    pos = 0

    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4

    for by in range(blocks_y):
        for bx in range(blocks_x):
            if pos + 16 > len(raw):
                return out

            # =========================
            # ALPHA BLOCK (8 bytes)
            # =========================
            a0 = raw[pos + 0]
            a1 = raw[pos + 1]

            alpha = [0] * 8
            alpha[0] = a0
            alpha[1] = a1

            if a0 > a1:
                for i in range(1, 7):
                    alpha[i + 1] = ((7 - i) * a0 + i * a1) // 7
            else:
                for i in range(1, 5):
                    alpha[i + 1] = ((5 - i) * a0 + i * a1) // 5
                alpha[6] = 0
                alpha[7] = 255

            abits = 0
            for i in range(6):
                abits |= raw[pos + 2 + i] << (8 * i)

            # =========================
            # COLOR BLOCK (DXT1)
            # =========================
            c0 = raw[pos + 8] | (raw[pos + 9] << 8)
            c1 = raw[pos + 10] | (raw[pos + 11] << 8)

            b0, g0, r0 = rgb565(c0)
            b1, g1, r1 = rgb565(c1)

            colors = [
                (b0, g0, r0),
                (b1, g1, r1),
                ((2*b0 + b1)//3, (2*g0 + g1)//3, (2*r0 + r1)//3),
                ((b0 + 2*b1)//3, (g0 + 2*g1)//3, (r0 + 2*r1)//3),
            ]

            cbits = int.from_bytes(raw[pos + 12:pos + 16], "little")

            # =========================
            # WRITE PIXELS
            # =========================
            for y in range(4):
                for x in range(4):
                    px = bx * 4 + x
                    py = by * 4 + y

                    if px >= width or py >= height:
                        continue

                    idx = y * 4 + x

                    c_idx = (cbits >> (idx * 2)) & 3
                    a_idx = (abits >> (idx * 3)) & 7

                    b, g, r = colors[c_idx]
                    a = alpha[a_idx]

                    i = (py * width + px) * 4
                    out[i:i+4] = bytes([b, g, r, a])

            pos += 16

    return out

def compute_mip0_size(width, height, format_tag):

    if format_tag in ["DXT1", "1TXD", "TXD1"]:
        return ((width + 3) // 4) * ((height + 3) // 4) * 8

    elif format_tag in ["DXT3", "3TXD", "TXD3",
                         "DXT5", "5TXD", "TXD5"]:
        return ((width + 3) // 4) * ((height + 3) // 4) * 16

    else:
        return width * height * 4

# =========================================================
#                        ENCODERS
# =========================================================

def rgb_to_565(r, g, b):
    return (
        ((r * 31 + 127) // 255) << 11 |
        ((g * 63 + 127) // 255) << 5  |
        ((b * 31 + 127) // 255)
    )


# =========================================================
# DXT1
# =========================================================
def encode_dxt1(rgba, width, height):

    out = bytearray()

    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4

    for by in range(blocks_y):
        for bx in range(blocks_x):

            pixels = []

            rmin = gmin = bmin = 255
            rmax = gmax = bmax = 0

            for y in range(4):
                for x in range(4):

                    sx = min(bx * 4 + x, width - 1)
                    sy = min(by * 4 + y, height - 1)

                    i = (sy * width + sx) * 4

                    r = rgba[i + 0]
                    g = rgba[i + 1]
                    b = rgba[i + 2]
                    a = rgba[i + 3]

                    pixels.append((r, g, b, a))

                    rmin = min(rmin, r)
                    gmin = min(gmin, g)
                    bmin = min(bmin, b)

                    rmax = max(rmax, r)
                    gmax = max(gmax, g)
                    bmax = max(bmax, b)

            c0 = rgb_to_565(rmax, gmax, bmax)
            c1 = rgb_to_565(rmin, gmin, bmin)

            if c0 == c1:
                if c0 > 0:
                    c1 -= 1
                else:
                    c0 += 1

            if c0 < c1:
                c0, c1 = c1, c0

            b0, g0, r0 = (
                (c0 & 0x1F) * 255 // 31,
                ((c0 >> 5) & 0x3F) * 255 // 63,
                ((c0 >> 11) & 0x1F) * 255 // 31
            )

            b1, g1, r1 = (
                (c1 & 0x1F) * 255 // 31,
                ((c1 >> 5) & 0x3F) * 255 // 63,
                ((c1 >> 11) & 0x1F) * 255 // 31
            )

            palette = [
                (r0, g0, b0),
                (r1, g1, b1),
                (
                    (2*r0+r1)//3,
                    (2*g0+g1)//3,
                    (2*b0+b1)//3
                ),
                (
                    (r0+2*r1)//3,
                    (g0+2*g1)//3,
                    (b0+2*b1)//3
                )
            ]

            bits = 0

            for i, (r, g, b, a) in enumerate(pixels):

                best = 0
                best_d = 999999999

                for k, (pr, pg, pb) in enumerate(palette):

                    dr = r - pr
                    dg = g - pg
                    db = b - pb

                    d = dr*dr + dg*dg + db*db

                    if d < best_d:
                        best_d = d
                        best = k

                bits |= best << (i * 2)

            out += c0.to_bytes(2, "little")
            out += c1.to_bytes(2, "little")
            out += bits.to_bytes(4, "little")

    return bytes(out)


# =========================================================
# DXT5
# =========================================================
def encode_dxt5(rgba, width, height):

    out = bytearray()

    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4

    for by in range(blocks_y):
        for bx in range(blocks_x):

            pixels = []

            amin = 255
            amax = 0

            for y in range(4):
                for x in range(4):

                    sx = min(bx * 4 + x, width - 1)
                    sy = min(by * 4 + y, height - 1)

                    i = (sy * width + sx) * 4

                    r = rgba[i + 0]
                    g = rgba[i + 1]
                    b = rgba[i + 2]
                    a = rgba[i + 3]

                    pixels.append((r, g, b, a))

                    amin = min(amin, a)
                    amax = max(amax, a)

            if amax == amin:
                if amax < 255:
                    amax += 1
                else:
                    amin -= 1

            alpha_palette = [0] * 8

            alpha_palette[0] = amax
            alpha_palette[1] = amin

            for i in range(1, 7):
                alpha_palette[i + 1] = (
                    ((7 - i) * amax + i * amin) // 7
                )

            abits = 0

            for i, (_, _, _, a) in enumerate(pixels):

                best = 0
                best_d = 999999

                for k in range(8):

                    d = abs(a - alpha_palette[k])

                    if d < best_d:
                        best_d = d
                        best = k

                abits |= best << (i * 3)

            out.append(amax)
            out.append(amin)

            for i in range(6):
                out.append((abits >> (8 * i)) & 0xFF)

            color_block = encode_dxt1_block(pixels)

            out += color_block

    return bytes(out)


# =========================================================
# DXT1 BLOCK HELPER
# =========================================================
def encode_dxt1_block(pixels):

    rmin = gmin = bmin = 255
    rmax = gmax = bmax = 0

    for r, g, b, a in pixels:

        rmin = min(rmin, r)
        gmin = min(gmin, g)
        bmin = min(bmin, b)

        rmax = max(rmax, r)
        gmax = max(gmax, g)
        bmax = max(bmax, b)

    c0 = rgb_to_565(rmax, gmax, bmax)
    c1 = rgb_to_565(rmin, gmin, bmin)

    if c0 == c1:
        if c0 > 0:
            c1 -= 1
        else:
            c0 += 1

    if c0 < c1:
        c0, c1 = c1, c0

    b0, g0, r0 = (
        (c0 & 0x1F) * 255 // 31,
        ((c0 >> 5) & 0x3F) * 255 // 63,
        ((c0 >> 11) & 0x1F) * 255 // 31
    )

    b1, g1, r1 = (
        (c1 & 0x1F) * 255 // 31,
        ((c1 >> 5) & 0x3F) * 255 // 63,
        ((c1 >> 11) & 0x1F) * 255 // 31
    )

    palette = [
        (r0, g0, b0),
        (r1, g1, b1),
        ((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3),
        ((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3)
    ]

    bits = 0

    for i, (r, g, b, a) in enumerate(pixels):

        best = 0
        best_d = 999999999

        for k, (pr, pg, pb) in enumerate(palette):

            dr = r - pr
            dg = g - pg
            db = b - pb

            d = dr*dr + dg*dg + db*db

            if d < best_d:
                best_d = d
                best = k

        bits |= best << (i * 2)

    out = bytearray()

    out += c0.to_bytes(2, "little")
    out += c1.to_bytes(2, "little")
    out += bits.to_bytes(4, "little")

    return out


# =========================================================
# DXT3
# =========================================================
def encode_dxt3(rgba, width, height):

    dxt5 = bytearray(encode_dxt5(rgba, width, height))

    blocks_x = (width + 3) // 4

    for blk_off in range(0, len(dxt5), 16):

        block_idx = blk_off // 16

        bx = block_idx % blocks_x
        by = block_idx // blocks_x

        abits = 0

        for y in range(4):
            for x in range(4):

                sx = min(bx * 4 + x, width - 1)
                sy = min(by * 4 + y, height - 1)

                i = (sy * width + sx) * 4

                a = rgba[i + 3]

                a4 = (a + 8) // 17

                if a4 > 15:
                    a4 = 15

                abits |= a4 << ((y * 4 + x) * 4)

        for i in range(8):
            dxt5[blk_off + i] = (abits >> (i * 8)) & 0xFF

    return bytes(dxt5)
