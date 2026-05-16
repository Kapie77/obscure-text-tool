import os
from PIL import Image

# ======= PS2 HVI CODECS ======== #
from formats.ps2.ps2_codecs_hvi import (
    decode_ps2_hvi,
    encode_ps2_hvi,       # rebuild com swizzle
    encode_ps2_8bpp_hvi,  # HVI 8bpp linear (sem swizzle)
    encode_ps2_4bpp_hvi   # HVI 4bpp linear (sem swizzle)
)

# PSP CODECS
from formats.psp.psp_codecs_hvi import (
    decode_psp_hvi,  # CORRETO
    encode_psp_hvi,  # opcional para rebuild futuro
)

# ==================================
# PARSER HVI (PS2 AND PSP)
# ==================================
def parse_ps2_psp_hvi(path, out_folder):
    with open(path, "rb") as f:
        data = f.read()

    print("[HVI] Parsing")

    if data[0:4] != b"HVI ":
        print("[!] Not a valid HVI")
        return

    width  = int.from_bytes(data[0x0C:0x10], "little")
    height = int.from_bytes(data[0x10:0x14], "little")
    bpp    = int.from_bytes(data[0x14:0x18], "little")

    print(f"Size: {width}x{height}")
    print(f"BPP: {bpp}")

    if bpp != 8:
        print("[!] Only 8bpp supported")
        return

    palette_offset = 0x18
    pixel_offset   = palette_offset + 1024

    palette = data[palette_offset:palette_offset + 1024]
    pixels  = data[pixel_offset:pixel_offset + width*height]

    is_psp = width <= 480 and height <= 272

    if not is_psp:
        print("[+] HVI platform: PS2")
        img = decode_ps2_hvi(pixels, palette, width, height)
    else:
        print("[+] HVI platform: PSP")
        img = decode_psp_hvi(pixels, palette, width, height)

    os.makedirs(out_folder, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    out_path = os.path.join(out_folder, base + ".png")
    img.save(out_path)
    print("[+] Saved:", out_path)

# ==================================
#          REBUILD PS2/PSP
# ==================================
class HviFile:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.data = bytearray(f.read())

        if self.data[0:4] != b"HVI ":
            raise ValueError("Not a valid HVI file")

        self.width  = int.from_bytes(self.data[0x0C:0x10], "little")
        self.height = int.from_bytes(self.data[0x10:0x14], "little")
        self.bpp    = int.from_bytes(self.data[0x14:0x18], "little")

        if self.bpp != 8:
            raise ValueError("Only 8bpp HVI supported")

        self.palette_offset = 0x18
        self.palette_size   = 1024
        self.pixel_offset   = self.palette_offset + self.palette_size
        self.pixel_size     = self.width * self.height

        self.palette = self.data[self.palette_offset:self.palette_offset+self.palette_size]
        self.pixels  = self.data[self.pixel_offset:self.pixel_offset+self.pixel_size]

        after_pixels = self.pixel_offset + self.pixel_size
        self.trailer = self.data[after_pixels:] if len(self.data) > after_pixels else b""

        self.is_psp   = self.width <= 480 and self.height <= 272
        self.platform = "PSP" if self.is_psp else "PS2"

    # ======================
    # Converte PNG para HVI bytes
    # ======================
    def encode_from_png(self, png_path):
        img = Image.open(png_path).convert("RGBA")
        w, h = img.size

        if self.platform == "PS2":
            # PS2 HVI rebuild - usa paleta original, sem swizzle
            pixels, palette = encode_ps2_hvi(img, w, h, self.palette, self.pixels)
        else:
            # PSP HVI rebuild ainda não implementado
            raise NotImplementedError("PSP HVI rebuild not implemented")

    # ======================
    # Salva HVI reconstruído
    # ======================
    def save(self, out_path, palette=None, pixels=None):
        palette = palette or self.palette
        pixels  = pixels  or self.pixels

        with open(out_path, "wb") as f:
            f.write(self.data[:self.palette_offset])  # header
            f.write(palette)
            f.write(pixels)
            if self.trailer:
                f.write(self.trailer)