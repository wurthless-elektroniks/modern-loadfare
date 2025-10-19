'''
hwinit bytecode disassembler
Original code and reverse engineering work by Mate Kukri
'''

import sys
from argparse import ArgumentParser,RawTextHelpFormatter
import struct

# bits
#
# 0-5   dest
# 6-10  op1
# 11-15 op2
# 16-31 imm
#

# Global constants
#
# registers during hwinit are used as follows:
# r3  - pointer to start of program
# r4  - pointer to end of program
# r5  - scratchpad
# r6  - scratchpad
# r7  - scratchpad
# r8  - scratchpad
# r9  - scratchpad
# r10 - work registers v0, v1 (32-bit halves)
# r11 - work registers v2, v3 (32-bit halves)
# r12 - work registers v4, v5 (32-bit halves)
# r13 - work registers v6, v7 (32-bit halves)
# r14 - 0xE108_E400_E102_E104 (pointers to PCI bridges and GPU/northbridge)
# r15 - 0xD001_E101_0000_D000 (pointers to PCI config space/BARs)
# r16 - program counter/instruction pointer
# r17 - current opcode being executed
# r18 - callstack?
# r19 - shadow registers s0,  s1
# r20 - shadow registers s2,  s3
# r21 - shadow registers s4,  s5
# r22 - shadow registers s6,  s7
# r23 - shadow registers s8,  s9
# r24 - shadow registers s10, s11
# r25 - shadow registers s12, s13
# r26 - shadow registers s14, s15
# r27 - callstack?
# r28 - callstack?

R14 = 0xE108_E400_E102_E104
R15 = 0xD001_E101_0000_D000

def make_gpu_register(reg: int) -> int:
    return f"0x{0xE4000000 | (reg << 2):08x}"

# from https://github.com/xenon-emu/xenon/blob/main/Xenon/Core/XGPU/XenosRegisters.h
MEMORY_CONTROLLER_REGISTERS = {
    "0xea001080": "SMC_FIFO_INBOX_DATA",
    "0xea001084": "SMC_FIFO_INBOX_CTRL_STATUS",
    "0xea001090": "SMC_FIFO_OUTBOX_DATA",
    "0xea001094": "SMC_FIFO_OUTBOX_CTRL_STATUS",
    

    make_gpu_register(0x0800): "MC0_CNTL",
    make_gpu_register(0x0801): "MC0_DRAM_CONFIG",
    make_gpu_register(0x0802): "MC0_BSB_SNOOPED_TIMER_CNTL",
    make_gpu_register(0x0803): "MC0_TUNING_0",
    make_gpu_register(0x0804): "MC0_TUNING_1",
	make_gpu_register(0x0805): "MC0_RD_BUFFER_CNTL_0",
	make_gpu_register(0x0806): "MC0_ARBITRATION_CNTL",
	make_gpu_register(0x0807): "MC0_TIMING_CNTL_0",
	make_gpu_register(0x0808): "MC0_TIMING_CNTL_1",
	make_gpu_register(0x0809): "MC0_TIMING_CNTL_2",
	make_gpu_register(0x080A): "MC0_PAD_CAL_CNTL",
	make_gpu_register(0x080B): "MC0_DRAM_CMD",
	make_gpu_register(0x080C): "MC0_DRAM_DATA",
	make_gpu_register(0x080D): "MC0_POINTER",
	make_gpu_register(0x080E): "MC0_RDBUF_DATA",
	make_gpu_register(0x080F): "MC0_DRAM_DQ",
	make_gpu_register(0x0810): "MC0_STATUS_0",
	make_gpu_register(0x0811): "MC0_STATUS_1",
	make_gpu_register(0x0812): "MC0_CRC_CNTL",
	make_gpu_register(0x0813): "MC0_DEBUG",
	make_gpu_register(0x0814): "MC0_CRC_READ",
	make_gpu_register(0x0815): "MC0_PERFCOUNTER0_CNTL",
	make_gpu_register(0x0816): "MC0_PERFCOUNTER0_HI",
	make_gpu_register(0x0817): "MC0_PERFCOUNTER0_LOW",
	make_gpu_register(0x0818): "MC0_PERFCOUNTER1_CNTL",
	make_gpu_register(0x0819): "MC0_PERFCOUNTER1_HI",
	make_gpu_register(0x081A): "MC0_PERFCOUNTER1_LOW",
	make_gpu_register(0x081B): "MC0_INTERRUPT_MASK",
	make_gpu_register(0x081C): "MC0_INTERRUPT_STATUS",
	make_gpu_register(0x081D): "MC0_INTERRUPT_ACK",
	make_gpu_register(0x081E): "MC0_SECURE_MEMORY_APERTURE_LOG_MH",
	make_gpu_register(0x081F): "MC0_SECURE_MEMORY_APERTURE_LOG_BIU",
	make_gpu_register(0x0820): "MC0_WR_STR_DLL_0",
	make_gpu_register(0x0821): "MC0_WR_STR_DLL_1",
	make_gpu_register(0x0822): "MC0_DLL_MASTER_ADJ_0",
	make_gpu_register(0x0823): "MC0_DLL_MASTER_ADJ_1",
	make_gpu_register(0x0824): "MC0_TERM_CNTL",
	make_gpu_register(0x0825): "MC0_WR_DATA_DLY_0",
	make_gpu_register(0x0826): "MC0_WR_DATA_DLY_1",
	make_gpu_register(0x0827): "MC0_RD_STR_DLY_0",
	make_gpu_register(0x0828): "MC0_RD_STR_DLY_1",
	make_gpu_register(0x0829): "MC0_WR_STR_DLY",
	make_gpu_register(0x082A): "MC0_PAD_CAL_STATUS",
	make_gpu_register(0x082B): "MC0_RD_STR_DLY_CNTL",
	make_gpu_register(0x0830): "MC0_PAD_IF_CNTL",
	make_gpu_register(0x0831): "MC0_PAD_IF_CNTL_2",
	make_gpu_register(0x0832): "MC0_RD_BUFFER_CNTL_1",
	make_gpu_register(0x0840): "MC1_CNTL",
	make_gpu_register(0x0841): "MC1_DRAM_CONFIG",
	make_gpu_register(0x0842): "MC1_BSB_SNOOPED_TIMER_CNTL",
	make_gpu_register(0x0843): "MC1_TUNING_0",
	make_gpu_register(0x0844): "MC1_TUNING_1",
	make_gpu_register(0x0845): "MC1_RD_BUFFER_CNTL_0",
	make_gpu_register(0x0846): "MC1_ARBITRATION_CNTL",
	make_gpu_register(0x0847): "MC1_TIMING_CNTL_0",
	make_gpu_register(0x0848): "MC1_TIMING_CNTL_1",
	make_gpu_register(0x0849): "MC1_TIMING_CNTL_2",
	make_gpu_register(0x084A): "MC1_PAD_CAL_CNTL",
	make_gpu_register(0x084B): "MC1_DRAM_CMD",
	make_gpu_register(0x084C): "MC1_DRAM_DATA",
	make_gpu_register(0x084D): "MC1_POINTER",
	make_gpu_register(0x084E): "MC1_RDBUF_DATA",
	make_gpu_register(0x084F): "MC1_DRAM_DQ",
	make_gpu_register(0x0850): "MC1_STATUS_0",
	make_gpu_register(0x0851): "MC1_STATUS_1",
	make_gpu_register(0x0852): "MC1_CRC_CNTL",
	make_gpu_register(0x0853): "MC1_DEBUG",
	make_gpu_register(0x0854): "MC1_CRC_READ",
	make_gpu_register(0x0855): "MC1_PERFCOUNTER0_CNTL",
	make_gpu_register(0x0856): "MC1_PERFCOUNTER0_HI",
	make_gpu_register(0x0857): "MC1_PERFCOUNTER0_LOW",
	make_gpu_register(0x0858): "MC1_PERFCOUNTER1_CNTL",
	make_gpu_register(0x0859): "MC1_PERFCOUNTER1_HI",
	make_gpu_register(0x085A): "MC1_PERFCOUNTER1_LOW",
	make_gpu_register(0x085B): "MC1_INTERRUPT_MASK",
	make_gpu_register(0x085C): "MC1_INTERRUPT_STATUS",
	make_gpu_register(0x085D): "MC1_INTERRUPT_ACK",
	make_gpu_register(0x085E): "MC1_SECURE_MEMORY_APERTURE_LOG_MH",
	make_gpu_register(0x085F): "MC1_SECURE_MEMORY_APERTURE_LOG_BIU",
	make_gpu_register(0x0860): "MC1_WR_STR_DLL_0",
	make_gpu_register(0x0861): "MC1_WR_STR_DLL_1",
	make_gpu_register(0x0862): "MC1_DLL_MASTER_ADJ_0",
	make_gpu_register(0x0863): "MC1_DLL_MASTER_ADJ_1",
	make_gpu_register(0x0864): "MC1_TERM_CNTL",
	make_gpu_register(0x0865): "MC1_WR_DATA_DLY_0",
	make_gpu_register(0x0866): "MC1_WR_DATA_DLY_1",
	make_gpu_register(0x0867): "MC1_RD_STR_DLY_0",
	make_gpu_register(0x0868): "MC1_RD_STR_DLY_1",
	make_gpu_register(0x0869): "MC1_WR_STR_DLY",
	make_gpu_register(0x086A): "MC1_PAD_CAL_STATUS",
	make_gpu_register(0x086B): "MC1_RD_STR_DLY_CNTL",
	make_gpu_register(0x0870): "MC1_PAD_IF_CNTL",
	make_gpu_register(0x0871): "MC1_PAD_IF_CNTL_2",
	make_gpu_register(0x0872): "MC1_RD_BUFFER_CNTL_1",
}

def rold(word, d):
    return ((word << d)&0xffff_ffff_ffff_ffff)| \
            ((word >> (64 - d))&0xffff_ffff_ffff_ffff)

def rolw(word, d):
    return ((word << d)&0xffff_ffff)|((word >> (32 - d))&0xffff_ffff)

def extrwi(word, n, b):
    return (rolw(word, b+n))&((1<<n)-1)


def readword(code: bytes, offset: int) -> tuple:
    assert offset < len(code)
    word = struct.unpack(">I",code[offset:offset+4])[0]
    return word, offset + 4

def parse_operand(word, in_op):
    if in_op < 15:
        return in_op - 7

    if in_op == 15:
        raise RuntimeError("no longer handled by this function")

    if in_op < 24:
        immed = word & 0xffff
        idx = in_op & 3

        if in_op < 20:
            return f"0x{rold(R15, idx * 0x10)&0xffff0000|immed:08x}"
        else:
            return f"0x{rold(R14, idx * 0x10)&0xffff0000|immed:08x}"

    half = in_op&1

    if (27 < in_op):
        if (29 < in_op):
            return f"%r13_{half}"
        return f"%r12_{half}"
    if (25 < in_op):
        return f"%r11_{half}"

    return f"%r10_{half}"

def parse_dest(word):
    half = word&1
    in_op = word&7
    if (3 < in_op):
        if (6 < in_op):
            return f"%r13_{half}"
        return f"%r12_{half}"
    if (2 < in_op):
        return f"%r11_{half}"
    return f"%r10_{half}"

def hwinit_disassemble(code: bytes, org: int = 0, fout = sys.stdout):

    offset = 0
    while offset < len(code):
        org_offset = org + offset

        word, offset = readword(code, offset)

        dest     = parse_dest(word)

        inop1 = extrwi(word, 5, 6)
        if inop1 == 15:
            operand1, offset = readword(code, offset)
            operand1 = f"0x{operand1:08x}"
        else:
            operand1 = parse_operand(word, inop1)

        inop2 = extrwi(word, 5, 11)
        if inop2 == 15:
            operand2, offset = readword(code, offset)
            operand2 = f"0x{operand2:08x}"
        else:
            operand2 = parse_operand(word, inop2)

        opcode   = word >> 26

        r = False
        match opcode:
            # opcodes 0~7 are branch opcodes that abuse powerpc logic exquisitely
            #
            # cmplw      cr7,r5,r6    <-- actually run comparison for jump
            # mfocrf     r7,cr7       <-- uh oh
            # vvv all this is decoding and masking the results of the comparison vvv
            # rlwinm     r7,r7,0x1f,0x1d,0x1f
            # rlwinm     r9,r8,0x0,0x1e,0x1f
            # rlwinm     r8,r8,0x1e,0x1f,0x1f
            # srw        r7,r7,r9
            # rlwinm     r7,r7,0x0,0x1f,0x1f
            #
            # then if r8 and r7 don't match, continue interpreting.
            # otherwise take the jump which is computed as follows:
            #
            # rlwinm     r8,r17,0x2,0xe,0x1d
            # add        r16,r3,r8            <-- r16 = instruction pointer
            case 0:
                opcode = "branch_cond0"
                ops = 2
            case 1:
                opcode = "branch_cond1"
                ops = 2
            case 2:
                opcode = "branch_cond2"
                ops = 2
            case 3:
                # typically unconditional i.e. branch_cond3 -7, -7
                opcode = "branch_cond3"
                ops = 2
            case 4:
                # this is guessed based on some spinloop behavior
                opcode = "beq"
                ops = 2
            case 5:
                opcode = "branch_cond5"
                ops = 2
            case 6:
                opcode = "branch_cond6"
                ops = 2
            case 7:
                opcode = "branch_cond7"
                ops = 2

            # writes 32-bit word using stwbrx
            #
            # rldicr     r8,r3,0x0,0x0
            # stwbrx     r5,r8,r6
            case 8:
                opcode = "store_word"
                ops = 2

            # similar to store_word, but writes the same word to offs and offs+0x100
            #
            # rldicr     r8,r3,0x0,0x0
            # stwbrx     r5,r8,r6
            # addi       r8,r8,0x100
            # stwbrx     r5,r8,r6
            #
            # this opcode is abused extensively when configuring the SDRAM controllers
            # because MC0 is mapped at 0xE4002000 and MC1 is at 0xE4002100. in theory
            # you could have two different kinds of SDRAM bankings that can be configured
            # independently, but microsoft never did this.
            case 9:
                opcode = "store_word_0_100"
                ops = 2

            # does this
            #
            # rldicr     r8,r3,0x0,0x0
            # lwbrx      r5,r8,r6
            # rlwimi     r17,r17,0xb,0x1d,0x1f
            #
            # ... then jumps to some code that places the word in the right register
            case 0xa:
                opcode = "load_word"
                ops = 1
                r = True

            # looks like a call/return opcode
            # relevant disassembly:
            # cmplwi     r6,0x1
            # beq        LAB_00000b24
            # cmplwi     r6,0x2
            # beq        FUN_00000dcc
            # cmplwi     r6,0x3
            # beq        FUN_00000dc4
            #
            # default case: pc = hwinit_prg_base + (r18 << 2)
            # (likely a return-from-subroutine procedure)
            #
            # case 1 is definitely a "call procedure" opcode
            # subf       r7,r3,r16
            # rlwinm     r7,r7,0x1e,0x10,0x1f
            # rldicl     r8,r28,0x10,0x30
            # cmpldi     r8,0x0
            # bne        FUN_00000dc4        <-- go to "done" block if r8 not zero
            # rldicl     r28,r28,0x10,0x0
            # ldicl      r27,r27,0x10,0x0
            # rldicl     r18,r18,0x10,0x0
            # rldimi     r28,r27,0x0,0x30
            # rldimi     r27,r18,0x0,0x30
            # rldimi     r18,r7,0x0,0x30      <-- set r18 to return address
            # rlwinm     r8,r17,0x2,0xe,0x1d  <-- r8 <<= 2
            # add        r16,r3,r8            <-- pc = hwinit_prg_base + r8
            #
            # case 2 immediately goes to hwinit failure case, which posts 0xA9 and halts
            # (let's call that "die")
            #
            # case 3 immediately goes to hwinit "done" case
            case 0xb:
                opcode = "op_B"
                ops = 2

            # delay multiplies r6 by 50 then adds that to the current timebase value
            # and waits until the timebase value reaches its target before continuing execution
            case 0xc:
                opcode = "delay"
                ops = 1
            case 0xd:
                opcode = "sync"
                ops = 0

            # both 0x0E and 0x0F do the same thing, which is move 0 to the target register.
            # however they're both unused; seems the microsoft assembler preferred to do
            # add %rX,0,0 to do the same thing.
            case 0xe:
                opcode = "load0_E"
                ops = 0
                r = True
            case 0xf:
                opcode = "load0_F"
                ops = 0
                r = True

            case 0x10:
                opcode = "nop_10"
                ops = 0
            case 0x11:
                opcode = "nop_11"
                ops = 0

            # some sort of short relative jump instruction that went unused
            #
            # rlwinm     r8,r17,0x2,0xe,0x1d  <-- r8 == (opcode & 0xFFFF) << 2
            # add        r16,r16,r8           <-- pc += r8
            case 0x12:
                opcode = "op_12"
                ops = 2

            case 0x13:
                opcode = "add"
                ops = 2
                r = True

            case 0x14:
                opcode = "and"
                ops = 2
                r = True

            # weird opcode that does this
            #
            # rlwimi     r5,r6,0x18,0x0,0x7
            # rlwimi     r5,r6,0x8,0x8,0xf
            # rlwimi     r5,r6,0x18,0x10,0x17
            # rlwimi     r5,r6,0x8,0x18,0x1f
            #
            # looks like some sort of endian swap opcode but it's useless because
            # load_word and store_word opcodes already do that for us
            case 0x15:
                opcode = "op_15"
                ops = 2
                r = True

            case 0x16:
                opcode = "or"
                ops = 2
                r = True
            case 0x17:
                opcode = "subf"
                ops = 2
                r = True
            case 0x18:
                opcode = "xor"
                ops = 2
                r = True
            case 0x19:
                opcode = "store_half"
                ops = 2
            case 0x1a:
                opcode = "load_half"
                ops = 1
                r = True
            case 0x1b:
                opcode = "mul"
                ops = 2
                r = True

            # divwu      r5,r5,r6
            case 0x1c:
                opcode = "div"
                ops = 2
                r = True

            # divwu      r8,r5,r6
            # mullw      r8,r8,r6
            # subf       r5,r8,r5
            case 0x1d:
                opcode = "rem"
                ops = 2
                r = True

            # op_1E exchanges r12 and r13 (v4,v5,v6,v7) with contents of shadow registers
            #
            # starts by doing this
            #
            # or         r7,r12,r12            <-- effectively just mov opcodes
            # or         r8,r13,r13
            # rlwinm     r5,r5,0x0,0x1e,0x1f   <-- r5 &= 3
            #
            # then:
            # case r5 < 1: ("excg v3-v7,s0-s3")
            #   or         r12,r19,r19
            #   or         r13,r20,r20
            #   or         r19,r7,r7
            #   or         r20,r8,r8
            # case r5 == 1: ("excg v3-v7,s4-s7")
            #   or         r12,r21,r21
            #   or         r13,r22,r22
            #   or         r21,r7,r7
            #   or         r22,r8,r8
            # case r5 < 3:  ("excg v3-v7,s8-s11")
            #   or         r12,r23,r23
            #   or         r13,r24,r24
            #   or         r23,r7,r7
            #   or         r24,r8,r8
            # default:      ("excg v3-v7,s12-s15")
            #   or         r12,r25,r25
            #   or         r13,r26,r26
            #   or         r25,r7,r7
            #   or         r26,r8,r8
            case 0x1e:
                opcode = "op_1E"
                ops = 2

            # opcode 0x1F, not implemented here, seems to be another "done" case
            # that exits the interpreter immediately with a "success" result

            # opcodes 0x20~0x3F do this
            #
            # rlwinm     r8,r17,0x6,0x1b,0x1f
            # rlwnm      r5,r5,r8,0x0,0x1f
            # and        r5,r5,r6
            #
            # ... then jump to the same code as load_word to dump the result where it belongs
            case other:
                assert opcode != 0x1f
                rotlcnt = extrwi(word, 5, 1)
                opcode = f"rotlw_by_{rotlcnt}_then_and"
                ops = 2
                r = True

        if r:
            match ops:
                case 0:
                    print(f"{org_offset:04x}: {dest} = {opcode}", file=fout)
                case 1:
                    # load from immediate 32-bit address
                    if opcode == "load_word" and operand1 == -7:
                        operand2 = operand2 if operand2 not in MEMORY_CONTROLLER_REGISTERS else MEMORY_CONTROLLER_REGISTERS[operand2]
                        print(f"{org_offset:04x}: {dest} = *({operand2})", file=fout)
                    else:
                        print(f"{org_offset:04x}: {dest} = {opcode} {operand1}", file=fout)


                case 2:
                    if opcode == "add" and operand2 == 0:
                        operand1 = operand1 if operand1 not in MEMORY_CONTROLLER_REGISTERS else MEMORY_CONTROLLER_REGISTERS[operand1]
                        print(f"{org_offset:04x}: {dest} = {operand1}", file=fout)
                    else:
                        print(f"{org_offset:04x}: {dest} = {opcode} {operand1}, {operand2}", file=fout)
                case other:
                    assert False
        else:
            if (word & 0xFC000000) == 0x2C000000:
                # hack for call/return but whatever
                if operand2 == 1:
                    print(f"{org_offset:04x}: call 0x{(word&0xFFFF)<<2:04x}", file=fout)
                elif operand2 == 2:
                    print(f"{org_offset:04x}: die", file=fout)
                elif operand2 == 3:
                    print(f"{org_offset:04x}: done", file=fout)
                else:
                    print(f"{org_offset:04x}: return", file=fout)
            elif (word & 0xFC000000) <= 0x1C000000:
                destaddr = (word&0xFFFF)<<2
                pos = '^' if destaddr < offset else 'v'

                if opcode == "branch_cond3" and operand1 == -7 and operand2 == -7:
                    print(f"{org_offset:04x}: jmp 0x{destaddr:04x} {pos}", file=fout)
                else:
                    print(f"{org_offset:04x}: {opcode} {operand1}, {operand2} -> 0x{destaddr:04x} {pos}", file=fout)

            else:
                match ops:
                    case 0:
                        print(f"{org_offset:04x}: {opcode}", file=fout)
                    case 1:
                        print(f"{org_offset:04x}: {opcode} {operand1}", file=fout)
                    case 2:
                        if operand2 in MEMORY_CONTROLLER_REGISTERS:
                            print(f"{org_offset:04x}: {opcode} {operand1}, {MEMORY_CONTROLLER_REGISTERS[operand2]}", file=fout)
                        else:                
                            print(f"{org_offset:04x}: {opcode} {operand1}, {operand2}", file=fout)
                    case other:
                        assert False


# old grandpa copypasting AI code. wow!
def hex_to_int(hex_string):
    try:
        return int(hex_string, 16)
    except ValueError:
        raise RuntimeError(f"Invalid hexadecimal value: '{hex_string}'")

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='hwinitdasm')

    argparser.add_argument("--org",
                            default=0x0000,
                            type=hex_to_int,
                            help="Set base address of program to this (default is 0x0000)")

    argparser.add_argument("hwinitfile",
                           nargs='?',
                           help="Path to hwinit bytecode dump")

    return argparser


def main():
    argparser = _init_argparser()
    args = argparser.parse_args()

    if args.hwinitfile is None:
        print("error: file not specified")
        return

    code = None
    with open(args.hwinitfile,"rb") as f:
        code = f.read()

    hwinit_disassemble(code, args.org)

if __name__ == '__main__':
    main()
