# hwinit program dumps

Disassemblies generated with [Mate's hwinit tool](https://codeberg.org/hax360/tools/src/branch/main/hwinit).

## Versions

### xenon_v1

- Known CBs: 1888, 1940, 1941, 1942

This is the "simplest", and therefore fastest, version of the hwinit programs.
It initializes SDRAM very quickly compared to the others and is able to boot any eight-chip SDRAM system,
although stability might be compromised.

### xenon_v2

- Known CBs: 1897

### xenon_v3

- Known CBs: 1902

### xenon_v4

- Known CBs: 1903, 1920, 1925, 1926, 1927, 1928

### xenon_v5

- Known CBs: 1921, 1922, 1923

### elpis

- Known CBs: All Elpis revisions (73xx), 8192

### zephyr_v1

- Known CBs: 4540

### zephyr_v2

- Known CBs: 4559, 4560, 4561, 4562, 4571, 4572

Single byte changed from zephyr_v1, otherwise identical.

### zephyr_v3

- Known CBs: 4558, 4569, 4574, 4575, 4576, 4577, 4578, 4579, 4580

### falcon_v1

- Known CBs: 5761, 5766

### falcon_v2

- Known CBs: 5770, 5771, 5772, 5773, 5774

Adds support for Falcons with four-chip SDRAM configurations.

### jasper_v1

- Known CBs: 6712

### jasper_v2

- Known CBs: 6723, 6750

### jasper_v3

- Known CBs: 6751, 6752, 6753, 6754

### trinity_v1

- Known CBs: 9188

Contains a bug where the hwinit program tries to initialize 0xE40001A4 (DBG_CNTL1_REG) before the GPU BAR is configured.
This is fixed in trinity_v2 and all Corona bytecodes.

### trinity_v2

- Known CBs: 9230, 9231

Contains aforementioned bugfix; otherwise identical to trinity_v1.

### corona_v1

- Known CBs: 13121, 13180, 13181

### corona_v2

- Known CBs: 13182, 16128

Adds support for Winbond SDRAMs. Also used on Winchester.
