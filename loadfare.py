from argparse import ArgumentParser,RawTextHelpFormatter
from oldcbpatcher import oldcb_ident,oldcb_try_patch
from xebuildgen import xebuild_patchlist_make
from hwinitpatcher import hwinit_apply_patches,hwinit_replace_bytecode

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
                           help="Install POST 6/7 toggler in HWINIT for SMCs that support it (e.g. two-wire RGH1.3)")
    
    argparser.add_argument("--smc-keepalive",
                           default=False,
                           action='store_true',
                           help="Install SMC keepalive code in HWINIT for SMCs that support it (e.g. one-wire RGH1.3)")
    
    argparser.add_argument("--fastdelay",
                           default=False,
                           action='store_true',
                           help="Change HWINIT delay multiplier from 50 to 10 (slight speedup, might be unstable)")

    argparser.add_argument("--no5050",
                           default=False,
                           action='store_true',
                           help="NOP out very long hwinit training loops (massive speedup, probably extremely unstable)")

    argparser.add_argument("--write-xebuild",
                           default=False,
                           action='store_true',
                           help="Write output patch in xeBuild format")

    argparser.add_argument("--xebuild-template",
                            help="Append template file to xeBuild patchfile before writing it")

    argparser.add_argument("--hwinit-bytecode",
                            help="Inject hwinit bytecode from the given file into the target CB")

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

    if args.post67 and args.smc_keepalive:
        print("error: post67 and smc keepalive patches can't be used at the same time")
        return

    patchparams = {
        'nofuse': args.nofuse,
        'nosmcsum': args.nosmcsum,
        'nopost': args.nopost,
        'nodecrypt': args.nodecrypt,
        'post67': args.post67,
        'smc_keepalive': args.smc_keepalive,
        'fastdelay': args.fastdelay,
        'no5050': args.no5050
    }

    cbb = None
    patched_cbb = None
    with open(args.cbb_in, "rb") as f:
        cbb = f.read()

    # bytecode must be replaced BEFORE patches are made
    hwinit_bytecode_file = args.hwinit_bytecode
    if hwinit_bytecode_file is not None:
        if args.no5050 is True:
            print("error: --no5050 is only to be used when not injecting replacement bytecode")
            return

        print(f"attempting to load and inject replacement hwinit bytecode from {hwinit_bytecode_file}")
        bytecode = None
        with open(hwinit_bytecode_file, "rb") as f:
            bytecode = f.read()
        
        cbb = hwinit_replace_bytecode(cbb, bytecode)
        if cbb is None:
            print("hwinit replacement failed, exiting.")
            return
        
    if oldcb_ident(cbb):
        print("found old-style CB, attempting patches...")
        patched_cbb = oldcb_try_patch(cbb, patchparams)

    if patched_cbb is None:
        print("unable to apply base CB patches, exiting.")
        return
    
    patched_cbb = hwinit_apply_patches(patched_cbb, patchparams)
    if patched_cbb is None:
        print("unable to apply hwinit patches, exiting.")
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
