from PIL import Image
from utils.palettes import build_palette

# ==============================
#        DECODERS (WII)
# ==============================

def offset_c4(x, y, width):
    tile_x = x // 8
    tile_y = y // 8

    tiles_per_row = width // 8

    tile_index = tile_y * tiles_per_row + tile_x

    in_tile_x = x % 8
    in_tile_y = y % 8

    byte_index = tile_index * 32 + (in_tile_y * 4) + (in_tile_x // 2)

    return byte_index

def offset_bpp8(x, y, w):
    return ((y & ~3) * w) + ((x & ~7) * 4) + ((y & 3) * 8) + (x & 7)


def decode_ia8(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            for y in range(4):
                for x in range(4):
                    if pos + 1 >= len(data):
                        return img

                    px = bx + x
                    py = by + y

                    a = data[pos]
                    i = data[pos + 1]
                    pos += 2

                    if px < width and py < height:
                        pixels[px, py] = (i, i, i, a)

    return img


def align(val, alignment):
    return (val + alignment - 1) & ~(alignment - 1)


def decode_rgba8(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    sw = (width + 3) & ~3
    sh = (height + 3) & ~3

    off = 0

    for y in range(0, sh, 4):
        for x in range(0, sw, 4):

            for dy in range(4):
                for dx in range(4):
                    if x + dx >= width or y + dy >= height:
                        off += 2
                        continue

                    a = data[off]
                    r = data[off + 1]
                    g = data[off + 32]
                    b = data[off + 33]

                    pixels[x + dx, y + dy] = (r, g, b, a)

                    off += 2

            off += 32

    return img

def decode_i8(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for by in range(0, height, 4):
        for bx in range(0, width, 8):
            for y in range(4):
                for x in range(8):
                    if pos >= len(data):
                        return img

                    px = bx + x
                    py = by + y

                    v = data[pos]
                    pos += 1

                    if px < width and py < height:
                        pixels[px, py] = (v, v, v, 255)

    return img

def decode_rgb5a3(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            for y in range(4):
                for x in range(4):
                    if pos + 1 >= len(data):
                        return img

                    px = bx + x
                    py = by + y

                    p = (data[pos] << 8) | data[pos + 1]
                    pos += 2

                    if px >= width or py >= height:
                        continue

                    if p & 0x8000:
                        r = ((p >> 10) & 0x1F) * 255 // 31
                        g = ((p >> 5) & 0x1F) * 255 // 31
                        b = (p & 0x1F) * 255 // 31
                        a = 255
                    else:
                        a = ((p >> 12) & 0x7) * 255 // 7
                        r = ((p >> 8) & 0xF) * 255 // 15
                        g = ((p >> 4) & 0xF) * 255 // 15
                        b = (p & 0xF) * 255 // 15

                    pixels[px, py] = (r, g, b, a)

    return img

def decode_c4(data, palette_data, width, height, pal_format):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pal = build_palette(palette_data, pal_format)

    for y in range(height):
        for x in range(width):
            sw = align(width, 8)
            off = offset_c4(x, y, sw)

            if off >= len(data):
                continue

            byte = data[off]

            if x & 1:
                idx = byte & 0x0F
            else:
                idx = byte >> 4

            if idx < len(pal):
                pixels[x, y] = pal[idx]

    return img

def decode_c8(data, palette_data, width, height, pal_format):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    sw = align(width, 8)
    pal = build_palette(palette_data, pal_format)

    for y in range(height):
        for x in range(width):
            off = offset_bpp8(x, y, sw)

            if off >= len(data):
                continue

            idx = data[off]

            if idx < len(pal):
                pixels[x, y] = pal[idx]

    return img