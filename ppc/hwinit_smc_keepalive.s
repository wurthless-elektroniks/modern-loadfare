#
# hwinit keepalive code using the SMC FIFOs instead of POST bits
#

    # hwinit programcounter must be past this point before sending SMC messages
    # otherwise we're talking to uninitialized PCI space
    .equ HWINIT_MINIMUM_PC_VALUE, 0x0300

    # keepalive signal (0xA2, 0xE2) - should blink RoL LEDs and reset watchdogs
    .equ SMC_HWINIT_KEEPALIVE_MSGID, 0xA2

    # "done" signal
    .equ SMC_HWINIT_DONE_MSGID, 0xA8

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
    # in contrast to the postcounter code this only reads the timebase counter.
    # we can't talk to the SMC until the hwinit program has set up the BARs and sent command 0x12
    # so we'll wait until that happens before sending the keepalive messages
    mftb   %r6              # read timebase counter
    andis. %r6,%r6,BASE_AND
    std    %r6,-0xA8(%r1)   # store in safe space on stack

    bl hwinit_register_setup_function
    b hwinit_interpreter_top

# ------------------------------------------------------------------------------------------------

hwinit_delay_case:
    # normal hwinit code
    mulli %r6,%r6,50
    mftb  %r8
    add   %r8,%r8,%r6

_hwinit_delay_loop:
    mftb %r7
    cmpld %r7,%r8
    bgt hwinit_interpreter_top            # original instruction is a ble

    bl smc_ipc_tick

    b _hwinit_delay_loop # and keep running the delay

hwinit_done:
    lis %r5,0x8000                      # point r5 at southbridge (0x80000200EA000000)
    ori %r5,%r5,0x0200
    rldicr %r5,%r5,32,31
    oris %r5,%r5,0xEA00

    lis %r6,0x0400                      # set FIFO tx active
    stw %r6,0x1084(%r5)

    li %r6,SMC_HWINIT_DONE_MSGID        # write command to FIFO (SMC will not reply)
    rlwinm %r6,24,0,7
    stw %r6,0x1080(%r5)

    li %r6,0                            # release FIFO
    stw %r6,0x1084(%r5)                       

    # return success and go to epilogue as normal
    li %r5,1
    b hwinit_exit

# ------------------------------------------------------------------------------------------------

smc_ipc_tick:
    std %r5,-0xB0(%r1)
    std %r6,-0xB8(%r1)
    std %r7,-0xC0(%r1)
    std %r8,-0xC8(%r1)

    # check that hwinit interpreter is past a certain point before sending SMC messages.
    # during hwinit, %r16 is the program counter and %r3 is the program base.
    sub %r5,%r16,%r3
    cmpwi %r5,HWINIT_MINIMUM_PC_VALUE
    blt _smc_ipc_tick_exit

    # otherwise, check timebase against last poll
    ld     %r6,-0xA8(%r1)               # read last poll
    mftb   %r5                          # read timebase counter
    andis. %r7,%r5,BASE_AND             # check bit (1 << 27)
    cmpld  %r6,%r7                      # has the bit flipped?
    beq    _smc_ipc_tick_exit           # if it hasn't, exit
    std   %r7,-0xA8(%r1)                # update last poll state

    lis %r5,0x8000                      # point r5 at southbridge (0x80000200EA000000)
    ori %r5,%r5,0x0200
    rldicr %r5,%r5,32,31
    oris %r5,%r5,0xEA00

    lis %r7,0x0400                       # r7 = 0x04000000 (sets FIFO active)
    stw %r7,0x1084(%r5)                  # start talking on FIFO

    li %r7,SMC_HWINIT_KEEPALIVE_MSGID   # prepare keepalive message
    cmpwi %r6,0                         # if the bit we checked earlier was 0, leave as-is
    beq _toggle_post_send_post
    ori %r7,%r7,0x40                    # otherwise toggle bit 6 (0xA2, 0xE2, 0xA2, etc...)
_toggle_post_send_post:
    rlwinm %r7,24,0,7                   # SMC command has to be shifted left too
    stw %r7,0x1080(%r5)                 # send SMC command (we don't care if it's acknowledged or not)
    li %r7,0                            # release FIFO
    stw %r7,0x1084(%r5)

_smc_ipc_tick_exit:
    ld %r5,-0xB0(%r1)
    ld %r6,-0xB8(%r1)
    ld %r7,-0xC0(%r1)
    ld %r8,-0xC8(%r1)
    blr
