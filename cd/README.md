# CD: Fourth-stage bootloader

Mostly for documentation purposes.

CD has been documented extensively already; links to docs will be added later.

8453 was the first revision to plug the JTAG exploit; any CB paired to it can't be used for JTAG.

## (Re-)Dumps wanted

- 1920 is encrypted
- 5766 is encrypted
- CB 5772 is paired to a bootloader with the RotSumSha hash of 39deb63001d36603e51a829beae748b5e44c2e19, which is missing
- CB 6752 is paired to a bootloader with the RotSumSha hash of 04be98797da12bf3e33466714e55f087402a4005, which is missing

## Custom/hacked CDs

### CDxell

CDxell is a custom CD by GliGli that's included with most XeLL ECC builds. It does basic PCI device initialization, then
loads one of two XeLL images depending on what the power up cause was.

Read the source [here](https://github.com/gligli/tools/blob/master/reset_glitch_hack/cdxell/cdxell.S).

### Freeboot (also xeBuild)

Freeboot was a hacked CD that became the basis for xeBuild's CD patches.
[DrSchottky's analysis](https://web.archive.org/web/20230201190325/https://www.razielconsole.com/forum/guide-e-tutorial-xbox-360/945-%5Bx360-reversing%5D-chapter-2-cd-patches.html)
basically says what I'm about to write, so go read that in the meantime.

The typical Freeboot patches redirect execution into a custom function that basically does what CDxell does. If the power up cause
matches one of two expected values (in NAND at 0x4E and 0x4F), it initializes the PCI devices the same way as CDxell, then loads
XeLL from a hardcoded address in NAND (typically 0x070000) and jumps to it. Otherwise, execution continues as normal.

Once the hypervisor/kernel has been decompressed and delta-patched, Freeboot applies the xeBuild kernel patches before running it.
The patch blob location is specified by the sum of two 32-bit words in the NAND header at 0x64 and 0x70. If 0x70 is 0, then default
it to 0x00010000.

Read a disassembly of the 9452 patches [here](https://github.com/mitchellwaite/xbox360_xebuild_patches/blob/main/src/4BL/9452/inc/cd_9452.S).

## Boot process

Work in progress for CD 9452

- POST 0x45, 0x46: HMAC init for CE decrypt
- POST 0x47: Decrypt CE
- POST 0x48: Compute RotSumSha of CE we just decrypted
- POST 0x49: Compare CE hash to one hardcoded in CD (always `89 8B C3 F9 7F A2 D8 20 72 01 46 5F 30 3F 70 F2 FC 8A F4 13`).
  If it doesn't match, panic 0xB3
- POST 0x4B: LZX decompress
- Calls function that POSTs 0x4D and grabs fuses (can fail with panic 0xB6)
- POST 0x53: Calls function that does signature validation but its return value is (seemingly) never used
- POST 0x4E: Get patch slot address from NAND (two words at 0x64 and 0x70, defaulting 0x70 to 0x010000 if it is zero)
- POST 0x4F: Validate patch slot address, failure = panic 0xB5
- POST 0x50, 0x51: Try both patch slots, calling load_patch_slot() on both of them. If both tries fail, panic 0xB7
- POST 0x52: Clear caches, turn on memory encryption in HRMOR, and start the hypervisor

### load_patch_slot

Returns non-zero value if successful, 0 otherwise.

- Initial CF header checks
- Copy encrypted CF to SDRAM
- RC4 decrypt CF and calc RotSumSha for signature verification. If signature verification fails, return 0
- Pass RotSumSha hash to a function that compares the CF RotSumSha to two known hashes
  (`52 F6 04 0A 74 98 5C 21 F2 D7 E5 21 13 01 5A 6D C5 C8 BE 9A` and `BB A0 A4 99 C3 C4 7E 25 48 66 19 A7 D7 46 08 25 5C A6 89 4F`)
  corresponding to kernels vulnerable to the King Kong and JTAG exploits. If the RotSumSha matches either of those
  hashes, panic immediately (POST 0xB8) instead of simply refusing to load the patch slot.
- CF header checks (to be described later)
- Some weird functions that might be patching exception vectors to point to CF instead
- Run CF and return the status of whatever it returned
