# ========================================
#       FINAL EXAM TEXTURE CODECS
# ========================================

from PIL import Image


# =========================================================
#                     PC CODECS
# =========================================================
# PC textures are mostly linear and require only
# channel conversion to internal BGRA format.
# =========================================================

def decode_bgra(raw, width, height):

    # Already stored as BGRA
    return raw


def decode_bgrx(raw, width, height):

    pixels = width * height
    out = bytearray(pixels * 4)

    for i in range(pixels):

        b = raw[i*4 + 0]
        g = raw[i*4 + 1]
        r = raw[i*4 + 2]

        # X channel ignored
        out[i*4 + 3] = 255

        out[i*4 + 0] = b
        out[i*4 + 1] = g
        out[i*4 + 2] = r

    return bytes(out)


# =========================================================
#                XBOX 360 / BIG ENDIAN
# =========================================================
# Xbox 360 ARGB textures are stored big-endian:
#
#     A R G B
#
# Internal tool format is BGRA.
# =========================================================

def decode_argb_be(raw, width, height):

    out = bytearray(width * height * 4)

    for i in range(width * height):

        a = raw[i*4 + 0]
        r = raw[i*4 + 1]
        g = raw[i*4 + 2]
        b = raw[i*4 + 3]

        out[i*4 + 0] = b
        out[i*4 + 1] = g
        out[i*4 + 2] = r
        out[i*4 + 3] = a

    return bytes(out)


# =========================================================
#                     PS3 LINEAR RGBA
# =========================================================
# Some PS3 Final Exam textures are NOT swizzled.
#
# Layout:
#
#     R G B A
#
# Converted to BGRA internally.
# =========================================================

def decode_rgba(raw, width, height):

    out = bytearray(width * height * 4)

    for i in range(width * height):

        r = raw[i*4 + 0]
        g = raw[i*4 + 1]
        b = raw[i*4 + 2]
        a = raw[i*4 + 3]

        out[i*4 + 0] = b
        out[i*4 + 1] = g
        out[i*4 + 2] = r
        out[i*4 + 3] = a

    return bytes(out)


# =========================================================
#                  PS3 SWIZZLE HELPERS
# =========================================================
# PS3 swizzled textures use Morton/Z-order tiling.
# =========================================================

def morton2(x, y):

    answer = 0

    for i in range(16):

        answer |= ((x >> i) & 1) << (2 * i)
        answer |= ((y >> i) & 1) << (2 * i + 1)

    return answer


def morton_index_rect(x, y, width, height):

    # Final Exam uses standard Morton layout
    return morton2(x, y)


# =========================================================
#                PS3 SWIZZLED RGBA
# =========================================================
# Mipmapped PS3 ARGB textures are swizzled.
#
# Stored format:
#
#     R G B A
#
# Swizzled using Morton order.
# Converted internally to BGRA.
# =========================================================

def decode_rgba_ps3_swizzled(raw, width, height):

    out = bytearray(width * height * 4)

    for y in range(height):
        for x in range(width):

            src = morton_index_rect(x, y, width, height) * 4
            dst = (y * width + x) * 4

            if src + 3 >= len(raw):
                continue

            out[dst + 0] = raw[src + 2]  # B
            out[dst + 1] = raw[src + 1]  # G
            out[dst + 2] = raw[src + 0]  # R
            out[dst + 3] = raw[src + 3]  # A

    return bytes(out)