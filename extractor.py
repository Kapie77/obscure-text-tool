import struct
import os


def read_be_u32(data, off):
    return (data[off] << 24) | (data[off+1] << 16) | (data[off+2] << 8) | data[off+3]


def is_printable(b):
    return 32 <= b < 127


def is_valid_name(data, off):
    if off >= len(data):
        return False

    name_len = data[off]
    if name_len < 1 or name_len > 48:
        return False

    if off + 1 + name_len > len(data):
        return False

    for i in range(name_len):
        if not is_printable(data[off + 1 + i]):
            return False

    return True


def is_valid_texture_entry(data, off):
    if not is_valid_name(data, off):
        return False

    name_len = data[off]
    p = off + 1 + name_len

    if p + 28 > len(data):
        return False

    width = read_be_u32(data, p)
    height = read_be_u32(data, p + 4)
    gx = read_be_u32(data, p + 16)
    size = read_be_u32(data, p + 24)

    if width not in [4,8,16,32,64,128,256,512,1024]:
        return False
    if height not in [4,8,16,32,64,128,256,512,1024]:
        return False

    if gx not in [1,3,5,6,8,9,14]:
        return False

    if size <= 0 or size > len(data):
        return False

    if p + 28 + size > len(data):
        return False

    return True


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

        data_offset = p + 28

        print(f"\n[{i}] {name}")
        print(f"Size: {width}x{height}")
        print(f"Format: {gx}")
        print(f"Data size: {size}")

        tex_data = data[data_offset:data_offset+size]

        # salva raw (por enquanto)
        with open(os.path.join(out_folder, f"{name}.bin"), "wb") as out:
            out.write(tex_data)

        # encontrar próximo entry
        min_next = data_offset + size
        next_offset = None

        for cand in range(min_next, min(min_next + 4096, len(data))):
            if is_valid_texture_entry(data, cand):
                next_offset = cand
                break

        if next_offset is None:
            print("[!] Não encontrou próxima entrada — fim")
            break

        offset = next_offset

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python extractor.py arquivo.dic")
        sys.exit(1)

    input_file = sys.argv[1]
    output_folder = "out"

    parse_wii_dic(input_file, output_folder)