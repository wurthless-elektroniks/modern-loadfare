# CA: First-stage bootloader/bootrom

The bootrom is the first bit of code to run on the PowerPC. It initializes the FSB (needed to access memory-mapped flash),
then loads, decrypts and verifies the second-stage loader (CB_A or CB). If all is well, execution continues in CB.

The bootrom can be placed in a weird test/debug mode depending on how some values are set (the program reads from
0x8000020000061008, which could be the POST input; not sure though). This however is completely useless as an exploit vector.

The bootrom is typically not the ideal attack point for glitching attacks because the signature verification process is
very slow (about 200 ms with no slowdown applied), but it is still vulnerable to reset glitching. Proof of concept
[here](https://github.com/wurthless-elektroniks/pigli360-workbench/blob/main/CAboom/caboom.py).

Bootrom pseudocode readable over [here](https://github.com/g91/XBLS/blob/3b88bd3bef80ab3fc9a51b843b7e43c821768bf4/Research/code/1bl_583.c).
There are some typos in there; a summary will be written here eventually. Even if eventually is never.

## Where are the dumps?

Not provided because they can easily be dumped from a console. CB and CD dumps are provided because
many have been lost to time; the bootrom however never changes.

If you want to dump your bootrom, run XeUnshackle through the exploit of your choice (it works on RGH systems too).
This will allow you to save out your bootrom.

## Known bootrom versions

- 1411: Waternoose and Loki (I dumped mine from a Falcon)
- 7500: Vejle and Oban (I dumped mine from a Winchester)

## Copyright string

- 1411: "(c) 2004-2005 Microsoft Corporation. All rights reserved. Do not unlawfully hack, circumvent, reverse engineer, modify or copy."
- 7500: "(c) 2008 Microsoft Corporation. All rights reserved. Do not unlawfully hack, circumvent, reverse engineer, modify or copy."

## Execution flow

Much of this TODO.

### cb_load_and_jump

- 0x11: FSB training step 1 (simple: delays a bit, checks if a flag is set, and if not, sets a flag somewhere else and delays some more)
- 0x12, 0x13: FSB training steps 2 and 3 (much more involved; these loop until the program is satisfied)
- 0x14: FSB training step 4 (finalization, pretty simple)
- 0x15: CB header check, failure = panic 0x94
- 0x16: Copy CB header into SRAM
- 0x17: Verify CB header. Minimum entrypoint on fats is 0x264, magic word must be "CB" or "SB", entry point must be 32-bit aligned,
  etc. Failure is panic 0x95
- 0x18: Load rest of CB to SRAM
- 0x19, 0x1A: HMAC init
- 0x1B: CB decrypt
- 0x1C: Calc RotSumSha hash of CB (zero-padded probably)
- 0x1D: Decrypt RSA-2048 signature in CB header and memcmp() the 256 bytes with the padded RotSumSha hash we just calculated.
  If values don't match, panic 0x96.
- 0x1E: Load parameters from CB header 0x20~0x40 into r27, r28, r29, r30 (used to verify SMC image later in CB). Do one more
  entry point check (panic 0x98 if it fails). Then zero the parameter values out in SRAM, load some initial values
  (clearing r0-r26 and ctr), and jump to CB.
