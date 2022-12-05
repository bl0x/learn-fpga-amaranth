import sys
from amaranth import *

from clockworks import Clockworks

class SOC(Elaboratable):

    def __init__(self):

        self.leds = Signal(5)

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

    def elaborate(self, platform):

        m = Module()

        cw = Clockworks(slow=21)
        m.submodules.cw = cw

        # Instruction sequence to be executed
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

        # Program counter
        pc = Signal(32)

        # Current instruction
        instr = Signal(32, reset=0b0110011)

        # Instruction memory initialised with above 'sequence'
        mem = Array([Signal(32, reset=x) for x in sequence])

        # Register bank
        regs = Array([Signal(32) for x in range(32)])
        rs1 = Signal(32)
        rs2 = Signal(32)

        writeBackData = C(0)
        writeBackEn = C(0)

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
        Simm = (Cat(instr[7:12], Cat(instr[25:31], Repl(instr[31], 21)))),
        Bimm = (Cat(0, Cat(instr[8:12], Cat(instr[25:31], Cat(
            instr[7], Repl(instr[31], 20))))))
        Jimm = (Cat(0, Cat(instr[21:31], Cat(instr[20], Cat(
            instr[12:20], Repl(instr[31], 12))))))

        # Register addresses decoder
        rs1Id = (instr[15:20])
        rs2Id = (instr[20:25])
        rdId = ( instr[7:12])

        # Function code decdore
        funct3 = (instr[12:15])
        funct7 = (instr[25:32])

        # Data write back
        with m.If(writeBackEn & (rdId != 0)):
            m.d.slow += regs[rdId].eq(writeBackData)

        # Main state machine
        with m.FSM(reset="FETCH_INSTR") as fsm:
            # Assign important signals to LEDS
            m.d.comb += self.leds.eq(Mux(isSystem, 31, (1 << fsm.state)))
            with m.State("FETCH_INSTR"):
                m.d.slow += instr.eq(mem[pc])
                m.next = "FETCH_REGS"
            with m.State("FETCH_REGS"):
                m.d.slow += [
                    rs1.eq(regs[rs1Id]),
                    rs2.eq(regs[rs2Id])
                ]
                m.next = "EXECUTE"
            with m.State("EXECUTE"):
                m.d.slow += pc.eq(pc + 1)
                m.next = "FETCH_INSTR"

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

        return m
