import os
from PIL import Image

from utils.binary import read_be_u32
from utils.detection import is_valid_texture_entry
from utils.palettes import read_palette

from .wii_codecs import (
    decode_i8,
    decode_ia8,
    decode_rgb5a3,
    decode_rgba8,
    decode_c4,
    decode_c8
)

from texture_codecs.dxt_codecs import decode_cmpr

# ==============================
#   PARSER OBSCURE 2 WII .DIC
# ==============================

DECODERS = {
    1: decode_i8,
    3: decode_ia8,
    5: decode_rgb5a3,
    6: decode_rgba8,
    14: decode_cmpr,
}

def parse_wii_dic(path, out_folder):
    with open(path, "rb") as f:
        data = f.read()

    count = read_be_u32(data, 0)
    offset = 7

    print(f"[+] Textures: {count}")

    os.makedirs(out_folder, exist_ok=True)

    for i in range(count):
        if offset >= len(data):
            break

        name_len = data[offset]
        name = data[offset+1:offset+1+name_len].decode(errors="ignore")

        p = offset + 1 + name_len

        width = read_be_u32(data, p)
        height = read_be_u32(data, p + 4)
        gx = read_be_u32(data, p + 16)
        size = read_be_u32(data, p + 24)

        unk = read_be_u32(data, p + 16)

        if unk == 0x20:
            # formato alternativo
            size = read_be_u32(data, p + 20)
            data_offset = p + 24
            print("[DEBUG] formato ALT detectado")
        else:
            size = read_be_u32(data, p + 24)
            data_offset = p + 28

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"Format: {gx}")
        print(f"Data size: {size}")

        tex_data = data[data_offset:data_offset+size]

        # ----------------------------
        # descobrir next_offset ANTES
        # ----------------------------
        min_next = data_offset + size
        next_offset = None

        for cand in range(min_next, min(min_next + 4096, len(data))):
            if is_valid_texture_entry(data, cand):
                next_offset = cand
                break

        if next_offset is None:
            next_offset = len(data)  # última textura fallback

        # ----------------------------
        # decode
        # ----------------------------
        img = None

        if gx in DECODERS:
            img = DECODERS[gx](tex_data, width, height)

        elif gx == 8:  # C4
            pal_off = data_offset + size
            pal_format, palette_data = read_palette(data, pal_off)

            img = decode_c4(tex_data, palette_data, width, height, pal_format)

        elif gx == 9:  # C8
            pal_off = data_offset + size
            pal_format, palette_data = read_palette(data, pal_off)

            img = decode_c8(tex_data, palette_data, width, height, pal_format)

        if img:
            out_path = os.path.join(out_folder, name + ".png")
            img.save(out_path)
            print("[+] Saved PNG:", out_path)
        else:
            out_path = os.path.join(out_folder, name + ".bin")
            with open(out_path, "wb") as f:
                f.write(tex_data)
            print("[!] Saved RAW:", out_path)

        # encontrar próxima textura
        offset = next_offset