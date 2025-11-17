'''
New-style CB patcher

New-style CBs typically have an entry point at 0x3E0, remove POST codes,
add random delays in an attempt to throw off glitch chips, and munge
some parameters before calling CD.

As you can expect, based on the fact we have to patch newer-style CBs to add POST codes back in
and to make header checks compatible with older CDs,
this patcher is way more complex than oldcbpatcher.py.
'''

from patcher import *
from signature import SignatureBuilder, WILDCARD, bulk_find, check_bulk_find_results, find_all_instances

# this is the only POST code that wasn't removed from newer CBs
NEWCB_PANIC_FUNCTION = SignatureBuilder() \
    .pattern([
        0x38, 0x60, 0x00, 0xae, # li r3,0xAE
        0x78, 0x63, 0xc1, 0xc6, # then usual panic case code follows
        0x38, 0x80, 0x02, 0x00,
        0x64, 0x84, 0x80, 0x00,
        0x78, 0x84, 0x07, 0xc6,
        0x64, 0x84, 0x00, 0x06,
        0xf8, 0x64, 0x10, 0x10, # store r3 @ POST register
        0x38, 0x00, 0x00, 0x00, # then loop forever
        0x7c, 0x18, 0x23, 0xa6,
        0x4b, 0xff, 0xff, 0xf8,
    ]) \
    .build()

# done several times in cd_load_and_jump - will be useful for claiming free space
# and patching in postcodes
NEWCB_RANDOM_DELAY_CALL_PATTERN = SignatureBuilder() \
    .pattern([
        0x38, 0xa0, 0x1b, 0xff,         # li         r5,0x1bff
        0x38, 0x80, 0x04, 0x00,         # li         r4,0x400
        0x38, 0x61, 0x00, 0x80,         # addi       r3,r1,0x80
        0x48, 0x00, WILDCARD, WILDCARD, # bl         time_waster
    ]) \
    .build()

# this is the infamous random delay function.
# it is called throughout cd_load_and_jump and nowhere else.
# it can also be found in CB_A.
NEWCB_RANDOM_DELAY_FUNCTION = SignatureBuilder() \
    .pattern([
        0x7d, 0x88, 0x02, 0xa6,                 # mfspr      r12,LR
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # call something that pushes buncha regs onto stack
        0xf8, 0x21, 0xff, 0x81,                 # stdu       r1,local_80(r1)
        0x7c, 0x7f, 0x1b, 0x78,                 # or         r31,r3,r3
        0x7c, 0x9d, 0x23, 0x78,                 # or         r29,r4,r4
        0x7c, 0xbe, 0x2b, 0x78,                 # or         r30,r5,r5
        0x38, 0xa0, 0x00, 0x04,                 # li         r5,0x4
        0x38, 0x81, 0x00, 0x50,                 # addi       r4,r1,0x50
        0x7f, 0xe3, 0xfb, 0x78,                 # or         r3,r31,r31
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # bl         rc4_pgra_decrypt
        0x81, 0x61, 0x00, 0x50,                 # lwz        r11,local_30(r1)
        0x7d, 0x6b, 0xf0, 0x38,                 # and        r11,r11,r30
        0x2b, 0x0b, 0x00, 0x00,                 # cmplwi     cr6,r11,0x0
        0x41, 0x9a, 0xff, 0xe4,                 # beq        cr6,LAB_00007838
        0x7c, 0x6b, 0xea, 0x14,                 # add        r3,r11,r29
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # call function that takes r3 and uses it to delay execution via timebase registers
        0x38, 0x21, 0x00, 0x80,                 # addi       r1,r1,0x80
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # branch to stack cleanup/exit point
    ]) \
    .build()

def _reclaim_random_delay(cbb: bytes, randomdelay_address: int):
    # patch function to return immediately
    cbb, offs = assemble_branch_to_link_register(cbb, randomdelay_address)

    # rest of it can be used as free space
    range_end = offs + (NEWCB_RANDOM_DELAY_FUNCTION.size() - 4)
    print(f"_reclaim_random_delay: reclaimed 0x{offs:04x} ~ 0x{range_end:04x} as free space")
    return cbb, FreeSpaceArea(offs, range_end)

NEWCB_CD_HASH_COMPARE_FUNCTION = SignatureBuilder() \
    .pattern([
        0x60, 0x00, 0x00, 0x00, # four nops in a function used across multiple CBs?
        0x60, 0x00, 0x00, 0x00, # you really are too kind, microsoft
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x39, 0x63, 0xff, 0xff,
        0x39, 0x84, 0xff, 0xff,
        0x7c, 0xa9, 0x03, 0xa6,
        0x60, 0x00, 0x00, 0x00,
        0x38, 0x60, 0x00, 0x00,
        0x7c, 0xa5, 0x00, 0x34,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7c, 0xb0, 0x21, 0x20,
        0x4d, 0x9a, 0x00, 0x20,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x38, 0x60, 0xff, 0xff,
        0x38, 0x80, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x8d, 0x0b, 0x00, 0x01,
        0x8d, 0x2c, 0x00, 0x01,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7d, 0x06, 0x4b, 0x78,
        0x69, 0x07, 0x00, 0xff,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7c, 0xe5, 0x4a, 0x78,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7c, 0x63, 0x28, 0x38,
        0x7c, 0x84, 0x33, 0x78,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x42, 0x00, 0xff, 0xc0,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7c, 0x85, 0x00, 0x34,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x54, 0xa5, 0xd0, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7c, 0xa5, 0xfe, 0x70,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7c, 0x63, 0x28, 0x78,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x7c, 0x63, 0x07, 0x74,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x60, 0x00, 0x00, 0x00,
        0x4e, 0x80, 0x00, 0x20,
    ]) \
    .build()

def _reclaim_cd_hash_compare(cbb: bytes, cd_hash_cmp_address: int):
    # patch routine to return -1 (always succeed)
    print(f"_reclaim_cd_hash_compare: patch function at 0x{cd_hash_cmp_address:04x} to always return -1")
    cbb[cd_hash_cmp_address:cd_hash_cmp_address+4] = bytes([0x38,0x60,0xff,0xff]) # li r3,-1
    cbb, offs = assemble_branch_to_link_register(cbb, cd_hash_cmp_address+4)
    
    # rest of it can be used as free space
    range_end = offs + (NEWCB_CD_HASH_COMPARE_FUNCTION.size() - 8)
    print(f"_reclaim_cd_hash_compare: reclaimed 0x{offs:04x} ~ 0x{range_end:04x} as free space")
    return cbb, FreeSpaceArea(offs, range_end)

# function that clears some params and calls hwinit.
# old-style CBs will POST 0x23 here, and then hwinit will POST 0x2E.
# if POSTs are enabled, the call to hwinit will be redirected to code that POSTs 0x2E.
NEWCB_HWINIT_PROXY = SignatureBuilder() \
    .pattern([
        0x7d, 0x88, 0x02, 0xa6,                 # +0x00
        0xf9, 0x81, 0xff, 0xf8,                 # +0x04
        0xfb, 0xe1, 0xff, 0xf0,                 # +0x08
        0xf8, 0x21, 0xff, 0xa1,                 # +0x0C
        0x7c, 0x7f, 0x1b, 0x78,                 # +0x10
        0x38, 0x80, 0x00, 0x00,                 # +0x14 li r4, 0 (useless - hwinit overwrites this anyway)
        0x38, 0x60, 0x00, 0x00,                 # +0x18 li r3, 0 (useless - hwinit overwrites this anyway)
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # +0x1C bl hwinit
        0x7f, 0xe3, 0xfb, 0x78,
        0x38, 0x21, 0x00, 0x60,
        0xe9, 0x81, 0xff, 0xf8,
        0x7d, 0x88, 0x03, 0xa6,
        0xeb, 0xe1, 0xff, 0xf0,
        0x4e, 0x80, 0x00, 0x20,
    ]) \
    .build()

def _postpatch_hwinitproxy(cbb: bytes, hwinitproxy_address: int, post_address: int, free_space: FreeSpaceArea):
    hwinit_address = decode_branch_address(cbb[hwinitproxy_address + 0x1C:hwinitproxy_address + 0x20], hwinitproxy_address + 0x1C)

    post_target_address = free_space.head()
    head = post_target_address
    cbb, head = assemble_post_call(cbb, head, post_address, 0x23) # to keep glitch chips happy
    cbb, head = assemble_post_call(cbb, head, post_address, 0x2E)
    cbb, head = assemble_branch(cbb, head, hwinit_address)
    free_space.create_func_and_set_head("hwinit_23_2e_reroute", head)

    cbb, _ = assemble_branch_with_link(cbb, hwinitproxy_address + 0x1C, post_target_address)
    return cbb

NEWCB_CB_LDV_PREAMBLE_PATTERN = SignatureBuilder() \
    .pattern([
        0x7f, 0x0b, 0x50, 0x00,     # +0x00 cmpw       cr6,r11,r10
        0x40, 0x9a, 0x00, 0x10,     # +0x04 bne        cr6,LAB_0000699c
        WILDCARD, WILDCARD, 0x04, 0x3e, # +0x08 rlwinm     r11,r21,0x0,0x10,0x1f
        0x61, WILDCARD, 0x00, 0x08, # +0x0C ori        r21,r11,0x8
        0x48, 0x00, 0x00, 0x2C      # +0x10 branch target different because panic is removed
    ]) \
    .build()

def _patch_cb_ldv_check(cbb: bytes, cb_ldv_address: int):
    cbb, _ = assemble_nop(cbb, cb_ldv_address+0x04)
    return cbb

def _reclaim_cb_ldv_fusecheck(cbb: bytes, cb_ldv_address: int):
    range_start = cb_ldv_address + 0x14
    range_end   = range_start + 0x2C
    print(f"_reclaim_cb_ldv_fusecheck: reclaimed 0x{range_start:04x} ~ 0x{range_end:04x} as free space")
    return cbb, FreeSpaceArea(range_start, range_end)

# identical to old CB
NEWCB_FUSECHECK_CALL = SignatureBuilder() \
    .pattern([
        0x7F, 0x63, 0xDB, 0x78,
        0x7F, 0x84, 0xE3, 0x78,
        0x7F, 0xA5, 0xEB, 0x78,
        0x7F, 0xC6, 0xF3, 0x78,
        0x48, WILDCARD, WILDCARD, WILDCARD, # +0x10 call to fusecheck function
        0x48, WILDCARD, WILDCARD, WILDCARD, # +0x14 call to secengine init function
        0x7c, 0x74, 0xfa, 0xa6, # +0x18 mfspr r3,IAC1 - POST 0x2F should be happening around here
    ]) \
    .build()

def _postpatch_fusecheck(cbb: bytes, fusecheck_call_addr: int, post_address: int, free_space: FreeSpaceArea) -> bytes:
    fusecheck_addr = decode_branch_address(cbb[fusecheck_call_addr + 0x10:fusecheck_call_addr + 0x14], fusecheck_call_addr + 0x10)

    post_target_address = free_space.head()
    cbb, head = assemble_post_call(cbb, post_target_address, post_address, 0x21)
    cbb, head = assemble_branch(cbb, head, fusecheck_addr)
    free_space.create_func_and_set_head("fusecheck_21_reroute", head)

    cbb, _ = assemble_branch_with_link(cbb, fusecheck_call_addr + 0x10, post_target_address)
    return cbb

def _postpatch_secengine_init(cbb: bytes, fusecheck_call_addr: int, post_address: int, free_space: FreeSpaceArea) -> bytes:
    secengine_init_addr = decode_branch_address(cbb[fusecheck_call_addr + 0x14:fusecheck_call_addr + 0x18], fusecheck_call_addr + 0x14)

    post_target_address = free_space.head()
    cbb, head = assemble_post_call(cbb, post_target_address, post_address, 0x22)
    cbb, head = assemble_branch(cbb, head, secengine_init_addr)
    free_space.create_func_and_set_head("seceng_22_reroute", head)

    cbb, _ = assemble_branch_with_link(cbb, fusecheck_call_addr + 0x14, post_target_address)
    return cbb

def _postpatch_relocate_and_init_vectors(cbb: bytes, fusecheck_call_addr: int, post_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb[post_target_address:post_target_address+4] = bytes([0x7c, 0x74, 0xfa, 0xa6])

    cbb, head = assemble_post_call(cbb, post_target_address+4, post_address, 0x2F)
    cbb, head = assemble_branch(cbb, head, fusecheck_call_addr + 0x1C)
    free_space.create_func_and_set_head("reloc_2F_reroute", head)

    cbb, _ = assemble_branch(cbb, fusecheck_call_addr + 0x18, post_target_address)

    return cbb

def _patch_nofuse(cbb: bytes, fusecheck_call_addr: int) -> bytes:
    base = fusecheck_call_addr+0x10
    print(f"_patch_nofuse: put nop at 0x{base:04x}")
    cbb, _ = assemble_nop(cbb, base)
    return cbb

NEWCB_SMCSUM_PATTERN = SignatureBuilder() \
    .pattern([
        0x48, WILDCARD, WILDCARD, WILDCARD, # bl to hmac verify function
        0x2F, 0x03, 0x00, 0x00,             # cmpwi cr6, r3, 0
        0x40, 0x9A, 0x00, 0x08,             # bne cr6,+0x8
        0x00, 0x00, 0x00, 0x00              # die (old CB panics with POST code 0xA4)
    ]) \
    .build()

def _patch_nosmcsum(cbb: bytes, smcsum_check_addr: int) -> bytes:
    base = smcsum_check_addr + 0x0C
    cbb, _ = assemble_branch(cbb, base, base+0x08)
    return cbb

def _panicpatch_smcsum(cbb: bytes, smcsum_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0xA4, panic_address)
    free_space.create_func_and_set_head("panic_A4", head)
    cbb, _ = assemble_branch(cbb, smcsum_check_addr + 0x0C, post_target_address)
    return cbb

NEWCB_SMCHEADER_PATTERN = SignatureBuilder() \
    .pattern([
        0x2b, 0x0a, 0x00, 0x00,   # +0x00 cmplwi     cr6,r10,0x0
        0x40, 0x9a, 0x00, 0x2c,   # +0x04 bne        cr6,LAB_00006e6c
        0x2b, 0x1e, 0x30, 0x00,   # +0x08 cmplwi     cr6,r30,0x3000
        0x41, 0x9a, 0x00, 0x0c,   # +0x0C beq        cr6,LAB_00006e54
        0x2b, 0x1e, 0x38, 0x00,   # +0x10 cmplwi     cr6,r30,0x3800 (for KSB SMC's)
        0x40, 0x9a, 0x00, 0x1c,   # +0x14 bne        cr6,LAB_00006e6c

        # have to check the rest of this block too
        0x7f, 0xc4, 0xf3, 0x78,   # +0x18
        0x7b, 0xe3, 0x00, 0x20,   # +0x1C
        WILDCARD, WILDCARD, WILDCARD, WILDCARD, # +0x20
        0xe9, 0x7d, 0x02, 0x58,   # +0x24
        0x2f, 0x03, 0x00, 0x00,   # +0x28
        0x40, 0x9a, 0x00, 0x08,   # +0x2C
        0x00, 0x00, 0x00, 0x00,   # normal 0xA3 panic case goes here
    ]) \
    .build()

def _patch_smc_panic_a3_case(cbb: bytes, smcheader_check_addr: int) -> bytes:
    cbb, _ = assemble_branch(cbb, smcheader_check_addr, smcheader_check_addr + 0x18)
    return cbb

def _panicpatch_smc_panic_a3_case(cbb: bytes, smcheader_check_addr: int, panic_address: int) -> bytes:
    cbb, _ = assemble_panic(cbb, smcheader_check_addr + 4, 0xA3, panic_address)
    cbb, _ = assemble_branch(cbb, smcheader_check_addr + 0x30, smcheader_check_addr + 4)
    return cbb

NEWCB_SECOTP_1_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x79, 0x8c, 0xd1, 0x46, # +0x00 rldicr     r12,r12,0x3a,0x5
        0x7d, 0x6a, 0x60, 0x38, # +0x04 and        r10,r11,r12
        0x2b, 0x2a, 0x00, 0x00, # +0x08 cmpldi     cr6,r10,0x0
        0x41, 0x9a, 0x00, 0x08, # +0x0C beq        cr6,LAB_00006bf8
        0x00, 0x00, 0x00, 0x00, # +0x10 fail with POST 0x9B
    ]) \
    .build()

def _panicpatch_secotp1(cbb: bytes, secotp1_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0x9B, panic_address)
    free_space.create_func_and_set_head("panic_9B", head)
    cbb, _ = assemble_branch(cbb, secotp1_check_addr + 0x10, post_target_address)

    return cbb

NEWCB_SECOTP_2_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x57, 0x07, 0x04, 0x3e, # rlwinm     r7,r24,0x0,0x10,0x1f
        0x54, 0xea, 0xff, 0xfe, # rlwinm     r10,r7,0x1f,0x1f,0x1f
        0x7f, 0x0b, 0x50, 0x00, # cmpw       cr6,r11,r10
        0x41, 0x9a, 0x00, 0x08, # beq        cr6,LAB_00006c3c
        0x00, 0x00, 0x00, 0x00, # +0x10 fail with POST 0x9C
    ]) \
    .build()

def _panicpatch_secotp2(cbb: bytes, secotp2_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0x9C, panic_address)
    free_space.create_func_and_set_head("panic_9C", head)
    cbb, _ = assemble_branch(cbb, secotp2_check_addr + 0x10, post_target_address)

    return cbb

# IMPORTANT! secotp 4, 5, 3 are checked out-of-order
NEWCB_SECOTP_4_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x41, 0x9a, 0x00, 0x14, # beq        cr6,LAB_00006c74
        0x79, WILDCARD, 0x07, 0x20, # rldicl     r9,r11,0x0,0x3c
        0x2b, WILDCARD, 0x00, 0x00, # cmpldi     cr6,r9,0x0
        0x41, 0x9a, 0x00, 0x08, # beq        cr6,LAB_00006c74
        0x00, 0x00, 0x00, 0x00, # +0x10 fail with POST 0x9E
    ]) \
    .build()

def _panicpatch_secotp4(cbb: bytes, secotp4_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0x9E, panic_address)
    free_space.create_func_and_set_head("panic_9E", head)
    cbb, _ = assemble_branch(cbb, secotp4_check_addr + 0x10, post_target_address)
    return cbb

NEWCB_SECOTP_5_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x7d, WILDCARD, WILDCARD, 0xf8, # nor        r6,r9,r9
        0x54, WILDCARD, 0x07, 0xfe, # rlwinm     r6,r6,0x0,0x1f,0x1f
        0x7f, WILDCARD, WILDCARD, 0x00, # cmpw       cr6,r6,r10
        0x41, 0x9a, 0x00, 0x08, # beq        cr6,LAB_00006320
        0x00, 0x00, 0x00, 0x00, # +0x10 fail with POST 0x9F
    ]) \
    .build()

def _panicpatch_secotp5(cbb: bytes, secotp5_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0x9F, panic_address)
    free_space.create_func_and_set_head("panic_9F", head)
    cbb, _ = assemble_branch(cbb, secotp5_check_addr + 0x10, post_target_address)
    return cbb

NEWCB_SECOTP_3_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x40, 0x9a, 0x00, 0x10, # bne        cr6,LAB_00006cc8
        0x54, 0xeb, 0x07, 0xbc, # rlwinm     r11,r7,0x0,0x1e,0x1e
        0x2b, 0x0b, 0x00, 0x00, # cmplwi     cr6,r11,0x0
        0x41, 0x9a, 0x00, 0x08, # beq        cr6,LAB_00006ccc
        0x00, 0x00, 0x00, 0x00, # +0x10 fail with POST 0x9D
    ]) \
    .build()

def _panicpatch_secotp3(cbb: bytes, secotp3_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0x9D, panic_address)
    free_space.create_func_and_set_head("panic_9D", head)
    cbb, _ = assemble_branch(cbb, secotp3_check_addr + 0x10, post_target_address)
    return cbb

NEWCB_CONSOLE_TYPE_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x79, 0x8c, 0x07, 0xc6, # rldicr     r12,r12,0x20,0x1f
        0x7d, 0x2b, 0x60, 0x38, # and        r11,r9,r12
        0x2b, 0x2b, 0x00, 0x00, # cmpldi     cr6,r11,0x0
        0x41, 0x9a, 0x00, 0x08, # beq        cr6,LAB_00006d7c
        0x00, 0x00, 0x00, 0x00, # +0x10 fail with POST 0xB0
    ]) \
    .build()

def _panicpatch_consoletype_check(cbb: bytes, consoletype_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0xB0, panic_address)
    free_space.create_func_and_set_head("panic_B0", head)
    cbb, _ = assemble_branch(cbb, consoletype_check_addr + 0x10, post_target_address)
    return cbb

NEWCB_SECOTP_7_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x48, 0x00, 0x00, 0x14, # b          LAB_00006df0
        0x57, 0x0b, 0x07, 0xbc, # rlwinm     r11,r24,0x0,0x1e,0x1e
        0x2b, 0x0b, 0x00, 0x00, # cmplwi     cr6,r11,0x0
        0x41, 0x9a, 0x00, 0x08, # beq        cr6,LAB_00006df0
        0x00, 0x00, 0x00, 0x00, # +0x10 fail with POST 0xA1
    ]) \
    .build()

def _panicpatch_secotp7(cbb: bytes, secotp7_check_addr: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0xA1, panic_address)
    free_space.create_func_and_set_head("panic_A1", head)
    cbb, _ = assemble_branch(cbb, secotp7_check_addr + 0x10, post_target_address)
    return cbb


# this block can be replaced with addis r31,r22,0x0400
NEWCB_REAL_ENTRYPOINT_DECRYPT_PATTERN = SignatureBuilder() \
    .pattern([
        0xe9, 0x5e, 0x02, 0xf8,
        0xe9, 0x7e, 0x03, 0x00,
        0x7f, 0xa9, 0x07, 0xb4,
        0xe9, 0x1e, 0x02, 0xf0,
        0x38, 0xa0, 0x1b, 0xff,
        0x7d, 0x6b, 0x52, 0x78,
        0x38, 0x80, 0x04, 0x00,
        0x7d, 0x6b, 0x42, 0x78,
        0x38, 0x61, 0x00, 0x80,
        0x7d, 0x6a, 0x4a, 0x78,
        0xe9, 0x7f, 0x03, 0xd8,
        0x7d, 0x4a, 0x5a, 0x78,
        0xe9, 0x7f, 0x03, 0xc8,
        0x7d, 0x4a, 0x5a, 0x78,
        0xe9, 0x7f, 0x03, 0xc0,
        0x7d, 0x4b, 0x5a, 0x78,
        0xe9, 0x41, 0x00, 0x68,
        0x7d, 0x6b, 0x52, 0x78,
        0xe9, 0x41, 0x00, 0x60,
        0x7d, 0x7f, 0x52, 0x78,
        0x48, WILDCARD, WILDCARD, WILDCARD,
        0x2f, 0x1d, 0xff, 0xff,
        0x41, 0x9a, 0x00, 0x08,
        0x00, 0x00, 0x00, 0x00,
    ]) \
    .build()

def _reclaim_real_entrypoint_decrypt(cbb: bytes, real_entrypoint_decrypt_address: int):
    offs = real_entrypoint_decrypt_address
    range_end = real_entrypoint_decrypt_address + NEWCB_REAL_ENTRYPOINT_DECRYPT_PATTERN.size()

    cbb[offs:offs+4] = bytes([0x3F, 0xF6, 0x04, 0x00]) # addis r31,r22,0x0400
    offs += 4
    cbb, offs = assemble_branch(cbb, offs, range_end)

    # rest of it can be used as free space
    print(f"_reclaim_real_entrypoint_decrypt: reclaimed 0x{offs:04x} ~ 0x{range_end:04x} as free space")
    return cbb, FreeSpaceArea(offs, range_end)

NEWCB_CD_HEADER_CHECK_PATTERN = SignatureBuilder() \
    .pattern([
        0x83, 0xbe, 0x00, 0x0c, # +0x00
        0x82, 0xde, 0x00, 0x08, # +0x04
        0x39, 0x7d, 0xf8, 0xf0, # +0x08 - subtract 0x710 from size on new CBs, 0x670 on old CBs
        0x2b, 0x0b, 0xf8, 0xf0, # +0x0C - difference can't exceed 0xF8F0 on new CBs and 0xF990 on old CBs
        0x41, 0x99, 0x00, 0x58, # +0x10
        0xa1, 0x7e, 0x00, 0x00, # +0x14
        0x55, 0x6b, 0x05, 0x1e, # +0x18
        0x2f, 0x0b, 0x03, 0x44, # +0x1C - magic word must be "CD" or "SD"
        0x40, 0x9a, 0x00, 0x48, # +0x20
        0x2b, 0x16, 0x03, 0x10, # +0x24 - minimum CD entry point is 0x0310 on new CBs, 0x270 on old CBs
        0x41, 0x98, 0x00, 0x40, # +0x28
        0x39, 0x7d, 0xff, 0xfc, # +0x2C
        0x7f, 0x16, 0x58, 0x40, # +0x30
        0x41, 0x99, 0x00, 0x34, # +0x34
        0x56, 0xcb, 0x07, 0xbe, # +0x38
        0x2b, 0x0b, 0x00, 0x00, # +0x3C
        0x40, 0x9a, 0x00, 0x28, # +0x40
        0xa1, 0x7f, 0x00, 0x06, # +0x44
        0x55, 0x6b, 0x05, 0xac, # +0x48
        0x2b, 0x0b, 0x00, 0x00, # +0x4C
        0x40, 0x9a, 0x00, 0x1c, # +0x50
        0x7f, 0xa4, 0xeb, 0x78, # +0x54
        0x7f, 0x83, 0xe3, 0x78, # +0x58
        0x48, WILDCARD, WILDCARD, WILDCARD, # +0x5C
        0x2f, 0x03, 0x00, 0x00, # +0x60
        0x40, 0x9a, 0x00, 0x08, # +0x64
        0x00, 0x00, 0x00, 0x00, # +0x68 - panic 0xAB here
    ]) \
    .build()

def _patch_cd_header_check(cbb: bytes, cd_header_check_address: int):
    base = cd_header_check_address
    
    # reinstate old CD size check
    cbb[base + 0x0A:base + 0x0C] = bytes([0xF9, 0xA0])
    cbb[base + 0x0E:base + 0x10] = bytes([0xF9, 0xA0])

    # reinstate old CD minimum entry point
    cbb[base + 0x26:base + 0x28] = bytes([0x02, 0x60])

    return cbb

def _panicpatch_cd_header_check(cbb: bytes, cd_header_check_address: int, panic_address: int, free_space: FreeSpaceArea) -> bytes:
    post_target_address = free_space.head()
    cbb, head = assemble_panic(cbb, post_target_address, 0xAB, panic_address)
    free_space.create_func_and_set_head("panic_AB", head)
    cbb, _ = assemble_branch(cbb, cd_header_check_address + 0x68, post_target_address)
    return cbb

# ----------------------------------------------------------------------------------------------------------------

def newcb_ident(cbb: bytes) -> bool:
    # entry point must be 0x3E0
    return cbb[0x0000:0x0002] == bytes([0x43, 0x42]) and \
           cbb[0x0008:0x000C] == bytes([0x00, 0x00, 0x03, 0xE0])

def newcb_try_patch(cbb: bytes, patchparams: dict) -> None | bytes:
    if newcb_ident(cbb) is False:
        return None
    
    resolver_params = {
        'panic_ae_address':          NEWCB_PANIC_FUNCTION,
        'randomdelay_address':       NEWCB_RANDOM_DELAY_FUNCTION,
        'cd_hash_cmp_address':       NEWCB_CD_HASH_COMPARE_FUNCTION,
        'hwinitproxy_address':       NEWCB_HWINIT_PROXY,

        'cb_ldv_address':            NEWCB_CB_LDV_PREAMBLE_PATTERN,
        'fusecheck_call_addr':       NEWCB_FUSECHECK_CALL,
        'smcsum_address':            NEWCB_SMCSUM_PATTERN,
        'smcheader_address':         NEWCB_SMCHEADER_PATTERN,
        'secotp1_address':           NEWCB_SECOTP_1_CHECK_PATTERN,
        'secotp2_address':           NEWCB_SECOTP_2_CHECK_PATTERN,
        'secotp4_address':           NEWCB_SECOTP_4_CHECK_PATTERN,
        'secotp5_address':           NEWCB_SECOTP_5_CHECK_PATTERN,
        'secotp3_address':           NEWCB_SECOTP_3_CHECK_PATTERN,
        'consoletype_check_address': NEWCB_CONSOLE_TYPE_CHECK_PATTERN,
        'secotp7_address':           NEWCB_SECOTP_7_CHECK_PATTERN,

        'real_entrypoint_decrypt_address': NEWCB_REAL_ENTRYPOINT_DECRYPT_PATTERN,
        'cd_header_check_address': NEWCB_CD_HEADER_CHECK_PATTERN,
    }

    resolved_sigs = bulk_find(resolver_params, cbb)
    if check_bulk_find_results(resolved_sigs):
        # some later new-style CBs (e.g. 16128) don't check the console type at all
        # so the console type check not being found doesn't mean we're missing a signature
        if resolved_sigs['consoletype_check_address'] is not None:
            print("error: one or more required signatures can't be found, cannot apply patches safely.")
            return None
        
        print("CB might not have console type checking, checking that all other sigs resolved...")
        del resolved_sigs['consoletype_check_address']
        if check_bulk_find_results(resolved_sigs):
            print("error: one or more required signatures can't be found, cannot apply patches safely.")
            return None
        
        print("all other sigs found, assuming console type check not present.")
        resolved_sigs['consoletype_check_address'] = None

    reenabling_posts = patchparams['nopost'] is False

    cbb = bytearray(cbb)

    # reclaim some free space while patching out useless functions
    cbb, cd_hash_compare_freespace = _reclaim_cd_hash_compare(cbb, resolved_sigs['cd_hash_cmp_address'])
    cbb, random_delay_freespace    = _reclaim_random_delay(cbb, resolved_sigs['randomdelay_address'])

    post_fcn_address = None
    panic_fcn_address = resolved_sigs['panic_ae_address'] + 4
    if reenabling_posts:
        post_fcn_address = random_delay_freespace.head()
        cbb, new_head = assemble_post_function(cbb, post_fcn_address)
        random_delay_freespace.create_func_and_set_head("post", new_head)

        # make sure any POST patches you add here don't conflict with any other patches!
        cbb = _postpatch_hwinitproxy(cbb, resolved_sigs['hwinitproxy_address'], post_fcn_address, cd_hash_compare_freespace)
        cbb = _postpatch_secengine_init(cbb, resolved_sigs['fusecheck_call_addr'], post_fcn_address, cd_hash_compare_freespace)
        cbb = _postpatch_relocate_and_init_vectors(cbb, resolved_sigs['fusecheck_call_addr'], post_fcn_address, cd_hash_compare_freespace)
    
    if patchparams['nofuse']:
        cbb = _patch_nofuse(cbb, resolved_sigs['fusecheck_call_addr'])
    else:
        if reenabling_posts:
            # POST 0x21 before running this function
            cbb = _postpatch_fusecheck(cbb, resolved_sigs['fusecheck_call_addr'], post_fcn_address, cd_hash_compare_freespace)

        if patchparams['nosmcsum']:
            cbb = _patch_nosmcsum(cbb, resolved_sigs['smcsum_address'])
        elif reenabling_posts:
            # re-enable 0xA4 panic when SMC checksum/HMAC check fails
            cbb = _panicpatch_smcsum(cbb, resolved_sigs['smcsum_address'], panic_fcn_address, cd_hash_compare_freespace)

        cbb = _patch_cb_ldv_check(cbb, resolved_sigs['cb_ldv_address'])

        # code following the LDV check is now free space for 10 instructions
        # giving us space to put 5 panics
        cbb, cb_ldv_freespace = _reclaim_cb_ldv_fusecheck(cbb, resolved_sigs['cb_ldv_address'])

        cbb = _patch_smc_panic_a3_case(cbb, resolved_sigs['smcheader_address'])
        if reenabling_posts:
            # re-enable 0xA3 panic
            cbb = _panicpatch_smc_panic_a3_case(cbb, resolved_sigs['smcheader_address'], panic_fcn_address)

        # rest of this is re-enabling all other panic cases in the fusecheck/SMC sanity check function
        if reenabling_posts:
            # at this point, A3/A4 panics have been reinstated above
            # put secotp panics where the CB LDV revocation check was
            cbb = _panicpatch_secotp1(cbb, resolved_sigs['secotp1_address'], panic_fcn_address, cb_ldv_freespace)
            cbb = _panicpatch_secotp2(cbb, resolved_sigs['secotp2_address'], panic_fcn_address, cb_ldv_freespace)
            cbb = _panicpatch_secotp4(cbb, resolved_sigs['secotp4_address'], panic_fcn_address, cb_ldv_freespace)
            cbb = _panicpatch_secotp5(cbb, resolved_sigs['secotp5_address'], panic_fcn_address, cb_ldv_freespace)
            cbb = _panicpatch_secotp3(cbb, resolved_sigs['secotp3_address'], panic_fcn_address, cb_ldv_freespace)

            # two cases remain: 0xB0 and 0xA1
            if resolved_sigs['consoletype_check_address'] is not None:
                cbb = _panicpatch_consoletype_check(cbb, resolved_sigs['consoletype_check_address'], panic_fcn_address, cd_hash_compare_freespace)

            cbb = _panicpatch_secotp7(cbb, resolved_sigs['secotp7_address'], panic_fcn_address, cd_hash_compare_freespace)

    random_delay_instances = find_all_instances(cbb, NEWCB_RANDOM_DELAY_CALL_PATTERN)
    for d in random_delay_instances:
        print(f"- random delay at 0x{d:04x}")

    cbb, real_entrypoint_decrypt_freespace = _reclaim_real_entrypoint_decrypt(cbb, resolved_sigs['real_entrypoint_decrypt_address'])

    cbb = _patch_cd_header_check(cbb, resolved_sigs['cd_header_check_address'])
    if reenabling_posts:
        cbb = _panicpatch_cd_header_check(cbb,
                                          resolved_sigs['cd_header_check_address'],
                                          panic_fcn_address,
                                          real_entrypoint_decrypt_freespace)
    
    if patchparams['im_a_developer'] is False:
        print("this patcher is still in development, returning error")
        print("to force writing output anyway pass --im-a-developer")
        print("resulting patch probably won't boot; for best results also pass --nopost")
        return None

    return cbb

def newcb_decode_real_entry_point(cbb: bytes, paired_cd: bytes) -> int:
    return \
        struct.unpack(">Q", paired_cd[0x300:0x308])[0] ^ \
        struct.unpack(">Q", paired_cd[0x2F8:0x300])[0] ^ \
        struct.unpack(">Q", paired_cd[0x2F0:0x2F8])[0] ^ \
        0xFFFFFFFFFFFFFFFF ^ \
        struct.unpack(">Q", cbb[0x3D8:0x3E0])[0] ^ \
        struct.unpack(">Q", cbb[0x3C8:0x3D0])[0] ^ \
        struct.unpack(">Q", cbb[0x3C0:0x3C8])[0] ^ \
        struct.unpack(">Q", cbb[0x3A4:0x3AC])[0] ^ \
        struct.unpack(">Q", cbb[0x39C:0x3A4])[0]
