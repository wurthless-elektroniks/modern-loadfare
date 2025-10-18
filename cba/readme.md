# CB_A: loader that loads a loader that loads another loader that loads the kernel

The split CB scheme was introduced on slim systems for a bit of extra security (supposedly).
Later, the split CBs were added to phats in an attempt to shut down RGH1.

The point of CB_A is to encrypt CB_B with the CPU key so it can't be easily modified, and to
prevent loading arbitrary code. However this was defeated early on because split CBs weren't all
that different than their single CB counterparts and a RC4 key brute force was enough to recover
the plaintext. Later, manufacturing CB_As leaked that allowed a zeropaired CB_B to be used, and
that became the standard for Glitch2 XeLL images going forward.

Microsoft could have shut down RGH2 and RGH1.2 had they put the CB lockdown value check in CB_A.
Instead, they left it in CB_B, which means any CB_A can be used for the exploit.

## Okay, so why are these here?

The answer is "softmods". A JTAG-like approach to softmodding, where the exploit reboots the system
into a hacked state with patched bootloaders, will need patches created for the most recent bootloaders.

These are also provided here for documentation and completion purposes.
