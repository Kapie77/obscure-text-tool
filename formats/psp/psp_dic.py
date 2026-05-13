import os

from PIL import Image

from .psp_codecs import (
    #decodes
    decode_psp_4bpp,
    decode_psp_8bpp,
    decode_psp_rgba8888,

    #encodes
    encode_psp_4bpp,
    encode_psp_8bpp,
    encode_psp_rgba8888,
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

        # =========================
        # name
        # =========================
        name_len = int.from_bytes(
            data[offset:offset+4],
            "little"
        )

        offset += 4

        name = data[
            offset:offset+name_len
        ].decode(
            "ascii",
            errors="ignore"
        )

        offset += name_len

        # =========================
        # texture header
        # =========================
        width = int.from_bytes(
            data[offset:offset+2],
            "little"
        )

        height = int.from_bytes(
            data[offset+2:offset+4],
            "little"
        )

        palette_entries = int.from_bytes(
            data[offset+4:offset+6],
            "little"
        )

        bpp = data[offset+6]

        palette_size = int.from_bytes(
            data[offset+12:offset+16],
            "little"
        )

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"BPP: {bpp}")

        # =========================
        # PAL4 / PAL8
        # =========================
        if bpp in (4, 8):

            palette_offset = offset + 16

            palette_data = data[
                palette_offset:
                palette_offset + palette_size
            ]

            image_offset = (
                palette_offset +
                palette_size +
                4
            )

            image_size = (
                width * height * bpp
            ) // 8

            pixel_data = data[
                image_offset:
                image_offset + image_size
            ]

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

            offset = image_offset + image_size

        # =========================
        # RGBA8888
        # =========================
        elif bpp == 32:

            image_offset = offset + 20

            image_size = width * height * 4

            pixel_data = data[
                image_offset:
                image_offset + image_size
            ]

            img = decode_psp_rgba8888(
                pixel_data,
                width,
                height
            )

            offset = image_offset + image_size

        # =========================
        # unsupported
        # =========================
        else:

            print("[!] Unsupported PSP format")

            break

        # =========================
        # save
        # =========================
        out_path = os.path.join(
            out_folder,
            name + ".png"
        )

        img.save(out_path)

        print("[+] Saved:", out_path)

# ==============================
#       REBUILD PSP (.DIC)
# ==============================
def rebuild_psp_dic_file(path, png_folder, output_path):

    from .psp_codecs import (
        encode_psp_4bpp,
        encode_psp_8bpp,
        encode_psp_rgba8888,
    )

    with open(path, "rb") as f:
        data = bytearray(f.read())

    count = int.from_bytes(data[0:4], "little")

    print(f"[PSP] Rebuilding {count} textures")

    offset = 4

    for i in range(count):

        entry_start = offset

        name_len = int.from_bytes(
            data[offset:offset+4],
            "little"
        )

        offset += 4

        name = data[
            offset:offset+name_len
        ].decode(
            "ascii",
            errors="ignore"
        )

        offset += name_len

        width = int.from_bytes(
            data[offset:offset+2],
            "little"
        )

        height = int.from_bytes(
            data[offset+2:offset+4],
            "little"
        )

        palette_entries = int.from_bytes(
            data[offset+4:offset+6],
            "little"
        )

        bpp = data[offset+6]

        palette_size = int.from_bytes(
            data[offset+12:offset+16],
            "little"
        )

        offset += 16

        print(f"[{i}] {name}")

        # =========================
        # load png
        # =========================

        png_path = os.path.join(
            png_folder,
            name + ".png"
        )

        if not os.path.isfile(png_path):

            print(f"[!] PNG not found: {name}")

            # skip original data
            if bpp == 32:

                offset += width * height * 4

            else:

                offset += palette_size
                offset += 4
                offset += (width * height * bpp) // 8

            continue

        img = Image.open(png_path).convert("RGBA")

        if img.size != (width, height):

            img = img.resize((width, height))

        # =========================
        # PAL4 / PAL8
        # =========================

        if bpp in (4, 8):

            palette_offset = offset

            palette_data = data[
                palette_offset:
                palette_offset + palette_size
            ]

            offset += palette_size

            # padding
            offset += 4

            image_offset = offset

            image_size = (
                width * height * bpp + 7
            ) // 8

            if bpp == 4:

                encoded = encode_psp_4bpp(
                    img,
                    width,
                    height,
                    palette_data
                )

            else:

                encoded = encode_psp_8bpp(
                    img,
                    width,
                    height,
                    palette_data
                )

            if len(encoded) != image_size:

                raise ValueError(
                    f"{name}: encoded size mismatch "
                    f"{len(encoded)} != {image_size}"
                )

            data[
                image_offset:
                image_offset + image_size
            ] = encoded

            offset += image_size

        # =========================
        # RGBA8888
        # =========================

        elif bpp == 32:

            # PSP RGBA8888 possui padding de 4 bytes
            offset += 4

            image_offset = offset

            image_size = width * height * 4

            encoded = encode_psp_rgba8888(img)

            if len(encoded) != image_size:

                raise ValueError(
                    f"{name}: encoded size mismatch "
                    f"{len(encoded)} != {image_size}"
                )

            data[
                image_offset:
                image_offset + image_size
            ] = encoded

            offset += image_size

        else:

            print(f"[!] Unsupported PSP bpp: {bpp}")
            continue

        print(f"[+] Rebuilt: {name}")

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"[+] Saved rebuilt file: {output_path}")