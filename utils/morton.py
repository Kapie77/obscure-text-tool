def morton_part1(v):
    v &= 0x0000FFFF
    v = (v | (v << 8)) & 0x00FF00FF
    v = (v | (v << 4)) & 0x0F0F0F0F
    v = (v | (v << 2)) & 0x33333333
    v = (v | (v << 1)) & 0x55555555
    return v

def morton_index(x, y):
    return morton_part1(x) | (morton_part1(y) << 1)

def morton_index_rect(x, y, width, height):

    if width == height:
        return morton_index(x, y)

    if width > height:
        block = x // height
        return block * height * height + morton_index(x % height, y)

    row_block = y // width
    return row_block * width * width + morton_index(x, y % width)