# CB(_B): second stage loaders

CB is the second stage bootloader on retail Xbox 360 systems.
CB_B on split CB systems is functionally the same as the CB on single CB systems.

This is brief documentation as to how it works, based on how 5772 works.
POST codes are listed in order of which they appear (I hope).


## List of CBs

| Version | Style | LDV  | hwinit code | Expected CD, or RotSumSha hash            |
|---------|-------|------|-------------|-------------------------------------------|
|  1888   | Old   | 2    | xenon_v1    |                                     1888  |
|  1897   | Old   | 2    | xenon_v2    |                                     1888  |
|  1902   | Old   | 2    | xenon_v3    |                                     1888  |
|  1903   | Old   | 2    | xenon_v4    |                                     1888  |
|  1920   | Old   | 4    | xenon_v4    | c45e1a1b5cc2ab593f8124f2ccaae7dc38caa8d2  |
|  1921   | Old   | 5    | xenon_v5    |                                     1921  |
|  1922   | Old   | 6    | xenon_v5    |                                     8453  |
|  1923   | Old   | 7    | xenon_v5    |                                     8453  |
|  1925   | New   | 9    | xenon_v4    |                                     1925  |
|  1926   | New   | 10   | xenon_v4    |                                     1926  |
|  1927   | New   | 11   | xenon_v4    |                                     1927  |
|  1928   | New   | 12   | xenon_v4    |                                     1928  |
|  1940   | Old   | 6    | xenon_v1    |                                     8453  |
|  1941   | New   | 9    | xenon_v1    |                                     1941  |
|  1942   | New   | 11   | xenon_v1    |                                     1942  |
|  4540   | Old   | 3    | zephyr_v1   |                                     4540  |
|  4558   | Old   | 4    | zephyr_v3   |                                     4558  |
|  4559   | New   | 9    | zephyr_v2   |                                     4559  |
|  4560   | New   | 10   | zephyr_v2   |                                     4560  |
|  4561   | New   | 11   | zephyr_v2   |                                     4561  |
|  4562   | New   | 12   | zephyr_v2   |                                     4562  |
|  4569   | New   | 12   | zephyr_v3   |                                     4569  |
|  4571   | Old   | 6    | zephyr_v2   |                                     8453  |
|  4572   | Old   | 7    | zephyr_v2   |                                     8453  |
|  4574   | New   | 11   | zephyr_v3   |                                     4574  |
|  4575   | New   | 10   | zephyr_v3   |                                     4575  |
|  4576   | New   | 9    | zephyr_v3   |                                     4576  |
|  4577   | Old   | 7    | zephyr_v3   |                                     8453  |
|  4578   | Old   | 7    | zephyr_v3   |                                     8453  |
|  4579   | Old   | 6    | zephyr_v3   |                                     8453  |
|  4580   | Old   | 5    | zephyr_v3   |                                     4580  |
|  5761   | Old   | 4    | falcon_v1   |                                     5761  |
|  5766   | Old   | 5    | falcon_v1   | 3d49e611f58512925c0d16f4c53968b908f43f4a  |
|  5770   | Old   | 5    | falcon_v2   |                                     5770  |
|  5771   | Old   | 7    | falcon_v2   |                                     8453  |
|  5772   | Old   | 8    | falcon_v2   | 39deb63001d36603e51a829beae748b5e44c2e19  |
|  5773   | New   | 10   | falcon_v2   |                                     5773  |
|  5774   | New   | 12   | falcon_v2   |                                     5774  |
|  6712   | Old   | 5    | jasper_v1   |                                     6712  |
|  6723   | Old   | 5    | jasper_v2   |                                     6723  |
|  6750   | Old   | 7    | jasper_v2   |                                     8453  |
|  6751   | Old   | 7    | jasper_v3   |                                     8453  |
|  6752   | Old   | 8    | jasper_v3   | 04be98797da12bf3e33466714e55f087402a4005  |
|  6753   | New   | 10   | jasper_v3   |                                     6753  |
|  6754   | New   | 12   | jasper_v3   |                                     6754  |
|  7373   | Old   | 7    | elpis       |                                     8453  |
|  7375   | Old   | 7    | elpis       |                                     8453  |
|  7377   | New   | 10   | elpis       |                                     7377  |
|  7378   | New   | 12   | elpis       |                                     7378  |
|  8192   | Old   | 5    | elpis       |                                     8192  |
|  9188   | Old   | 1    | trinity_v1  |                                     9452  |
|  9230   | New   | 3    | trinity_v2  |                                     9230  |
|  9231   | New   | 4    | trinity_v2  |                                     9231  |
| 13121   | Old   | 2    | corona_v1   |                                    12905  |
| 13180   | New   | 3    | corona_v1   |                                    13180  |
| 13181   | New   | 4    | corona_v1   |                                    13181  |
| 13182   | New   | 4    | corona_v2   |                                    13182  |
| 16128   | New   | 5    | corona_v2   |                                    16128  |

## Old-style vs new-style CBs

Todo.

## CB boot procedure

### POST 0x20 - CB starting execution

Sets up some stuff (to be described later)

### POST 0x21 - Fusecheck / SMC sanity check

Fuselines are decoded to make sure the CB is running on a system it should be.

Panics in the early stages are:
- Panics 0x9B, 0x9C, 0x9D, 0x9E, 0x9F aren't really important from a RGH perspective.
- 0xA0 means the CB LDV fusecheck has failed.
- 0xB0 can happen after the CB LDV fusecheck.
- 0xA1 appears to be raised by some sort of integrity checks.

To check the CB LDV fuseline, get the lockdown value first, then compare the lockdown value
to the byte at 0x3B1; if it matches, set a flag and continue:
```
        rlwinm     r11,r21,0x0,0x10,0x1f
        ori        r21,r11,0x8
```
If the LDV value didn't match and wasn't less than or equal to 0, get the 16-bit bitfield
at 0x3B2, then compute `v = bitfield & (1 << (ldv-1))`. If the result is non-zero, the
CB has been revoked and execution will stop with POST 0xA0.

After that, r22, r23, r24 and r25 (the CB header values from 0x20~0x40) are compared to zero.
These arguments should have been passed from the previous stage. If they are zero, then the
SMC integrity checks are skipped and a flag is set to enter zero-paired mode:

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

When in zero-paired mode, the kernel will usually end up in manufacturing mode (displays
Christmas lights and stops the boot). There are some (xeBuild-patched) kernels that don't.

Further panics are:
- 0xA2 - not sure yet
- 0xA3 - SMC program is not in the right place in NAND or is not the right size
- 0xA4 - Actual SMC checksum did not match expected values passed by previous stage

SMC integrity checks are a bit complex:
- Calculate 12 magic seed values from some place in RAM I don't really know the location of
- Compute the 128-bit HMAC key `key = ((seed[2] | seed[3]) << 64) | (seed[4] | seed[5]))`
- Checksum the entire encrypted SMC from flash. The checksum routine is almost identical to the
  one used by RotSumSha, in that it computes a sum and a difference that are both bitwise rotated
  as the loop continues. The result will be a 16-byte value.
- Run HMAC verification. The key is as computed above, the message is `cb_salt + cb[0x20:0x30] + checksum_result`.
  If this value does not match the one at `cb[0x30:0x40]`, verification fails.

(Remember that the previous stage zeroes 0x20-0x40 before CB_B runs.)

### POST 0x22 - Init security engine

Not really that interesting...

### POST 0x2F - Setup TLB and relocate program

- TLB init
- CB_B copies itself into SDRAM, which hasn't been fully initialized yet (or so it looks, anyway)
- An exception handler that POSTs 0xAE (unexpected IRQ) and dies is installed
- Some general purpose exception handler is installed (this MUST be present if you want to run the kernel)
- More TLB-related crap happens
- Execution continues at relocated address (0x03003000? + entry point)

6752 does this to setup the address to continue execution to:

```
        0000069c 3c c0 00 00     lis        r6,0x0
        000006a0 38 c6 06 e0     addi       r6,r6,0x6e0    <-- 0x06E0 within the context of the CB_B
        000006a4 3c c6 03 00     addis      r6,r6,0x300
        000006a8 38 c6 30 00     addi       r6,r6,0x3000   <-- execution actually continues at 0x03003000 + 0x06E0
        000006ac 7c da 03 a6     mtspr      SRR0,r6        <-- RFID happens soon after
```

### POST 0x23 - hwinit about to run

This is documented as "INIT_SYSRAM" in most sources but in reality it does nothing.
This POST happens in a wrapper function where hwinit executes.

### POST 0x2E - hwinit running

hwinit is a mess of code that is still being reverse engineered and there's not much to
say about it that's different than what's already been written, but as a reminder, it's
a big interpreter that does PCIe, SDRAM and device configuration depending on what kind
of hardware it detects.

The PCIe BARs (Base Address Registers) are configured during this phase, allowing the CPU
to talk to the PCI devices. Then the devices are configured. The devices should live at
addresses that are already publicly documented, as in libxenon.

The typical workflow is:
- Init PCI-PCI bridge
- Init GPU BARs and some GPU registers
- Init Southbridge BAR (`store_word 0xea001000, 0xd0150010 / store_half 2, 0xd0150004`)
- Write 0x000001E6 to Southbridge UART configuration register, probably to disable the UART
- Send command 0x12 to the SMC (gets SMC version and the contents of two SMC memory cells) and then store one byte(?) of its response to 0xE400002C,
  to be used as a parameter during SDRAM init
- Run SDRAM detection, configuration and training (this is the most involved part of the whole process)
- Finish up PCI-PCI bridge configuration and exit

When reading hwinit disassemblies keep in mind that 0xD0000000 is the PCI configuration
space, including each device's BARs, and that 0xE0000000 are where the configured devices
end up living.

A rough idea of what's mapped to what:
- 0xE0xxxxxx, 0xE1xxxxxx - host bridges
- 0xE4xxxxxx - GPU, SDRAM controllers (MC0 and MC1), and other northbridgey stuff (see [here](https://github.com/xenon-emu/xenon/blob/main/Xenon/Core/XGPU/XenosRegisters.h) for register names)
- 0xEAxxxxxx - Southbridge, including the SMC and audio controller

After hwinit runs, 0xE1040000 is read to determine what the system RAM size is.
Anything less than 512 MB will halt with a panic (POST 0xAF). However, the hwinit
bytecode will usually explicitly set this value to 0x20000000, so the check should
always pass.

### SDRAM training errors

The hwinit program will throw RRoDs if it fails to initialize SDRAM (and if the CPU doesn't crash while it happens). These include:

| SMC command   | SMC command word | RRoD Error | Error Name                                    |
|---------------|------------------|------------|-----------------------------------------------|
| `9A 10 10 00` | `0x0010109a`     | 0100       | ERROR_NBINIT_MEM_VENDOR_ID                    |
| `9A 11 11 00` | `0x0011119a`     | 0101       | ERROR_NBINIT_MEM_READ_STROBE_DATA_WRITE       |
| `9A 12 12 00` | `0x0012129a`     | 0102       | ERROR_NBINIT_MEM_READ_STROBE_DELAY_TRAINING   |
| `9A 13 13 00` | `0x0013139a`     | 0103       | ERROR_NBINIT_MEM_WRITE_STROBE_DELAY_TRAINING  |
| `9A 14 14 00` | `0x0014149a`     | 0110       | ERROR_MEMORY_ADDRESSING                       |
| `9A 15 15 00` | `0x0015159a`     | 0111       | ERROR_MEMORY_DATA                             |
| `9A 16 16 00` | `0x0016169a`     | 0112       | Undocumented (probably same as 0111)          |

### cd_load_and_jump

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

#### New-style CD entry point obfuscation

New-style CB/CD pairings typically obfuscate the real CD entry point. The way to compute the real entry point is
as follows, using CB/CD 7378 as an example:

```
uVar12 = 0x05E1272D24F81CDA # cd @ 0x2F8
uVar7  = 0x0000000000000000 # cd @ 0x300 
uVar5  = 0xBBA218337EADBCEF # cd @ 0x2F0
uVar8  = 0x20C5A472B94B44B9 # cb @ 0x3D8
uVar9  = 0xFC96783760CA74AA # cb @ 0x3C8
uVar10 = 0xF1AD214506091F14 # cb @ 0x3C0
local_2e8 = 0xD8B0672E8DAD7398 # CD rotsumsha hash, bytes 8~15
local_2f0 = 0xB4F25ACFF38F0045 # CD rotsumsha hash, bytes 0~7

real_entry_point = uVar7 ^ uVar12 ^ uVar5 ^ 0xffffffffffffffff ^ uVar8 ^ uVar9 ^ uVar10 ^ local_2e8 ^ local_2f0
```

In this case the entry point will be `0x04000310`, which in practice isn't any different than the entry point specified
in the CD header (`0x0310`).

This seems like an attempt by Microsoft to prevent pairing random CB/CD pairings, and to cause an intentional crash
if CD has been tampered with. Obviously, it's not a very successful attempt, because it can be bypassed easily
by patching cd_jump to start CD the same way as an old-style CB would.
