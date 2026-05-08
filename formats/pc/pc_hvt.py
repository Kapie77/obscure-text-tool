# ===============================
#   DECODERS FINAL EXAM (.HVT)
# ===============================
def decode_bgra(raw, width, height):
    return raw  # já está no formato correto

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
    
def decode_bgrx(raw, width, height):
    pixels = width * height
    out = bytearray(pixels * 4)

    for i in range(pixels):
        b = raw[i*4 + 0]
        g = raw[i*4 + 1]
        r = raw[i*4 + 2]
        # raw[i*4 + 3] = X (ignorado)

        out[i*4 + 0] = b
        out[i*4 + 1] = g
        out[i*4 + 2] = r
        out[i*4 + 3] = 255  # alpha forçado

    return bytes(out)

def decode_rgba_ps3_swizzled(raw, width, height):

    out = bytearray(width * height * 4)

    for y in range(height):
        for x in range(width):

            src = morton_index_rect(x, y, width, height) * 4
            dst = (y * width + x) * 4

            if src + 3 >= len(raw):
                continue

            # PS3 armazena RGBA
            out[dst + 0] = raw[src + 2]  # B
            out[dst + 1] = raw[src + 1]  # G
            out[dst + 2] = raw[src + 0]  # R
            out[dst + 3] = raw[src + 3]  # A

    return bytes(out)