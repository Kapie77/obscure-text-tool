import os
from PIL import Image
from utils.binary import read_be_u32

from .pc_codecs import (
    decode_pc_rgba8_bgra,
    decode_pc_r5g6b5,
    decode_pc_r5g5b5a1,

    encode_dip_b8g8r8a8,
    encode_dip_r5g6b5,
    encode_dip_a1r5g5b5,
)

# ==================================
#    PARSER PC .DIC (Obscure 2)
# ==================================
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

# ==================================
#        REBUILD PC .DIC
# ==================================
def rebuild_pc_dic_file(dic_path, png_folder, output_path):

    with open(dic_path, "rb") as f:
        data = bytearray(f.read())

    count = read_be_u32(data, 0)
    offset = 4

    print(f"[PC DIC] Total textures: {count}")

    for i in range(count):

        offset += 4  # skip

        name_len = read_be_u32(data, offset)
        offset += 4

        name = data[offset:offset+name_len].decode(
            "shift_jis",
            errors="ignore"
        )
        offset += name_len

        mipmaps = read_be_u32(data, offset); offset += 4
        alpha_flag = read_be_u32(data, offset); offset += 4
        onebit_alpha = read_be_u32(data, offset); offset += 4
        width = read_be_u32(data, offset); offset += 4
        height = read_be_u32(data, offset); offset += 4
        fmt = read_be_u32(data, offset); offset += 4

        first_mip_offset = None
        first_mip_size = None

        # =========================
        # percorre mipmaps
        # =========================
        for m in range(mipmaps):

            mip_size = read_be_u32(data, offset)
            offset += 4

            if m == 0:
                first_mip_offset = offset
                first_mip_size = mip_size

            offset += mip_size

        # =========================
        # PNG
        # =========================
        png_path = os.path.join(
            png_folder,
            name + ".png"
        )

        if not os.path.isfile(png_path):
            print(f"[!] PNG not found: {name}")
            continue

        img = Image.open(png_path).convert("RGBA")

        if img.size != (width, height):
            img = img.resize((width, height))

        # =========================
        # encode
        # =========================
        if fmt == 21:
            encoded = encode_dip_b8g8r8a8(img)

        elif fmt == 23:
            encoded = encode_dip_r5g6b5(img)

        elif fmt == 25:
            encoded = encode_dip_a1r5g5b5(img)

        else:
            print(f"[!] Unsupported format {fmt} for {name}")
            continue

        if len(encoded) != first_mip_size:
            raise ValueError(
                f"{name}: encoded size {len(encoded)} != original {first_mip_size}"
            )

        # sobrescreve mip0
        data[
            first_mip_offset:first_mip_offset+first_mip_size
        ] = encoded

        print(f"[+] Rebuilt texture: {name}")

    # =========================
    # save
    # =========================
    with open(output_path, "wb") as f:
        f.write(data)

    print(f"[+] Saved rebuilt DIC: {output_path}")