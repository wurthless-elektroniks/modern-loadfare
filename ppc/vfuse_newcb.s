
    # r4 in this function is the destination pointer
    # so move it to r10 so it doesn't get trashed
    mr %r10, %r4

    # setup pointer to NAND (0x80000200_C8000000)
    lis %r3,0x8000
    addi %r3,%r3,0x0200
    rldicr %r3,%r3,0x20,0x1F # <<= 32
    oris %r3,%r3,0xC800

    lwz %r4, 0x64(%r3)
    lwz %r5, 0x70(%r3)
    add %r3, %r3, %r4
    add %r4, %r3, %r5   # point r4 at data we're about to copy
    mr %r3, %r10        # r3 = data copy destination
    li %r5, 0xc         # r5 = num of 64-bit words to copy

    # branch to 64-bit memcpy routine here...
