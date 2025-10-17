'''
Patches for both the hwinit interpreter and its bytecode

hwinit is basically unchanged between old-style and new-style CBs so we can throw everything in here.
'''

import struct
from patcher import assemble_nop, assemble_branch, decode_branch_address, decode_branch_conditional_address
from signature import SignatureBuilder, WILDCARD, bulk_find
from postcounter import assemble_hwinit_postcount_block_universal
from smckeepalive import assemble_hwinit_smc_keepalive_block_universal


# this is within the hwinit bytecode itself
HWINIT_TRAINING_LOOP_CONDITION_PATTERN = SignatureBuilder() \
    .pattern([
        0x03, 0x4F, WILDCARD, WILDCARD, 0x50, 0x50, 0x50, 0x50
    ]) \
    .build()

def _patch_no5050(cbb: bytes, hwinit_bytecode_start_address: int, hwinit_bytecode_end_address: int) -> bytes:
    offset = hwinit_bytecode_start_address

    # replace all instances of this pattern with NOPs to disable the long training loops
    found_one = False
    while offset < hwinit_bytecode_end_address:
        offset = HWINIT_TRAINING_LOOP_CONDITION_PATTERN.find(cbb, offset)
        if offset is None or offset >= hwinit_bytecode_end_address:
            break

        found_one = True
        print(f"_patch_no5050: insert two nops in hwinit bytecode at 0x{offset:04x}")
        cbb[offset:offset+8] = bytes([0x40, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00])
        offset += 8

    if found_one is False:
        print("_patch_no5050: unable to find wait condition(s). no changes applied.")

    return cbb

def _patch_fast5050(cbb: bytes, hwinit_bytecode_start_address: int, hwinit_bytecode_end_address: int, step: int = 4) -> bytes:
    if step not in [ 1, 2, 4, 8, 16 ]:
        print("_patch_fast5050: error: illegal training step value. must be 1, 2, 4, 8, 16")
        return None

    new_training_values = bytes([step, step, step, step])

    offset = hwinit_bytecode_start_address
    found_one = False
    while offset < hwinit_bytecode_end_address:
        offset = HWINIT_TRAINING_LOOP_CONDITION_PATTERN.find(cbb, offset)
        if offset is None or offset >= hwinit_bytecode_end_address:
            break

        if cbb[offset-4:offset] != bytes([0x01, 0x01, 0x01, 0x01]):
            continue

        found_one = True
        print(f"_patch_fast5050: at 0x{offset-4:04x} change 0x01010101 to 0x{struct.unpack(">I",new_training_values)[0]:08x}")
        cbb[offset-4:offset] = new_training_values
        offset += 8

    if found_one is False:
        print("_patch_fast5050: unable to find wait condition(s). no changes applied.")

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

def hwinit_find_bytecode(cbb: bytes) -> dict | None:
    hwinit_top_address = OLDCB_HWINIT_TOP_PATTERN.find(cbb)
    if hwinit_top_address is None:
        print("error: cannot find top of hwinit interpreter")
        return None

    # old hwinits like 5761 hardcode the hwinit bytecode program size into the function itself
    hwinit_setup_exec_hardcoded_pattern = SignatureBuilder() \
        .pattern([
            0x3c, 0x60, 0x00, 0x00,           # +0x00 lis  r3,0x0
            0x38, 0x63, WILDCARD, WILDCARD,   # +0x04 addi r3,r3,0x8b8   <-- hwinit bytecode location
            0x7c, 0x62, 0x1a, 0x14,           # +0x08 add  r3,r2,r3
            0x38, 0x83, WILDCARD, WILDCARD,   # +0x0C addi r4,r3,0x44d8  <-- bytecode size
        ]) \
        .build()
    
    # more recent hwinits like 6752 have the hwinit bytecode program size headered
    hwinit_setup_exec_headered_pattern = SignatureBuilder() \
        .pattern([
            0x3c, 0x60, 0x00, 0x00,          # +0x00 lis  r3,0x0
            0x38, 0x63, WILDCARD, WILDCARD,  # +0x04 addi r3,r3,0xf70  <-- hwinit bytecode location
            0x7c, 0x62, 0x1a, 0x14,          # add  r3,r2,r3
            0x80, 0x83, 0x00, 0x00,          # lwz  r4,0x0(r3)   <-- bytecode size
            0x38, 0x63, 0x00, 0x04,          # addi r3,r3,0x4    <-- r3 now points to actual hwinit start
        ]) \
        .build()
    
    headered_address = hwinit_setup_exec_headered_pattern.find(cbb, hwinit_top_address - 0x80)
    if headered_address is not None:
        hwinit_bytecode_address = struct.unpack(">H", cbb[headered_address+6:headered_address+8])[0]
        hwinit_size = struct.unpack(">I", cbb[hwinit_bytecode_address:hwinit_bytecode_address+4])[0]
        return {
            'headered':              True,
            'offset':                hwinit_bytecode_address,
            'program_start_address': hwinit_bytecode_address+4,
            'program_size':          hwinit_size
        }

    hardcoded_address = hwinit_setup_exec_hardcoded_pattern.find(cbb, hwinit_top_address - 0x80)
    if hardcoded_address is not None:
        hwinit_bytecode_address = struct.unpack(">H", cbb[hardcoded_address+0x06:hardcoded_address+0x08])[0]
        hwinit_size             = struct.unpack(">H", cbb[hardcoded_address+0x0E:hardcoded_address+0x10])[0]
        return {
            'headered':              False,
            'offset':                hwinit_bytecode_address,
            'program_start_address': hwinit_bytecode_address,
            'program_size':          hwinit_size
        }

    return None

def hwinit_extract_bytecode(cbb: bytes) -> None | bytes:
    hwinit_meta = hwinit_find_bytecode(cbb)
    if hwinit_meta is None:
        return None
    
    hwinit_bytecode_address = hwinit_meta['program_start_address']
    hwinit_size = hwinit_meta['program_size']
    return cbb[hwinit_bytecode_address:hwinit_bytecode_address+hwinit_size]

def hwinit_replace_bytecode(cbb: bytes, hwinit_bytecode: bytes) -> bytes | None:
    hwinit_meta = hwinit_find_bytecode(cbb)
    if hwinit_meta is None:
        return None
    
    if hwinit_meta['headered'] is False:
        print("error: CB has hardcoded size. please use a CB with headered hwinit")
        return None
    maximum_size = hwinit_meta['program_size']
    if len(hwinit_bytecode) > maximum_size:
        print(f"error: replacement hwinit bytecode is too large (current size {maximum_size}, replacement size {len(hwinit_bytecode)})")
        return None
    
    hwinit_bytecode_address = hwinit_meta['program_start_address']
    cbb = bytearray(cbb)
    cbb[hwinit_bytecode_address:hwinit_bytecode_address+len(hwinit_bytecode)] = hwinit_bytecode

    hwinit_offset = hwinit_meta['offset']
    cbb[hwinit_offset:hwinit_offset+4] = struct.pack(">I",len(hwinit_bytecode))

    return cbb

def hwinit_apply_patches(cbb: bytes, patchparams: dict) -> bytes:
    resolver_params = {
        'hwinit_top_addr':      OLDCB_HWINIT_TOP_PATTERN,
        'hwinit_delay_addr':    OLDCB_HWINIT_DELAY_PATTERN
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

    meta = hwinit_find_bytecode(cbb)
    if meta is None:
        print("error: can't find hwinit bytecode")
        return None

    hwinit_start_address = meta['program_start_address']
    hwinit_size          = meta['program_size']

    cbb = bytearray(cbb)

    if patchparams['post67'] or patchparams['smc_keepalive']:
        hwinit_top_address   = resolved_sigs['hwinit_top_addr']
        hwinit_delay_address = resolved_sigs['hwinit_delay_addr']

        hwinit_register_setup_address = _get_hwinit_register_setup_fcn_address(cbb, hwinit_top_address)
        hwinit_loop_top_address       = _get_hwinit_loop_top_address(hwinit_top_address)
        hwinit_done_address           = _get_hwinit_done_address(cbb, hwinit_top_address)

        # unconditional branch lives here, i hope
        hwinit_exit_address = hwinit_done_address + 4

        if patchparams['post67']:
            print("installing post67...")
            cbb = assemble_hwinit_postcount_block_universal(cbb,
                                                            0x280,
                                                            hwinit_register_setup_address,
                                                            hwinit_loop_top_address,
                                                            hwinit_exit_address,
                                                            patchparams['fastdelay'])
        elif patchparams['smc_keepalive']:
            print("installing smc_keepalive...")
            cbb = assemble_hwinit_smc_keepalive_block_universal(
                                                            cbb,
                                                            0x280,
                                                            hwinit_register_setup_address,
                                                            hwinit_loop_top_address,
                                                            hwinit_exit_address,
                                                            patchparams['fastdelay'])
        else:
            raise RuntimeError("code execution shouldn't have ended up here bucko")

        cbb, _ = assemble_branch(cbb, _get_hwinit_init_hook_address(hwinit_top_address), 0x280 + 0)
        cbb, _ = assemble_branch(cbb, hwinit_delay_address, 0x280 + 4)
        cbb, _ = assemble_branch(cbb, hwinit_done_address, 0x280 + 8)

    elif patchparams['fastdelay']:
        cbb = _patch_fastdelay(cbb, resolved_sigs['hwinit_delay_addr'])

    if patchparams['no5050']:
        cbb = _patch_no5050(cbb, hwinit_start_address, hwinit_start_address+hwinit_size)
    elif patchparams['sdram_step'] not in [ None, 1 ]:
        cbb = _patch_fast5050(cbb, hwinit_start_address, hwinit_start_address+hwinit_size, step=patchparams['sdram_step'])


    return cbb