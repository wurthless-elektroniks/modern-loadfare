import sys
import struct
from zlib import crc32
from cbheader import get_cb_version

# base kernel never changes
CE_1888_CRC32 = 0xff9b60df

KERNEL_CRC_ENTRIES = {
    # Blades
    6717: {
        'cf': 0x796c7a1f,
        'cg': 0x3180015f
    },
    # NXE
    9199: {
        'cf': 0xf19cf13f,
        'cg': 0x61d7b727
    },
    # Kinect
    13604: {
        'cf': 0xdf80ba19,
        'cg': 0x34237cd1
    },
    # Nu Metro
    17559: {
        'cf': 0x0883e155,
        'cg': 0x10fbc84d
    }
}

#
# For calculating CRC-32s of loaders (from xeBuild docs):
#
# "note, with bls the following is true (before calculating CRC for an ini):
# - the file is truncated to the u32 size found at offset 0xC
# - CB/CB_A/CB_B 0x0 fill: @0x10 for 0x30 bytes
# - CD 0x0 fill: @0x10 for 0x10"
#

def _truncate_loader_for_crc32_calc(loader: bytes) -> bytes:
    data_size = struct.unpack(">I", loader[0x0C:0x10])[0]
    return loader[:data_size]

def _calc_cb_crc32(cbb: bytes) -> int:
    truncated = bytearray(_truncate_loader_for_crc32_calc(cbb))
    truncated[0x10:0x40] = bytes([0] * 0x30)
    return crc32(truncated)

def _calc_cd_crc32(cd: bytes):
    truncated = bytearray(_truncate_loader_for_crc32_calc(cd))
    truncated[0x10:0x20] = bytes([0] * 0x10)
    return crc32(truncated)

def print_glitch2_crc32s(cba: bytes,
                         cbb: bytes,
                         cd: bytes,
                         kernel_version: int,
                         printstream=sys.stdout):
    if kernel_version not in KERNEL_CRC_ENTRIES:
        raise RuntimeError(f"unrecognized kernel version: {kernel_version}")

    print(f"cba_{get_cb_version(cba)}.bin,{_calc_cb_crc32(cba):08x}", file=printstream)
    print(f"cbb_{get_cb_version(cbb)}.bin,{_calc_cb_crc32(cbb):08x}", file=printstream)
    print(f"cd_{get_cb_version(cd)}.bin,{_calc_cd_crc32(cd):08x}", file=printstream)
    print(f"ce_1888.bin,{CE_1888_CRC32:08x}", file=printstream)
    print(f"cf_{kernel_version}.bin,{KERNEL_CRC_ENTRIES[kernel_version]['cf']:08x}", file=printstream)
    print(f"cg_{kernel_version}.bin,{KERNEL_CRC_ENTRIES[kernel_version]['cg']:08x}", file=printstream)
