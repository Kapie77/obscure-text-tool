from PIL import Image

# ========================================
#   DECODERS FINAL EXAM XBOX 360 (.HVT)
# ========================================
def decode_bgra(raw, width, height):
    return raw  # já está no formato correto


    
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

def morton2(x, y):

    answer = 0

    for i in range(16):
        answer |= ((x >> i) & 1) << (2 * i)
        answer |= ((y >> i) & 1) << (2 * i + 1)

    return answer


def morton_index_rect(x, y, width, height):
    return morton2(x, y)

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


def decode_argb_be(raw, width, height):

    out = bytearray(width * height * 4)

    for i in range(width * height):

        a = raw[i*4 + 0]
        r = raw[i*4 + 1]
        g = raw[i*4 + 2]
        b = raw[i*4 + 3]

        out[i*4 + 0] = b
        out[i*4 + 1] = g
        out[i*4 + 2] = r
        out[i*4 + 3] = a

    return bytes(out)