from PIL import Image

# ==============================
#        DECODERS (XBOX)
# ==============================
def xbox_swizzle_offset(x, y, w, h):
    offset = 0
    xs = 0
    ys = 0
    dest = 0

    while (1 << xs) < w or (1 << ys) < h:
        if (1 << xs) < w:
            offset |= ((x >> xs) & 1) << dest
            xs += 1
            dest += 1

        if (1 << ys) < h:
            offset |= ((y >> ys) & 1) << dest
            ys += 1
            dest += 1

    return offset

def decode_xbox_r5g6b5(data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            s = xbox_swizzle_offset(x, y, width, height) * 2

            if s + 1 >= len(data):
                continue

            v = data[s] | (data[s+1] << 8)

            r = ((v >> 11) & 0x1F) * 255 // 31
            g = ((v >> 5) & 0x3F) * 255 // 63
            b = (v & 0x1F) * 255 // 31

            pixels[x, y] = (r, g, b, 255)

    return img

def decode_xbox_a8r8g8b8(data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            s = xbox_swizzle_offset(x, y, width, height) * 4

            if s + 3 >= len(data):
                continue

            b = data[s + 0]
            g = data[s + 1]
            r = data[s + 2]
            a = data[s + 3]

            pixels[x, y] = (r, g, b, a)

    return img

def decode_xbox_a1r5g5b5(data, width, height):

    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            s = xbox_swizzle_offset(x, y, width, height) * 2

            if s + 1 >= len(data):
                continue

            v = data[s] | (data[s+1] << 8)

            r = ((v >> 10) & 0x1F) * 255 // 31
            g = ((v >> 5) & 0x1F) * 255 // 31
            b = (v & 0x1F) * 255 // 31
            a = 255 if (v & 0x8000) else 0

            pixels[x, y] = (r, g, b, a)

    return img

# ==============================
#         ENCODERS
# ==============================
def encode_xbox_r5g6b5(pixels, width, height):

    out = bytearray(width * height * 2)

    for y in range(height):
        for x in range(width):

            src = (y * width + x) * 4

            r = pixels[src + 0]
            g = pixels[src + 1]
            b = pixels[src + 2]

            v = (
                ((r * 31 // 255) << 11) |
                ((g * 63 // 255) << 5) |
                ((b * 31 // 255))
            )

            d = xbox_swizzle_offset(x, y, width, height) * 2

            out[d + 0] = v & 0xFF
            out[d + 1] = (v >> 8) & 0xFF

    return bytes(out)


def encode_xbox_a1r5g5b5(pixels, width, height):

    out = bytearray(width * height * 2)

    for y in range(height):
        for x in range(width):

            src = (y * width + x) * 4

            r = pixels[src + 0]
            g = pixels[src + 1]
            b = pixels[src + 2]
            a = pixels[src + 3]

            v = (
                ((1 if a >= 128 else 0) << 15) |
                ((r * 31 // 255) << 10) |
                ((g * 31 // 255) << 5) |
                ((b * 31 // 255))
            )

            d = xbox_swizzle_offset(x, y, width, height) * 2

            out[d + 0] = v & 0xFF
            out[d + 1] = (v >> 8) & 0xFF

    return bytes(out)


def encode_xbox_a8r8g8b8(pixels, width, height):

    out = bytearray(width * height * 4)

    for y in range(height):
        for x in range(width):

            src = (y * width + x) * 4

            r = pixels[src + 0]
            g = pixels[src + 1]
            b = pixels[src + 2]
            a = pixels[src + 3]

            d = xbox_swizzle_offset(x, y, width, height) * 4

            out[d + 0] = b
            out[d + 1] = g
            out[d + 2] = r
            out[d + 3] = a

    return bytes(out)