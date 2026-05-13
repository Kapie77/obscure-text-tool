import sys
import os
import argparse

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

from formats.ps2.ps2_codecs import (
    # decode
    decode_ps2_8bpp,
    decode_ps2_4bpp,
    decode_ps2_rgba8888,
    decode_ps2_rgb5551,

    # encode
    encode_ps2_8bpp,
    encode_ps2_4bpp,
    encode_ps2_rgba8888,
    encode_ps2_rgb5551,
)

from formats.psp.psp_dic import parse_psp_dic
from formats.wii.wii_dic import parse_wii_dic

from formats.common.ps2_psp_hvi import parse_ps2_psp_hvi

from formats.xbox.xbox_xbr import parse_xbox_xbr
from formats.finalexam.finalexam_hvt import parse_finalexam_hvt
from formats.xbox.xbox_xbr import XbrFile

from formats.xbox.xbox_codecs import (
    encode_xbox_r5g6b5,
    encode_xbox_a1r5g5b5,
    encode_xbox_a8r8g8b8,
)

# ==============================
#           CLI
# ==============================
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Obscure Texture Tool CLI")
    parser.add_argument("input", help="DIC/HVT/XBR/etc. file")
    parser.add_argument("--rebuild", "-r", help="Page containing edited PNGs for the reconstruction")
    args = parser.parse_args()

    input_path = args.input
    base, ext = os.path.splitext(os.path.basename(input_path))
    ext = ext.lower()
    input_dir = os.path.dirname(input_path)

    # arquivo rebuild padrão: mesmo nome + .new antes da extensão
    output_file = f"{os.path.join(input_dir, base)}.new{ext}"

    # =========================
    # Rebuild mode
    # =========================
    if args.rebuild:

        png_folder = args.rebuild

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

                    exit(0)

            # PSP
            # === psp (.dic) ==== #
            if looks_like_psp_dic(data):

                print("[+] PSP signature validated")

                rebuild_psp_dic_file(
                    input_path,
                    png_folder,
                    output_file
                )

                exit(0)

            # Wii
            if looks_like_wii_dic(data):
                print("[+] Wii DIC rebuild not implemented")
                exit(1)

            # PC
            print("[+] Detected PC DIC")

            rebuild_pc_dic_file(
                input_path,
                png_folder,
                output_file
            )

            exit(0)

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

            exit(0)

        # =========================
        # XBR
        # =========================
        elif ext == ".xbr":

            # seu código atual do xbr aqui

            exit(0)

        else:
            print("[!] Rebuild not supported")
            exit(1)

    # ==========================
    #         EXTRAÇÃO
    # ===========================
    final_out = os.path.join(input_dir, base)
    os.makedirs(final_out, exist_ok=True)
    # =========================
    # HVT (Wii ou Final Exam)
    # =========================
    if ext == ".hvt":
        if is_finalexam_hvt(args.input):
            print("[+] Detected Final Exam HVT")
            parse_finalexam_hvt(args.input, final_out)

    # =================
    # HVI (PS2/PSP)
    # =================
    elif ext == ".hvi":

        with open(args.input, "rb") as f:
            magic = f.read(4)

        if magic == b"HVI ":

            print("[+] Detected HVI")

            parse_ps2_psp_hvi(
                args.input,
                final_out
            )

        else:
            print("[!] Invalid HVI file")

    # =========================
    # DIC (multi-plataforma)
    # =========================
    elif ext == ".dic":

        with open(args.input, "rb") as f:
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

            exit(0)

        # =================================
        # PSP
        # =================================
        if looks_like_psp_dic(data):

            print("[+] Detected PSP DIC")

            parse_psp_dic(
                input_path,
                final_out
            )

            exit(0)

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
                        parse_wii_dic(args.input, final_out)
                        exit()

        # =================================
        # PC fallback
        # =================================
        print("[+] Detected PC DIC")
        parse_pc_dic(args.input, final_out)
        
    # =========================
    # XBR (Xbox)
    # =========================
    elif ext == ".xbr":
        with open(args.input, "rb") as f:
            data = f.read(12)

        if len(data) >= 12:
            table_size  = int.from_bytes(data[0:4], "little")
            data_offset = int.from_bytes(data[8:12], "little")

            # heurística básica válida
            if table_size % 20 == 0 and data_offset > 0:
                print("[+] Detected Xbox XBR")
                parse_xbox_xbr(args.input, final_out)
            else:
                print("[!] Invalid XBR file")
        else:
            print("[!] File too small")
    
    # =========================
    # DIP (PC - Obscure 1)
    # =========================
    elif ext == ".dip":
        print("[+] Detected PC DIP")
        parse_pc_dip(args.input, final_out)

    else:
        print("[!] Unknown file type")