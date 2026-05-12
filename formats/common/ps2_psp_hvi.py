import os

from formats.ps2.ps2_codecs import decode_ps2_hvi

from formats.psp.psp_codecs import (
    decode_psp_hvi,
    decode_psp_8bpp
)

# ==================================
#      PARSER HVI (PS2 AND PSP)
# ==================================
def is_ps2_palette(palette):
    max_alpha = max(palette[3::4])
    return max_alpha <= 0x90


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
    palette_size = 1024

    pixel_offset = palette_offset + palette_size
    pixel_size = width * height

    palette = data[palette_offset:palette_offset + palette_size]
    pixels  = data[pixel_offset:pixel_offset + pixel_size]

    # =====================================
    # Detect platform
    # =====================================

    is_psp = (
        width <= 480 and
        height <= 272
    )

    if not is_psp:

        print("[+] HVI platform: PS2")

        img = decode_ps2_hvi(
            pixels,
            palette,
            width,
            height
        )

    else:

        print("[+] HVI platform: PSP")

        img = decode_psp_8bpp(
            pixels,
            palette,
            width,
            height
        )

    os.makedirs(out_folder, exist_ok=True)

    base = os.path.splitext(os.path.basename(path))[0]

    out_path = os.path.join(
        out_folder,
        base + ".png"
    )

    img.save(out_path)

    print("[+] Saved:", out_path)