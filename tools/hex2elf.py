import sys

filename = sys.argv[1]

class Ram():
    def __init__(self):
        self.max_addr = 0
        self.mem = 0

class Elf32Header():
    def __init__(self, data):
        def get(data):
            return int.from_bytes(data, byteorder='little')
        self.type = get(data[0:2])
        self.machine = get(data[2:4])
        self.version = get(data[4:8])
        self.entry = get(data[8:12])
        self.phoff = get(data[12:16])
        self.shoff = get(data[16:20])
        self.flags = get(data[20:24])
        self.ehsize = get(data[24:26])
        self.phentsize = get(data[26:28])
        self.phnum = get(data[28:30])
        self.shentsize = get(data[30:32])
        self.shnum = get(data[32:34])
        self.shstrndx = get(data[34:36])

        if self.ehsize == 36:
            print("I'll fix it.")
    def __str__(self):
        text = ""
        text += "type=     0x{:04x}\n".format(self.type)
        text += "machine=  0x{:04x}\n".format(self.machine)
        text += "version=  0x{:04x}\n".format(self.version)
        text += "ehsize=   0x{:04x}\n".format(self.ehsize)
        text += "shentsize=0x{:04x}\n".format(self.shentsize)
        text += "shnum=    0x{:04x}\n".format(self.shnum)
        return text

def load_ram_elf(filename):
    data = None
    with open(filename, "rb") as f:
        data = bytearray(f.read())
        ram = Ram()

        header = Elf32Header(data)

        print(str(header))

        return ram


ram = load_ram_elf(filename)
