'''
xeBuild patchlist generator
'''

import struct

class Patch():
    def __init__(self, start_address: int):
        self._start_address = start_address
        self._bits = bytearray()

    def push(self, bits32: bytes):
        if len(bits32) != 4:
            raise RuntimeError("bits32 must be 4 bytes long")
        self._bits += bits32

    def serialize(self) -> bytes:
        header = struct.pack(">II", self._start_address, int(len(self._bits) / 4))
        return header + self._bits

def xebuild_patchlist_make(cbb_original: bytes, cbb_patched: bytes) -> bytes:
    if len(cbb_original) != len(cbb_patched):
        raise RuntimeError("original/patched not the same length")

    patchlist = []
    pos = 0
    current_patch = None
    while pos < len(cbb_original):
        original_bytes = cbb_original[pos:pos+4]
        patched_bytes  = cbb_patched[pos:pos+4]
        if original_bytes == patched_bytes:
            if current_patch is not None:
                patchlist.append(current_patch)
                current_patch = None
                print(f"xebuild_patchlist_make: diff end {pos:08x}")
        else:
            if current_patch is None:
                current_patch = Patch(pos)
                print(f"xebuild_patchlist_make: diff start {pos:08x}")

            current_patch.push(patched_bytes)

        pos += 4
    bytes_out = bytearray()
    for patch in patchlist:
        bytes_out += patch.serialize()
    bytes_out += bytes([ 0xFF, 0xFF, 0xFF, 0xFF ])
    return bytes_out
