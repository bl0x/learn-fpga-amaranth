#!/usr/bin/env python3

# instructions

RInstructions = [
    ("ADD",  0b000, 0b0000000),
    ("SUB",  0b000, 0b0100000),
    ("SLL",  0b001, 0b0000000),
    ("SLT",  0b010, 0b0000000),
    ("SLTU", 0b011, 0b0000000),
    ("XOR",  0b100, 0b0000000),
    ("SRL",  0b101, 0b0000000),
    ("SRA",  0b101, 0b0100000),
    ("OR",   0b110, 0b0000000),
    ("AND",  0b111, 0b0000000)
]
ROps = [x[0] for x in RInstructions]

IInstructions = [
    ("ADDI",  0b000),
    ("SLTI",  0b010),
    ("SLTIU", 0b011),
    ("XORI",  0b100),
    ("ORI",   0b110),
    ("ANDI",  0b111)
]
IOps = [x[0] for x in IInstructions]

IRInstructions = [
    ("SLLI", 0b001, 0b0000000),
    ("SRLI", 0b101, 0b0000000),
    ("SRAI", 0b101, 0b0100000)
]
IROps = [x[0] for x in IRInstructions]

JInstructions = [
    ("JAL",  0b1101111),
    ("JALR", 0b1100111, 0b000)
]
JOps = [x[0] for x in JInstructions]

BInstructions = [
    ("BEQ",  0b000),
    ("BNE",  0b001),
    ("BLT",  0b100),
    ("BGE",  0b101),
    ("BLTU", 0b110),
    ("BGEU", 0b111)
]
BOps = [x[0] for x in BInstructions]

UInstructions = [
    ("LUI",   0b0110111),
    ("AUIPC", 0b0010111)
]
UOps = [x[0] for x in UInstructions]

LInstructions = [
    ("LB",  0b000),
    ("LH",  0b001),
    ("LW",  0b010),
    ("LBU", 0b100),
    ("LHU", 0b101)
]
LOps = [x[0] for x in LInstructions]

SInstructions = [
    ("SB",  0b000),
    ("SH",  0b001),
    ("SW",  0b010)
]
SOps = [x[0] for x in SInstructions]

SysInstructions = [
    ("FENCE",),
    ("FENCE_I",),
    ("ECALL",),
    ("EBREAK",),
    ("CSRRW",),
    ("CSRRS",),
    ("CSRRWI",),
    ("CSRRSI",),
    ("CSRRCI",)
]
SysOps = [x[0] for x in SysInstructions]

class Instruction():
    def __init__(self, op, *args):
        self.op = op
        self.args = args
    def __repr__(self):
        text = "("
        for arg in self.args:
            text += "{:2}".format(arg)
            if arg is not self.args[-1]:
                text += ", "
        text += ")"
        return "({:4} {})".format(self.op, text)

abi_names = {
    'zero': 0,
    'ra'  : 1,
    'sp'  : 2,
    'gp'  : 3,
    'tp'  : 4,
    't0'  : 5,
    't1'  : 6,
    't2'  : 7,
    'fp'  : 8,
    's0'  : 8,
    's1'  : 9,
    'a0'  : 10,
    'a1'  : 11,
    'a2'  : 12,
    'a3'  : 13,
    'a4'  : 14,
    'a5'  : 15,
    'a6'  : 16,
    'a7'  : 17,
    's2'  : 18,
    's3'  : 19,
    's4'  : 20,
    's5'  : 21,
    's6'  : 22,
    's7'  : 23,
    's8'  : 24,
    's9'  : 25,
    's10' : 26,
    's11' : 27,
    't3'  : 28,
    't4'  : 29,
    't5'  : 30,
    't6'  : 31
}

def reg2int(arg):
    if len(arg) == 0:
        return None
    if arg.lower() in abi_names:
        return abi_names[arg.lower()]
    if arg[0].upper() == "X":
        return int(arg[1:])

class RiscvAssembler():
    def __init__(self):
        self.pc = 0
        self.labels = {}
        self.instructions = []
        self.mem = []

    def assemble(self):
        for inst in self.instructions:
            self.mem.append(self.encode(inst))

    def encodeR(self, f7, rs2, rs1, f3, rd, op):
        return ((f7 << 25) | (rs2 << 20) | (rs1 << 15)
                | (f3 << 12) | (rd << 7) | op)

    def encodeI(self, imm, rs, f3, rd, op):
        return (imm << 20) | (rs << 15) | (f3 << 12) | (rd << 7) | op

    def encodeJ(self, imm, rd, op):
        imm31 = (imm >> 20) & 1
        imm21 = (imm >> 1) & 0x3ff
        imm20 = (imm >> 11) & 1
        imm12 = (imm >> 12) & 0xff
        return ((imm31 << 31) | (imm21 << 21) | (imm20 << 20)
                | (imm12 << 12) | (rd << 7) | op)

    def encodeB(self, imm, rs2, rs1, f3, op):
        imm31 = (imm >> 12) & 1
        imm25 = (imm >> 5) & 0x3f
        imm8 =  (imm >> 1) & 0xf
        imm7 =  (imm >> 11) & 1
        return ((imm31 << 31) | (imm25 << 25) | (rs2 << 20) | (rs1 << 15)
                | (f3 << 12) | (imm8 << 8) | (imm7 << 7) | op)

    def encodeU(self, imm, rd, op):
        return (imm & 0xfffff000) | (rd << 7) | op

    def encodeS(self, imm, rs2, rs1, f3, op):
        imm25 = (imm >> 5) & 0x7f
        imm7  = imm & 0x1f
        return ((imm25 << 25) | (rs1 << 20) | (rs2 << 15)
                | (f3 << 12) | (imm7 << 7) | op)

    def encodeRops(self, instruction):
        rd, rs1, rs2 = [reg2int(x) for x in instruction.args]
        _, f3, f7 = [x for x in RInstructions if x[0] == instruction.op][0]
        return self.encodeR(f7, rs2, rs1, f3, rd, 0b0110011)

    def encodeIops(self, instruction):
        rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in IInstructions if x[0] == instruction.op][0]
        return self.encodeI(imm, rs, f3, rd, 0b0010011)

    def encodeIRops(self, instruction):
        rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3, f7 = [x for x in IRInstructions if x[0] == instruction.op][0]
        return self.encodeR(f7, imm, rs, f3, rd, 0b0010011)

    def encodeJops(self, instruction):
        if instruction.op == "JAL":
            rd = reg2int(instruction.args[0])
            imm = self.imm2int(instruction.args[1])
            _, op = [x for x in JInstructions if x[0] == instruction.op][0]
            return self.encodeJ(imm, rd, 0b1101111)
        elif instruction.op == "JALR":
            rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
            imm = self.imm2int(instruction.args[2])
            _, op, f3 = [x for x in JInstructions if x[0] == instruction.op][0]
            return self.encodeI(imm, rs, f3, rd, 0b1100111)

    def encodeBops(self, instruction):
        rs1, rs2 = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in BInstructions if x[0] == instruction.op][0]
        return self.encodeB(imm, rs2, rs1, f3, 0b1100011)

    def encodeUops(self, instruction):
        rd = reg2int(instruction.args[0])
        imm = self.imm2int(instruction.args[1])
        _, op = [x for x in UInstructions if x[0] == instruction.op][0]
        return self.encodeU(imm, rd, op)

    def encodeLops(self, instruction):
        rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in LInstructions if x[0] == instruction.op][0]
        return self.encodeI(imm, rs, f3, rd, 0b0000011)

    def encodeSops(self, instruction):
        rs2, rs1 = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in SInstructions if x[0] == instruction.op][0]
        return self.encodeS(imm, rs2, rs1, f3, 0b0100011)

    def encodeSysops(self, instruction):
        op = instruction.op
        if op == "FENCE": #! TODO
            return 0b00000000000000000000000001110011
        elif op == "FENCE_I":
            return 0b00000000000000000001000001110011
        elif op == "ECALL":
            return 0b00000000000000000000000001110011
        elif op == "EBREAK":
            return 0b00000000000100000000000001110011
        else:
            print("Unhandled system op {}".format(op))

    def encode(self, instruction):
        encoded = 0
        if instruction.op in ROps:
            encoded = self.encodeRops(instruction)
        elif instruction.op in IOps:
            encoded = self.encodeIops(instruction)
        elif instruction.op in IROps:
            encoded = self.encodeIRops(instruction)
        elif instruction.op in JOps:
            encoded = self.encodeJops(instruction)
        elif instruction.op in BOps:
            encoded = self.encodeBops(instruction)
        elif instruction.op in UOps:
            encoded = self.encodeUops(instruction)
        elif instruction.op in LOps:
            encoded = self.encodeLops(instruction)
        elif instruction.op in SOps:
            encoded = self.encodeSops(instruction)
        elif instruction.op in SysOps:
            encoded = self.encodeSysops(instruction)
        else:
            print("Unhandled instruction / opcode {}".format(instruction))
            exit(1)
        print("  enc@pc=0x{:03x} {} -> 0b{:032b}".format(
            self.pc, instruction, encoded))
        self.pc += 4
        return encoded

    def read(self, text):
        instructions = []
        for line in text.splitlines():
            line = line.strip()
            i = None
            if ':' in line:
                label, line = [x.strip() for x in line.split(':', maxsplit=1)]
                pc = len(instructions) * 4
                self.labels[label.upper()] = pc
                print("found label '{}', pc = {}".format(label, pc))
            if len(line) == 0:
                continue
            if ' ' not in line:
                i = Instruction(line)
            else:
                op, rest = [x.strip().upper() for x in (
                    line.split(' ', maxsplit=1))]
                # print("op = {}, rest = {}".format(op, rest))
                items = [x.strip() for x in rest.split(',')]
                i = Instruction(op, *items)
            if i is not None:
                instructions.append(i)
        self.instructions += instructions

    def imm2int(self, arg):
        if len(arg) == 0:
            return None
        if arg in self.labels:
            offset = self.labels[arg] - self.pc
            # print("label offset = {}".format(offset))
            return offset
        try:
            return int(arg)
        except ValueError as e:
            return int(arg, 16)


if __name__ == "__main__":
    a = RiscvAssembler()
    a.read("""begin:
           step4:
           ADD   x0, x0, x0
           ADD   x1, x0, x0
           ADDI  x1, x1,  1
           ADDI  x1, x1,  1
           ADDI  x1, x1,  1
           ADDI  x1, x1,  1
           LW    x2, x1,  0
           SW    x2, x1,  0
           EBREAK
           start:
           ADD x3, x2, x1
           ADDI  x1, x0,  4
           ADDI  ra, zero,  4
           AND   x2, x1, x0
           SUB   x4, x1, x0
           SRAI  x4, x1,  3
           jumps:
           JAL   x4, 255
           JALR  x5, x7,  start
           branches:
           BEQ   x3, x4,  1
           BNE   x3, x4,  1
           BLT   x3, x4,  1
           BGE   x3, x4,  1
           BLTU  x3, x4,  1
           BGEU  x3, x4,  1
           luiandauipc:
           lui: LUI   x5,  0x30000
           AUIPC x5,  0x30000
           load:
           LB    x7, x10, 0xaa
           LH    x7, x10, 0xab
           LW    x7, x10, 0xac
           LBU   x7, x10, 0xad
           LHU   x7, x10, 0xae
           finish:
           store:
           SB    x7, x10, 1
           SH    x7, x10, 2
           SW    x7, x10, 3
           EBREAK
    """)
    print(a.instructions)
    a.assemble()
