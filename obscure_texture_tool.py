import sys
import os
import argparse
from PIL import Image # pro rebuild do .hvi de ps2

from utils.binary import read_be_u32
from utils.binary import read_u32_le

# import detection #
from utils.detection import (
    is_finalexam_hvt,
    looks_like_psp_dic,
    looks_like_wii_dic
)

# import .dip #
from formats.pc.pc_dip import (
    parse_pc_dip,
    rebuild_pc_dip_file
)

# import .dic (pc) #
from formats.pc.pc_dic import (
    parse_pc_dic,
    rebuild_pc_dic_file
)

# import .dic (ps2) #
from formats.ps2.ps2_dic import (
    parse_ps2_dic,
    rebuild_ps2_dic_file
)

# import .dic (psp) #
from formats.psp.psp_dic import rebuild_psp_dic_file

# import .hvi (psp/ps2) #
from formats.common.ps2_psp_hvi import parse_ps2_psp_hvi

# import .hvi (psp) #
from formats.common.ps2_psp_hvi import (
    decode_psp_hvi,
    #parse_ps2_psp_hvi,
    encode_psp_hvi
)

# import .hvi (ps2) #
from formats.ps2.ps2_codecs_hvi import (
    decode_ps2_hvi,        # decode HVI
    encode_ps2_hvi,        # rebuild HVI
    encode_ps2_8bpp_hvi,   # rebuild HVI 8bpp
    encode_ps2_4bpp_hvi    # rebuild HVI 4bpp
)

# import .dic (wii) #
from formats.wii.wii_dic import parse_wii_dic
from formats.wii.wii_dic import rebuild_wii_dic

# import .hvt (wii) #
from formats.wii.wii_hvt import (
    parse_wii_hvt,
    rebuild_wii_hvt
)

# import .dic (psp) #
from formats.psp.psp_dic import parse_psp_dic

# import .hvt (pc/ps3/xbox 360) do final exam #
from formats.finalexam.finalexam_hvt import (
    parse_finalexam_hvt,
    rebuild_finalexam_hvt
)

from formats.xbox.xbox_xbr import parse_xbox_xbr
from formats.xbox.xbox_xbr import XbrFile

# encode do .xbr de xbox
from formats.xbox.xbox_codecs import (
    # encode
    encode_xbox_r5g6b5,
    encode_xbox_a1r5g5b5,
    encode_xbox_a8r8g8b8,
)

# ==============================
#      DETECTAÇÃO DE MODO 
#  (DRAG AND DROP OU COMANDO)
# ===============================
def detect_args(argv):
    """
    Suporte:
    - drag file -> extract
    - drag file + folder -> rebuild
    - CLI: extract/rebuild file folder
    """

    args = [a.strip().strip('"') for a in argv[1:]]

    if len(args) == 0:
        return None

    # CLI tradicional
    if args[0] in ["extract", "rebuild"]:
        mode = args[0]
        input_path = args[1] if len(args) > 1 else None
        folder = args[2] if len(args) > 2 else None
        return mode, input_path, folder

    # drag & drop / auto mode
    if len(args) == 1:
        return "extract", args[0], None

    if len(args) == 2:

        a, b = args

        if os.path.isdir(a) and os.path.isfile(b):
            return "rebuild", b, a

        if os.path.isfile(a) and os.path.isdir(b):
            return "rebuild", a, b

        # fallback
        return "rebuild", a, b

    return None


# ==============================
#           CLI
# ==============================
if __name__ == "__main__":

    parsed = detect_args(sys.argv)

    if not parsed:
        print("""
Usage:
  extract file.ext
  rebuild file.ext folder/
  OR drag & drop:
  - file -> extract
  - file + folder -> rebuild
""")
        sys.exit(0)

    mode, input_path, folder = parsed

    if not input_path:
        print("[!] Missing input file")
        sys.exit(1)

    base, ext = os.path.splitext(os.path.basename(input_path))
    ext = ext.lower()
    input_dir = os.path.dirname(input_path)

    # =========================
    # REBUILD MODE
    # =========================
    if mode == "rebuild":

        png_folder = folder

        if not png_folder:
            print("[!] Missing folder for rebuild")
            sys.exit(1)

        print(f"[+] Rebuild mode, loading PNGs from: {png_folder}")

        base_name, ext = os.path.splitext(os.path.basename(input_path))

        output_file = f"{os.path.join(input_dir, base_name)}.new{ext}"

        # =========================
        # DIC
        # =========================
        if ext == ".dic":

            with open(input_path, "rb") as f:
                data = f.read()

            # PS2
            if len(data) >= 4:
                rw_id = int.from_bytes(data[0:4], "little")

                if rw_id == 0x16:

                    print("[+] Detected PS2 DIC")

                    rebuild_ps2_dic_file(
                        input_path,
                        png_folder,
                        output_file
                    )

                    sys.exit(0)

            # PSP
            # === psp (.dic) ==== #
            if looks_like_psp_dic(data):

                print("[+] PSP signature validated")

                rebuild_psp_dic_file(
                    input_path,
                    png_folder,
                    output_file
                )

                sys.exit(0)

            # Wii
            if looks_like_wii_dic(data):
                print("[+] Detected Wii DIC, starting rebuild")

                # Reconstrói o DIC Wii
                rebuild_wii_dic(
                    input_path,
                    png_folder,
                    output_file
                )
                sys.exit(0)

            # PC
            print("[+] Detected PC DIC")

            rebuild_pc_dic_file(
                input_path,
                png_folder,
                output_file
            )

            sys.exit(0)
        
        # =========================
        # HVT
        # =========================
        elif ext == ".hvt":

            # Final Exam
            if is_finalexam_hvt(input_path):

                print("[+] Detected Final Exam HVT")

                hvt_name = os.path.splitext(os.path.basename(input_path))[0]

                png_path = os.path.join(
                    png_folder,
                    hvt_name + ".png"
                )

                if not os.path.isfile(png_path):

                    print(f"[!] PNG not found for rebuild: {png_path}")
                    sys.exit(1)

                rebuild_finalexam_hvt(
                    input_path,
                    png_path,
                    output_file
                )

                sys.exit(0)

            # Wii
            else:

                print("[+] Detected Wii HVT")

                rebuild_wii_hvt(
                    input_path,
                    png_folder,
                    output_file
                )

                sys.exit(0)

        # =========================
        # DIP
        # =========================
        elif ext == ".dip":

            print("[+] Detected PC DIP")

            rebuild_pc_dip_file(
                input_path,
                png_folder,
                output_file
            )

            sys.exit(0)

        # =========================
        # XBR
        # =========================
        elif ext == ".xbr":

            from formats.xbox.xbox_xbr import XbrFile, rebuild_xbr

            print("[+] Detected Xbox XBR")

            # Carrega o arquivo XBR
            xbr = XbrFile(input_path)

            # Reconstrói usando os PNGs da pasta
            rebuild_xbr(xbr, png_folder, output_file)

            sys.exit(0)
        
        # =========================
        # HVI (PS2 / PSP)
        # =========================
        elif ext == ".hvi":

            print("[+] Detected PS2/PSP HVI")

            # Carrega HVI original
            with open(input_path, "rb") as f:
                data = f.read()

            width  = int.from_bytes(data[0x0C:0x10], "little")
            height = int.from_bytes(data[0x10:0x14], "little")

            # detecta plataforma
            is_psp = width <= 480 and height <= 272

            hvi_name = os.path.splitext(os.path.basename(input_path))[0]
            png_path = os.path.join(png_folder, hvi_name + ".png")

            if not os.path.isfile(png_path):
                print(f"[!] PNG not found for rebuild: {png_path}")
                sys.exit(1)

            # Abre o PNG
            img = Image.open(png_path).convert("RGBA")

            # =========================
            # PS2 rebuild
            # =========================
            if not is_psp:
                # usa palette original
                palette = data[0x18:0x18+1024]
                new_pixels, new_palette = encode_ps2_8bpp_hvi(img, width, height, palette)
            
            # =========================
            # PSP rebuild
            # =========================
            else:
                palette = data[0x18:0x18+1024]
                pixel_data = data[0x18+1024:0x18+1024+width*height]  # índices originais
                new_pixels, _ = encode_psp_hvi(img, width, height, palette)

            # =========================
            # Salva o HVI reconstruído
            # =========================
            output_file = os.path.join(input_dir, hvi_name + ".new.hvi")
            with open(output_file, "wb") as f:
                f.write(data[:0x18])        # header
                f.write(palette)            # palette
                f.write(new_pixels)         # pixel data
                if len(data) > 0x18 + 1024:
                    f.write(data[0x18+1024:])  # trailer se existir

            print(f"[+] Rebuilt HVI saved: {output_file}")
            sys.exit(0)

    # ==========================
    #         EXTRAÇÃO
    # ===========================
    elif mode == "extract":

        final_out = os.path.join(input_dir, base)
        os.makedirs(final_out, exist_ok=True)

        # =========================
        # HVT (Wii ou Final Exam)
        # =========================
        if ext == ".hvt":
            # Final Exam
            if is_finalexam_hvt(input_path):

                print("[+] Detected Final Exam HVT")

                parse_finalexam_hvt(
                    input_path,
                    final_out
                )

            # Wii
            else:

                print("[+] Detected Wii HVT")

                parse_wii_hvt(
                    input_path,
                    final_out
                )

        # =================
        # HVI (PS2/PSP)
        # =================
        elif ext == ".hvi":

            with open(input_path, "rb") as f:
                magic = f.read(4)

            if magic == b"HVI ":

                print("[+] Detected HVI")

                parse_ps2_psp_hvi(
                    input_path,
                    final_out
                )

            else:
                print("[!] Invalid HVI file")

        # =========================
        # DIC (multi-plataforma)
        # =========================
        elif ext == ".dic":

            with open(input_path, "rb") as f:
                data = f.read()

            # =================================
            # PS2 (RenderWare)
            # =================================
            rw_id = int.from_bytes(data[0:4], "little")

            if rw_id == 0x16:

                print("[+] Detected PS2 DIC")

                parse_ps2_dic(
                    input_path,
                    final_out
                )

                sys.exit(0)

            # =================================
            # PSP
            # =================================
            if looks_like_psp_dic(data):

                print("[+] Detected PSP DIC")

                parse_psp_dic(
                    input_path,
                    final_out
                )

                sys.exit(0)

            # =================================
            # Wii
            # =================================
            if len(data) > 64:

                count_be = read_be_u32(data, 0)

                if 0 < count_be < 4096:

                    name_len = data[7]

                    if 1 <= name_len <= 48:

                        printable = all(
                            32 <= data[8+i] < 127
                            for i in range(name_len)
                        )

                        if printable:
                            print("[+] Detected Wii DIC")
                            parse_wii_dic(input_path, final_out)
                            sys.exit(0)

            # =================================
            # PC fallback
            # =================================
            print("[+] Detected PC DIC")
            parse_pc_dic(input_path, final_out)
            
        # =========================
        # XBR (Xbox)
        # =========================
        elif ext == ".xbr":
            with open(input_path, "rb") as f:
                data = f.read(12)

            if len(data) >= 12:
                table_size  = int.from_bytes(data[0:4], "little")
                data_offset = int.from_bytes(data[8:12], "little")

                # heurística básica válida
                if table_size % 20 == 0 and data_offset > 0:
                    print("[+] Detected Xbox XBR")
                    parse_xbox_xbr(input_path, final_out)
                else:
                    print("[!] Invalid XBR file")
            else:
                print("[!] File too small")
        
        # =========================
        # DIP (PC - Obscure 1)
        # =========================
        elif ext == ".dip":
            print("[+] Detected PC DIP")
            parse_pc_dip(input_path, final_out)

        else:
            print("[!] Unknown file type")