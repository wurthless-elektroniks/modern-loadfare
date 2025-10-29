from argparse import ArgumentParser,RawTextHelpFormatter
from xebuildgen import xebuild_patchlist_make

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='xebuilddiff')


    argparser.add_argument("file_a",
                           nargs='?',
                           help="Unmodified CB binary (MUST be in plaintext)")
  
    argparser.add_argument("file_b",
                           nargs='?',
                           help="Patched CB binary (MUST be in plaintext)")
  
    argparser.add_argument("patch_out",
                           nargs='?',
                           help="Output patch (default format is xeBuild)")
  
    return argparser

def _load_or_die(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def main():
    argparser = _init_argparser()
    args = argparser.parse_args()

    if args.file_a is None or args.file_b is None or args.patch_out is None:
        print("error: invalid usage")
        return

    file_a = _load_or_die(args.file_a)
    file_b = _load_or_die(args.file_b)
    patchlist = xebuild_patchlist_make(file_a, file_b)
    with open(args.patch_out, "wb") as f:
        f.write(patchlist)

if __name__ == '__main__':
    main()
