def read_be_u32(data, off):
    return (data[off] << 24) | (data[off+1] << 16) | (data[off+2] << 8) | data[off+3]

def read_u16_le(data, pos):
    return data[pos] | (data[pos + 1] << 8)

def read_u16_be(data, pos):
    return (data[pos] << 8) | data[pos + 1]

def read_u32_le(data, off):
    return data[off] | (data[off+1] << 8) | (data[off+2] << 16) | (data[off+3] << 24)