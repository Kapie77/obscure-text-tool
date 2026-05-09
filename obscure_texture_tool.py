import os
import argparse
from PIL import Image

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
from formats.finalexam.finalexam_hvt import parse_finalexam_hvt
from formats.xbox.xbox_xbr import XbrFile

from formats.xbox.xbox_codecs import (
    encode_xbox_r5g6b5,
    encode_xbox_a1r5g5b5,
    encode_xbox_a8r8g8b8,
)

# ================================
#      Rebuild Helpers
# ================================
def replace_image_bytes(dic_data: bytearray, tex, new_image: bytes):
    """
    Substitui os bytes da textura no container.
    dic_data: bytearray com o arquivo DIC/HVT completo
    tex: objeto DicTexture
    new_image: bytes da imagem já codificada no formato original
    """
    if len(new_image) != tex.ImageSize:
        raise ValueError(
            f"Encoded image is {len(new_image)} bytes; container slot expects {tex.ImageSize}."
        )
    start = tex.ImageOffset
    dic_data[start:start+len(new_image)] = new_image

def rebuild_dic(dic_file, png_folder, out_path):
    """
    Reconstrói o DIC/HVT com base nos PNGs editados na pasta.
    dic_file: objeto DicFile já carregado
    png_folder: caminho onde estão os PNGs com nomes correspondentes
    out_path: arquivo final a ser salvo
    """
    dic_data = bytearray(dic_file.Data)  # cópia para modificar
    for tex in dic_file.Textures:
        png_path = os.path.join(png_folder, tex.Name + ".png")
        if not os.path.isfile(png_path):
            print(f"[!] PNG not found, skipping: {png_path}")
            continue

        img = Image.open(png_path).convert("RGBA")
        img = img.resize((tex.Width, tex.Height))  # garante o tamanho original
        pixels = img.tobytes()

        # =================================
        # Encode de acordo com a plataforma
        # =================================
        if tex.Platform == "PSP":
            if tex.Format == "PSP_RGBA8888":
                encoded = encode_psp_rgba8888(pixels, tex.Width, tex.Height)
            elif tex.Format in ("PSP_4bpp_swizzled", "PSP_8bpp_swizzled"):
                # opcional: implementar palettized encoding
                raise NotImplementedError("PSP palettized rebuild não implementado ainda")
            else:
                raise NotImplementedError(f"PSP format {tex.Format} not supported")
        elif tex.Platform == "FinalExam":
            from formats.finalexam.finalexam_codec import EncodePs3Argb
            encoded = EncodePs3Argb(tex, pixels)
        else:
            # fallback linear RGBA
            encoded = pixels

        replace_image_bytes(dic_data, tex, encoded)
        print(f"[+] Rebuilt texture: {tex.Name}")

    # salva o arquivo final
    with open(out_path, "wb") as f:
        f.write(dic_data)
    print(f"[+] Saved rebuilt file: {out_path}")

# ================================
#       PSP RGBA8888 Encoder
# ================================
def encode_psp_rgba8888(pixels: bytes, width: int, height: int) -> bytes:
    """
    PSP armazena linear bytes como R,G,B,A mas swizzled no arquivo final.
    """
    from formats.psp.psp_codecs import swizzle_psp
    # converte de RGBA (Pillow) para ordem R,G,B,A do PSP
    linear = bytearray(pixels)
    return swizzle_psp(linear, width, height, 32)


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

        if ext == ".dic" or ext == ".hvt" or ext == ".hvi":
            # usa rebuild_dic como você já tem
            # precisa criar o dic_file com .Textures e .Data
            with open(input_path, "rb") as f:
                file_data = bytearray(f.read())

            dic_file = type("DicFile", (), {"Data": file_data, "Textures": []})()

            if ext == ".dic":
                if looks_like_psp_dic(file_data):
                    print("[+] Detected PSP DIC")
                    parse_psp_dic(input_path, png_folder)
                else:
                    print("[+] Detected PC DIC")
                    parse_pc_dic(input_path, png_folder)
            elif ext == ".hvt":
                if is_finalexam_hvt(input_path):
                    parse_finalexam_hvt(input_path, png_folder)
            elif ext == ".hvi":
                parse_ps2_hvi(input_path, png_folder)

            # Reconstrói e salva
            rebuild_dic(dic_file, png_folder, output_file)
            exit(0)

        elif ext == ".xbr":
            from formats.xbox.xbox_codecs import (
                encode_xbox_r5g6b5,
                encode_xbox_a1r5g5b5,
                encode_xbox_a8r8g8b8,
            )
            xbr = XbrFile(input_path)

            for tex in xbr.Textures:
                png_path = os.path.join(png_folder, tex.Name + ".png")
                if not os.path.isfile(png_path):
                    print(f"[!] PNG not found, skipping: {png_path}")
                    continue

                img = Image.open(png_path).convert("RGBA")
                if img.size != (tex.Width, tex.Height):
                    img = img.resize((tex.Width, tex.Height))
                pixels = img.tobytes()

                if tex.Format == 0x05:
                    encoded = encode_xbox_r5g6b5(pixels, tex.Width, tex.Height)
                elif tex.Format == 0x02:
                    encoded = encode_xbox_a1r5g5b5(pixels, tex.Width, tex.Height)
                elif tex.Format == 0x06:
                    encoded = encode_xbox_a8r8g8b8(pixels, tex.Width, tex.Height)
                else:
                    print(f"[!] Unsupported Xbox format: 0x{tex.Format:02X}")
                    continue

                xbr.ReplaceImageBytes(tex, encoded, len(encoded))
                print(f"[+] Rebuilt texture: {tex.Name}")

            xbr.Save(output_file)
            print(f"[+] Saved rebuilt file: {output_file}")
            exit(0)

        else:
            print("[!] Rebuild only supports .dic, .hvt, .hvi, .xbr")
            exit(1)

        # =========================================================
        # Itera sobre as texturas e reencode
        # =========================================================
        for tex in dic_file.Textures:
            png_path = os.path.join(png_folder, tex.Name + ".png")
            if not os.path.isfile(png_path):
                print(f"[!] PNG not found, skipping: {png_path}")
                continue

            img = Image.open(png_path).convert("RGBA")
            if img.size != (tex.Width, tex.Height):
                img = img.resize((tex.Width, tex.Height))

            pixels = img.tobytes()

            # encode de acordo com plataforma
            if tex.Platform == "PSP" and tex.Format == "PSP_RGBA8888":
                encoded = swizzle_psp(bytearray(pixels), tex.Width, tex.Height, 32)
            elif tex.Platform == "FinalExam":
                encoded = DecodePs3Rgba(pixels, tex.Width, tex.Height)
            elif tex.Platform == "Xbox":

                from formats.xbox.xbox_codecs import (
                    encode_xbox_r5g6b5,
                    encode_xbox_a1r5g5b5,
                    encode_xbox_a8r8g8b8,
                )

                if tex.Format == 0x05:
                    encoded = encode_xbox_r5g6b5(
                        pixels,
                        tex.Width,
                        tex.Height
                    )

                elif tex.Format == 0x02:
                    encoded = encode_xbox_a1r5g5b5(
                        pixels,
                        tex.Width,
                        tex.Height
                    )

                elif tex.Format == 0x06:
                    encoded = encode_xbox_a8r8g8b8(
                        pixels,
                        tex.Width,
                        tex.Height
                    )

                else:
                    print(f"[!] Unsupported Xbox format: 0x{tex.Format:02X}")
                    continue
            else:
                # fallback linear
                encoded = pixels

            # substitui no arquivo
            start = tex.ImageOffset
            dic_file.Data[start:start+len(encoded)] = encoded
            print(f"[+] Rebuilt texture: {tex.Name}")

        # =========================================================
        # Salva arquivo rebuild direto como .new
        # =========================================================
        with open(output_file, "wb") as f:
            f.write(dic_file.Data)

        print(f"[+] Saved rebuilt file: {output_file}")
        exit(0)

    # =========================
    # Caso normal: extração
    # =========================
    final_out = os.path.join(input_dir, base)
    os.makedirs(final_out, exist_ok=True)

    if ext == ".hvt":
        if is_finalexam_hvt(input_path):
            print("[+] Detected Final Exam HVT")
            parse_finalexam_hvt(input_path, final_out)

    elif ext == ".hvi":
        with open(input_path, "rb") as f:
            magic = f.read(4)
        if magic == b"HVI ":
            print("[+] Detected PS2 HVI")
            parse_ps2_hvi(input_path, final_out)
        else:
            print("[!] Invalid HVI file")

    elif ext == ".dic":
        with open(input_path, "rb") as f:
            data = f.read()

        if len(data) >= 4:
            rw_id = int.from_bytes(data[0:4], "little")
            if rw_id == 0x16:
                print("[+] Detected PS2 DIC (RenderWare)")
                parse_ps2_dic(input_path, final_out)
            elif looks_like_psp_dic(data):
                print("[+] Detected PSP DIC")
                parse_psp_dic(input_path, final_out)
            else:
                print("[+] Detected PC DIC")
                parse_pc_dic(input_path, final_out)
    
    elif ext == ".xbr":

        print("[+] Detected Xbox XBR")

        dic_file = XbrFile(input_path)

    else:
        print("[!] Unknown file type")

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