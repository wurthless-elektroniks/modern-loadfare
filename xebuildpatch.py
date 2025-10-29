import struct
from argparse import ArgumentParser,RawTextHelpFormatter

def xebuild_apply_cb_patch(cbb_original: bytes, patch: bytes) -> bytes:
    pos = 0

    cbb = bytearray(cbb_original)

    while pos < len(patch):
        offset = struct.unpack(">I", patch[pos:pos+4])[0]
        if offset == 0xFFFFFFFF:
            break

        length_in_32_bit_words = struct.unpack(">I", patch[pos+4:pos+8])[0]
        patch_length = length_in_32_bit_words * 4
        pos += 8

        unmodified_data = cbb[offset:offset+patch_length]
        patch_data      = patch[pos:pos+patch_length]
        print(f"xebuild_apply_cb_patch: at 0x{offset} changed {unmodified_data.encode("hex")} to {patch_data.encode(hex)}")

        cbb[offset:offset+patch_length] = patch[pos:pos+patch_length]
        pos += patch_length

    return cbb

def xebuild_apply_cb_patch_from_file(cbb_original: bytes, patchfile: str) -> bytes:
    patch = None
    print(f"applying patch from file: {patchfile}")
    with open(patchfile, "rb") as f:
        patch = f.read()
    return xebuild_apply_cb_patch(cbb_original, patch)


def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='xebuilddiff')


    argparser.add_argument("cbb",
                           nargs='?',
                           help="Unmodified CB binary (MUST be in plaintext)")
  
    argparser.add_argument("patch",
                           nargs='?',
                           help="Patch to apply")
  
    argparser.add_argument("output",
                           nargs='?',
                           help="Output binary")
  
    return argparser

def _load_or_die(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def main():
    argparser = _init_argparser()
    args = argparser.parse_args()
    if args.cbb is None or args.patch is None or args.output is None:
        print("error: invalid usage")
        return

    cbb = _load_or_die(args.cbb)
    cbb = xebuild_apply_cb_patch_from_file(cbb, args.patch)
    with open(args.output, "wb") as f:
        f.write(cbb)

if __name__ == '__main__':
    main()

