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

Read a disassembly of the 9452 patches [here](https://github.com/mitchellwaite/glitch2m_17559/blob/main/src/include/cd_9452.S).
