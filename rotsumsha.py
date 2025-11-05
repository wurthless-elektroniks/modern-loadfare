'''
"RotSumSha" variant of SHA-1

SHA-1 was known to be vulnerable to collision attacks in the early 2000s so Microsoft
created the RotSumSha variant to make hash collisions even less viable.

The algorithm basically is:
- Calculate a 256-bit checksum of the data we're about to hash
- Feed the checksum into the SHA-1 state twice
- Feed the data to be hashed into the SHA-1 state
- Invert all bits of the 256-bit checksum
- Feed the inverted checksum into the SHA-1 state twice
- Compute the final digest

This is a really good example of how far Microsoft went to lock down the Xbox 360
against any sort of software-based modification. Their paranoia was a bit overblown
because even today it's prohibitively expensive for the average Joe to generate a
SHA-1 collision. Obviously that didn't stop kernel exploits (KK/JTAG and BadUpdate),
and it certainly didn't stop RGH...
'''

import struct
import hashlib

def _checksum_calc(buffer: bytes, seeds: list):
    a = seeds[0]
    b = seeds[1]
    c = seeds[2]
    d = seeds[3]
    offset = 0

    while offset < len(buffer):
        val = struct.unpack(">Q", buffer[offset:offset+8])[0]
        offset += 8

        b = val + b
        d = d - val

        b &= 0xFFFFFFFFFFFFFFFF
        d &= 0xFFFFFFFFFFFFFFFF

        if b < val:
            a += 1
        if val < d:
            c -= 1

        b = b * 0x20000000 | b >> 0x23
        d = d * 0x80000000 | d >> 0x21

        a &= 0xFFFFFFFFFFFFFFFF
        b &= 0xFFFFFFFFFFFFFFFF
        c &= 0xFFFFFFFFFFFFFFFF
        d &= 0xFFFFFFFFFFFFFFFF

    return [a,b,c,d]

def rotsumsha_calc(first_buffer: bytes, second_buffer: bytes) -> bytes:
    first_seeds = _checksum_calc(first_buffer, [0,0,0,0])
    checksum_ints = _checksum_calc(second_buffer, first_seeds)

    checksum_bytes = struct.pack(">QQQQ", checksum_ints[0], checksum_ints[1], checksum_ints[2], checksum_ints[3])

    sha = hashlib.sha1()
    sha.update(checksum_bytes)
    sha.update(checksum_bytes)

    sha.update(first_buffer) # header
    sha.update(second_buffer) # rest of data
    
    checksum_ints[0] = (~checksum_ints[0]) & 0xFFFFFFFFFFFFFFFF
    checksum_ints[1] = (~checksum_ints[1]) & 0xFFFFFFFFFFFFFFFF
    checksum_ints[2] = (~checksum_ints[2]) & 0xFFFFFFFFFFFFFFFF
    checksum_ints[3] = (~checksum_ints[3]) & 0xFFFFFFFFFFFFFFFF
    checksum_bytes = struct.pack(">QQQQ", checksum_ints[0], checksum_ints[1], checksum_ints[2], checksum_ints[3])
    sha.update(checksum_bytes)
    sha.update(checksum_bytes)

    return sha.digest()
