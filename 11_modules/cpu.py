from amaranth import *

class CPU(Elaboratable):

    def __init__(self):
        self.mem_addr = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_rdata = Signal(32)
        self.x1 = Signal(32)
        self.fsm = None

    def elaborate(self, platform):
        m = Module()

        # Program counter
        pc = Signal(32)
        self.pc = pc

        # Current instruction
        instr = Signal(32, reset=0b0110011)
        self.instr = instr

        # Register bank
        regs = Array([Signal(32, name="x"+str(x)) for x in range(32)])
        rs1 = Signal(32)
        rs2 = Signal(32)

        # ALU registers
        aluOut = Signal(32)
        takeBranch = Signal(32)

        # Opcode decoder
        isALUreg = (instr[0:7] == 0b0110011)
        isALUimm = (instr[0:7] == 0b0010011)
        isBranch = (instr[0:7] == 0b1100011)
        isJALR =   (instr[0:7] == 0b1100111)
        isJAL =    (instr[0:7] == 0b1101111)
        isAUIPC =  (instr[0:7] == 0b0010111)
        isLUI =    (instr[0:7] == 0b0110111)
        isLoad =   (instr[0:7] == 0b0000011)
        isStore =  (instr[0:7] == 0b0100011)
        isSystem = (instr[0:7] == 0b1110011)
        self.isALUreg = isALUreg
        self.isALUimm = isALUimm
        self.isBranch = isBranch
        self.isLoad = isLoad
        self.isStore = isStore
        self.isSystem = isSystem

        # Immediate format decoder
        Uimm = (Cat(Repl(0, 12), instr[12:32]))
        Iimm = (Cat(instr[20:31], Repl(instr[31], 21)))
        Simm = (Cat(instr[7:12], Cat(instr[25:31], Repl(instr[31], 21)))),
        Bimm = (Cat(0, Cat(instr[8:12], Cat(instr[25:31], Cat(
            instr[7], Repl(instr[31], 20))))))
        Jimm = (Cat(0, Cat(instr[21:31], Cat(instr[20], Cat(
            instr[12:20], Repl(instr[31], 12))))))
        self.Iimm = Iimm

        # Register addresses decoder
        rs1Id = (instr[15:20])
        rs2Id = (instr[20:25])
        rdId = ( instr[7:12])

        self.rdId = rdId
        self.rs1Id = rs1Id
        self.rs2Id = rs2Id

        # Function code decdore
        funct3 = (instr[12:15])
        funct7 = (instr[25:32])
        self.funct3 = funct3

        # ALU
        aluIn1 = rs1
        aluIn2 = Mux(isALUreg, rs2, Iimm)
        shamt = Mux(isALUreg, rs2[0:5], instr[20:25])

        # Wire memory address to pc
        m.d.comb += self.mem_addr.eq(pc)

        with m.Switch(funct3) as alu:
            with m.Case(0b000):
                m.d.comb += aluOut.eq(Mux(funct7[5] & instr[5],
                                          (aluIn1 - aluIn2), (aluIn1 + aluIn2)))
            with m.Case(0b001):
                m.d.comb += aluOut.eq(aluIn1 << shamt)
            with m.Case(0b010):
                m.d.comb += aluOut.eq(aluIn1.as_signed() < aluIn2.as_signed())
            with m.Case(0b011):
                m.d.comb += aluOut.eq(aluIn1 < aluIn2)
            with m.Case(0b100):
                m.d.comb += aluOut.eq(aluIn1 ^ aluIn2)
            with m.Case(0b101):
                m.d.comb += aluOut.eq(Mux(
                    funct7[5],
                    (aluIn1.as_signed() >> shamt),     # arithmetic right shift
                    (aluIn1.as_unsigned() >> shamt)))  # logical right shift
            with m.Case(0b110):
                m.d.comb += aluOut.eq(aluIn1 | aluIn2)
            with m.Case(0b111):
                m.d.comb += aluOut.eq(aluIn1 & aluIn2)

        with m.Switch(funct3) as alu_branch:
            with m.Case(0b000):
                m.d.comb += takeBranch.eq(rs1 == rs2)
            with m.Case(0b001):
                m.d.comb += takeBranch.eq(rs1 != rs2)
            with m.Case(0b100):
                m.d.comb += takeBranch.eq(rs1.as_signed() < rs2.as_signed())
            with m.Case(0b101):
                m.d.comb += takeBranch.eq(rs1.as_signed() >= rs2.as_signed())
            with m.Case(0b110):
                m.d.comb += takeBranch.eq(rs1 < rs2)
            with m.Case(0b111):
                m.d.comb += takeBranch.eq(rs1 >= rs2)
            with m.Case("---"):
                m.d.comb += takeBranch.eq(0)

        # Next program counter is either next intstruction or depends on
        # jump target
        nextPc = Mux((isBranch & takeBranch), pc + Bimm,
                     Mux(isJAL, pc + Jimm,
                         Mux(isJALR, rs1 + Iimm,
                             pc + 4)))

        # Main state machine
        with m.FSM(reset="FETCH_INSTR") as fsm:
            self.fsm = fsm
            m.d.comb += self.mem_rstrb.eq(fsm.ongoing("FETCH_INSTR"))
            with m.State("FETCH_INSTR"):
                m.next = "WAIT_INSTR"
            with m.State("WAIT_INSTR"):
                m.d.sync += instr.eq(self.mem_rdata)
                m.next = ("FETCH_REGS")
            with m.State("FETCH_REGS"):
                m.d.sync += [
                    rs1.eq(regs[rs1Id]),
                    rs2.eq(regs[rs2Id])
                ]
                m.next = "EXECUTE"
            with m.State("EXECUTE"):
                m.d.sync += pc.eq(nextPc)
                m.next = "FETCH_INSTR"

        # Register write back
        writeBackData = Mux((isJAL | isJALR), (pc + 4),
                            Mux(isLUI, Uimm,
                                Mux(isAUIPC, (pc + Uimm), aluOut)))
        writeBackEn = fsm.ongoing("EXECUTE") & (
                isALUreg |
                isALUimm |
                isLUI    |
                isAUIPC  |
                isJAL    |
                isJALR)

        self.writeBackData = writeBackData

        with m.If(writeBackEn & (rdId != 0)):
            m.d.sync += regs[rdId].eq(writeBackData)
            # Also assign to debug output to see what is happening
            m.d.sync += self.x1.eq(writeBackData)

        return m
