import os
import rotsumsha
import struct

# cd = None
# with open("cd/cd_7378.bin", "rb") as f:
#     cd = f.read()

# print(rotsumsha.rotsumsha_calc(cd[0:0x10], cd[0x120:]).hex())

hash_table = {}

for cdfile in os.listdir("cd"):
    if cdfile.endswith('.bin') is False:
        continue
    cd = None
    with open(os.path.join("cd",cdfile), "rb") as f:
        cd = f.read()

    cdver = struct.unpack(">H",cd[2:4])[0]
    hash_table[rotsumsha.rotsumsha_calc(cd[0:0x10], cd[0x120:]).hex()] = cdver

print(hash_table)
