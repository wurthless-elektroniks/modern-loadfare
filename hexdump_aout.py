
with open("ppc/a.out", "rb") as f:
    data = f.read()

    if data[0x2C0:0x2C4] != bytes([0x48, 0x00, 0x00, 0x18]):
        print("something's wrong with the ELF")
        exit(1)
    
    formatted = []

    ctr = 0
    for b in data[0x2C0:0x3C0]:
        formatted.append(f"0x{b:02x}, ")
        ctr += 1
        if ctr == 16:
            formatted.append("\n")
            ctr = 0

    print(u"".join(formatted))
