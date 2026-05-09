from PIL import Image
from utils.palettes import build_palette

# ==============================
#          HELPERS
# ==============================

def align(val, alignment):
    return (val + alignment - 1) & ~(alignment - 1)

def offset_c4(x, y, width):
    tile_x = x // 8
    tile_y = y // 8
    tiles_per_row = width // 8
    tile_index = tile_y * tiles_per_row + tile_x
    in_tile_x = x % 8
    in_tile_y = y % 8
    return tile_index * 32 + (in_tile_y * 4) + (in_tile_x // 2)

def offset_bpp8(x, y, w):
    return ((y & ~3) * w) + ((x & ~7) * 4) + ((y & 3) * 8) + (x & 7)

# Crop RGBA buffer to BGRA PIL Image
def crop_to_image(rgba_buf, sw, sh, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            i = (y * sw + x) * 4
            pixels[x, y] = (rgba_buf[i+0], rgba_buf[i+1], rgba_buf[i+2], rgba_buf[i+3])
    return img

# ==============================
#          DECODERS
# ==============================

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
                    v = data[pos]
                    pos += 1
                    px, py = bx + x, by + y
                    if px < width and py < height:
                        pixels[px, py] = (v, v, v, 255)
    return img

def encode_i8(img):
    width, height = img.size
    pixels = img.load()
    sw = align(width, 8)
    sh = align(height, 4)
    buf = bytearray(sw*sh)
    pos = 0
    for by in range(0, sh, 4):
        for bx in range(0, sw, 8):
            for y in range(4):
                for x in range(8):
                    px, py = bx + x, by + y
                    v = 0
                    if px < width and py < height:
                        r, g, b, a = pixels[px, py]
                        v = (r + g + b) // 3
                    buf[pos] = v
                    pos += 1
    return bytes(buf)

def decode_ia8(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()
    pos = 0
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            for y in range(4):
                for x in range(4):
                    if pos+1 >= len(data):
                        return img
                    a = data[pos]
                    i = data[pos+1]
                    pos += 2
                    px, py = bx + x, by + y
                    if px < width and py < height:
                        pixels[px, py] = (i, i, i, a)
    return img

def encode_ia8(img):
    width, height = img.size
    pixels = img.load()
    sw = align(width, 4)
    sh = align(height, 4)
    buf = bytearray(sw*sh*2)
    pos = 0
    for by in range(0, sh, 4):
        for bx in range(0, sw, 4):
            for y in range(4):
                for x in range(4):
                    px, py = bx + x, by + y
                    r = g = b = a = 0
                    if px < width and py < height:
                        r, g, b, a = pixels[px, py]
                    i = (r + g + b)//3
                    buf[pos] = a
                    buf[pos+1] = i
                    pos += 2
    return bytes(buf)

def decode_rgb5a3(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()
    pos = 0
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            for y in range(4):
                for x in range(4):
                    if pos+1 >= len(data):
                        return img
                    p = (data[pos] << 8) | data[pos+1]
                    pos += 2
                    px, py = bx + x, by + y
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

def encode_rgb5a3(img):
    width, height = img.size
    pixels = img.load()
    sw = align(width, 4)
    sh = align(height, 4)
    buf = bytearray(sw*sh*2)
    pos = 0
    for by in range(0, sh, 4):
        for bx in range(0, sw, 4):
            for y in range(4):
                for x in range(4):
                    px, py = bx+x, by+y
                    r = g = b = a = 0
                    if px < width and py < height:
                        r, g, b, a = pixels[px, py]
                    if a >= 248:  # fully opaque
                        p = 0x8000 | ((r*31)//255 <<10) | ((g*31)//255 <<5) | ((b*31)//255)
                    else:
                        p = ((a*7)//255 <<12) | ((r*15)//255 <<8) | ((g*15)//255 <<4) | ((b*15)//255)
                    buf[pos] = (p >> 8) & 0xFF
                    buf[pos+1] = p & 0xFF
                    pos += 2
    return bytes(buf)

def decode_rgba8(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()
    sw = align(width, 4)
    sh = align(height, 4)
    off = 0
    for by in range(0, sh, 4):
        for bx in range(0, sw, 4):
            for y in range(4):
                for x in range(4):
                    if bx+x >= width or by+y >= height:
                        off += 2
                        continue
                    a = data[off]
                    r = data[off+1]
                    g = data[off+32]
                    b = data[off+33]
                    pixels[bx+x, by+y] = (r, g, b, a)
                    off += 2
            off += 32
    return img

def encode_rgba8(img):
    width, height = img.size
    pixels = img.load()
    sw = align(width, 4)
    sh = align(height, 4)
    buf = bytearray(sw*sh*2 + (sw*sh//2))  # overallocate safe
    off = 0
    for by in range(0, sh, 4):
        for bx in range(0, sw, 4):
            for y in range(4):
                for x in range(4):
                    px, py = bx+x, by+y
                    r=g=b=a=0
                    if px < width and py < height:
                        r,g,b,a = pixels[px, py]
                    buf[off] = a
                    buf[off+1] = r
                    buf[off+32] = g
                    buf[off+33] = b
                    off += 2
            off += 32
    return bytes(buf)

def decode_c4(data, palette_data, width, height, pal_format):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()
    pal = build_palette(palette_data, pal_format)
    sw = align(width, 8)
    for y in range(height):
        for x in range(width):
            off = offset_c4(x, y, sw)
            if off >= len(data):
                continue
            byte = data[off]
            idx = (byte & 0x0F) if (x&1) else (byte >>4)
            if idx < len(pal):
                pixels[x, y] = pal[idx]
    return img

def encode_c4(img, palette_data, pal_format):
    width, height = img.size
    pixels = img.load()
    sw = align(width, 8)
    pal = build_palette(palette_data, pal_format)
    buf = bytearray(sw*height//2)
    for y in range(height):
        for x in range(width):
            off = offset_c4(x, y, sw)
            r,g,b,a = pixels[x, y]
            # encontrar índice mais próximo na paleta
            best_idx = min(range(len(pal)), key=lambda i: sum((pixels[x,y][j]-pal[i][j])**2 for j in range(4)))
            if x&1:
                buf[off] = (buf[off]&0xF0) | best_idx
            else:
                buf[off] = (buf[off]&0x0F) | (best_idx<<4)
    return bytes(buf)

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

def encode_c8(img, palette_data, pal_format):
    width, height = img.size
    pixels = img.load()
    sw = align(width, 8)
    pal = build_palette(palette_data, pal_format)
    buf = bytearray(sw*height)
    for y in range(height):
        for x in range(width):
            r,g,b,a = pixels[x, y]
            best_idx = min(range(len(pal)), key=lambda i: sum((pixels[x,y][j]-pal[i][j])**2 for j in range(4)))
            off = offset_bpp8(x, y, sw)
            buf[off] = best_idx
    return bytes(buf)