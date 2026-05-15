import os
from PIL import Image

from .xbox_codecs import (
    encode_xbox_r5g6b5,
    encode_xbox_a1r5g5b5,
    encode_xbox_a8r8g8b8,
)

from .xbox_codecs import (
    decode_xbox_r5g6b5,
    decode_xbox_a1r5g5b5,
    decode_xbox_a8r8g8b8,
    encode_xbox_r5g6b5,
    encode_xbox_a1r5g5b5,
    encode_xbox_a8r8g8b8
)

# ==============================
#          EXTRACT
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

# ==============================
#        XBR FILE CLASS
# ==============================
class XbrTexture:
    def __init__(self):
        self.Index = 0
        self.Name = ""
        self.Width = 0
        self.Height = 0
        self.ImageOffset = 0
        self.ImageSize = 0
        self.Format = 0
        self.Platform = "Xbox"


class XbrFile:

    def __init__(self, path):

        with open(path, "rb") as f:
            self.Data = bytearray(f.read())

        data = self.Data

        def u32(off):
            return int.from_bytes(data[off:off+4], "little")

        table_size  = u32(0x00)
        file_size   = u32(0x04)
        data_offset = u32(0x08)

        tex_count = table_size // 20

        entries = []

        for i in range(tex_count):

            off = 0x0C + i * 20

            rel  = u32(off + 4)
            fmt  = u32(off + 12)

            entries.append((rel, fmt))

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

        self.Textures = []

        for i in range(tex_count):

            rel, fmt = entries[i]

            abs_off = data_offset + rel

            next_off = (
                file_size
                if i + 1 >= tex_count
                else data_offset + entries[i + 1][0]
            )

            size = next_off - abs_off

            color = (fmt >> 8) & 0xFF
            sizeU = (fmt >> 20) & 0xF
            sizeV = (fmt >> 24) & 0xF

            tex = XbrTexture()

            tex.Index = i
            tex.Name = names[i] if i < len(names) else f"tex_{i:03d}"
            tex.Width = 1 << sizeU
            tex.Height = 1 << sizeV
            tex.ImageOffset = abs_off
            tex.ImageSize = size
            tex.Format = color

            self.Textures.append(tex)

    def save(self, path):

        with open(path, "wb") as f:
            f.write(self.Data)

class XbrTexture:
    pass


class XbrFile:

    def __init__(self, path):

        with open(path, "rb") as f:
            self.Data = bytearray(f.read())

        data = self.Data

        def u32(off):
            return int.from_bytes(data[off:off+4], "little")

        self.DataOffset = u32(0x08)

        table_size = u32(0x00)
        file_size  = u32(0x04)

        tex_count = table_size // 20

        entries = []

        for i in range(tex_count):

            off = 0x0C + i * 20

            rel = u32(off + 4)
            fmt = u32(off + 12)

            entries.append((rel, fmt))

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

        self.Textures = []

        for i in range(tex_count):

            rel, fmt = entries[i]

            abs_off = self.DataOffset + rel

            next_off = (
                file_size
                if i + 1 >= tex_count
                else self.DataOffset + entries[i + 1][0]
            )

            size = next_off - abs_off

            color = (fmt >> 8) & 0xFF
            sizeU = (fmt >> 20) & 0xF
            sizeV = (fmt >> 24) & 0xF

            tex = XbrTexture()

            tex.Index = i
            tex.Name = names[i] if i < len(names) else f"tex_{i:03d}"

            tex.Width  = 1 << sizeU
            tex.Height = 1 << sizeV

            tex.Format = color

            tex.ImageOffset = abs_off
            tex.ImageSize   = size

            tex.Platform = "Xbox"

            self.Textures.append(tex)

    def ReplaceImageBytes(self, tex, new_image, level0_bytes):

        if level0_bytes > tex.ImageSize:
            raise Exception(
                f"Encoded mip0 ({level0_bytes}) exceeds slot ({tex.ImageSize})"
            )

        start = tex.ImageOffset

        self.Data[start:start+level0_bytes] = new_image

    def Save(self, out_path):

        with open(out_path, "wb") as f:
            f.write(self.Data)

# ==============================
#          REBUILD
# ==============================
def rebuild_xbr(xbr: XbrFile, png_folder: str, output_file: str):
    """
    Rebuild an Xbox XBR file using PNGs from a folder.
    """

    print(f"[+] Rebuilding XBR using PNGs from: {png_folder}")

    for tex in xbr.Textures:
        png_name = tex.Name + ".png"
        png_path = os.path.join(png_folder, png_name)

        if not os.path.exists(png_path):
            print(f"[!] PNG not found for texture {tex.Name}, keeping original")
            continue

        print(f"[{tex.Index}] Rebuilding {tex.Name} from {png_name}")

        # Load RGBA data
        img = Image.open(png_path).convert("RGBA")
        width, height = img.size
        rgba = img.tobytes()  # bytes in RGBA order

        # Encode according to Xbox format
        if tex.Format == 0x05:  # R5G6B5
            encoded = encode_xbox_r5g6b5(rgba, width, height)
        elif tex.Format == 0x02:  # A1R5G5B5
            encoded = encode_xbox_a1r5g5b5(rgba, width, height)
        elif tex.Format == 0x06:  # A8R8G8B8
            encoded = encode_xbox_a8r8g8b8(rgba, width, height)
        else:
            print(f"[!] Unsupported format 0x{tex.Format:02X} for {tex.Name}, skipping")
            continue

        # Replace level 0 image bytes in XBR file
        xbr.ReplaceImageBytes(tex, encoded, len(encoded))

    # Save rebuilt XBR
    xbr.Save(output_file)
    print(f"[+] Rebuilt XBR saved as {output_file}")