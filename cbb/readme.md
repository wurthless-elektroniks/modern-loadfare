# CB(_B): second stage loaders

CB is the second stage bootloader on retail Xbox 360 systems.
CB_B on split CB systems is functionally the same as the CB on single CB systems.

This is brief documentation as to how it works, based on how 5772 works.
POST codes are listed in order of which they appear (I hope).


## List of CBs

| Version | Style | LDV  | hwinit code | Expected CD hash                          |
|---------|-------|------|-------------|-------------------------------------------|
|  1888   | Old   | 2    | xenon_v1    | 1f3137c27dc66f37d2aea7820284a1a90d2ccf88  |
|  1897   | Old   | 2    | xenon_v2    | 1f3137c27dc66f37d2aea7820284a1a90d2ccf88  |
|  1902   | Old   | 2    | xenon_v3    | 1f3137c27dc66f37d2aea7820284a1a90d2ccf88  |
|  1903   | Old   | 2    | xenon_v4    | 1f3137c27dc66f37d2aea7820284a1a90d2ccf88  |
|  1920   | Old   | 4    | xenon_v4    | c45e1a1b5cc2ab593f8124f2ccaae7dc38caa8d2  |
|  1921   | Old   | 5    | xenon_v5    | a9f90c32561084a3034eae9c867b659c986bc767  |
|  1922   | Old   | 6    | xenon_v5    | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  1923   | Old   | 7    | xenon_v5    | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  1925   | New   | 9    | xenon_v4    | 09ee1fb320afc484b969475d6a768f49e3d7f99b  |
|  1926   | New   | 10   | xenon_v4    | e46528587e38b36f50a65ae9e7eca8fc7d74b2ea  |
|  1927   | New   | 11   | xenon_v4    | cb9adca498139bc97600e0f999ef9b18ee275918  |
|  1928   | New   | 12   | xenon_v4    | a8abe5082ef910b79786857bfd26eb1220be5bf4  |
|  1940   | Old   | 6    | xenon_v1    | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  1941   | New   | 9    | xenon_v1    | 54e919caee636d3632a00d7eb38fe53c9c1e3107  |
|  1942   | New   | 11   | xenon_v1    | 0b6bcc0d32986cce0e4d5270d23789c9979ee0d9  |
|  4540   | Old   | 3    | zephyr_v1   | e7a761b642e353aaa336fc19887c2bd27c73eeb9  |
|  4558   | Old   | 4    | zephyr_v3   | 49e873bf1048643569eae676a2e3f0416571d221  |
|  4559   | New   | 9    | zephyr_v2   | c2f1d5aa4eae3ee9d62de1ef9391cb37ee8df158  |
|  4560   | New   | 10   | zephyr_v2   | 70d986a298aeaa39a9fef78dd5a44bf05434c83e  |
|  4561   | New   | 11   | zephyr_v2   | 82119856e14097c52bd6d8ef2b66fba8af544372  |
|  4562   | New   | 12   | zephyr_v2   | ba69e42f5573bb25cc9c822a4e0cc9af18d48744  |
|  4569   | New   | 12   | zephyr_v3   | 467fee4cbe642a6ce2d6734de3b9d5f6280045fa  |
|  4571   | Old   | 6    | zephyr_v2   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  4572   | Old   | 7    | zephyr_v2   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  4574   | New   | 11   | zephyr_v3   | 555bbc3672d779bf63a5c6ee3077868a6ae1ffc5  |
|  4575   | New   | 10   | zephyr_v3   | 28bddc2121fd67136ee7fa4f25cc124b87529249  |
|  4576   | New   | 9    | zephyr_v3   | 90b755a438013904a26b3a7c813be74619c878b7  |
|  4577   | Old   | 7    | zephyr_v3   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  4578   | Old   | 7    | zephyr_v3   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  4579   | Old   | 6    | zephyr_v3   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  4580   | Old   | 5    | zephyr_v3   | 4017f21906ba719463468bd5d2090b842aea475b  |
|  5761   | Old   | 4    | falcon_v1   | 1a1cd4fb8b23544fff0808543e0c18d939a165b1  |
|  5766   | Old   | 5    | falcon_v1   | 3d49e611f58512925c0d16f4c53968b908f43f4a  |
|  5770   | Old   | 5    | falcon_v2   | a1d5c20f4a6328b37c459aa55a7b2ed676db39e0  |
|  5771   | Old   | 7    | falcon_v2   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  5772   | Old   | 8    | falcon_v2   | 39deb63001d36603e51a829beae748b5e44c2e19  |
|  5773   | New   | 10   | falcon_v2   | 329497897988db09cc442a7a27c59e69cbc37160  |
|  5774   | New   | 12   | falcon_v2   | d60bbc71b842e451dc76f5bfe6a0643b06b5528a  |
|  6712   | Old   | 5    | jasper_v1   | 90e22dae8c0c160ac1c362bb481c1fe2463a0799  |
|  6723   | Old   | 5    | jasper_v2   | 3eaad2d0671d15b93ffe4bdcb12f5f0daad7633e  |
|  6750   | Old   | 7    | jasper_v2   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  6751   | Old   | 7    | jasper_v3   | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  6752   | Old   | 8    | jasper_v3   | 04be98797da12bf3e33466714e55f087402a4005  |
|  6753   | New   | 10   | jasper_v3   | a1bb4e3cd0e41237331d1f0f9b22e12d1626a70c  |
|  6754   | New   | 12   | jasper_v3   | 3b9dfd23d8b57f1c8ff72d2ab4e965e68b218405  |
|  7373   | Old   | 7    | elpis       | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  7375   | Old   | 7    | elpis       | b3bf4187247a6dfe1a28125adeb7ed2f991ecfca  |
|  7377   | New   | 10   | elpis       | 9401691f6dcb5018a1cd2d57c10bdcf7cafbd7d7  |
|  7378   | New   | 12   | elpis       | b4f25acff38f0045d8b0672e8dad739872b292ce  |
|  8192   | Old   | 5    | elpis       | 200fe9ab29769d47589feda3cbde7fa8284e6610  |
|  9188   | Old   | 1    | trinity_v1  | 1e0fab1e483cf9241f1386e91f8d5fa3ba8e043c  |
|  9230   | New   | 3    | trinity_v2  | d5e8edde0df1617e20e6b21e56f61560f5cc2bd2  |
|  9231   | New   | 4    | trinity_v2  | 9867e98b5689fe5f7381b7e96270d80b030039c3  |
| 13121   | Old   | 2    | corona_v1   | 944e2feeeee40d4725575ed2dc06ca1cb2d58afb  |
| 13180   | New   | 3    | corona_v1   | b2ce24975267fb055d5111a222abb261ab8832cc  |
| 13181   | New   | 4    | corona_v1   | 051fed8582f966c2e5989f62da2de026dc4fde22  |
| 13182   | New   | 4    | corona_v2   | 450149f40c0a0b0d50fc739c2dbadebf153f4264  |
| 16128   | New   | 5    | corona_v2   | 9adcdb5f3c2b640d1205b0adfee8335ff53a2afd  |

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
