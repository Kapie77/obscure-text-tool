from PIL import Image


# ============================
#   SWIZZLE AND UNSWIZZLE
# ============================
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

    return swizzled[:expected_size]

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

    return linear

# ==============================
#        DECODERS (PSP)
# ==============================
def decode_psp_8bpp(pixel_data, palette_data, width, height):

    img = Image.new("RGBA", (width, height))

    pixels = img.load()

    indices = unswizzle_psp(pixel_data, width, height, 8)

    palette = []

    for i in range(256):

        r = palette_data[i*4 + 0]
        g = palette_data[i*4 + 1]
        b = palette_data[i*4 + 2]
        a = palette_data[i*4 + 3]

        palette.append((r, g, b, a))

    for y in range(height):
        for x in range(width):

            idx = indices[y * width + x]

            pixels[x, y] = palette[idx]

    return img

def decode_psp_4bpp(pixel_data, palette_data, width, height):

    img = Image.new("RGBA", (width, height))

    pixels = img.load()

    linear_packed = unswizzle_psp(pixel_data, width, height, 4)

    indices = []

    for b in linear_packed:
        indices.append(b & 0x0F)
        indices.append((b >> 4) & 0x0F)

    palette = []

    for i in range(16):

        r = palette_data[i*4 + 0]
        g = palette_data[i*4 + 1]
        b = palette_data[i*4 + 2]
        a = palette_data[i*4 + 3]

        palette.append((r, g, b, a))

    for y in range(height):
        for x in range(width):

            idx = indices[y * width + x]

            pixels[x, y] = palette[idx]

    return img