from amaranth import *

class CPU(Elaboratable):

    def __init__(self):
        self.mem_addr = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_rdata = Signal(32)
        self.mem_wdata = Signal(32)
        self.mem_wmask = Signal(4)
        self.x10 = Signal(32)
        self.fsm = None

    def elaborate(self, platform):
        m = Module()

        # Program counter
        pc = Signal(32)
        self.pc = pc

        # Memory
        mem_rdata = self.mem_rdata

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
        # It is nice to have these as actual signals for simulation
        isALUreg = Signal()
        isALUimm = Signal()
        isBranch = Signal()
        isJALR   = Signal()
        isJAL    = Signal()
        isAUIPC  = Signal()
        isLUI    = Signal()
        isLoad   = Signal()
        isStore  = Signal()
        isSystem = Signal()
        m.d.comb += [
            isALUreg.eq(instr[0:7] == 0b0110011),
            isALUimm.eq(instr[0:7] == 0b0010011),
            isBranch.eq(instr[0:7] == 0b1100011),
            isJALR.eq(instr[0:7] == 0b1100111),
            isJAL.eq(instr[0:7] == 0b1101111),
            isAUIPC.eq(instr[0:7] == 0b0010111),
            isLUI.eq(instr[0:7] == 0b0110111),
            isLoad.eq(instr[0:7] == 0b0000011),
            isStore.eq(instr[0:7] == 0b0100011),
            isSystem.eq(instr[0:7] == 0b1110011)
        ]
        self.isALUreg = isALUreg
        self.isALUimm = isALUimm
        self.isBranch = isBranch
        self.isLoad = isLoad
        self.isStore = isStore
        self.isSystem = isSystem

        # Extend a signal with a sign bit repeated n times
        def SignExtend(signal, sign, n):
            return Cat(signal, Repl(sign, n))

        # Immediate format decoder
        Uimm = Signal(32)
        Iimm = Signal(32)
        Simm = Signal(32)
        Bimm = Signal(32)
        Jimm = Signal(32)
        m.d.comb += [
            Uimm.eq(Cat(Repl(0, 12), instr[12:32])),
            Iimm.eq(Cat(instr[20:31], Repl(instr[31], 21))),
            Simm.eq(Cat(instr[7:12], instr[25:31], Repl(instr[31], 21))),
            Bimm.eq(Cat(0, instr[8:12], instr[25:31], instr[7],
                Repl(instr[31], 20))),
            Jimm.eq(Cat(0, instr[21:31], instr[20], instr[12:20],
                Repl(instr[31], 12)))
        ]
        self.Iimm = Iimm

        # Register addresses decoder
        rs1Id = instr[15:20]
        rs2Id = instr[20:25]
        rdId = instr[7:12]

        self.rdId = rdId
        self.rs1Id = rs1Id
        self.rs2Id = rs2Id

        # Function code decdore
        funct3 = instr[12:15]
        funct7 = instr[25:32]
        self.funct3 = funct3

        # ALU
        aluIn1 = Signal.like(rs1)
        aluIn2 = Signal.like(rs2)
        shamt = Signal(5)
        aluMinus = Signal(33)
        aluPlus = Signal.like(aluIn1)

        m.d.comb += [
            aluIn1.eq(rs1),
            aluIn2.eq(Mux((isALUreg | isBranch), rs2, Iimm)),
            shamt.eq(Mux(isALUreg, rs2[0:5], instr[20:25]))
        ]

        m.d.comb += [
            aluMinus.eq(Cat(~aluIn1, C(0,1)) + Cat(aluIn2, C(0,1)) + 1),
            aluPlus.eq(aluIn1 + aluIn2)
        ]

        EQ = aluMinus[0:32] == 0
        LTU = aluMinus[32]
        LT = Mux((aluIn1[31] ^ aluIn2[31]), aluIn1[31], aluMinus[32])

        def flip32(x):
            a = [x[i] for i in range(0, 32)]
            return Cat(*reversed(a))

        # TODO: check these again!
        shifter_in = Mux(funct3 == 0b001, flip32(aluIn1), aluIn1)
        shifter = Cat(shifter_in, (instr[30] & aluIn1[31])) >> aluIn2[0:5]
        leftshift = flip32(shifter)

        with m.Switch(funct3) as alu:
            with m.Case(0b000):
                m.d.comb += aluOut.eq(Mux(funct7[5] & instr[5],
                                          aluMinus[0:32], aluPlus))
            with m.Case(0b001):
                m.d.comb += aluOut.eq(leftshift)
            with m.Case(0b010):
                m.d.comb += aluOut.eq(LT)
            with m.Case(0b011):
                m.d.comb += aluOut.eq(LTU)
            with m.Case(0b100):
                m.d.comb += aluOut.eq(aluIn1 ^ aluIn2)
            with m.Case(0b101):
                m.d.comb += aluOut.eq(shifter)
            with m.Case(0b110):
                m.d.comb += aluOut.eq(aluIn1 | aluIn2)
            with m.Case(0b111):
                m.d.comb += aluOut.eq(aluIn1 & aluIn2)

        with m.Switch(funct3) as alu_branch:
            with m.Case(0b000):
                m.d.comb += takeBranch.eq(EQ)
            with m.Case(0b001):
                m.d.comb += takeBranch.eq(~EQ)
            with m.Case(0b100):
                m.d.comb += takeBranch.eq(LT)
            with m.Case(0b101):
                m.d.comb += takeBranch.eq(~LT)
            with m.Case(0b110):
                m.d.comb += takeBranch.eq(LTU)
            with m.Case(0b111):
                m.d.comb += takeBranch.eq(~LTU)
            with m.Case("---"):
                m.d.comb += takeBranch.eq(0)

        # Next program counter is either next intstruction or depends on
        # jump target
        pcPlusImm = pc + Mux(instr[3], Jimm[0:32],
                             Mux(instr[4], Uimm[0:32],
                                 Bimm[0:32]))
        pcPlus4 = pc + 4

        nextPc = Mux(((isBranch & takeBranch) | isJAL), pcPlusImm,
                     Mux(isJALR, Cat(C(0, 1), aluPlus[1:32]),
                         pcPlus4))

        # Main state machine
        with m.FSM(reset="FETCH_INSTR") as fsm:
            self.fsm = fsm
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
                with m.If(~isSystem):
                    m.d.sync += pc.eq(nextPc)
                with m.If(isLoad):
                    m.next = "LOAD"
                with m.Elif(isStore):
                    m.next = "STORE"
                with m.Else():
                    m.next = "FETCH_INSTR"
            with m.State("LOAD"):
                m.next = "WAIT_DATA"
            with m.State("WAIT_DATA"):
                m.next = "FETCH_INSTR"
            with m.State("STORE"):
                m.next = "FETCH_INSTR"

        ## Load and store

        loadStoreAddr = Signal(32)
        m.d.comb += loadStoreAddr.eq(rs1 + Mux(isStore, Simm, Iimm))

        # Load
        memByteAccess = Signal()
        memHalfwordAccess = Signal()
        loadHalfword = Signal(16)
        loadByte = Signal(8)
        loadSign = Signal()
        loadData = Signal(32)

        m.d.comb += [
            memByteAccess.eq(funct3[0:2] == C(0,2)),
            memHalfwordAccess.eq(funct3[0:2] == C(1,2)),
            loadHalfword.eq(Mux(loadStoreAddr[1], mem_rdata[16:32],
                                mem_rdata[0:16])),
            loadByte.eq(Mux(loadStoreAddr[0], loadHalfword[8:16],
                            loadHalfword[0:8])),
            loadSign.eq(~funct3[2] & Mux(memByteAccess, loadByte[7],
                                         loadHalfword[15])),
            loadData.eq(
                Mux(memByteAccess, SignExtend(loadByte, loadSign, 24),
                    Mux(memHalfwordAccess, SignExtend(loadHalfword,
                                                      loadSign, 16),
                        mem_rdata)))
        ]

        # Store
        m.d.comb += [
            self.mem_wdata[ 0: 8].eq(rs2[0:8]),
            self.mem_wdata[ 8:16].eq(
                Mux(loadStoreAddr[0], rs2[0:8], rs2[8:16])),
            self.mem_wdata[16:24].eq(
                Mux(loadStoreAddr[1], rs2[0:8], rs2[16:24])),
            self.mem_wdata[24:32].eq(
                Mux(loadStoreAddr[0], rs2[0:8],
                    Mux(loadStoreAddr[1], rs2[8:16], rs2[24:32])))
        ]

        store_wmask = Signal(4)
        m.d.comb += store_wmask.eq(
                Mux(memByteAccess,
                    Mux(loadStoreAddr[1],
                        Mux(loadStoreAddr[0], 0b1000, 0b0100),
                        Mux(loadStoreAddr[0], 0b0010, 0b0001)
                        ),
                    Mux(memHalfwordAccess,
                        Mux(loadStoreAddr[1], 0b1100, 0b0011),
                        0b1111)
                    )
                )

        # Wire memory address to pc or loadStoreAddr
        m.d.comb += [
            self.mem_addr.eq(
                Mux(fsm.ongoing("WAIT_INSTR") | fsm.ongoing("FETCH_INSTR"),
                    pc, loadStoreAddr)),
            self.mem_rstrb.eq(fsm.ongoing("FETCH_INSTR") | fsm.ongoing("LOAD")),
            self.mem_wmask.eq(Repl(fsm.ongoing("STORE"), 4) & store_wmask)
        ]


        # Register write back
        writeBackData = Mux((isJAL | isJALR), pcPlus4,
                            Mux(isLUI, Uimm,
                                Mux(isAUIPC, pcPlusImm,
                                    Mux(isLoad, loadData,
                                    aluOut))))

        writeBackEn = ((fsm.ongoing("EXECUTE") & ~isBranch & ~isStore & ~isLoad)
                       | fsm.ongoing("WAIT_DATA"))

        self.writeBackData = writeBackData


        with m.If(writeBackEn & (rdId != 0)):
            m.d.sync += regs[rdId].eq(writeBackData)
            # Also assign to debug output to see what is happening
            with m.If(rdId == 10):
                m.d.sync += self.x10.eq(writeBackData)

        return m
