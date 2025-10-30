import struct

def _count_bits_val16(value):
    counted = 0
    for _ in range(0,16):
        if (value & 1) != 0:
            counted += 1
        value >>= 1
    return counted

def parse_cb_ldv(cbb: bytes):
    bitfield = struct.unpack(">H", cbb[0x3B2:0x3B4])[0]
    return {
        'bitfield': bitfield,
        'ldv': _count_bits_val16(bitfield)
    }

def get_cb_version(cbb: bytes):
    return struct.unpack(">H", cbb[2:4])[0]
