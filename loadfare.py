from argparse import ArgumentParser,RawTextHelpFormatter
from oldcbpatcher import oldcb_ident,oldcb_try_patch
from xebuildgen import xebuild_patchlist_make

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='loadfare')

    argparser.add_argument("--nofuse",
                           default=False,
                           action='store_true',
                           help="Skip fusechecks altogether (needed for XeLL builds)")
    
    argparser.add_argument("--nosmcsum",
                           default=False,
                           action='store_true',
                           help="Skip SMC checksum in fusecheck function")
    
    argparser.add_argument("--nopost",
                           default=False,
                           action='store_true',
                           help="Disable POST on CBs that have them and don't patch them in for CBs that don't have them")

    argparser.add_argument("--nodecrypt",
                           default=False,
                           action='store_true',
                           help="Skip CD decrypt (needed for XeLL builds)")

    argparser.add_argument("--post67",
                           default=False,
                           action='store_true',
                           help="Install POST 6/7 toggler in HWINIT for RGH1.3/EXT+3 SMC's")
    
    argparser.add_argument("--fastdelay",
                           default=False,
                           action='store_true',
                           help="Change HWINIT delay multiplier from 50 to 10 (slight speedup, might be unstable)")

    argparser.add_argument("--write-xebuild",
                           default=False,
                           action='store_true',
                           help="Write output patch in xeBuild format")

    argparser.add_argument("--xebuild-template",
                            help="Append template file to xeBuild patchfile before writing it")

    argparser.add_argument("cbb_in",
                           nargs='?',
                           help="Input CB binary (MUST be in plaintext)")
  
    argparser.add_argument("patch_out",
                           nargs='?',
                           help="Output patch (default format is binary)")
  
    return argparser


def main():
    argparser = _init_argparser()
    args = argparser.parse_args()

    if args.cbb_in is None or args.patch_out is None:
        print("error: must specify cbb_in and patch_out arguments")
        return

    patchparams = {
        'nofuse': args.nofuse,
        'nosmcsum': args.nosmcsum,
        'nopost': args.nopost,
        'nodecrypt': args.nodecrypt,
        'post67': args.post67,
        'fastdelay': args.fastdelay
    }

    cbb = None
    patched_cbb = None
    with open(args.cbb_in, "rb") as f:
        cbb = f.read()

    if oldcb_ident(cbb):
        print("found old-style CB, attempting patches...")
        patched_cbb = oldcb_try_patch(cbb, patchparams)

    if patched_cbb is None:
        print("unable to patch CB, exiting.")
        return

    output = None
    if args.write_xebuild:
        print("producing output in xeBuild format")
        output = xebuild_patchlist_make(cbb, patched_cbb)

        if args.xebuild_template is not None:
            print(f"appending template from file: {args.xebuild_template}")

            template = None
            with open(args.xebuild_template, "rb") as f:
                template = f.read()
            
            output += template
        
        print("patch generated, ready to write it.")
    else:
        print("writing binary output directly")
        output = patched_cbb

    with open(args.patch_out, "wb") as f:
        f.write(output)

    print("wrote output successfully!")


if __name__ == '__main__':
    main()
