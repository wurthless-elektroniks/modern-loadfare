'''
Old-style CB patcher

Old-style CBs typically have POST codes, an entry point at 0x3C0,
and no obfuscation when calling cd_jump.
'''

import struct
from patcher import assemble_nop, assemble_branch, assemble_branch_with_link, decode_branch_address, decode_branch_conditional_address
from signature import SignatureBuilder, WILDCARD, bulk_find
from postcounter import assemble_hwinit_postcount_block_universal
from smckeepalive import assemble_hwinit_smc_keepalive_block_universal
from vfusespatcher import COPY_64BIT_BLOCKS_PATTERN, VFUSE_LI_600_PATTERN, \
                          SECENGINE_FUSE_COPY_LOOP, vfuses_patch_li_600, \
                          vfuses_patch_secengine_fuse_copy_loop

OLDCB_POST_FUNCTION = SignatureBuilder() \
    .pattern([
        0x78, 0x84, 0xC1, 0xC6,
        0xF8, 0x83, 0x00, 0x00,
        0x4E, 0x80, 0x00, 0x20
    ]) \
    .build()

# this is the weird three nops that xeBuild applies, basically some sort of header
# check against the SMC that really doesn't matter much. but we include this as a placebo
# because failure here leads to a panic (POST 0xA3)
OLDCB_SMCHEADER_PATTERN = SignatureBuilder() \
    .pattern([
        0x57, 0xeb, 0x05, 0x3e, # rlwinm     r11,r31,0x0,0x14,0x1f
        0x2b, 0x0b, 0x00, 0x00, # cmplwi     cr6,r11,0x0
        0x40, 0x9a, 0x00, 0x20, # bne        cr6,LAB_00006ac0 <-- nop
        0x2b, WILDCARD, 0x30, 0x00, # cmplwi     cr6,r30,0x3000   <-- nop
        0x40, 0x9a, 0x00, 0x18, # bne        cr6,LAB_00006ac0 <-- nop
        0x38, 0x80, 0x30, 0x00, # li         r4,0x3000
    ]) \
    .build()

def _patch_smc_panic_a3_case(cbb: bytes, smcheader_check_addr: int) -> bytes:
    base = smcheader_check_addr + 8
    cbb, base = assemble_nop(cbb, base)
    cbb, base = assemble_nop(cbb, base)
    cbb, base = assemble_nop(cbb, base)
    return cbb

OLDCB_SMCSUM_PATTERN = SignatureBuilder() \
    .pattern([
        0x2F, 0x03, 0x00, 0x00, # cmpwi cr6, r3, 0
        0x40, 0x9A, 0x00, 0x14, # bne cr6,+0x14
        0x38, 0x80, 0x00, 0xA4  # li r4,0xA4 (loading POST code 0xA4 for panic ahead)
    ]) \
    .build()

def _patch_nosmcsum(cbb: bytes, smcsum_check_addr: int) -> bytes:
    base = smcsum_check_addr + 4
    cbb, _ = assemble_branch(cbb, base, base+0x14)
    return cbb

OLDCB_FUSECHECK_CALL = SignatureBuilder() \
    .pattern([
        0x7F, 0x63, 0xDB, 0x78,
        0x7F, 0x84, 0xE3, 0x78,
        0x7F, 0xA5, 0xEB, 0x78,
        0x7F, 0xC6, 0xF3, 0x78,
        0x48, WILDCARD, WILDCARD, WILDCARD,
    ]) \
    .build()

def _patch_nofuse(cbb: bytes, fusecheck_call_addr: int) -> bytes:
    base = fusecheck_call_addr+0x10
    print(f"- nofuse: put nop at 0x{base:04x}")
    cbb, _ = assemble_nop(cbb, base)
    return cbb

# this code comes imediately before the actual LDV check
# but virtually all patches will nop out the bne so the fusecheck is skipped
OLDCB_CB_LDV_PREAMBLE_PATTERN = SignatureBuilder() \
    .pattern([
        0x7f, 0x0b, 0x50, 0x00,     # cmpw       cr6,r11,r10
        0x40, 0x9a, 0x00, 0x10,     # bne        cr6,LAB_0000699c
        0x56, WILDCARD, 0x04, 0x3e, # rlwinm     r11,r21,0x0,0x10,0x1f
        0x61, WILDCARD, 0x00, 0x08, # ori        r21,r11,0x8
        0x48, 0x00, 0x00, 0x38      # b          LAB_000069d0
    ]) \
    .build()

def _patch_cb_ldv_check(cbb: bytes, cb_ldv_address: int):
    cbb, _ = assemble_nop(cbb, cb_ldv_address+0x04)
    return cbb

OLDCB_DECRYPT_CD_PATTERN = SignatureBuilder() \
    .pattern([
        0x38, 0x80, 0x00, 0x36, # +0x00
        0x7F, 0xE3, 0xFB, 0x78, # +0x04
        0x48, WILDCARD, WILDCARD, WILDCARD, # +0x08 bl post
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # +0x0C these instructions setup params for rc4_decrypt
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # +0x10 we really don't care what they are as long as
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # +0x14 there's a call to rc4_decrypt after them
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # +0x18
        0x48, WILDCARD, WILDCARD, WILDCARD, # +0x1C bl rc4_decrypt
    ]) \
    .build()

def _patch_nodecrypt(cbb: bytes, decrypt_cd_addr: int) -> bytes:
    base = decrypt_cd_addr+0x1C
    print(f"- nodecrypt: put nop at 0x{base:04x}")
    cbb, _ = assemble_nop(cbb, base)
    return cbb

OLDCB_CD_HASHCHECK_FAILURE_CASE_PATTERN = SignatureBuilder() \
    .pattern([
        0x2F, 0x03, 0x00, 0x00,     # cmpwi cr6,r3,0
        WILDCARD, 0x9A, 0x00, 0x14, # beq/bne cr6,+0x14  - newer uses beq, older uses bne
        0x38, 0x80, 0x00, 0xAD,     # otherwise POST 0xAD and stop
        0x7F, 0xE3, 0xFB, 0x78,
        0x48, WILDCARD, WILDCARD, WILDCARD, # bl post
    ]) \
    .build()

def _patch_cd_hashcheck(cbb: bytes, cd_hashcheck_addr: int) -> bytes:
    base = cd_hashcheck_addr + 4
    target = base+0x14
    print(f"- cd hashcheck: branch from 0x{base:04x} to 0x{target:04x}")
    cbb, _ = assemble_branch(cbb, base, target)
    return cbb


# fuse copy loop (i think???)
# on 6752 this is inlined in the fusecheck function.
# on 7378 this is in a separate function that is also called in cd_load_and_jump.
# this one from 7378, register usage differs between builds, hence the wildcards
OLDCB_FUSE_COPY_LOOP_PATTERN = SignatureBuilder() \
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
    print(f"_patch_fuse_copy_loop: applying inlined patch at 0x{fuse_copy_loop_address:04x}")

    pos = fuse_copy_loop_address

    # same as g2m for falcon/jasper
    # https://github.com/mitchellwaite/xbox360_xebuild_patches/blob/main/src/2BL/6752/inc/cbb_6752.S 
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

# -------------------------------------------------------------------------------------

def oldcb_ident(cbb: bytes) -> bool:
    # entry point must be 0x3C0
    # opcode at 0x3DC must be 38 80 00 20 (li r5,0x20 - about to POST 0x20)
    return cbb[0x0000:0x0002] == bytes([0x43, 0x42]) and \
           (
            # most old-style ones
            (cbb[0x0008:0x000C] == bytes([0x00, 0x00, 0x03, 0xC0]) and \
             cbb[0x03DC:0x03E0] == bytes([0x38, 0x80, 0x00, 0x20]))
             or \
            # CB_B 13121 is like this, who knows why
            (cbb[0x0008:0x000C] == bytes([0x00, 0x00, 0x03, 0xD0]) and \
             cbb[0x03EC:0x03F0] == bytes([0x38, 0x80, 0x00, 0x20]))
           )

def oldcb_try_patch(cbb: bytes, patchparams: dict) -> None | bytes:
    if oldcb_ident(cbb) is False:
        return None

    resolver_params = {
        'postfcn_address':      OLDCB_POST_FUNCTION,
        'cb_ldv_address':       OLDCB_CB_LDV_PREAMBLE_PATTERN,
        'smcheader_address':    OLDCB_SMCHEADER_PATTERN,
        'smcsum_address':       OLDCB_SMCSUM_PATTERN,
        'fusecheck_call_addr':  OLDCB_FUSECHECK_CALL,
        'decrypt_cd_addr':      OLDCB_DECRYPT_CD_PATTERN,
        'hashcheck_addr':       OLDCB_CD_HASHCHECK_FAILURE_CASE_PATTERN,
        'copy_64bit_blocks_address': COPY_64BIT_BLOCKS_PATTERN,
        'li_600_address': VFUSE_LI_600_PATTERN,
        'fuse_copy_loop_address': OLDCB_FUSE_COPY_LOOP_PATTERN,
        'secengine_fuse_copy_loop_address': SECENGINE_FUSE_COPY_LOOP
    }

    resolved_sigs = bulk_find(resolver_params, cbb)

    any_none = False
    for name, offset in resolved_sigs.items():
        if offset is not None:
            print(f"{name} = 0x{offset:04x}")
        else:
            print(f"{name} = NOT FOUND")
            any_none = True

    if any_none:
        print("error: one or more required signatures can't be found, cannot apply patches safely.")
        return None

    copy_64bit_blocks_address = resolved_sigs['copy_64bit_blocks_address']

    cbb = bytearray(cbb)

    if patchparams['nofuse']:
        cbb = _patch_nofuse(cbb, resolved_sigs['fusecheck_call_addr'])
    else:
        if patchparams['nosmcsum']:
            cbb = _patch_nosmcsum(cbb, resolved_sigs['smcsum_address'])

        # on old CBs this is inlined in the fusecheck/SMC sanity check function, so it's fine to put here
        if patchparams['vfuse']:
            cbb = _patch_fuse_copy_loop(cbb, resolved_sigs['fuse_copy_loop_address'], copy_64bit_blocks_address)

        if patchparams['disable_default'] is False:
            cbb = _patch_cb_ldv_check(cbb, resolved_sigs['cb_ldv_address'])
            cbb = _patch_smc_panic_a3_case(cbb, resolved_sigs['smcheader_address'])

    if patchparams['vfuse']:
        cbb = vfuses_patch_li_600(cbb, resolved_sigs['li_600_address'])
        cbb = vfuses_patch_secengine_fuse_copy_loop(cbb, resolved_sigs['secengine_fuse_copy_loop_address'], copy_64bit_blocks_address)

    if patchparams['nodecrypt']:
        cbb = _patch_nodecrypt(cbb, resolved_sigs['decrypt_cd_addr'])

    if patchparams['disable_default'] is False:
        cbb = _patch_cd_hashcheck(cbb, resolved_sigs['hashcheck_addr'])

    return cbb
