import os

from PIL import Image

from .psp_codecs import (
    decode_psp_4bpp,
    decode_psp_8bpp,
)

# ==============================
#       PARSER PSP (.DIC)
# ==============================
def parse_psp_dic(path, out_folder):

    with open(path, "rb") as f:
        data = f.read()

    count = int.from_bytes(data[0:4], "little")

    print(f"[PSP DIC] Textures: {count}")

    offset = 4

    os.makedirs(out_folder, exist_ok=True)

    for i in range(count):

        name_len = int.from_bytes(data[offset:offset+4], "little")
        offset += 4

        name = data[offset:offset+name_len].decode(
            "ascii",
            errors="ignore"
        )

        offset += name_len

        width  = int.from_bytes(data[offset:offset+2], "little")
        height = int.from_bytes(data[offset+2:offset+4], "little")

        palette_entries = int.from_bytes(data[offset+4:offset+6], "little")

        bpp = data[offset+6]

        palette_size = int.from_bytes(data[offset+12:offset+16], "little")

        offset += 16

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"BPP: {bpp}")

        # =========================
        # PAL4 / PAL8
        # =========================

        if bpp in (4, 8):

            palette_data = data[offset:offset+palette_size]

            offset += palette_size

            # 4-byte padding
            offset += 4

            image_size = (width * height * bpp) // 8

            pixel_data = data[offset:offset+image_size]

            offset += image_size

            if bpp == 4:
                img = decode_psp_4bpp(
                    pixel_data,
                    palette_data,
                    width,
                    height
                )
            else:
                img = decode_psp_8bpp(
                    pixel_data,
                    palette_data,
                    width,
                    height
                )

        # =========================
        # RGBA8888
        # =========================

        elif bpp == 32:

            # PSP entries possuem padding de 4 bytes
            offset += 4

            image_size = width * height * 4

            pixel_data = data[offset:offset+image_size]

            offset += image_size

            img = Image.frombytes(
                "RGBA",
                (width, height),
                pixel_data
            )

        else:

            print("[!] Unsupported PSP format")
            continue

        out_path = os.path.join(out_folder, name + ".png")

        img.save(out_path)

        print("[+] Saved:", out_path)