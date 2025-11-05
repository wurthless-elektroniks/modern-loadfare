
import os
import sys
import hashlib

from oldcbpatcher import oldcb_ident
from newcbpatcher import newcb_ident
from hwinitpatcher import hwinit_extract_bytecode
from hwinitdump import KNOWN_SHAS
from cbheader import get_cb_version, get_cd_rotsumsha, get_cb_ldv_revocation_bitfield, get_cb_expected_ldv


KNOWN_CD_HASHES = {
    '49e873bf1048643569eae676a2e3f0416571d221': 4558,
    'c2f1d5aa4eae3ee9d62de1ef9391cb37ee8df158': 4559,
    '9adcdb5f3c2b640d1205b0adfee8335ff53a2afd': 16128,
    '1e0fab1e483cf9241f1386e91f8d5fa3ba8e043c': 9452,
    '90b755a438013904a26b3a7c813be74619c878b7': 4576,
    'ba69e42f5573bb25cc9c822a4e0cc9af18d48744': 4562,
    '82119856e14097c52bd6d8ef2b66fba8af544372': 4561,
    '28bddc2121fd67136ee7fa4f25cc124b87529249': 4575,
    '555bbc3672d779bf63a5c6ee3077868a6ae1ffc5': 4574,
    '70d986a298aeaa39a9fef78dd5a44bf05434c83e': 4560,
    'b4f25acff38f0045d8b0672e8dad739872b292ce': 7378,
    'a8abe5082ef910b79786857bfd26eb1220be5bf4': 1928,
    '90e22dae8c0c160ac1c362bb481c1fe2463a0799': 6712,
    '450149f40c0a0b0d50fc739c2dbadebf153f4264': 13182,
    'd5e8edde0df1617e20e6b21e56f61560f5cc2bd2': 9230,
    'b2ce24975267fb055d5111a222abb261ab8832cc': 13180,
    '1f3137c27dc66f37d2aea7820284a1a90d2ccf88': 1888,
    '051fed8582f966c2e5989f62da2de026dc4fde22': 13181,
    '9867e98b5689fe5f7381b7e96270d80b030039c3': 9231,
    'cb9adca498139bc97600e0f999ef9b18ee275918': 1927,
    'a1d5c20f4a6328b37c459aa55a7b2ed676db39e0': 5770,
    'b3bf4187247a6dfe1a28125adeb7ed2f991ecfca': 8453,
    'e46528587e38b36f50a65ae9e7eca8fc7d74b2ea': 1926,
    '329497897988db09cc442a7a27c59e69cbc37160': 5773,
    '944e2feeeee40d4725575ed2dc06ca1cb2d58afb': 12905,
    '9ede2a3d93f9ed1c2bf5eb708e911911b6ff9993': 5766,
    '3eaad2d0671d15b93ffe4bdcb12f5f0daad7633e': 6723,
    '09ee1fb320afc484b969475d6a768f49e3d7f99b': 1925,
    'a9f90c32561084a3034eae9c867b659c986bc767': 1921,
    '9401691f6dcb5018a1cd2d57c10bdcf7cafbd7d7': 7377,
    '553b9ac3bb1bdf9880acfbf42c485d3a7fe31524': 1920,
    '1a1cd4fb8b23544fff0808543e0c18d939a165b1': 5761,
    'd60bbc71b842e451dc76f5bfe6a0643b06b5528a': 5774,
    '3b9dfd23d8b57f1c8ff72d2ab4e965e68b218405': 6754,
    '0b6bcc0d32986cce0e4d5270d23789c9979ee0d9': 1942,
    '4017f21906ba719463468bd5d2090b842aea475b': 4580,
    '54e919caee636d3632a00d7eb38fe53c9c1e3107': 1941,
    'a1bb4e3cd0e41237331d1f0f9b22e12d1626a70c': 6753,
    'e7a761b642e353aaa336fc19887c2bd27c73eeb9': 4540,
    '200fe9ab29769d47589feda3cbde7fa8284e6610': 8192,
    '467fee4cbe642a6ce2d6734de3b9d5f6280045fa': 4569
}


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
            'hwinit':               KNOWN_SHAS[hwinit_hash] if hwinit_hash in KNOWN_SHAS else hwinit_hash,
            'cdhash':               get_cd_rotsumsha(cbb),
        }
        records.append(record)

    records.sort(key = lambda r: r['version'])

    for record in records:
        # |---------|-------|------|-------------|-------------------------------------------|
        #. 12345.   |.      | ..     ........... 

        cd = f"{record['cdhash']:40s}" if record['cdhash'] not in KNOWN_CD_HASHES else f"{KNOWN_CD_HASHES[record['cdhash']]:40d}"
        print(f"| {record['version']:5d}   | {record['style']}   | {record['expected_ldv']:2s}   | {record['hwinit']:11s} | {cd}  |")

#        print(record)


def main():
    _make_report(sys.stdout)

if __name__ == '__main__':
    main()
