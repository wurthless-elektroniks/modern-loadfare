# Modern Loadfare: universal Xbox 360 CB bootloader patcher

![](loadfare.png)

Modern Loadfare is [elpiss](https://github.com/wurthless-elektroniks/elpiss) taken to its logical extreme. It's
designed to patch virtually every CB revision for use in RGH scenarios.

In short, older CBs are faster but less compatible, and newer CBs are slower but more compatible.
For example, CB 1940 boots Xenons almost as quickly as Jaspers normally do, and CB 7378 takes about three times as long.

Note that this is still a work in progress, many CBs are currently unsupported, and things are a bit buggy, so use everything
here at your own risk.

## Okay, so what is a CB anyway?

The CB is the second-stage bootloader on Xbox 360 systems. It runs fusechecks, verifies the integrity of the SMC program
and next stage bootloader, and most importantly initializes the hardware (this procedure is aptly named "hwinit").

The reason there are so many CBs is because Microsoft kept updating them for the following reasons:
- New hardware configurations. On Falcon, 5761 and 5766 only support the old eight-chip SDRAM configuration, while
  5770 updated the hwinit program to support the newer four-chip SDRAM configuration. The same thing happened
  on Coronas with Winbond SDRAMs; 13182 was introduced to support them.

- Updated CB/CD pairings. CB and CD are paired together; if one of them is updated, the other must be updated too.

- CB lockdown value changes. Certain software updates burn efuses that change the CB lockdown values to prevent
  downgrading to older bootloaders. This was most infamously used to patch the JTAG exploit.

- Efforts to frustrate RGH. Later CB versions remove the POST codes and introduce random delays in an attempt to
  prevent glitching. However, split CBs render that moot because there is no fusecheck in any CB_A, and Glitch2
  and Glitch3 families of RGH exploits can consequently run any CB_B they want.

Most of the CB version updates fall under the latter three points.

## What loader is best for my system?

The answer is "it depends". If you use the wrong loader for your board, then the system will either crash
during hwinit or just before the kernel/XeLL starts. Also, switching to another loader isn't guaranteed
to speed up boot times because of weird hwinit intricacies that I haven't figured out yet.

The unique hwinit configurations can be seen in the hwinit_bytecode/ directory, but here are CBs
with unique hwinit programs:

- Xenon: 1888, 1897, 1902, 1903, 1921
- Elpis: 7373
- Zephyr: 4540, 4558, 4571
- Falcon: 5761 (for eight-chip SDRAM systems), 5770 (for four-chip SDRAM systems)
- Jasper: 6712, 6723, 6751
- Trinity: 9188, 9230
- Corona: 13121 (for systems without Winbond SDRAMs), 13182 (for Winbond SDRAM systems)

## What loader boots my system the fastest?

Again, that depends on if the thing works with your board. These are just the results of my experimentation
and aren't guaranteed to be stable.

- 1888 boots Xenons as fast as Jaspers. It also works on Falcons with eight SDRAM chips; on four-chip
  Falcons it will get past HWINIT but will crash soon after, likely because the SDRAM banking configuration
  doesn't work with those boards. Unfortunately, the eight-chip Falcons are all ones with faulty GPUs.

More are to be tested.

## Why are Falcons so slow to boot?

The answer, to the best of my knowledge, is "because the hwinit bytecode is programmed that way".
There is an explicit wait loop that will delay execution until some condition is met, and I'm not
sure what the condition is just yet. Reverse engineering efforts continue.

This affects both Falcon hwinit bytecode revisions (CBs 5761 and 5770) but is known to happen on
other loaders (7373 is also slow). It also makes Falcon loaders less than ideal for booting other
systems because they will enter the same wait loop.

The relevant code from Falcon v2 (1d107e2710b427e376a69767f29245c30bf4ff29) is:

```
3738: %r10_0 = add %r11_0, 0x01010101
3740: branch_cond0 %r11_0, 0x50505050 -> 0x34bc ^
```

```
3ab4: %r10_0 = add %r11_0, 0x01010101
3abc: branch_cond0 %r11_0, 0x50505050 -> 0x3834 ^
```

To skip these loops, and massively speed up your boots (and probably make your system very unstable
in the process), use `--no5050` with loadfare.py.

## License

Public domain
