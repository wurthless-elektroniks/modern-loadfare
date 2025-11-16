'''
vfuses patcher for Glitch2m builds and similar
Kept separate from main CB patches for... uh... reasons
'''

from signature import SignatureBuilder, WILDCARD, bulk_find, check_bulk_find_results
from patcher import assemble_branch_with_link

# this 64-bit block move function goes unchanged between all CBs, it seems.
# mostly it's used for moving data from NAND to memory (to load CD), but
# the vfuse patches abuse it to load whatever data it loads.
# this one from 7378
COPY_64BIT_BLOCKS_PATTERN = SignatureBuilder() \
    .pattern([
        0x7c, 0x64, 0x18, 0x50,     # subf       r3,r4,r3
        0x7c, 0xa9, 0x03, 0xa6,     # mtspr      CTR,r5
        0x80, 0xc4, 0x00, 0x00,     # lwz        r6,0x0(r4)
        0x80, 0xe4, 0x00, 0x04,     # lwz        r7,0x4(r4)
        0x78, 0xc7, 0x00, 0x0e,     # rldimi     r7,r6,0x20,0x0
        0x7c, 0xe3, 0x21, 0x2a,     # stdx       r7,r3,r4
        0x38, 0x84, 0x00, 0x08,     # addi       r4,r4,0x8
        0x43, 0x20, 0xff, 0xec,     # bdnz       LAB_00007878
        0x4e, 0x80, 0x00, 0x20,     # blr
    ]) \
    .build()

# first vfuse patch changes this li r4,0x600 to li r4,0x601
# same between 6752 and 7378
VFUSE_LI_600_PATTERN = SignatureBuilder() \
    .pattern([
        0xa0, 0x62, 0x00, 0x06,     # lhz        r3,offset DAT_8000020000010006(r2)
        0x38, 0x80, 0x06, 0x00,     # li         r4,0x600
        0x7c, 0x63, 0x20, 0x78,     # andc       r3,r3,r4
    ]) \
    .build()

def _patch_li_600(cbb: bytes, li_600_address: int) -> bytes:
    base = li_600_address + 7
    cbb[base] = 1

    print(f"_patch_li_600: change byte at 0x{base:04x} from 0 to 1")
    return cbb

# fuse copy loop (i think???)
# on 6752 this is inlined in the fusecheck function.
# on 7378 this is in a separate function that is also called in cd_load_and_jump.
# this one from 7378, register usage differs between builds, hence the wildcards
FUSE_COPY_LOOP_PATTERN = SignatureBuilder() \
    .pattern([
        0x7d, 0x69, 0x07, 0xb4,              # extsw      r9,r11
        0x39, 0x6b, 0x00, 0x40,              # addi       r11,r11,0x40
        0x79, WILDCARD, 0x1f, 0x24,          # rldicr     r8,r9,0x3,0x3c
        0x2f, 0x0b, 0x03, 0x00,              # cmpwi      cr6,r11,0x300
        WILDCARD, WILDCARD, WILDCARD, 0x2a,  # ldarx      r7,r8,r3
        WILDCARD, WILDCARD, 0x00, 0x00,      # std        r7,0x0(r10)
        0x39, 0x4a, 0x00, 0x08,              # addi       r10,r10,0x8
        0x41, 0x98, 0xff, 0xe4,              # blt        cr6,LAB_000076b8
    ]) \
    .build()

def _patch_fuse_copy_loop(cbb: bytes, fuse_copy_loop_address: int, copy_64bit_blocks_address: int) -> bytes:
    # detect if the fuse copy loop is inlined, or if it's in its own function.
    # if it's in its own function (as it is on 7378), alternative patches must be applied
    end_pos = fuse_copy_loop_address + FUSE_COPY_LOOP_PATTERN.size()
    if cbb[end_pos:end_pos+4] != bytes([0x4e, 0x80, 0x00, 0x20]):
        print(f"_patch_fuse_copy_loop: applying inlined patch at 0x{fuse_copy_loop_address:04x}")

        pos = fuse_copy_loop_address

        # same as g2m for falcon/jasper
        # https://github.com/mitchellwaite/glitch2m_17559/blob/main/src/include/cbb_6752.S
        fuse_copy_patch = bytes([
            0xE8, 0x7D, 0x02, 0x58, # ld %r3, 0x258(%r29) - get NAND base
            0x80, 0x83, 0x00, 0x64, # lwz %r4, 0x64(%r3)
            0x80, 0xA3, 0x00, 0x70, # lwz %r5, 0x70(%r3)
            0x7C, 0x63, 0x22, 0x14, # add %r3, %r3, %r4
            0x7C, 0x83, 0x2A, 0x14, # add %r4, %r3, %r5   - point r4 at data we're about to copy
            0x7D, 0x43, 0x53, 0x78, # mr %r3, %r10        - r3 = data copy destination
            0x38, 0xA0, 0x00, 0x0C, # li %r5, 0xc         - r5 = num of 64-bit words to copy
        ])

        cbb[pos:pos+len(fuse_copy_patch)] = fuse_copy_patch
        pos += len(fuse_copy_patch)
        cbb, pos = assemble_branch_with_link(cbb, pos, copy_64bit_blocks_address)

        return cbb
    
    print("_patch_fuse_copy_loop: signature was found in its own function. patch still TODO.")
    print("NOT applying patches here; this could cause crashes later on...")
    return cbb

# some other fuse copy loop in the secengine init function
SECENGINE_FUSE_COPY_LOOP = SignatureBuilder() \
    .pattern([
        0x39, WILDCARD, 0x00, 0x00,     # li         r8,0x0
        0x79, WILDCARD, 0x1f, 0x4c,     # rldimi     r8,r11,0x3,0x1d
        0x39, 0x6b, 0x00, 0x40,         # addi       r11,r11,0x40
        0x2b, 0x0b, 0x03, 0x00,         # cmplwi     cr6,r11,0x300
        0x7d, WILDCARD, WILDCARD, 0x2a, # ldarx      r8,r8,r9
        0xf9, WILDCARD, 0x00, 0x00,     # std        r8,0x0(r10)=>local_a0
        0x39, 0x4a, 0x00, 0x08,         # addi       r10,r10,0x8
        0x41, 0x98, 0xff, 0xe4,         # blt        cr6,LAB_00006f1c
    ]) \
    .build()

def _patch_secengine_fuse_copy_loop(cbb: bytes, secengine_fuse_copy_loop_address: int, copy_64bit_blocks_address: int) -> bytes:
    print(f"_patch_secengine_fuse_copy_loop: applying patch at 0x{secengine_fuse_copy_loop_address:04x}")

    pos = secengine_fuse_copy_loop_address

    # patch identical to the one above, but uses r26 instead of r29
    secengine_fuse_copy_patch = bytes([
        0xE8, 0x7A, 0x02, 0x58, # ld %r3, 0x258(%r26) - get NAND base
        0x80, 0x83, 0x00, 0x64, # lwz %r4, 0x64(%r3)
        0x80, 0xA3, 0x00, 0x70, # lwz %r5, 0x70(%r3)
        0x7C, 0x63, 0x22, 0x14, # add %r3, %r3, %r4
        0x7C, 0x83, 0x2A, 0x14, # add %r4, %r3, %r5   - point r4 at data we're about to copy
        0x7D, 0x43, 0x53, 0x78, # mr %r3, %r10        - r3 = data copy destination
        0x38, 0xA0, 0x00, 0x0C, # li %r5, 0xc         - r5 = num of 64-bit words to copy
    ])

    cbb[pos:pos+len(secengine_fuse_copy_patch)] = secengine_fuse_copy_patch
    pos += len(secengine_fuse_copy_patch)
    cbb, pos = assemble_branch_with_link(cbb, pos, copy_64bit_blocks_address)

    return cbb

def vfuses_try_patch(cbb: bytes) -> bytes:
        
    resolver_params = {
        'copy_64bit_blocks_address': COPY_64BIT_BLOCKS_PATTERN,
        'li_600_address': VFUSE_LI_600_PATTERN,
        'fuse_copy_loop_address': FUSE_COPY_LOOP_PATTERN,
        'secengine_fuse_copy_loop_address': SECENGINE_FUSE_COPY_LOOP
    }

    resolved_sigs = bulk_find(resolver_params, cbb)
    if check_bulk_find_results(resolved_sigs):
        print("vfuses_try_patch: error, one or more signatures missing, cannot apply patches safely.")
        return None
    
    copy_64bit_blocks_address = resolved_sigs['copy_64bit_blocks_address']
    
    cbb = _patch_li_600(cbb, resolved_sigs['li_600_address'])
    cbb = _patch_fuse_copy_loop(cbb, resolved_sigs['fuse_copy_loop_address'], copy_64bit_blocks_address)
    cbb = _patch_secengine_fuse_copy_loop(cbb, resolved_sigs['secengine_fuse_copy_loop_address'], copy_64bit_blocks_address)

    return cbb
