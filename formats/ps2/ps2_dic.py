import os
from PIL import Image

from utils.renderware import iter_chunks

from .ps2_codecs import (
    decode_ps2_8bpp,
    decode_ps2_4bpp,
    decode_ps2_rgba8888,
    decode_ps2_rgb5551,


    encode_ps2_rgba8888,
    encode_ps2_rgb5551,
)

# ==============================
#       PARSER PS2 .DIC
# ==============================
def parse_ps2_dic(path, out_folder):
    with open(path, "rb") as f:
        data = f.read()

    print("[PS2] Parsing RenderWare TXD")

    os.makedirs(out_folder, exist_ok=True)

    RW_STRUCT = 0x01
    RW_STRING = 0x02
    RW_TEXTURE_NATIVE = 0x15
    RW_TEXTURE_DICTIONARY = 0x16

    root_id = int.from_bytes(data[0:4], "little")
    root_size = int.from_bytes(data[4:8], "little")

    if root_id != RW_TEXTURE_DICTIONARY:
        print("[!] Not a valid TXD")
        return

    root_start = 12
    root_end = root_start + root_size

    index = 0

    for c in iter_chunks(data, root_start, root_end):
        if c["id"] != RW_TEXTURE_NATIVE:
            continue

        name = f"texture_{index:03}"
        blob_offset = -1
        blob_size = 0

        # =========================
        # parse subchunks
        # =========================
        for cc in iter_chunks(data, c["body_start"], c["body_end"]):

            # nome da textura
            if cc["id"] == RW_STRING:
                raw = data[cc["body_start"]:cc["body_end"]]
                extracted = raw.split(b"\x00")[0].decode("ascii", errors="ignore").strip()

                if extracted:
                    name = extracted

            # struct grande (onde estão os dados reais)
            elif cc["id"] == RW_STRUCT and cc["size"] > 64 and blob_offset < 0:

                # pular marker "PS2\0"
                if data[cc["body_start"]:cc["body_start"]+4] == b"PS2\x00":
                    continue

                blob_offset = cc["body_start"]
                blob_size = cc["size"]

        if blob_offset < 0:
            index += 1
            continue

        # =========================
        # ler dados REAIS
        # =========================
        width  = int.from_bytes(data[blob_offset+0x0C:blob_offset+0x10], "little")
        height = int.from_bytes(data[blob_offset+0x10:blob_offset+0x14], "little")
        bpp    = int.from_bytes(data[blob_offset+0x14:blob_offset+0x18], "little")

        image_packet_size   = int.from_bytes(data[blob_offset+0x3C:blob_offset+0x40], "little")
        palette_packet_size = int.from_bytes(data[blob_offset+0x40:blob_offset+0x44], "little")

        image_offset = blob_offset + 0xA8

        if bpp == 4:
            image_size = (width * height + 1) // 2

        elif bpp == 8:
            image_size = width * height

        else:
            image_size = width * height * (bpp // 8)

        palette_offset = (
            blob_offset + 0x50 + image_packet_size + 0x58
            if palette_packet_size > 0 else -1
        )

        if bpp == 4:
            palette_size = 16 * 4

        elif bpp == 8:
            palette_size = (
                1024 if palette_packet_size >= 0x450
                else (512 if palette_packet_size > 0 else 0)
            )

        else:
            palette_size = 0

        print(f"\n[{index}] {name}")
        print(f"Size: {width}x{height}")
        print(f"BPP: {bpp}")

        # =========================
        # extrair dados
        # =========================
        pixels = data[image_offset:image_offset+image_size]

        img = None

        if bpp == 8 and palette_offset != -1:

            palette = data[palette_offset:palette_offset+palette_size]
            img = decode_ps2_8bpp(pixels, palette, width, height)

        elif bpp == 4 and palette_offset != -1:

            palette = data[palette_offset:palette_offset+palette_size]
            img = decode_ps2_4bpp(pixels, palette, width, height)

        elif bpp == 32:

            img = decode_ps2_rgba8888(
                pixels,
                width,
                height
            )

        elif bpp == 16:

            img = decode_ps2_rgb5551(
                pixels,
                width,
                height
            )

        # =========================
        # salvar
        # =========================
        if img:
            out_path = os.path.join(out_folder, name + ".png")
            img.save(out_path)
            print("[+] Saved:", out_path)
        else:
            print("[!] Unsupported format (for now)")

        index += 1

# ==============================
#       REBUILD PS2 .DIC
# ==============================
def rebuild_ps2_dic_file(path, png_folder, output_path):

    with open(path, "rb") as f:
        data = bytearray(f.read())

    print("[PS2] Rebuilding RenderWare TXD")

    RW_STRUCT = 0x01
    RW_STRING = 0x02
    RW_TEXTURE_NATIVE = 0x15
    RW_TEXTURE_DICTIONARY = 0x16

    root_id = int.from_bytes(data[0:4], "little")
    root_size = int.from_bytes(data[4:8], "little")

    if root_id != RW_TEXTURE_DICTIONARY:
        print("[!] Not a valid TXD")
        return

    root_start = 12
    root_end = root_start + root_size

    index = 0

    for c in iter_chunks(data, root_start, root_end):

        if c["id"] != RW_TEXTURE_NATIVE:
            continue

        name = f"texture_{index:03}"

        blob_offset = -1

        for cc in iter_chunks(data, c["body_start"], c["body_end"]):

            if cc["id"] == RW_STRING:

                raw = data[cc["body_start"]:cc["body_end"]]

                extracted = (
                    raw.split(b"\x00")[0]
                    .decode("ascii", errors="ignore")
                    .strip()
                )

                if extracted:
                    name = extracted

            elif cc["id"] == RW_STRUCT and cc["size"] > 64 and blob_offset < 0:

                if data[cc["body_start"]:cc["body_start"]+4] == b"PS2\x00":
                    continue

                blob_offset = cc["body_start"]

        if blob_offset < 0:
            index += 1
            continue

        # =========================
        # texture info
        # =========================

        width  = int.from_bytes(data[blob_offset+0x0C:blob_offset+0x10], "little")
        height = int.from_bytes(data[blob_offset+0x10:blob_offset+0x14], "little")
        bpp    = int.from_bytes(data[blob_offset+0x14:blob_offset+0x18], "little")

        image_packet_size = int.from_bytes(
            data[blob_offset+0x3C:blob_offset+0x40],
            "little"
        )

        palette_packet_size = int.from_bytes(
            data[blob_offset+0x40:blob_offset+0x44],
            "little"
        )

        palette_offset = (
            blob_offset + 0x50 + image_packet_size + 0x58
            if palette_packet_size > 0 else -1
        )

        image_offset = blob_offset + 0xA8

        if bpp == 4:
            image_size = (width * height + 1) // 2

        elif bpp == 8:
            image_size = width * height

        else:
            image_size = width * height * (bpp // 8)

        # =========================
        # load png
        # =========================

        png_path = os.path.join(
            png_folder,
            name + ".png"
        )

        if not os.path.isfile(png_path):
            print(f"[!] PNG not found: {name}")
            index += 1
            continue

        img = Image.open(png_path).convert("RGBA")

        if img.size != (width, height):
            img = img.resize((width, height))

        # =========================
        # encode
        # =========================

        encoded = None
        encoded_palette = None

        # =========================
        # 32bpp
        # =========================
        if bpp == 32:

            encoded = encode_ps2_rgba8888(
                img,
                width,
                height
            )

        # =========================
        # 16bpp
        # =========================
        elif bpp == 16:

            encoded = encode_ps2_rgb5551(
                img,
                width,
                height
            )

        # =========================
        # 8bpp
        # =========================
        elif bpp == 8:

            encoded, encoded_palette = encode_ps2_8bpp(
                img,
                width,
                height
            )

        # =========================
        # 4bpp
        # =========================
        elif bpp == 4:

            encoded, encoded_palette = encode_ps2_4bpp(
                img,
                width,
                height
            )

        # =========================
        # validation
        # =========================
        if encoded is None:

            print(f"[!] Unsupported rebuild format: {name}")

            index += 1
            continue

        if len(encoded) != image_size:

            raise ValueError(
                f"{name}: encoded size mismatch "
                f"{len(encoded)} != {image_size}"
            )

        # =========================
        # replace texture
        # =========================
        data[
            image_offset:image_offset+image_size
        ] = encoded

        # =========================
        # replace palette
        # =========================
        if encoded_palette is not None and palette_offset != -1:

            palette_size = len(encoded_palette)

            data[
                palette_offset:palette_offset+palette_size
            ] = encoded_palette

        print(f"[+] Rebuilt: {name}")

        index += 1

    # =========================
    # save
    # =========================

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"[+] Saved rebuilt file: {output_path}")