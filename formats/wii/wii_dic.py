import os
from PIL import Image

from utils.binary import read_be_u32
from utils.detection import is_valid_texture_entry
from utils.palettes import read_palette
import struct

from formats.wii.wii_codecs_dic import (
    decode_i8,
    decode_ia8,
    decode_rgb5a3,
    decode_rgba8,
    decode_c4,
    decode_c8
)

from formats.wii.wii_codecs_dic import (
    encode_i8, 
    encode_ia8, 
    encode_rgb5a3, 
    encode_rgba8, 
    encode_c4, 
    encode_c8
)

from texture_codecs.dxt_codecs_wii_dic_hvt import encode_cmpr, decode_cmpr

# Decoders para extração
DECODERS = {
    1: decode_i8,
    3: decode_ia8,
    5: decode_rgb5a3,
    6: decode_rgba8,
    14: decode_cmpr,
}

# encoders para rebuild
ENCODERS = {
    1: encode_i8,
    3: encode_ia8,
    5: encode_rgb5a3,
    6: encode_rgba8,
    8: encode_c4,
    9: encode_c8,
    14: encode_cmpr,
}

# ======================
#        EXTRACT
# ======================
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

# ======================
#        REBUILD
# ======================
def rebuild_wii_dic(input_path, png_folder, out_path):

    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    count = read_be_u32(data, 0)
    offset = 7

    print(f"[+] Wii textures: {count}")

    rebuilt = 0

    for i in range(count):

        if offset >= len(data):
            break

        if not is_valid_texture_entry(data, offset):
            print(f"[!] Invalid texture entry at {offset:X}")
            break

        name_len = data[offset]

        name = data[
            offset + 1:
            offset + 1 + name_len
        ].decode(errors="ignore")

        p = offset + 1 + name_len

        width  = read_be_u32(data, p + 0)
        height = read_be_u32(data, p + 4)

        gx = read_be_u32(data, p + 16)

        unk = read_be_u32(data, p + 16)

        # formato alternativo
        if unk == 0x20:
            size = read_be_u32(data, p + 20)
            data_offset = p + 24
        else:
            size = read_be_u32(data, p + 24)
            data_offset = p + 28

        print(f"\n[{i}] {name}")
        print(f"GX: {gx}")
        print(f"Size: {width}x{height}")
        print(f"Data size: {size}")

        # -----------------------------
        # próxima textura
        # -----------------------------
        min_next = data_offset + size
        next_offset = None

        for cand in range(
            min_next,
            min(min_next + 4096, len(data))
        ):
            if is_valid_texture_entry(data, cand):
                next_offset = cand
                break

        if next_offset is None:
            next_offset = len(data)

        # -----------------------------
        # PNG
        # -----------------------------
        png_path = os.path.join(
            png_folder,
            name + ".png"
        )

        if not os.path.isfile(png_path):
            print(f"[!] PNG not found: {png_path}")
            offset = next_offset
            continue

        img = Image.open(png_path).convert("RGBA")

        if img.width != width or img.height != height:
            print("[!] Size mismatch, skipping")
            offset = next_offset
            continue

        # -----------------------------
        # ENCODE
        # -----------------------------
        try:

            # -------------------------
            # normal formats
            # -------------------------
            if gx in [1, 3, 5, 6]:

                new_raw = ENCODERS[gx](img)

            # -------------------------
            # C4
            # -------------------------
            elif gx == 8:

                pal_off = data_offset + size

                palette_data = data[
                    pal_off:
                    pal_off + 32
                ]

                new_raw = encode_c4(
                    img,
                    palette_data,
                    gx
                )

            # -------------------------
            # C8
            # -------------------------
            elif gx == 9:

                pal_off = data_offset + size

                palette_data = data[
                    pal_off:
                    pal_off + 512
                ]

                new_raw = encode_c8(
                    img,
                    palette_data,
                    gx
                )

            # -------------------------
            # CMPR
            # -------------------------
            elif gx == 14:

                tex_data = data[
                    data_offset:
                    data_offset + size
                ]

                new_raw = encode_cmpr(
                    img,
                    width,
                    height,
                    tex_data
                )

            else:

                print(f"[!] Unsupported GX: {gx}")
                offset = next_offset
                continue

        except Exception as e:

            print(f"[!] Encode failed: {e}")
            offset = next_offset
            continue

        # -----------------------------
        # VALIDAR TAMANHO
        # -----------------------------
        if len(new_raw) != size:

            print(
                f"[!] Encoded size mismatch "
                f"({len(new_raw)} != {size})"
            )

            offset = next_offset
            continue

        # -----------------------------
        # OVERWRITE ORIGINAL DATA
        # -----------------------------
        data[
            data_offset:
            data_offset + size
        ] = new_raw

        rebuilt += 1

        print("[+] Rebuilt")

        # próxima entrada
        offset = next_offset

    # =============================
    # SAVE
    # =============================
    with open(out_path, "wb") as f:
        f.write(data)

    print(f"\n[+] Wii DIC rebuilt: {rebuilt} textures")
    print(f"[+] Saved: {out_path}")