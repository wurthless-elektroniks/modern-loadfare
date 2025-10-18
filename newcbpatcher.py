'''
New-style CB patcher

New-style CBs typically have an entry point at 0x3E0, remove POST codes,
add random delays in an attempt to throw off glitch chips, and munge
some parameters before calling CD.
'''

from patcher import *
from signature import SignatureBuilder, WILDCARD, bulk_find, check_bulk_find_results

# this is the only POST code that wasn't removed from newer CBs
NEWCB_PANIC_FUNCTION = SignatureBuilder() \
    .pattern([
        0x38, 0x60, 0x00, 0xae, # li r3,0xA3
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

# this is the infamous random delay function.
# it is called throughout cd_load_and_jump and nowhere else.
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
    cbb[cd_hash_cmp_address:cd_hash_cmp_address+4] = bytes([0x38,0x60,0xff,0xff])
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
        0x7f, 0x0b, 0x50, 0x00,     # cmpw       cr6,r11,r10
        0x40, 0x9a, 0x00, 0x10,     # bne        cr6,LAB_0000699c
        WILDCARD, WILDCARD, 0x04, 0x3e, # rlwinm     r11,r21,0x0,0x10,0x1f
        0x61, WILDCARD, 0x00, 0x08, # ori        r21,r11,0x8
        0x48, 0x00, 0x00, 0x2C      # branch target different because panic is removed
    ]) \
    .build()

def _patch_cb_ldv_check(cbb: bytes, cb_ldv_address: int):
    cbb, _ = assemble_nop(cbb, cb_ldv_address+0x04)
    return cbb

# identical to old CB
NEWCB_FUSECHECK_CALL = SignatureBuilder() \
    .pattern([
        0x7F, 0x63, 0xDB, 0x78,
        0x7F, 0x84, 0xE3, 0x78,
        0x7F, 0xA5, 0xEB, 0x78,
        0x7F, 0xC6, 0xF3, 0x78,
        0x48, WILDCARD, WILDCARD, WILDCARD, # +0x10 call to fusecheck function
        0x48, WILDCARD, WILDCARD, WILDCARD, # +0x14 call to secengine init function
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

def _postpatch_secengine_init(cbb: bytes, fusecheck_call_addr: int,post_address: int, free_space: FreeSpaceArea) -> bytes:
    secengine_init_addr = decode_branch_address(cbb[fusecheck_call_addr + 0x14:fusecheck_call_addr + 0x18], fusecheck_call_addr + 0x14)

    post_target_address = free_space.head()
    cbb, head = assemble_post_call(cbb, post_target_address, post_address, 0x22)
    cbb, head = assemble_branch(cbb, head, secengine_init_addr)
    free_space.create_func_and_set_head("seceng_22_reroute", head)

    cbb, _ = assemble_branch_with_link(cbb, fusecheck_call_addr + 0x14, post_target_address)
    return cbb

def _patch_nofuse(cbb: bytes, fusecheck_call_addr: int) -> bytes:
    base = fusecheck_call_addr+0x10
    print(f"_patch_nofuse: put nop at 0x{base:04x}")
    cbb, _ = assemble_nop(cbb, base)
    return cbb

def newcb_ident(cbb: bytes) -> bool:
    # entry point must be 0x3E0
    return cbb[0x0000:0x0002] == bytes([0x43, 0x42]) and \
           cbb[0x0008:0x000C] == bytes([0x00, 0x00, 0x03, 0xE0])

def newcb_try_patch(cbb: bytes, patchparams: dict) -> None | bytes:
    if newcb_ident(cbb) is False:
        return None
    
    resolver_params = {
        'panic_a3_address':          NEWCB_PANIC_FUNCTION,
        'randomdelay_address':       NEWCB_RANDOM_DELAY_FUNCTION,
        'cd_hash_cmp_address':       NEWCB_CD_HASH_COMPARE_FUNCTION,
        'hwinitproxy_address':       NEWCB_HWINIT_PROXY,

        'cb_ldv_address':            NEWCB_CB_LDV_PREAMBLE_PATTERN,
        'fusecheck_call_addr':       NEWCB_FUSECHECK_CALL,
    }

    resolved_sigs = bulk_find(resolver_params, cbb)
    if check_bulk_find_results(resolved_sigs):
        print("error: one or more required signatures can't be found, cannot apply patches safely.")
        return None

    reenabling_posts = patchparams['nopost'] is False

    cbb = bytearray(cbb)

    # reclaim some free space while patching out useless functions
    cbb, cd_hash_compare_freespace = _reclaim_cd_hash_compare(cbb, resolved_sigs['cd_hash_cmp_address'])
    cbb, random_delay_freespace    = _reclaim_random_delay(cbb, resolved_sigs['randomdelay_address'])
    post_fcn_address = None

    if reenabling_posts:
        post_fcn_address = random_delay_freespace.head()
        cbb, new_head = assemble_post_function(cbb, post_fcn_address)
        random_delay_freespace.create_func_and_set_head("post", new_head)

        # make sure any POST patches you add here don't conflict with any other patches!
        cbb = _postpatch_hwinitproxy(cbb, resolved_sigs['hwinitproxy_address'], post_fcn_address, cd_hash_compare_freespace)
        cbb = _postpatch_secengine_init(cbb, resolved_sigs['fusecheck_call_addr'], post_fcn_address, cd_hash_compare_freespace)

    if patchparams['nofuse']:
        cbb = _patch_nofuse(cbb, resolved_sigs['fusecheck_call_addr'])
    else:
        if reenabling_posts:
            cbb = _postpatch_fusecheck(cbb, resolved_sigs['fusecheck_call_addr'], post_fcn_address, cd_hash_compare_freespace)

        # if patchparams['nosmcsum']:
            # cbb = _patch_nosmcsum(cbb, resolved_sigs['smcsum_address'])
        cbb = _patch_cb_ldv_check(cbb, resolved_sigs['cb_ldv_address'])
        # cbb = _patch_smc_panic_a3_case(cbb, resolved_sigs['smcheader_address'])


    print("i'm still in development - returning None.")
    return None
