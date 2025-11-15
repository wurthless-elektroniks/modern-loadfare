import struct
from argparse import ArgumentParser,RawTextHelpFormatter
from zlib import crc32

# ------------------------------------------------------------------------------------------

def _init_argparser():
    argparser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                               prog='loadfare',
                               description="Bulk builds xeBuild patches")
    
    argparser.add_argument("--xenon-for-falcon",
                           default=False,
                           action='store_true',
                           help="Classify Xenon/Elpis bootloaders as Falcon loaders")
    
    argparser.add_argument("--zephyr-for-falcon",
                           default=False,
                           action='store_true',
                           help="Classify Zephyr bootloaders as Falcon loaders")
    
    return argparser

def main():
    pass

if __name__ == '__main__':
    main()
