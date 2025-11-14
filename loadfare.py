
import struct
from argparse import ArgumentParser,RawTextHelpFormatter
from oldcbpatcher import oldcb_ident,oldcb_try_patch
from newcbpatcher import newcb_ident,newcb_try_patch,newcb_decode_real_entry_point
from xebuildgen import xebuild_patchlist_make
from hwinitpatcher import hwinit_apply_patches,hwinit_replace_bytecode
from vfusespatcher import vfuses_try_patch
from cbheader import get_cd_rotsumsha
from rotsumsha import rotsumsha_calc

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='loadfare')

    argparser.add_argument("--hwinit-only",
                           default=False,
                           action='store_true',
                           help="Disable **ALL** CB patches and patch hwinit only (will NOT produce a bootable patch)")

    argparser.add_argument("--disable-default",
                           default=False,
                           action='store_true',
                           help="Disable all default CB patches (will NOT produce a bootable patch)")

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
                           help="Skip patching POST codes into new-style CBs")

    argparser.add_argument("--nodecrypt",
                           default=False,
                           action='store_true',
                           help="Skip CD decrypt (needed for XeLL builds)")

    argparser.add_argument("--oldcd",
                           default=False,
                           action='store_true',
                           help="Patch new-style CBs to work with older CDs")

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
    
    argparser.add_argument("--sdram-step",
                           type=int,
                           help="Change hwinit SDRAM calibration loop step value (1, 2, 4, 8, 16; lower = more stable, higher = faster)")

    argparser.add_argument("--no5050",
                           default=False,
                           action='store_true',
                           help="Skip SDRAM training loops in hwinit (DANGER: extremely unstable)")

    argparser.add_argument("--vfuse",
                           default=False,
                           action='store_true',
                           help="Apply vfuse patches for Glitch2m images and similar")

    argparser.add_argument("--write-xebuild",
                           default=False,
                           action='store_true',
                           help="Write output patch in xeBuild format")

    argparser.add_argument("--xebuild-template",
                            help="Append template file to xeBuild patchfile before writing it")

    argparser.add_argument("--hwinit-bytecode",
                            help="Inject hwinit bytecode from the given file into the target CB")

    argparser.add_argument("--set-version",
                           type=int,
                           help="Set version field to the given value (for binary outputs only)")

    argparser.add_argument("--paired-cd",
                           help="For new-style CBs: input (paired) CD file for e.g. deobfuscating entry points")

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
        'no5050': args.no5050,
        'sdram_step': args.sdram_step,
        'disable_default': args.disable_default,
    }

    cbb = None
    patched_cbb = None
    with open(args.cbb_in, "rb") as f:
        cbb = f.read()

    if (cbb[0:2] == bytes([0x43, 0x42]) and \
        cbb[8:10] == bytes([0x00, 0x00]) and \
        cbb[12:14] == bytes([0x00, 0x00])) is False:
        print("error: doesn't look like a valid CB")
        return

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
    
    if args.hwinit_only:
        print("DANGER: bypassing CB patches. resulting CB_B will not be bootable.")
        patched_cbb = bytearray(cbb)
    elif oldcb_ident(cbb):
        print("found old-style CB, attempting patches...")
        patched_cbb = oldcb_try_patch(cbb, patchparams)
    elif newcb_ident(cbb):
        
        if args.paired_cd is not None:
            print(f"paired CD mode on, loading paired CD from: {args.paired_cd}")
        
            paired_cd_bin = None
            with open(args.paired_cd, "rb") as f:
                paired_cd_bin = f.read()
            
            expected_rotsumsha = get_cd_rotsumsha(cbb)
            actual_rotsumsha = rotsumsha_calc(paired_cd_bin[:0x10], paired_cd_bin[0x120:]).hex()
            if actual_rotsumsha != expected_rotsumsha:
                print("error: CD is not paired with this CB")
                print(f"\texpected rotsumsha: {expected_rotsumsha}")
                print(f"\tactual rotsumsha: {actual_rotsumsha}")
                return
            
            print("CB/CD pairing successful")
            print(f"real CD entrypoint is: 0x{newcb_decode_real_entry_point(cbb, paired_cd_bin):08x}")

        print("found new-style CB, attempting patches...")
        patched_cbb = newcb_try_patch(cbb, patchparams)

    if patched_cbb is None:
        print("unable to apply base CB patches, exiting.")
        return
    
    if args.vfuse:
        patched_cbb = vfuses_try_patch(patched_cbb)

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
        if args.set_version is not None:
            print(f"change version to {args.set_version}")
            patched_cbb[2:4] = struct.pack(">H",args.set_version)

        print("writing binary output directly")
        output = patched_cbb

    with open(args.patch_out, "wb") as f:
        f.write(output)

    print("wrote output successfully!")


if __name__ == '__main__':
    main()
