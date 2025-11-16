import struct
from argparse import ArgumentParser,RawTextHelpFormatter
from xebuildinigen import calc_cb_crc32

def pad_bootloader(bl: bytes, pad_to: int) -> bytes:
    current_bl_size = struct.unpack(">I", bl[0x0C:0x10])[0]

    if current_bl_size > pad_to:
        raise RuntimeError("loader too big")

    if current_bl_size == pad_to:
        return bl
    
    if (pad_to & 0xF) != 0:
        raise RuntimeError("target size should be multiple of 0x10")
    
    padded = bytearray(bl)
    padded += bytes([0] * (pad_to - current_bl_size))
    padded[0x0C:0x10] = struct.pack(">I", pad_to)
    return padded

# --------------------------------------------------------------------------------------------------

def hex_to_int(hex_string):
    try:
        return int(hex_string, 16)
    except ValueError:
        raise RuntimeError(f"Invalid hexadecimal value: '{hex_string}'")

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='padbl',
                               description="Zero-pads bootloader")

    argparser.add_argument("--pad-to",
                            default=0x9350,
                            type=hex_to_int,
                            help="Pad to this number of bytes in hexadecimal (default matches CB_B 5772)")

    argparser.add_argument("bl_in",
                           nargs='?',
                           help="Input binary (MUST be in plaintext)")
  
    argparser.add_argument("bl_out",
                           nargs='?',
                           help="Output binary")
  
    return argparser

def main():
    argparser = _init_argparser()
    args = argparser.parse_args()

    if args.bl_in is None or args.bl_out is None:
        print("bl_in or bl_out not specified")
        return

    bl = None
    with open(args.bl_in, "rb") as f:
        bl = f.read()

    bl = pad_bootloader(bl, args.pad_to)

    if bl[1] == 0x42:
        print(f"CB detected. new xebuild crc32 will be: {calc_cb_crc32(bl):08x}")

    print("bootloader padded, writing it now...")

    with open(args.bl_out, "wb") as f:
        f.write(bl)

if __name__ == '__main__':
    main()
