import os
from PIL import Image

from utils.binary import (
    read_be_u32,
    read_u16_be
)

from texture_codecs.dxt_codecs_wii_dic_hvt import (
    decode_cmpr,
    encode_cmpr
)

from formats.wii.wii_codecs_hvt import (
    decode_rgba32,
    encode_rgba32,

    decode_rgb5a3,
    encode_rgb5a3,

    decode_ia8,
    encode_ia8,

    decode_i8,
    encode_i8,

    decode_c8,
    encode_c8
)

# =========================================
# HVT FORMATS
# =========================================

HVT_FORMATS = {
    b"S3TW": "CMPR",
    b"G8A8": "IA8",
    b"GRY8": "I8",
    b"4443": "RGB5A3",
    b"ARGB": "RGBA32",
    b"P8WI": "C8"
}

# =========================================
# PIXEL SIZE
# =========================================

def compute_pixel_size(width, height, bpp):

    bits = width * height * bpp

    return (bits + 7) // 8

# =========================================
# EXTRACT
# =========================================
def parse_wii_hvt(path, out_folder):

    with open(path, "rb") as f:
        data = f.read()

    # =====================================
    # HEADER
    # =====================================

    if data[0:4] != b" IVH":
        raise Exception("Not a Wii HVT file")

    format_tag = data[8:12]

    if format_tag not in HVT_FORMATS:
        raise Exception(
            f"Unsupported Wii HVT format: {format_tag}"
        )

    fmt = HVT_FORMATS[format_tag]

    width = read_u16_be(data, 0x0E)
    height = read_u16_be(data, 0x12)

    bpp = read_be_u32(data, 0x14)

    print("[+] Wii HVT")
    print("Format:", fmt)
    print("Width:", width)
    print("Height:", height)
    print("BPP:", bpp)

    # =====================================
    # PIXELS
    # =====================================

    pixel_size = compute_pixel_size(
        width,
        height,
        bpp
    )

    pixel_offset = 0x18

    pixel_data = data[
        pixel_offset:
        pixel_offset + pixel_size
    ]

    # =====================================
    # PALETTE
    # =====================================

    palette = None

    if fmt == "C8":

        pal_offset = pixel_offset + pixel_size

        palette = data[
            pal_offset:
            pal_offset + 512
        ]

    # =====================================
    # DECODE
    # =====================================

    if fmt == "CMPR":

        img = decode_cmpr(
            pixel_data,
            width,
            height
        )

    elif fmt == "RGBA32":

        img = decode_rgba32(
            pixel_data,
            width,
            height
        )

    elif fmt == "RGB5A3":

        img = decode_rgb5a3(
            pixel_data,
            width,
            height
        )

    elif fmt == "IA8":

        img = decode_ia8(
            pixel_data,
            width,
            height
        )

    elif fmt == "I8":

        img = decode_i8(
            pixel_data,
            width,
            height
        )

    elif fmt == "C8":

        img = decode_c8(
            pixel_data,
            palette,
            width,
            height
        )

    else:

        raise Exception("Unsupported format")

    # =====================================
    # SAVE
    # =====================================

    os.makedirs(out_folder, exist_ok=True)

    base_name = os.path.splitext(
        os.path.basename(path)
    )[0]

    out_png = os.path.join(
        out_folder,
        base_name + ".png"
    )

    img.save(out_png)

    print("[+] Saved PNG:", out_png)

    # =====================================
    # SAVE PALETTE
    # =====================================

    if palette:

        pal_path = os.path.join(
            out_folder,
            base_name + "_pal.bin"
        )

        with open(pal_path, "wb") as f:
            f.write(palette)

        print("[+] Saved Palette:", pal_path)

# =========================================
# REBUILD
# =========================================
def rebuild_wii_hvt(original_path, png_folder, output_file):

    with open(original_path, "rb") as f:
        original = f.read()

    # =====================================
    # HEADER
    # =====================================

    if original[0:4] != b" IVH":
        raise Exception("Not a Wii HVT file")

    header = original[:0x18]

    format_tag = original[8:12]

    if format_tag not in HVT_FORMATS:
        raise Exception(
            f"Unsupported Wii HVT format: {format_tag}"
        )

    fmt = HVT_FORMATS[format_tag]

    width = read_u16_be(original, 0x0E)
    height = read_u16_be(original, 0x12)

    bpp = read_be_u32(original, 0x14)

    pixel_size = compute_pixel_size(
        width,
        height,
        bpp
    )

    pixel_offset = 0x18

    original_pixels = original[
        pixel_offset:
        pixel_offset + pixel_size
    ]

    trailer_offset = pixel_offset + pixel_size

    palette = b""
    trailer = b""

    # =====================================
    # C8 PALETTE
    # =====================================

    if fmt == "C8":

        palette = original[
            trailer_offset:
            trailer_offset + 512
        ]

        trailer = original[
            trailer_offset + 512:
        ]

    else:

        trailer = original[
            trailer_offset:
        ]

    # =====================================
    # LOAD PNG
    # =====================================
    hvt_name = os.path.splitext(
        os.path.basename(original_path)
    )[0]

    png_path = os.path.join(
        png_folder,
        hvt_name + ".png"
    )

    if not os.path.isfile(png_path):

        raise Exception(
            f"PNG not found: {png_path}"
        )

    img = Image.open(png_path).convert("RGBA")

    if img.size != (width, height):

        raise Exception(
            f"PNG dimensions must be "
            f"{width}x{height}"
        )

    # =====================================
    # ENCODE
    # =====================================
    if fmt == "CMPR":

        encoded = encode_cmpr(
            img,
            width,
            height,
            original_pixels
        )

    elif fmt == "RGBA32":

        encoded = encode_rgba32(
            img,
            width,
            height
        )

    elif fmt == "RGB5A3":

        encoded = encode_rgb5a3(
            img,
            width,
            height,
            original_pixels
        )

    elif fmt == "IA8":

        encoded = encode_ia8(
            img,
            width,
            height
        )

    elif fmt == "I8":

        encoded = encode_i8(
            img,
            width,
            height
        )

    elif fmt == "C8":

        encoded = encode_c8(
            img,
            palette,
            width,
            height,
            original_pixels
        )

    else:

        raise Exception("Unsupported format")

    # =====================================
    # WRITE
    # =====================================

    with open(output_file, "wb") as f:

        f.write(header)

        f.write(encoded)

        if palette:
            f.write(palette)

        if trailer:
            f.write(trailer)

    print("[+] Rebuilt:", output_file)

    return output_file