
import os
import sys
import hashlib

from oldcbpatcher import oldcb_ident
from newcbpatcher import newcb_ident
from hwinitpatcher import hwinit_extract_bytecode
from hashes import KNOWN_HWINIT_SHA_HASHES, KNOWN_CD_ROTSUMSHA_HASHES
from cbheader import get_cb_version, get_cd_rotsumsha, get_cb_ldv_revocation_bitfield, get_cb_expected_ldv



def _make_report(fout):
#    print("--- cbdoc dumped it ---", file=fout)


    print(\
u"""
| Version | Style | LDV  | hwinit code | Expected CD hash                          |
|---------|-------|------|-------------|-------------------------------------------|
""")
    
    records = []

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
            'version':              get_cb_version(cbb),
            'style':                style,
            'revocation_bitfield':  f"{get_cb_ldv_revocation_bitfield(cbb):016b}",
            'expected_ldv':         f"{get_cb_expected_ldv(cbb)}",
            'hwinit':               KNOWN_HWINIT_SHA_HASHES[hwinit_hash] if hwinit_hash in KNOWN_HWINIT_SHA_HASHES else hwinit_hash,
            'cdhash':               get_cd_rotsumsha(cbb),
        }
        records.append(record)

    records.sort(key = lambda r: r['version'])

    for record in records:
        # |---------|-------|------|-------------|-------------------------------------------|
        #. 12345.   |.      | ..     ........... 

        cd = f"{record['cdhash']:40s}" if record['cdhash'] not in KNOWN_CD_ROTSUMSHA_HASHES else f"{KNOWN_CD_ROTSUMSHA_HASHES[record['cdhash']]:40d}"
        print(f"| {record['version']:5d}   | {record['style']}   | {record['expected_ldv']:2s}   | {record['hwinit']:11s} | {cd}  |")

#        print(record)


def main():
    _make_report(sys.stdout)

if __name__ == '__main__':
    main()
