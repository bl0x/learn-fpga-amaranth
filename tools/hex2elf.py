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
        self.ident = data[0:16]
        self.type = get(data[16:18])
        self.machine = get(data[18:20])
        self.version = get(data[20:24])
        self.entry = get(data[24:28])
        self.phoff = get(data[28:32])
        self.shoff = get(data[32:36])
        self.flags = get(data[36:40])
        self.ehsize = get(data[40:42])
        self.phentsize = get(data[42:44])
        self.phnum = get(data[44:46])
        self.shentsize = get(data[46:48])
        self.shnum = get(data[48:50])
        self.shstrndx = get(data[50:52])

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
