from amaranth import *

from clockworks import Clockworks

class SOC(Elaboratable):

    def __init__(self):

        self.leds = Signal(5)

    def elaborate(self, platform):

        m = Module()

        cw = Clockworks(slow=21)
        m.submodules.cw = cw

        sequence = [
                #       24      16       8       0
                # .......|.......|.......|.......|
                #R         rs2  rs1 f3   rd     op
                #I         imm  rs1 f3   rd     op
                #S    imm  rs2  rs1 f3  imm     op
                # ......|....|....|..|....|......|
                0b00000000000000000000000000110011, # R add  x0, x0, x0
                0b00000000000000000000000010110011, # R add  x1, x0, x0
                0b00000000000100001000000010010011, # I addi x1, x1,  1
                0b00000000000100001000000010010011, # I addi x1, x1,  1
                0b00000000000100001000000010010011, # I addi x1, x1,  1
                0b00000000000100001000000010010011, # I addi x1, x1,  1
                0b00000000000000001010000100000011, # I lw   x2, 0(x1)
                0b00000000000100010010000000100011, # S sw   x2, 0(x1)
                0b00000000000100000000000001110011  # S ebreak
        ]

        # Signal declarations
        isALUreg = Signal()
        isALUimm = Signal()
        isBranch = Signal()
        isJALR = Signal()
        isJAL = Signal()
        isAUIPC = Signal()
        isLUI = Signal()
        isLoad = Signal()
        isStore = Signal()
        isSystem = Signal()

        Uimm, Iimm, Bimm, Simm, Jimm = [Signal(32) for _ in range(5)]
        rs1Id, rs2Id, rdId = [Signal(5) for _ in range(3)]
        funct3, funct7 = [Signal(3), Signal(7)]

        pc = Signal(32)
        instr = Signal(32, reset=0b0110011)
        mem = Array([Signal(32, reset=x) for x in sequence])

        self.pc = pc
        self.instr = instr
        self.isALUreg = isALUreg
        self.isALUimm = isALUimm
        self.isSystem = isSystem
        self.rdId = rdId
        self.rs1Id = rs1Id
        self.rs2Id = rs2Id
        self.Iimm = Iimm
        self.funct3 = funct3

        # Opcode decoder
        m.d.comb += [
            isALUreg.eq(instr[0:7] == 0b0110011),
            isALUimm.eq(instr[0:7] == 0b0010011),
            isBranch.eq(instr[0:7] == 0b1100011),
            isJALR.eq(  instr[0:7] == 0b1100111),
            isJAL.eq(   instr[0:7] == 0b1101111),
            isAUIPC.eq( instr[0:7] == 0b0010111),
            isLUI.eq(   instr[0:7] == 0b0110111),
            isLoad.eq(  instr[0:7] == 0b0000011),
            isStore.eq( instr[0:7] == 0b0100011),
            isSystem.eq(instr[0:7] == 0b1110011),
        ]

        # Immediate format decoder
        m.d.comb += [
            Uimm.eq(Cat(Repl(0, 12), instr[12:32])),
            Iimm.eq(Cat(instr[20:31], Repl(instr[31], 21))),
            Simm.eq(Cat(instr[7:12], Cat(instr[25:31], Repl(instr[31], 21)))),
            Bimm.eq(Cat(0, Cat(instr[8:12], Cat(instr[25:31], Cat(
                instr[7], Repl(instr[31], 20)))))),
            Jimm.eq(Cat(0, Cat(instr[21:31], Cat(instr[20], Cat(
                instr[12:20], Repl(instr[31], 12))))))
        ]

        # Register addresses decoder
        m.d.comb += [
            rs1Id.eq(instr[15:20]),
            rs2Id.eq(instr[20:25]),
            rdId.eq( instr[7:12])
        ]

        # Function code decdore
        m.d.comb += [
            funct3.eq(instr[12:15]),
            funct7.eq(instr[25:32])
        ]

        # Fetch instruction and increase PC
        m.d.slow += [
                instr.eq(mem[pc]),
                pc.eq(Mux(isSystem, 0, pc + 1))
        ]

        # Assign important signals to LEDS
        m.d.comb += self.leds.eq(Mux(isSystem, 31, Cat(isLoad, Cat(
            isStore, Cat(isALUimm, Cat(isALUreg, pc[0]))))))

        return m
