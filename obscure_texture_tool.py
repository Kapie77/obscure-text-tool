import os
import argparse

from utils.binary import read_be_u32

from utils.detection import (
    is_finalexam_hvt,
    looks_like_psp_dic
)

from formats.pc.pc_dic import parse_pc_dic
from formats.pc.pc_dip import parse_pc_dip
from formats.ps2.ps2_dic import parse_ps2_dic
from formats.ps2.ps2_hvi import parse_ps2_hvi
from formats.psp.psp_dic import parse_psp_dic
from formats.wii.wii_dic import parse_wii_dic

from formats.xbox.xbox_xbr import parse_xbox_xbr
from formats.xbox360.xbox360_hvt import parse_finalexam_hvt


# ==============================
#           CLI
# ==============================
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("input")

    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.input))[0]
    input_dir = os.path.dirname(args.input)

    final_out = os.path.join(input_dir, base_name)
    os.makedirs(final_out, exist_ok=True)

    ext = os.path.splitext(args.input)[1].lower()

    # =========================
    # HVT (Wii ou Final Exam)
    # =========================
    if ext == ".hvt":
        if is_finalexam_hvt(args.input):
            print("[+] Detected Final Exam HVT")
            parse_finalexam_hvt(args.input, final_out)

    # =========================
    # HVI (PS2)
    # =========================
    elif ext == ".hvi":
        with open(args.input, "rb") as f:
            magic = f.read(4)

        if magic == b"HVI ":
            print("[+] Detected PS2 HVI")
            parse_ps2_hvi(args.input, final_out)
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
        if len(data) >= 4:
            rw_id = int.from_bytes(data[0:4], "little")

            if rw_id == 0x16:
                print("[+] Detected PS2 DIC (RenderWare)")
                parse_ps2_dic(args.input, final_out)
                exit()

        # =================================
        # PSP
        # =================================
        if looks_like_psp_dic(data):
            print("[+] Detected PSP DIC")
            parse_psp_dic(args.input, final_out)
            exit()

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