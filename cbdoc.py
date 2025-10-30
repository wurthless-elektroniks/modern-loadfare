
import os
import sys
import hashlib

from oldcbpatcher import oldcb_ident
from newcbpatcher import newcb_ident
from hwinitpatcher import hwinit_extract_bytecode
from hwinitdump import KNOWN_SHAS
from cbheader import get_cb_version, parse_cb_ldv

def _make_report(fout):
    print("--- cbdoc dumped it ---", file=fout)

    for cbbfile in os.listdir("cbb"):
        if cbbfile.endswith('.bin') is False:
            continue

        cbb = None
        with open(os.path.join("cbb",cbbfile), "rb") as f:
            cbb = f.read()

        style = "ERROR"
        if oldcb_ident(cbb):
            style = "Old"
        elif newcb_ident(cbb):
            style = "New"

        hwinit_bytecode = hwinit_extract_bytecode(cbb)
        hwinit_hash = hashlib.sha1(hwinit_bytecode).hexdigest()

        record = {
            'version':       get_cb_version(cbb),
            'style':         style,
            'ldv_bitfield':  f"{parse_cb_ldv(cbb)['bitfield']:016b}",
            'ldv':           parse_cb_ldv(cbb)['ldv'],
            'hwinit':        KNOWN_SHAS[hwinit_hash] if hwinit_hash in KNOWN_SHAS else hwinit_hash
        }

        print(record)


def main():
    _make_report(sys.stdout)

if __name__ == '__main__':
    main()
