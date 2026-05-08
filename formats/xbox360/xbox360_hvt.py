import os

from PIL import Image

from texture_codecs.dxt_codecs import (
    decode_dxt1,
    decode_dxt3,
    decode_dxt5,
    compute_mip0_size
)

from .xbox360_codecs import (
    decode_bgra,
    decode_bgrx,
    decode_argb_be,
    decode_rgba_ps3_swizzled
)

# =========================================
#    PARSER FINAL EXAM XBOX 360 (.HVT)
# =========================================
from PIL import Image

def save_png(raw_bgra, width, height, path):
    rgba = bytearray(width * height * 4)

    for i in range(width * height):
        b = raw_bgra[i*4 + 0]
        g = raw_bgra[i*4 + 1]
        r = raw_bgra[i*4 + 2]
        a = raw_bgra[i*4 + 3]

        rgba[i*4 + 0] = r
        rgba[i*4 + 1] = g
        rgba[i*4 + 2] = b
        rgba[i*4 + 3] = a

    img = Image.frombytes("RGBA", (width, height), bytes(rgba))
    img.save(path)

def crop_rgba(img, w, h, aligned_w):
    out = bytearray(w * h * 4)
    for y in range(h):
        src = y * aligned_w * 4
        dst = y * w * 4
        out[dst:dst + w*4] = img[src:src + w*4]
    return out

def align(v, a):
    return (v + a - 1) & ~(a - 1)


def x360_byte_swap(data):
    swapped = bytearray(len(data))
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            swapped[i] = data[i+1]
            swapped[i+1] = data[i]
    return swapped


def x360_tiled_x(block_offset, width_in_blocks, texel_pitch):
    aligned_width = (width_in_blocks + 31) & ~31

    log_bpp = (texel_pitch >> 2) + ((texel_pitch >> 1) >> (texel_pitch >> 2))
    offset_byte = block_offset << log_bpp

    offset_tile = ((offset_byte & ~0xFFF) >> 3) + ((offset_byte & 0x700) >> 2) + (offset_byte & 0x3F)
    offset_macro = offset_tile >> (7 + log_bpp)

    macro_x = (offset_macro % (aligned_width >> 5)) << 2
    tile = (((offset_tile >> (5 + log_bpp)) & 2) + (offset_byte >> 6)) & 3
    macro = (macro_x + tile) << 3

    micro = ((((offset_tile >> 1) & ~0xF) + (offset_tile & 0xF)) & ((texel_pitch << 3) - 1)) >> log_bpp

    return macro + micro


def x360_tiled_y(block_offset, width_in_blocks, texel_pitch):
    aligned_width = (width_in_blocks + 31) & ~31

    log_bpp = (texel_pitch >> 2) + ((texel_pitch >> 1) >> (texel_pitch >> 2))
    offset_byte = block_offset << log_bpp

    offset_tile = ((offset_byte & ~0xFFF) >> 3) + ((offset_byte & 0x700) >> 2) + (offset_byte & 0x3F)
    offset_macro = offset_tile >> (7 + log_bpp)

    macro_y = (offset_macro // (aligned_width >> 5)) << 2
    tile = ((offset_tile >> (6 + log_bpp)) & 1) + ((offset_byte & 0x800) >> 10)
    macro = (macro_y + tile) << 3

    micro = (((offset_tile & ((texel_pitch << 6) - 1 & ~0x1F)) +
              ((offset_tile & 0xF) << 1)) >> (3 + log_bpp)) & ~1

    return macro + micro + ((offset_tile & 0x10) >> 4)


def x360_unswizzle(data, width, height, block_size, texel_pitch):
    wb = width // block_size
    hb = height // block_size

    padded_wb = (wb + 31) & ~31
    padded_hb = (hb + 31) & ~31

    out = bytearray(wb * hb * texel_pitch)

    total = padded_wb * padded_hb

    for i in range(total):
        x = x360_tiled_x(i, padded_wb, texel_pitch)
        y = x360_tiled_y(i, padded_wb, texel_pitch)

        if x >= wb or y >= hb:
            continue

        src = i * texel_pitch
        dst = (y * wb + x) * texel_pitch

        if src + texel_pitch <= len(data):
            out[dst:dst+texel_pitch] = data[src:src+texel_pitch]

    return out


def crop_image(data, src_w, dst_w, dst_h):
    out = bytearray(dst_w * dst_h * 4)

    for y in range(dst_h):
        src_off = y * src_w * 4
        dst_off = y * dst_w * 4
        out[dst_off:dst_off + dst_w*4] = data[src_off:src_off + dst_w*4]

    return out

def parse_finalexam_hvt(path, out_dir):
    with open(path, "rb") as f:
        data = f.read()

    def read_u32(off, be):
        return int.from_bytes(data[off:off+4], "big" if be else "little")

    # =========================
    # HEADER
    # =========================
    magic = data[0:4]
    is_be = (magic == b" IVH")

    format_tag = data[0x14:0x18].decode("ascii", errors="ignore")

    width  = read_u32(0x18, is_be)
    height = read_u32(0x1C, is_be)
    bpp    = read_u32(0x20, is_be)
    mipmaps = read_u32(0x28, is_be)

    # =========================
    # PLATFORM
    # =========================
    if magic == b"HVI ":
        platform = "PC"
    else:
        arch = data[0x24:0x28]
        if arch == b"X360":
            platform = "X360"
        else:
            platform = "PS3"

    # =========================
    # OFFSETS
    # =========================
    if platform == "X360":

        # -------------------------
        # X360 alignment
        # -------------------------
        if format_tag in ["DXT1", "1TXD", "TXD1",
                        "DXT3", "3TXD", "TXD3",
                        "DXT5", "5TXD", "TXD5"]:

            aligned_w = align(width, 128)
            aligned_h = align(height, 128)

        else:
            aligned_w = align(width, 32)
            aligned_h = align(height, 32)

        mip0_size = compute_mip0_size(
            aligned_w,
            aligned_h,
            format_tag
        )

        pixel_offset = 0x84

    else:
        mip0_size = read_u32(0x3C, is_be)
        pixel_offset = 0x40

    print(f"[+] Final Exam HVT detected")
    print(f"    Platform: {platform}")
    print(f"    Format: {format_tag}")
    print(f"    Size: {width}x{height}")
    print(f"    Mips: {mipmaps}")

    raw = data[pixel_offset:pixel_offset + mip0_size]

    # =========================================================
    # ===================== X360 ===============================
    # =========================================================
    if platform == "X360":

        if format_tag in ["1TXD", "3TXD", "5TXD", "DXT1", "DXT3", "DXT5"]:

            if format_tag in ["1TXD", "DXT1"]:
                block_bytes = 8
            else:
                block_bytes = 16

            wb = (width + 3) // 4
            hb = (height + 3) // 4

            aligned_wb = align(wb, 32)
            aligned_hb = align(hb, 32)

            aligned_w = aligned_wb * 4
            aligned_h = aligned_hb * 4

            raw = x360_unswizzle(raw, aligned_w, aligned_h, 4, block_bytes)
            raw = x360_byte_swap(raw)

            if format_tag in ["1TXD", "DXT1"]:
                img = decode_dxt1(raw, aligned_w, aligned_h)

            elif format_tag in ["3TXD", "DXT3"]:
                img = decode_dxt3(raw, aligned_w, aligned_h)

            else:
                img = decode_dxt5(raw, aligned_w, aligned_h)

            img = crop_rgba(img, width, height, aligned_w)

        elif format_tag == "ARGB":

            aligned_w = align(width, 32)
            aligned_h = align(height, 32)

            raw = x360_unswizzle(raw, aligned_w, aligned_h, 1, 4)
            raw = x360_byte_swap(raw)

            img = decode_argb_be(raw, aligned_w, aligned_h)
            img = crop_rgba(img, width, height, aligned_w)

        else:
            print(f"[!] Unsupported X360 format: {format_tag}")
            return

    # =========================================================
    # ===================== PC / PS3 ===========================
    # =========================================================
    else:

        if format_tag == "BGRA":
            img = decode_bgra(raw, width, height)

        elif format_tag == "BGRX":
            img = decode_bgrx(raw, width, height)

        elif format_tag in ["1TXD", "DXT1"]:
            img = decode_dxt1(raw, width, height)

        elif format_tag in ["3TXD", "DXT3"]:
            img = decode_dxt3(raw, width, height)

        elif format_tag in ["5TXD", "DXT5"]:
            img = decode_dxt5(raw, width, height)

        elif format_tag == "ARGB":

            if platform == "PS3":
                img = decode_rgba_ps3_swizzled(raw, width, height)

            else:
                img = decode_argb_be(raw, width, height)

        else:
            print(f"[!] Unsupported format: {format_tag}")
            return

    # =========================
    # SAVE PNG
    # =========================
    base_name = os.path.splitext(os.path.basename(path))[0]
    out_path = os.path.join(out_dir, base_name + ".png")

    print(f"[+] Saving: {out_path}")

    save_png(img, width, height, out_path)