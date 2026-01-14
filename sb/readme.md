# SB: second stage loaders for devkits

## Main differences from retail CBs

- hwinit bytecode is loaded from a signed bootloader payload, SC

## SB boot procedure

TODO: this is mostly copied from the CB docs, with some changes...

### POST 0x20 - CB starting execution

### POST 0x21 - Fusecheck / SMC sanity check

### POST 0x22 - Init security engine

### POST 0x2F - Setup TLB and relocate program

### POST 0x23 - hwinit about to run

Since SB loads its hwinit bytecode from the SC bootloader stage, this function does a few more operations
before it runs hwinit.

- POST 0x24
- POST 0x25
- POST 0x26: Copy SC header from flash
- POST 0x27: SC header check. Failure leads to panic 0xA7
- POST 0x28: Copy the rest of SC from flash
- POST 0x29
- POST 0x2A
- POST 0x2B
- POST 0x2C: Calc RotSumSha of SC
- POST 0x2D: RSA verify SC, failure = panic 0xA8

### POST 0x2E - hwinit running

The SB hwinit interpreter is mostly identical to the one on retail CBs, but with debugging
opcodes enabled. On retail CBs, those opcodes are stubbed out; they either return 0 or do nothing.

### cd_load_and_jump

Similar to retail CB with the following differences:

- POST 0x39, which does a memcmp() with the expected hash, will instead panic with 0xAC instead of 0xAD on failure
- No POST 0x3B so no PCI initialization is done here

