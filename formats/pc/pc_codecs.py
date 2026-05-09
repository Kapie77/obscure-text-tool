from PIL import Image

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

# ==============================
#        ENCODERS (PC DIP)
# ==============================
def encode_dip_b8g8r8a8(img: "PIL.Image.Image") -> bytes:
    """Converte RGBA → DIP B8G8R8A8 (PC)."""
    img = img.convert("RGBA")
    data = img.tobytes()  # RGBA linear
    out = bytearray(len(data))
    for i in range(len(data)//4):
        r, g, b, a = data[i*4:i*4+4]
        out[i*4+0] = b
        out[i*4+1] = g
        out[i*4+2] = r
        out[i*4+3] = a
    return bytes(out)

def encode_dip_r5g6b5(img: "PIL.Image.Image") -> bytes:
    """Converte RGBA → DIP B5G6R5 (PC)."""
    img = img.convert("RGBA")
    data = img.tobytes()
    w, h = img.size
    out = bytearray(w*h*2)
    for i in range(w*h):
        r = data[i*4+0] * 31 // 255
        g = data[i*4+1] * 63 // 255
        b = data[i*4+2] * 31 // 255
        val = (r << 11) | (g << 5) | b
        out[i*2+0] = val & 0xFF
        out[i*2+1] = val >> 8
    return bytes(out)

def encode_dip_a1r5g5b5(img: "PIL.Image.Image") -> bytes:
    """Converte RGBA → DIP B5G5R5A1 (PC)."""
    img = img.convert("RGBA")
    data = img.tobytes()
    w, h = img.size
    out = bytearray(w*h*2)
    for i in range(w*h):
        r = data[i*4+0] * 31 // 255
        g = data[i*4+1] * 31 // 255
        b = data[i*4+2] * 31 // 255
        a = 1 if data[i*4+3] >= 128 else 0
        val = (a << 15) | (r << 10) | (g << 5) | b
        out[i*2+0] = val & 0xFF
        out[i*2+1] = val >> 8
    return bytes(out)