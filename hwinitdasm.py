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
            case 8:
                opcode = "store_word"
                ops = 2
            case 9:
                opcode = "store_word_0_100"
                ops = 2
            case 0xa:
                opcode = "load_word"
                ops = 1
                r = True
            
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
            case 0x1c:
                opcode = "div"
                ops = 2
                r = True
            case 0x1d:
                opcode = "rem"
                ops = 2
                r = True
            case 0x1e:
                opcode = "op_E"
                ops = 2
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
