# ==============================
#      RenderWare Helpers
# ==============================
def iter_chunks(data, start, end):

    off = start

    while off + 12 <= end:

        chunk_id = int.from_bytes(data[off:off+4], "little")

        size = int.from_bytes(data[off+4:off+8], "little")

        version = int.from_bytes(data[off+8:off+12], "little")

        body_start = off + 12
        body_end   = body_start + size

        yield {
            "id": chunk_id,
            "size": size,
            "version": version,
            "body_start": body_start,
            "body_end": body_end
        }

        off += 12 + size