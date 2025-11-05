# CA: First-stage bootloader/bootrom

The bootrom is the first bit of code to run on the PowerPC. It initializes the FSB (needed to access memory-mapped flash),
then loads, decrypts and verifies the second-stage loader (CB_A or CB). If all is well, execution continues in CB.

The bootrom can be placed in a weird test/debug mode depending on how some values are set, presumably on the POST_IN bus.
This however is completely useless as an exploit vector.

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
