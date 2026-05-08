from PIL import Image

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

# ==============================
# Texture helpers
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