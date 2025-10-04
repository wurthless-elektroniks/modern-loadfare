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

## License

Public domain
