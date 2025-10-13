'''
Old-style CB patcher

Old-style CBs typically have POST codes, an entry point at 0x3C0,
and no obfuscation when calling cd_jump.
'''

import struct
from patcher import assemble_nop, assemble_branch, decode_branch_address, decode_branch_conditional_address
from signature import SignatureBuilder, WILDCARD, bulk_find
from postcounter import assemble_hwinit_postcount_block_universal
from smckeepalive import assemble_hwinit_smc_keepalive_block_universal

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

OLDCB_HWINIT_TOP_PATTERN = SignatureBuilder() \
    .pattern([
        0x7c, 0x00, 0x04, 0xac,             # +0x00 sync       0x0
        0x7d, 0x88, 0x02, 0xa6,             # +0x04 mfspr      r12,LR
        0xf9, 0x81, 0xff, 0xf8,             # +0x08 std        r12,-0x8(r1)
        0xf9, 0xa1, 0xff, 0xf0,             # +0x0C std        r13,-0x10(r1)
        0xf9, 0xc1, 0xff, 0xe8,             # +0x10 std        r14,-0x18(r1)
        0xf9, 0xe1, 0xff, 0xe0,             # +0x14 std        r15,-0x20(r1)
        0xfa, 0x01, 0xff, 0xd8,             # +0x18 std        r16,-0x28(r1)
        0xfa, 0x21, 0xff, 0xd0,             # +0x1C std        r17,-0x30(r1)
        0xfa, 0x41, 0xff, 0xc8,             # +0x20 std        r18,-0x38(r1)
        0xfa, 0x61, 0xff, 0xc0,             # +0x24 std        r19,-0x40(r1)
        0xfa, 0x81, 0xff, 0xb8,             # +0x28 std        r20,-0x48(r1)
        0xfa, 0xa1, 0xff, 0xb0,             # +0x2C std        r21,-0x50(r1)
        0xfa, 0xc1, 0xff, 0xa8,             # +0x30 std        r22,-0x58(r1)
        0xfa, 0xe1, 0xff, 0xa0,             # +0x34 std        r23,-0x60(r1)
        0xfb, 0x01, 0xff, 0x98,             # +0x38 std        r24,-0x68(r1)
        0xfb, 0x21, 0xff, 0x90,             # +0x3C std        r25,-0x70(r1)
        0xfb, 0x41, 0xff, 0x88,             # +0x40 std        r26,-0x78(r1)
        0xfb, 0x61, 0xff, 0x80,             # +0x44 std        r27,-0x80(r1)
        0xfb, 0x81, 0xff, 0x78,             # +0x48 std        r28,-0x88(r1)
        0xfb, 0xa1, 0xff, 0x70,             # +0x4C std        r29,-0x90(r1)
        0xfb, 0xc1, 0xff, 0x68,             # +0x50 std        r30,-0x98(r1)
        0xfb, 0xe1, 0xff, 0x60,             # +0x54 std        r31,-0xa0(r1)
        0x48, 0x00, WILDCARD, WILDCARD,     # +0x58 bl         FUN_00000d5c  <-- register setup function
        0x7c, 0x30, 0x20, 0x40,             # +0x5C cmpld      r16,r4        <-- first instruction in hwinit interpreter loop
        0x40, 0xc0, WILDCARD, WILDCARD      # +0x60 bge        FUN_00000dc4  <-- branch to "done" block
    ]) \
    .build()

def _get_hwinit_register_setup_fcn_address(cbb: bytes, hwinit_top_address: int):
    base = hwinit_top_address + 0x58
    return decode_branch_address(cbb[base:base+4], base)

def _get_hwinit_init_hook_address(hwinit_top_address: int):
    return hwinit_top_address + 0x58

def _get_hwinit_loop_top_address(hwinit_top_address: int):
    return hwinit_top_address+0x5C

def _get_hwinit_done_address(cbb: bytes, hwinit_top_address: int):
    base = hwinit_top_address+0x60
    return decode_branch_conditional_address(cbb[base:base+4], base)

OLDCB_HWINIT_DELAY_PATTERN = SignatureBuilder() \
    .pattern([
        0x1c, 0xc6, 0x00, 0x32,     # mulli      r6,r6,50
        0x7d, 0x0c, 0x42, 0xe6,     # mftb       r8,TBLr
        0x7d, 0x08, 0x32, 0x14,     # add        r8,r8,r6
        0x7c, 0xec, 0x42, 0xe6,     # mftb       r7,TBLr
        0x7c, 0x27, 0x40, 0x40,     # cmpld      r7,r8
        0x40, 0xe1, 0xff, 0xf8,     # ble        LAB_000009f4
    ]) \
    .build()

def _patch_fastdelay(cbb: bytes, hwinit_delay_address: int):
    cbb[hwinit_delay_address+3] = 10
    return cbb

def oldcb_ident(cbb: bytes) -> bool:
    # entry point must be 0x3C0
    # opcode at 0x3DC must be 38 80 00 20 (li r5,0x20 - about to POST 0x20)
    return cbb[0x0000:0x0002] == bytes([0x43, 0x42]) and \
           cbb[0x0008:0x000C] == bytes([0x00, 0x00, 0x03, 0xC0]) and \
           cbb[0x03DC:0x03E0] == bytes([0x38, 0x80, 0x00, 0x20])

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

    cbb = bytearray(cbb)

    if patchparams['nofuse']:
        cbb = _patch_nofuse(cbb, resolved_sigs['fusecheck_call_addr'])
    else:
        if patchparams['nosmcsum']:
            cbb = _patch_nosmcsum(cbb, resolved_sigs['smcsum_address'])
        cbb = _patch_cb_ldv_check(cbb, resolved_sigs['cb_ldv_address'])
        cbb = _patch_smc_panic_a3_case(cbb, resolved_sigs['smcheader_address'])

    if patchparams['nodecrypt']:
        cbb = _patch_nodecrypt(cbb, resolved_sigs['decrypt_cd_addr'])

    cbb = _patch_cd_hashcheck(cbb, resolved_sigs['hashcheck_addr'])

    return cbb
