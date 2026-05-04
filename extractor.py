import struct
import os
from PIL import Image


# ==============================
# Helpers
# ==============================

def read_be_u32(data, off):
    return (data[off] << 24) | (data[off+1] << 16) | (data[off+2] << 8) | data[off+3]


def is_printable(b):
    return 32 <= b < 127


def is_valid_texture_entry(data, off):
    if off >= len(data):
        return False

    name_len = data[off]
    if name_len < 1 or name_len > 48:
        return False

    if off + 1 + name_len > len(data):
        return False

    for i in range(name_len):
        if not is_printable(data[off + 1 + i]):
            return False

    p = off + 1 + name_len
    if p + 28 > len(data):
        return False

    width = read_be_u32(data, p)
    height = read_be_u32(data, p + 4)
    gx = read_be_u32(data, p + 16)
    size = read_be_u32(data, p + 24)

    if width not in [4,8,16,32,64,128,256,512,1024]:
        return False
    if height not in [4,8,16,32,64,128,256,512,1024]:
        return False
    if gx not in [1,3,5,6,8,9,14]:
        return False
    if size <= 0 or size > len(data):
        return False
    if p + 28 + size > len(data):
        return False

    return True

# ==============================
# Função de deswizzle (morton)
# ==============================
def morton2D(x, y):
    def part1by1(n):
        n &= 0xFFFF
        n = (n | (n << 8)) & 0x00FF00FF
        n = (n | (n << 4)) & 0x0F0F0F0F
        n = (n | (n << 2)) & 0x33333333
        n = (n | (n << 1)) & 0x55555555
        return n

    return part1by1(x) | (part1by1(y) << 1)

# ==============================
# Decoders
# ==============================

def offset_bpp8(x, y, w):
    blocks_x = (w + 7) >> 3
    xb = x >> 3
    yb = y >> 2
    xp = x & 7
    yp = y & 3
    return ((yb * blocks_x + xb) << 5) + ((yp << 3) + xp)

def offset_bpp16(x, y, w):
    blocks_x = (w + 3) >> 2
    xb = x >> 2
    yb = y >> 2
    xp = x & 3
    yp = y & 3
    return ((yb * blocks_x + xb) << 5) + ((yp << 3) + (xp << 1))


def decode_ia8(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    sw = (width + 3) & ~3

    for y in range(height):
        for x in range(width):
            off = offset_bpp16(x, y, sw)

            if off + 1 >= len(data):
                continue

            a = data[off]
            i = data[off + 1]

            pixels[x, y] = (i, i, i, a)

    return img


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

    sw = (width + 7) & ~7

    for y in range(height):
        for x in range(width):
            index = offset_bpp8(x, y, sw)

            if index >= len(data):
                continue

            v = data[index]
            pixels[x, y] = (v, v, v, 255)

    return img

def decode_rgb5a3(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            sw = (width + 3) & ~3
            index = offset_bpp16(x, y, sw)

            if index + 1 >= len(data):
                continue

            p = (data[index] << 8) | data[index+1]

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

            pixels[x, y] = (r, g, b, a)

    return img

def decode_c4(data, palette_data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pal = build_palette_rgb5a3(palette_data)

    pos = 0

    for by in range(0, height, 8):
        for bx in range(0, width, 8):
            for y in range(8):
                for xpair in range(4):

                    if pos >= len(data):
                        return img

                    v = data[pos]
                    pos += 1

                    for dx in range(2):
                        idx = (v >> 4) if dx == 0 else (v & 0x0F)

                        px = bx + xpair*2 + dx
                        py = by + y

                        if px < width and py < height:
                            if idx < len(pal):
                                pixels[px, py] = pal[idx]

    return img

# ================
# DECODE NOVO
# ================
def build_palette_rgb5a3(palette_data):
    pal = []

    count = len(palette_data) // 2

    for i in range(count):
        p = (palette_data[i*2] << 8) | palette_data[i*2 + 1]

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

        pal.append((r, g, b, a))

    return pal


def decode_c8(data, palette_data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    sw = (width + 7) & ~7
    pal = build_palette_rgb5a3(palette_data)

    for y in range(height):
        for x in range(width):
            off = offset_bpp8(x, y, sw)

            if off >= len(data):
                continue

            idx = data[off]

            if idx < len(pal):
                pixels[x, y] = pal[idx]

    return img

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
# Main parser
# ==============================

def parse_wii_dic(path, out_folder):
    with open(path, "rb") as f:
        data = f.read()

    count = read_be_u32(data, 0)
    offset = 7

    print(f"[+] Textures: {count}")

    os.makedirs(out_folder, exist_ok=True)

    for i in range(count):
        if offset >= len(data):
            break

        name_len = data[offset]
        name = data[offset+1:offset+1+name_len].decode(errors="ignore")

        p = offset + 1 + name_len

        width = read_be_u32(data, p)
        height = read_be_u32(data, p + 4)
        gx = read_be_u32(data, p + 16)
        size = read_be_u32(data, p + 24)

        data_offset = p + 28

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"Format: {gx}")
        print(f"Data size: {size}")

        tex_data = data[data_offset:data_offset+size]

        # ----------------------------
        # descobrir next_offset ANTES
        # ----------------------------
        min_next = data_offset + size
        next_offset = None

        for cand in range(min_next, min(min_next + 4096, len(data))):
            if is_valid_texture_entry(data, cand):
                next_offset = cand
                break

        if next_offset is None:
            next_offset = len(data)  # última textura fallback

        # ----------------------------
        # decode
        # ----------------------------
        img = None

        if gx == 1:
            img = decode_i8(tex_data, width, height)

        elif gx == 3:
            img = decode_ia8(tex_data, width, height)

        elif gx == 5:
            img = decode_rgb5a3(tex_data, width, height)

        elif gx == 6:
            img = decode_rgba8(tex_data, width, height)

        elif gx == 8:  # C4
            pal_off = data_offset + size
            palette_data = data[pal_off:next_offset]

            img = decode_c4(tex_data, palette_data, width, height)

            size = next_offset - data_offset

        elif gx == 9:  # C8
            pal_off = data_offset + size
            palette_data = data[pal_off:next_offset]

            img = decode_c8(tex_data, palette_data, width, height)

            size = next_offset - data_offset

        elif gx == 14:
            img = decode_cmpr(tex_data, width, height)

        if img:
            out_path = os.path.join(out_folder, name + ".png")
            img.save(out_path)
            print("[+] Saved PNG:", out_path)
        else:
            out_path = os.path.join(out_folder, name + ".bin")
            with open(out_path, "wb") as f:
                f.write(tex_data)
            print("[!] Saved RAW:", out_path)

        # encontrar próxima textura
        offset = next_offset


# ==============================
# CLI
# ==============================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("-o", "--output", default="out")

    args = parser.parse_args()

    parse_wii_dic(args.input, args.output)