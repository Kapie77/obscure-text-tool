import os

from utils.binary import read_be_u32

from .pc_codecs import (
    decode_pc_rgba8_bgra,
    decode_pc_r5g6b5,
    decode_pc_r5g5b5a1,
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

