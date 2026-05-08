from utils.binary import read_be_u32

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

# ===================
#   READ PALETTE
# ===================
def read_palette(data, offset):
    pal_count = read_be_u32(data, offset)
    pal_format = read_be_u32(data, offset + 4)
    pal_size = read_be_u32(data, offset + 8)

    palette_data = data[offset + 12 : offset + 12 + pal_size]

    return pal_format, palette_data