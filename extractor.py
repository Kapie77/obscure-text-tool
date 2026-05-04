import struct
import os
from PIL import Image


# ==============================
# Helpers
# ==============================

def read_be_u32(data, off):
    return (data[off] << 24) | (data[off+1] << 16) | (data[off+2] << 8) | data[off+3]

def read_u16_le(data, pos):
    return data[pos] | (data[pos + 1] << 8)

def read_u16_be(data, pos):
    return (data[pos] << 8) | data[pos + 1]

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

    if not is_power_of_two(width) or width > 1024:
        return False
    if not is_power_of_two(height) or height > 1024:
        return False
    if gx not in [1,3,5,6,8,9,14]:
        return False
    if size <= 0 or size > len(data):
        return False
    if p + 28 + size > len(data):
        return False

    return True

def is_power_of_two(v):
        return v != 0 and (v & (v - 1)) == 0

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

# ==============================
#        DECODERS (PC)
# ==============================
def decode_pc_rgba8_rgba(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for y in range(height):
        for x in range(width):
            if pos + 3 >= len(data):
                return img

            r = data[pos]
            g = data[pos + 1]
            b = data[pos + 2]
            a = data[pos + 3]
            pos += 4

            pixels[x, y] = (r, g, b, a)

    return img

def decode_pc_rgba8_bgra(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for y in range(height):
        for x in range(width):
            if pos + 3 >= len(data):
                return img

            b = data[pos]
            g = data[pos + 1]
            r = data[pos + 2]
            a = data[pos + 3]
            pos += 4

            pixels[x, y] = (r, g, b, a)

    return img

def decode_pc_rgba8(data, width, height):
    img1 = decode_pc_rgba8_rgba(data, width, height)
    img2 = decode_pc_rgba8_bgra(data, width, height)

    # heurística simples: escolher a menos "verde absurda"
    def score(img):
        pixels = img.load()
        w, h = img.size
        s = 0
        for y in range(0, h, max(1, h//10)):
            for x in range(0, w, max(1, w//10)):
                r, g, b, a = pixels[x, y]
                s += abs(g - r) + abs(g - b)
        return s

    return img1 if score(img1) < score(img2) else img2

def decode_pc_r5g6b5(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for y in range(height):
        for x in range(width):
            if pos + 1 >= len(data):
                return img

            v = data[pos] | (data[pos + 1] << 8)
            pos += 2

            r = ((v >> 11) & 0x1F) * 255 // 31
            g = ((v >> 5) & 0x3F) * 255 // 63
            b = (v & 0x1F) * 255 // 31

            pixels[x, y] = (r, g, b, 255)

    return img

def decode_pc_r5g5b5a1(data, width, height):
    img = Image.new("RGBA", (width, height))
    pixels = img.load()

    pos = 0

    for y in range(height):
        for x in range(width):
            if pos + 1 >= len(data):
                return img

            # SEM heurística — PC é sempre little-endian
            v = data[pos] | (data[pos + 1] << 8)
            pos += 2

            r = ((v >> 10) & 0x1F) * 255 // 31
            g = ((v >> 5) & 0x1F) * 255 // 31
            b = (v & 0x1F) * 255 // 31
            a = 255 if (v & 0x8000) else 0

            pixels[x, y] = (r, g, b, a)

    return img
    
# ====================
#   BUILD PALETTE
# ====================
def build_palette(palette_data, palette_format):
    pal = []

    for i in range(len(palette_data)//2):
        v = (palette_data[i*2] << 8) | palette_data[i*2+1]

        if palette_format == 1:  # RGB565
            r = ((v >> 11) & 0x1F) * 255 // 31
            g = ((v >> 5) & 0x3F) * 255 // 63
            b = (v & 0x1F) * 255 // 31
            a = 255

        elif palette_format == 0:  # IA8
            i8 = v & 0xFF
            a = (v >> 8) & 0xFF
            r = g = b = i8

        else:  # RGB5A3
            if v & 0x8000:
                r = ((v >> 10) & 0x1F) * 255 // 31
                g = ((v >> 5) & 0x1F) * 255 // 31
                b = (v & 0x1F) * 255 // 31
                a = 255
            else:
                a = ((v >> 12) & 0x7) * 255 // 7
                r = ((v >> 8) & 0xF) * 255 // 15
                g = ((v >> 4) & 0xF) * 255 // 15
                b = (v & 0xF) * 255 // 15

        pal.append((r, g, b, a))

    return pal

# =============
# READ PALETTE
# ==============
def read_palette(data, offset):
    pal_count = read_be_u32(data, offset)
    pal_format = read_be_u32(data, offset + 4)
    pal_size = read_be_u32(data, offset + 8)

    palette_data = data[offset + 12 : offset + 12 + pal_size]

    return pal_format, palette_data

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
#       PARSER WII .DIC
# ==============================

DECODERS = {
    1: decode_i8,
    3: decode_ia8,
    5: decode_rgb5a3,
    6: decode_rgba8,
    14: decode_cmpr,
}

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

        unk = read_be_u32(data, p + 16)

        if unk == 0x20:
            # formato alternativo
            size = read_be_u32(data, p + 20)
            data_offset = p + 24
            print("[DEBUG] formato ALT detectado")
        else:
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

        if gx in DECODERS:
            img = DECODERS[gx](tex_data, width, height)

        elif gx == 8:  # C4
            pal_off = data_offset + size
            pal_format, palette_data = read_palette(data, pal_off)

            img = decode_c4(tex_data, palette_data, width, height, pal_format)

        elif gx == 9:  # C8
            pal_off = data_offset + size
            pal_format, palette_data = read_palette(data, pal_off)

            img = decode_c8(tex_data, palette_data, width, height, pal_format)

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
#       PARSER WII .HVT
# ==============================
def parse_wii_hvt(path, out_folder):
    with open(path, "rb") as f:
        data = f.read()

    if data[0:4] != b"\x20IVH":
        print("[!] Not a valid HVT")
        return

    format_tag = data[8:12].decode()
    width = (data[0x0E] << 8) | data[0x0F]
    height = (data[0x12] << 8) | data[0x13]
    bpp = (data[0x14] << 24) | (data[0x15] << 16) | (data[0x16] << 8) | data[0x17]

    print(f"[HVT] {path}")
    print(f"Format: {format_tag}")
    print(f"Size: {width}x{height}")
    print(f"BPP: {bpp}")

    header_size = 0x18
    pixel_size = (width * height * bpp + 7) // 8

    pixel_data = data[header_size:header_size + pixel_size]

    palette_data = None

    if format_tag == "P8WI":
        pal_off = header_size + pixel_size
        palette_data = data[pal_off:pal_off + 512]

    # =====================
    # decode
    # =====================
    img = None

    if format_tag == "S3TW":
        img = decode_cmpr(pixel_data, width, height)

    elif format_tag == "G8A8":
        img = decode_ia8(pixel_data, width, height)

    elif format_tag == "GRY8":
        img = decode_i8(pixel_data, width, height)

    elif format_tag == "4443":
        img = decode_rgb5a3(pixel_data, width, height)

    elif format_tag == "ARGB":
        img = decode_rgba8(pixel_data, width, height)

    elif format_tag == "P8WI":
        img = decode_c8(pixel_data, palette_data, width, height, 2)  
        # 2 = RGB5A3

    # =====================
    # save
    # =====================
    os.makedirs(out_folder, exist_ok=True)

    name = os.path.splitext(os.path.basename(path))[0]

    if img:
        out_path = os.path.join(out_folder, name + ".png")
        img.save(out_path)
        print("[+] Saved:", out_path)
    else:
        print("[!] Unknown format")

# ==============================
#       PARSER PC .DIC
# ==============================
def parse_pc_dic(path, out_folder):
    with open(path, "rb") as f:
        data = f.read()

    count = read_be_u32(data, 0)
    offset = 4

    print(f"[PC DIC] Textures: {count}")

    os.makedirs(out_folder, exist_ok=True)

    for i in range(count):
        offset += 4  # skip

        name_len = read_be_u32(data, offset)
        offset += 4

        name = data[offset:offset+name_len].decode("shift_jis", errors="ignore")
        offset += name_len

        mipmaps = read_be_u32(data, offset); offset += 4
        alpha_flag = read_be_u32(data, offset); offset += 4
        onebit_alpha = read_be_u32(data, offset); offset += 4
        width = read_be_u32(data, offset); offset += 4
        height = read_be_u32(data, offset); offset += 4
        fmt = read_be_u32(data, offset); offset += 4

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"Format: {fmt}")
        print(f"Mipmaps: {mipmaps}")

        first_mip = None

        for m in range(mipmaps):
            mip_size = read_be_u32(data, offset)
            offset += 4

            mip_data = data[offset:offset+mip_size]
            offset += mip_size

            if m == 0:
                first_mip = mip_data

        # ======================
        # decode
        # ======================
        img = None

        if fmt == 21:
            img = decode_pc_rgba8_bgra(first_mip, width, height)

        elif fmt == 23:
            img = decode_pc_r5g6b5(first_mip, width, height)

        elif fmt == 25:
            img = decode_pc_r5g5b5a1(first_mip, width, height)

        # ======================
        # save
        # ======================
        if img:
            out_path = os.path.join(out_folder, name + ".png")
            img.save(out_path)
            print("[+] Saved:", out_path)
        else:
            out_path = os.path.join(out_folder, name + ".bin")
            with open(out_path, "wb") as f:
                f.write(first_mip)
            print("[!] Unknown format, saved RAW")

# ==============================
#       PARSER PC .DIP
# ==============================
def read_u32_le(data, off):
    return data[off] | (data[off+1] << 8) | (data[off+2] << 16) | (data[off+3] << 24)

def parse_pc_dip(path, out_folder):
    with open(path, "rb") as f:
        data = f.read()

    offset = 0

    offset += 4  # skip zero
    count = read_u32_le(data, offset)
    offset += 4

    print(f"[DIP] Textures: {count}")

    os.makedirs(out_folder, exist_ok=True)

    for i in range(count):
        offset += 4  # skip

        name_len = read_u32_le(data, offset)
        offset += 4

        name = data[offset:offset+name_len].decode("ascii", errors="ignore")
        offset += name_len

        mipmaps = read_u32_le(data, offset); offset += 4
        alpha_flag = read_u32_le(data, offset); offset += 4
        onebit_alpha = read_u32_le(data, offset); offset += 4
        width = read_u32_le(data, offset); offset += 4
        height = read_u32_le(data, offset); offset += 4
        fmt = read_u32_le(data, offset); offset += 4

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"Format: {fmt}")
        print(f"Mipmaps: {mipmaps}")

        first_mip = None

        for m in range(mipmaps):
            mip_size = read_u32_le(data, offset)
            offset += 4

            mip_data = data[offset:offset+mip_size]
            offset += mip_size

            if m == 0:
                first_mip = mip_data

        # ======================
        # decode
        # ======================
        img = None

        if fmt == 21:  # B8G8R8A8
            img = decode_pc_rgba8_bgra(first_mip, width, height)

        elif fmt == 23:  # B5G6R5
            img = decode_pc_r5g6b5(first_mip, width, height)

        elif fmt == 25:  # B5G5R5A1
            img = decode_pc_r5g5b5a1(first_mip, width, height)

        # ======================
        # save
        # ======================
        if img:
            out_path = os.path.join(out_folder, name + ".png")
            img.save(out_path)
            print("[+] Saved:", out_path)
        else:
            print("[!] Unknown format")

# ==============================
#           CLI
# ==============================
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("input")

    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.input))[0]
    input_dir = os.path.dirname(args.input)

    final_out = os.path.join(input_dir, base_name)

    os.makedirs(final_out, exist_ok=True)

    ext = os.path.splitext(args.input)[1].lower()

    if ext == ".hvt":
        parse_wii_hvt(args.input, final_out)

    elif ext == ".dic":
        # detectar se é Wii ou PC
        with open(args.input, "rb") as f:
            data = f.read(64)

        count = read_be_u32(data, 0)

        if count > 0 and count < 4096:
            name_len = data[7]
            if 1 <= name_len <= 48:
                printable = all(32 <= data[8+i] < 127 for i in range(name_len))
                if printable:
                    parse_wii_dic(args.input, final_out)
                else:
                    parse_pc_dic(args.input, final_out)
            else:
                parse_pc_dic(args.input, final_out)
        else:
            parse_pc_dic(args.input, final_out)

    elif ext == ".dip":
        parse_pc_dip(args.input, final_out)

    else:
        print("[!] Unknown file type")