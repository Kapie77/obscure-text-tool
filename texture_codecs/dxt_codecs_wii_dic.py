from PIL import Image

# ==============================
#           ENCODERS
# ==============================
def rgb565_pack(r, g, b):
    return (
        ((r * 31 + 127) // 255) << 11 |
        ((g * 63 + 127) // 255) << 5 |
        ((b * 31 + 127) // 255)
    )

def rgb565_unpack(c):
    return (
        ((c >> 11) & 0x1F) * 255 // 31,
        ((c >> 5) & 0x3F) * 255 // 63,
        (c & 0x1F) * 255 // 31,
        255
    )

def encode_dxt1_block(block):

    opaque = [p for p in block if p[3] >= 128]

    alpha_mode = len(opaque) != 16

    if not opaque:
        c0 = 0
        c1 = 0
    else:

        # média
        mr = sum(p[0] for p in opaque) / len(opaque)
        mg = sum(p[1] for p in opaque) / len(opaque)
        mb = sum(p[2] for p in opaque) / len(opaque)

        # PCA simples
        vx = 1.0
        vy = 1.0
        vz = 1.0

        min_dot = 999999999
        max_dot = -999999999

        min_color = opaque[0]
        max_color = opaque[0]

        for p in opaque:

            dot = (
                (p[0] - mr) * vx +
                (p[1] - mg) * vy +
                (p[2] - mb) * vz
            )

            if dot < min_dot:
                min_dot = dot
                min_color = p

            if dot > max_dot:
                max_dot = dot
                max_color = p

        c0 = rgb565_pack(
            max_color[0],
            max_color[1],
            max_color[2]
        )

        c1 = rgb565_pack(
            min_color[0],
            min_color[1],
            min_color[2]
        )

        if alpha_mode and c0 > c1:
            c0, c1 = c1, c0

        elif not alpha_mode and c0 < c1:
            c0, c1 = c1, c0

    p0 = rgb565_unpack(c0)
    p1 = rgb565_unpack(c1)

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

        palette.append((0,0,0,0))

    bits = 0

    for i, px in enumerate(block):

        best = 0
        best_d = 999999999

        max_index = 2 if c0 <= c1 else 3

        if alpha_mode and px[3] < 128 and c0 <= c1:
            best = 3
        else:

            for k in range(max_index + 1):

                pr, pg, pb, pa = palette[k]

                dr = px[0] - pr
                dg = px[1] - pg
                db = px[2] - pb

                d = dr*dr + dg*dg + db*db

                if d < best_d:
                    best_d = d
                    best = k

        bits |= (best & 3) << (30 - i * 2)

    out = bytearray()

    out += c0.to_bytes(2, "big")
    out += c1.to_bytes(2, "big")
    out += bits.to_bytes(4, "big")

    return out

def encode_cmpr(img, width, height, original=None):

    if isinstance(img, Image.Image):
        pixels = img.load()
    else:
        raise Exception("encode_cmpr requires PIL Image")

    out = bytearray()

    sw = (width + 7) & ~7
    sh = (height + 7) & ~7

    for by in range(0, sh, 8):
        for bx in range(0, sw, 8):

            for sub in range(4):

                sx = bx + (sub & 1) * 4
                sy = by + (sub >> 1) * 4

                block = []

                for y in range(4):
                    for x in range(4):

                        px = sx + x
                        py = sy + y

                        if px < width and py < height:
                            block.append(
                                pixels[px, py]
                            )
                        else:
                            block.append((0,0,0,0))

                out += encode_dxt1_block(block)

    return bytes(out)
# ==============================
# CMPR (DXT1-like) decoder
# ==============================
def decode_cmpr_block(block):
    c0 = (block[0] << 8) | block[1]
    c1 = (block[2] << 8) | block[3]

    def decode_565(c):
        r = ((c >> 11) & 31) * 255 // 31
        g = ((c >> 5) & 63) * 255 // 63
        b = (c & 31) * 255 // 31
        return (r, g, b, 255)

    p0 = decode_565(c0)
    p1 = decode_565(c1)

    if c0 > c1:
        p2 = tuple((2*p0[i] + p1[i]) // 3 for i in range(4))
        p3 = tuple((2*p1[i] + p0[i]) // 3 for i in range(4))
    else:
        p2 = tuple((p0[i] + p1[i]) // 2 for i in range(4))
        p3 = (0, 0, 0, 0)

    palette = [p0, p1, p2, p3]

    pixels = []

    offset = 4
    for row in range(4):
        bits = block[offset]
        offset += 1

        for col in range(4):
            idx = (bits >> (6 - col*2)) & 3
            pixels.append(palette[idx])

    return pixels


def decode_cmpr(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    offset = 0

    for y in range(0, height, 8):
        for x in range(0, width, 8):

            for by in range(2):
                for bx in range(2):

                    block = data[offset:offset+8]
                    offset += 8

                    block_pixels = decode_cmpr_block(block)

                    i = 0
                    for dy in range(4):
                        for dx in range(4):
                            px = x + bx*4 + dx
                            py = y + by*4 + dy

                            if px < width and py < height:
                                pixels[px, py] = block_pixels[i]
                            i += 1

    return img