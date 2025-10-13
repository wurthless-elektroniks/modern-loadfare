#
# patch for hwinit that outputs delay programcounter stuff to the POST lines
#

    .org 0x0280
hwinit_postcount_code_start:
    # stubs - code in cbbpatch.py uses these instead of going to the routines directly
    b hwinit_init           # +0x00
    b hwinit_delay_case     # +0x04
    b hwinit_done           # +0x08

    # exit points to be dropped in by cbbpatch
hwinit_register_setup_function:
    b hwinit_register_setup_function
hwinit_interpreter_top:
    b hwinit_interpreter_top
hwinit_exit:
    b hwinit_exit

# ------------------------------------------------------------------------------------------------

hwinit_init:
    bl hwinit_register_setup_function
    b hwinit_interpreter_top

# ------------------------------------------------------------------------------------------------

hwinit_delay_case:
    std %r5,-0xB0(%r1)
    std %r6,-0xB8(%r1)

    lis %r5,0x8000         # load POST base
    ori %r5,%r5,0x0200
    rldicr %r5,%r5,32,31
    oris %r5,%r5,0x0006

    li %r6,0x88
    rldicr %r6,%r6,56,7    # r6 <<= 56 
    std %r6,0x1010(%r5)    # write to POST register

    lis %r6,2
    mtctr %r6
_wait_loop_1:
    bdnz _wait_loop_1

    sub %r6,%r16,%r3       # r6 = pc within program
    rldicr %r6,%r6,56,7    # r6 <<= 56 
    std %r6,0x1010(%r5)    # write to POST register

    lis %r6,2
    mtctr %r6
_wait_loop_2:
    bdnz _wait_loop_2

    sub %r6,%r16,%r3       # r6 = pc within program
    rldicr %r6,%r6,48,7    # r6 <<= 48 
    std %r6,0x1010(%r5)    # write to POST register

    lis %r6,2
    mtctr %r6
_wait_loop_3:
    bdnz _wait_loop_3
    b hwinit_interpreter_top

    # keep scripts happy
    mulli %r6,%r6,50

hwinit_done:
    # return success and go to epilogue as normal
    li %r5,1
    b hwinit_exit
