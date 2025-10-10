# CB(_B): second stage loaders

CB is the second stage bootloader on retail Xbox 360 systems.
CB_B on split CB systems is functionally the same as the CB on single CB systems.

This is brief documentation as to how it works, based on how 5772 works.
POST codes are listed in order of which they appear (I hope).

## POST 0x20 - CB starting execution

Sets up some stuff (to be described later)

## POST 0x21 - Fusecheck / SMC sanity check

Fuselines are decoded to make sure the CB is running on a system it should be.

Panics in the early stages are:
- Panics 0x9B, 0x9C, 0x9D, 0x9E, 0x9F aren't really important from a RGH perspective.
- 0xA0 means the CB LDV fusecheck has failed.
- 0xB0 can happen after the CB LDV fusecheck.
- 0xA1 appears to be raised by some sort of integrity checks.

After that, r22, r23, r24 and r25 are compared to zero. These arguments should have been
passed from the previous stage. If they are zero, a flag is set and SMC integrity checks
are skipped:

```
        00006a48 7f 2b c3 78     or         r11,r25,r24
        00006a4c 7d 6b bb 78     or         r11,r11,r23
        00006a50 7d 6b b3 78     or         r11,r11,r22
        00006a54 2b 2b 00 00     cmpldi     cr6,r11,0x0
        00006a58 40 9a 00 10     bne        cr6,LAB_00006a68
        00006a5c 56 ab 04 3e     rlwinm     r11,r21,0x0,0x10,0x1f
        00006a60 61 75 00 01     ori        r21,r11,0x1
        00006a64 48 00 00 dc     b          LAB_00006b40
```

Further panics are:
- 0xA2 - not sure yet
- 0xA3 - SMC program is not in the right place in NAND or is not the right size
- 0xA4 - Actual SMC checksum did not match expected values passed by previous stage

It is important to pass real arguments to the CB; if zeros are passed in their place, then
the kernel will almost certainly end up in manufacturing mode and display Christmas lights
on the Ring of Light. Note that manufacturing mode was abused for JTAG, and it could also
be abused for a softmod...

## POST 0x22 - Init security engine

Not really that interesting...

## POST 0x2F - Setup TLB and relocate program (to SDRAM?)

The CB also sets up some exception vectors during this phase. They are not to be tampered
with if you want to run the kernel, as the kernel will be using them.

## POST 0x23 - hwinit about to run

This is documented as "INIT_SYSRAM" in most sources but in reality it does nothing.
This POST happens in a wrapper function where hwinit executes.

## POST 0x2E - hwinit running

hwinit is a mess of code that is still being reverse engineered and there's not much to
say about it that's different than what's already been written, but as a reminder, it's
a big interpreter that does PCIe, SDRAM and device configuration depending on what kind
of hardware it detects.

The PCIe BARs (Base Address Registers) are configured during this phase, allowing the CPU
to talk to the PCI devices. Then the devices are configured. The devices should live at
addresses that are already publicly documented, as in libxenon.

When reading hwinit disassemblies keep in mind that 0xD0000000 is the PCI configuration
space, including each device's BARs, and that 0xE0000000 are where the configured devices
end up living.

A rough idea of what's mapped to what:
- 0xE0xxxxxx, 0xE1xxxxxx - host bridges
- 0xE4xxxxxx - GPU, SDRAM controllers (MC0 and MC1), and other northbridgey stuff (see [here](https://github.com/xenon-emu/xenon/blob/main/Xenon/Core/XGPU/XenosRegisters.h) for register names)
- 0xEAxxxxxx - Southbridge, including the SMC and audio controller

After hwinit runs, 0xE1040000 is read to determine what the system RAM size is.
Anything less than 512 MB will halt with a panic (POST 0xAF).

## cd_load_and_jump

Long procedure that performs the following in order:

- POST 0x30 - Verify CD offset, probably to prevent reading beyond the end of the memory-mapped flash. Failure
  case is POST 0xAA.
- POST 0x31 - Copy CD header from NAND
- POST 0x32 - CD header checks which vary between CB revisions, any failure ends up with POST 0xAB.
- POST 0x33 - Load encrypted CD from NAND
- POST 0x34, 0x35 - Init HMAC for RC4 decrypt
- POST 0x36 - RC4 decrypt CD
- POST 0x37 - Compute RotSumSha hash of CD
- POST 0x39 - memcmp() computed hash with expected hash, if they don't match, POST 0xAD and die. There are some small
  tasks that follow; on new-style CBs the code munges some parameters that will be used when calling CD.
- POST 0x3B - pci_init (mostly southbridge init tasks, but some GPU stuff happens here, have to document this later)
- POST 0x3A - cd_jump: clear caches and execute CD

This function was probably written in C because, even though execution never returns here, there's a bit of code
that handles stack maintenance and cleanup after the call to cd_jump.

