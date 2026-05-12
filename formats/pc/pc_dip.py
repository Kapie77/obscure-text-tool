import os
from PIL import Image
from utils.binary import read_u32_le

from .pc_codecs import (
    decode_pc_rgba8_bgra,
    decode_pc_r5g6b5,
    decode_pc_r5g5b5a1,

    encode_dip_b8g8r8a8,
    encode_dip_r5g6b5,
    encode_dip_a1r5g5b5,
)

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

# =========================
#      Rebuild PC DIP
# =========================
def rebuild_pc_dip_file(dip_path: str, png_folder: str, output_path: str):

    with open(dip_path, "rb") as f:
        data = bytearray(f.read())

    offset = 4  # pula zero inicial
    if offset + 4 > len(data):
        raise ValueError("Arquivo DIP muito pequeno")
    count = read_u32_le(data, offset)
    offset += 4

    print(f"[DIP] Total textures: {count}")

    for i in range(count):
        # skip desconhecido
        if offset + 4 > len(data):
            print(f"[!] EOF inesperado no skip para texture {i}")
            break
        offset += 4

        # nome da textura
        if offset + 4 > len(data):
            print(f"[!] EOF inesperado lendo name length para texture {i}")
            break
        name_len = read_u32_le(data, offset); offset += 4

        if offset + name_len > len(data):
            print(f"[!] EOF inesperado lendo nome para texture {i}")
            break
        name = data[offset:offset+name_len].decode("ascii", errors="ignore"); offset += name_len

        # header
        if offset + 7*4 > len(data):
            print(f"[!] EOF inesperado lendo header para texture {name}")
            break
        mipmaps = read_u32_le(data, offset); offset += 4
        alpha_flag = read_u32_le(data, offset); offset += 4
        onebit_alpha = read_u32_le(data, offset); offset += 4
        width = read_u32_le(data, offset); offset += 4
        height = read_u32_le(data, offset); offset += 4
        fmt = read_u32_le(data, offset); offset += 4

        # =========================
        # Lê todos os mipmaps
        # =========================
        first_mip_offset = None
        first_mip_size = None

        for m in range(mipmaps):

            if offset + 4 > len(data):
                print(f"[!] EOF inesperado lendo mip size {m} para {name}")
                break

            mip_size = read_u32_le(data, offset)
            offset += 4

            if offset + mip_size > len(data):
                print(f"[!] EOF inesperado lendo mip data {m} para {name}")
                break

            if m == 0:
                first_mip_offset = offset
                first_mip_size = mip_size

            offset += mip_size

        # ======================
        # Rebuild com PNG
        # ======================
        png_path = os.path.join(png_folder, name + ".png")
        if not os.path.isfile(png_path):
            print(f"[!] PNG não encontrado, pulando {name}")
            continue

        img = Image.open(png_path).convert("RGBA")
        if img.size != (width, height):
            img = img.resize((width, height))

        # encode
        if fmt == 21:
            encoded = encode_dip_b8g8r8a8(img)
        elif fmt == 23:
            encoded = encode_dip_r5g6b5(img)
        elif fmt == 25:
            encoded = encode_dip_a1r5g5b5(img)
        else:
            print(f"[!] Formato DIP não suportado {fmt} para {name}")
            continue

        if len(encoded) != first_mip_size:
            raise ValueError(
                f"{name}: encoded size {len(encoded)} != original {first_mip_size}"
            )

        # sobrescreve mip0
        data[first_mip_offset:first_mip_offset+first_mip_size] = encoded
        print(f"[+] Rebuilt texture: {name}")

    # salva DIP rebuild
    with open(output_path, "wb") as f:
        f.write(data)
    print(f"[+] Saved rebuilt DIP file: {output_path}")