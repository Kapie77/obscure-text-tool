import os

from .pc_codecs import (
    decode_pc_rgba8_bgra,
    decode_pc_r5g6b5,
    decode_pc_r5g5b5a1,
)

from utils.binary import read_u32_le
# ================================
#    PARSER OBSCURE 1 PC .DIP
# ================================
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