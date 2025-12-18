#!/bin/bash

cbs=(5772 1942 1928 4569 4562 7378 6752 4577)

for i in "${cbs[@]}"
do
    python3 loadfare.py --im-a-developer --nopost --nofuse --nodecrypt --write-xebuild cbb/cbb_$i.bin private/cbb_"$i"_xell.bin

    python3 loadfare.py --im-a-developer --nopost --write-xebuild cbb/cbb_$i.bin private/cbb_$i.bin

    python3 loadfare.py --hwinit-only --smc-keepalive --write-xebuild cbb/cbb_$i.bin private/cbb_"$i"_ipc.bin
    python3 loadfare.py --hwinit-only --post67 --write-xebuild cbb/cbb_$i.bin private/cbb_"$i"_post67.bin
done
