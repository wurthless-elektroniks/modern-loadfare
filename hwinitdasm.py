'''
hwinit bytecode disassembler
Original code and reverse engineering work by Mate Kukri
'''

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

def hwinit_disassemble(code: bytes, org: int = 0):

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
                opcode = "branch_cond3"
                ops = 2
            case 4:
                opcode = "branch_cond4"
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
                    print(f"{org_offset:04x}: {dest} = {opcode}")
                case 1:
                    print(f"{org_offset:04x}: {dest} = {opcode} {operand1}")
                case 2:
                    print(f"{org_offset:04x}: {dest} = {opcode} {operand1}, {operand2}")
                case other:
                    assert False
        else:
            if (word & 0xFC000000) == 0x2C000000:
                # hack for call/return but whatever
                if operand2 == 1:
                    print(f"{org_offset:04x}: call 0x{(word&0xFFFF)<<2:04x}")
                elif operand2 == 2:
                    print(f"{org_offset:04x}: die")
                elif operand2 == 3:
                    print(f"{org_offset:04x}: done")
                else:
                    print(f"{org_offset:04x}: return")
            elif (word & 0xFC000000) <= 0x1C000000:
                destaddr = (word&0xFFFF)<<2
                pos = '^' if destaddr < offset else 'v'
                print(f"{org_offset:04x}: {opcode} {operand1}, {operand2} -> 0x{destaddr:04x} {pos}")

            else:
                match ops:
                    case 0:
                        print(f"{org_offset:04x}: {opcode}")
                    case 1:
                        print(f"{org_offset:04x}: {opcode} {operand1}")
                    case 2:
                        print(f"{org_offset:04x}: {opcode} {operand1}, {operand2}")
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
