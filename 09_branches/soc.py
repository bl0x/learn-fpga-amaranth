import sys
from amaranth import *

from clockworks import Clockworks
from riscv_assembler import RiscvAssembler

class SOC(Elaboratable):

    def __init__(self):

        self.leds = Signal(5)

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

        a = RiscvAssembler()
        a.read("""begin:
        ADD  x1, x0, x0
        ADDI x2, x0, 32
        l0:
        ADDI x1, x1,  1
        BNE  x1, x2, l0
        EBREAK
        """)

        a.assemble()
        self.sequence = a.mem
        print("memory = {}".format(self.sequence))

    def elaborate(self, platform):

        m = Module()

        cw = Clockworks(m, slow=21, sim_slow=10)
        m.submodules.cw = cw

        # Program counter
        pc = Signal(32)

        # Current instruction
        instr = Signal(32, reset=0b0110011)

        # Instruction memory initialised with above 'sequence'
        mem = Array([Signal(32, reset=x, name="mem") for x in self.sequence])

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

        # Immediate format decoder
        Uimm = (Cat(Const(0).replicate(12), instr[12:32]))
        Iimm = (Cat(instr[20:31], instr[31].replicate(21)))
        Simm = (Cat(instr[7:12], instr[25:31], instr[31].replicate(21))),
        Bimm = (Cat(0, instr[8:12], instr[25:31], instr[7], instr[31].replicate(20)))
        Jimm = (Cat(0, instr[21:31], instr[20], instr[12:20], instr[31].replicate(12)))

        # Register addresses decoder
        rs1Id = (instr[15:20])
        rs2Id = (instr[20:25])
        rdId =  (instr[7:12])

        # Function code decdore
        funct3 = (instr[12:15])
        funct7 = (instr[25:32])

        # ALU
        aluIn1 = rs1
        aluIn2 = Mux(isALUreg, rs2, Iimm)
        shamt = Mux(isALUreg, rs2[0:5], instr[20:25])

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
        with m.FSM(reset="FETCH_INSTR", domain="slow") as fsm:
            with m.State("FETCH_INSTR"):
                m.d.slow += instr.eq(mem[pc[2:32]])
                m.next = "FETCH_REGS"
            with m.State("FETCH_REGS"):
                m.d.slow += [
                    rs1.eq(regs[rs1Id]),
                    rs2.eq(regs[rs2Id])
                ]
                m.next = "EXECUTE"
            with m.State("EXECUTE"):
                m.d.slow += pc.eq(nextPc)
                m.next = "FETCH_INSTR"

        # Register write back
        writeBackData = Mux((isJAL | isJALR), (pc + 4), aluOut)
        writeBackEn = fsm.ongoing("EXECUTE") & (
                isALUreg |
                isALUimm |
                isJAL    |
                isJALR)

        with m.If(writeBackEn & (rdId != 0)):
            m.d.slow += regs[rdId].eq(writeBackData)
            # Assign writeBackData to leds to see what is happening
            m.d.slow += self.leds.eq(writeBackData)

        # Export signals for simulation
        def export(signal, name):
            if type(signal) is not Signal:
                newsig = Signal(signal.shape(), name = name)
                m.d.comb += newsig.eq(signal)
            else:
                newsig = signal
            self.ports.append(newsig)
            setattr(self, name, newsig)

        if platform is None:
            export(ClockSignal("slow"), "slow_clk")
            export(pc, "pc")
            export(instr, "instr")
            export(isALUreg, "isALUreg")
            export(isALUimm, "isALUimm")
            export(isBranch, "isBranch")
            export(isJAL, "isJAL")
            export(isJALR, "isJALR")
            export(isLoad, "isLoad")
            export(isStore, "isStore")
            export(isSystem, "isSystem")
            export(rs1Id, "rs1Id")
            export(rs2Id, "rs2Id")
            export(Iimm, "Iimm")
            export(Bimm, "Bimm")
            export(Jimm, "Jimm")
            export(funct3, "funct3")
            export(rdId, "rdId")
            export(rs1, "rs1")
            export(rs2, "rs2")
            export(writeBackData, "writeBackData")
            export(writeBackEn, "writeBackEn")
            export(aluOut, "aluOut")
            export((1 << fsm.state), "state")

        return m
