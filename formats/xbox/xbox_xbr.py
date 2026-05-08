import os

from .xbox_codecs import (
    decode_xbox_r5g6b5,
    decode_xbox_a1r5g5b5,
    decode_xbox_a8r8g8b8,
)

# ==============================
#       PARSER XBOX .XBR
# ==============================
def parse_xbox_xbr(path, out_folder):

    with open(path, "rb") as f:
        data = f.read()

    def u32(off):
        return int.from_bytes(data[off:off+4], "little")

    table_size  = u32(0x00)
    file_size   = u32(0x04)
    data_offset = u32(0x08)

    if table_size % 20 != 0:
        print("[!] Invalid descriptor table")
        return

    tex_count = table_size // 20
    print(f"[XBOX] Textures: {tex_count}")

    # =========================
    # 1. DESCRIPTORS
    # =========================
    entries = []

    for i in range(tex_count):
        off = 0x0C + i * 20

        flag = u32(off + 0)
        rel  = u32(off + 4)
        fmt  = u32(off + 12)

        entries.append((rel, fmt))

    # =========================
    # 2. NAMES (igual ao C#)
    # =========================
    metadata_len = (tex_count + 2) * 8 + 4
    p = 0x0C + table_size + metadata_len

    names = []
    while len(names) < tex_count and p < len(data):
        end = p
        while end < len(data) and data[end] != 0:
            end += 1

        name = data[p:end].decode("ascii", errors="ignore")

        if name == "SYMBOLTABLE" or name == "":
            break

        names.append(name)
        p = end + 1

    # =========================
    # 3. EXTRAIR TEXTURAS
    # =========================
    os.makedirs(out_folder, exist_ok=True)

    for i in range(tex_count):
        rel, fmt = entries[i]

        abs_off = data_offset + rel

        next_off = file_size if i + 1 >= tex_count else data_offset + entries[i+1][0]
        size = next_off - abs_off

        # decode format word
        color = (fmt >> 8) & 0xFF
        mip   = (fmt >> 16) & 0xF
        sizeU = (fmt >> 20) & 0xF
        sizeV = (fmt >> 24) & 0xF

        width  = 1 << sizeU
        height = 1 << sizeV

        name = names[i] if i < len(names) else f"tex_{i:03d}"

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"Format: 0x{color:02X}")

        pixel_data = data[abs_off:abs_off + size]

        # =========================
        # 4. DECODE
        # =========================
        try:
            if color == 0x05:
                img = decode_xbox_r5g6b5(pixel_data, width, height)

            elif color == 0x02:
                img = decode_xbox_a1r5g5b5(pixel_data, width, height)

            elif color == 0x06:
                img = decode_xbox_a8r8g8b8(pixel_data, width, height)

            else:
                print("[!] Unsupported format")
                continue

        except Exception as e:
            print("[!] Decode error:", e)
            continue

        # =========================
        # 5. SAVE
        # =========================
        out_path = os.path.join(out_folder, name + ".png")
        img.save(out_path)

        print("[+] Saved:", out_path)