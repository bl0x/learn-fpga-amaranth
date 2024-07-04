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
        ADD  x0, x0, x0
        ADD  x1, x0, x0
        ADDI x1, x1,  1
        ADDI x1, x1,  1
        ADDI x1, x1,  1
        ADDI x1, x1,  1
        ADD  x2, x1, x0
        ADD  x3, x1, x2
        SRLI x3, x3,  3
        SLLI x3, x3, 31
        SRAI x3, x3,  5
        SRLI x1, x3, 26
        EBREAK
        """)

        a.assemble()
        self.sequence = a.mem
        print("memory = {}".format(self.sequence))

    def elaborate(self, platform):

        m = Module()

        cw = Clockworks(slow=21, sim_slow=10)
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
        Uimm = (Cat(Repl(0, 12), instr[12:32]))
        Iimm = (Cat(instr[20:31], Repl(instr[31], 21)))
        Simm = (Cat(instr[7:12], instr[25:31], Repl(instr[31], 21))),
        Bimm = (Cat(0, instr[8:12], instr[25:31], instr[7], Repl(instr[31], 20)))
        Jimm = (Cat(0, instr[21:31], instr[20], instr[12:20], Repl(instr[31], 12)))

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
                m.d.slow += pc.eq(pc + 4)
                m.next = "FETCH_INSTR"

        # Assign important signals to LEDS
        # Note: fsm.state is only accessible outside of the FSM context
        m.d.comb += self.leds.eq(Mux(isSystem, 31, (1 << fsm.state)))

        # Register write back
        writeBackData = aluOut
        writeBackEn = fsm.ongoing("EXECUTE") & (isALUreg | isALUimm)

        with m.If(writeBackEn & (rdId != 0)):
            m.d.slow += regs[rdId].eq(writeBackData)

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
            export(isLoad, "isLoad")
            export(isStore, "isStore")
            export(isSystem, "isSystem")
            export(rdId, "rdId")
            export(rs1Id, "rs1Id")
            export(rs2Id, "rs2Id")
            export(Iimm, "Iimm")
            export(funct3, "funct3")
            export(rdId, "rdId")
            export(rs1, "rs1")
            export(rs2, "rs2")
            export(writeBackData, "writeBackData")
            export(writeBackEn, "writeBackEn")
            export(aluOut, "aluOut")
            export((1 << fsm.state), "state")

        return m
