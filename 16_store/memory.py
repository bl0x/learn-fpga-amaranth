from amaranth import *
from riscv_assembler import RiscvAssembler

class Memory(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        LI  a0, 0
        LI  s1, 16
        LI  s0, 0

        l0:
        LB  a1, s0, 400
        SB  a1, s0, 800
        CALL wait
        ADDI s0, s0, 1
        BNE s0, s1, l0

        LI s0, 0

        l1:
        LB a0, s0, 800
        CALL wait
        ADDI s0, s0, 1
        BNE s0, s1, l1
        EBREAK

        wait:
        LI t0, 1
        SLLI t0, t0, 3

        l2:
        ADDI t0, t0, -1
        BNEZ t0, l2
        RET
        """)

        a.assemble()
        self.instructions = a.mem

        # Add some data at offset 400 / word 100
        while len(self.instructions) < 100:
            self.instructions.append(0)
        self.instructions.append(0x04030201)
        self.instructions.append(0x08070605)
        self.instructions.append(0x0c0b0a09)
        self.instructions.append(0xff0f0e0d)
        # Add 0 memory up to offset 1024 / word 256
        while len(self.instructions) < 256:
            self.instructions.append(0)

        print("memory = {}".format(self.instructions))

        # Instruction memory initialised with above instructions
        self.mem = Array([Signal(32, reset=x, name="mem{}".format(i))
                          for i,x in enumerate(self.instructions)])

        self.mem_addr = Signal(32)
        self.mem_rdata = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_wdata = Signal(32)
        self.mem_wmask = Signal(4)

    def elaborate(self, platform):
        m = Module()

        word_addr = self.mem_addr[2:32]

        with m.If(self.mem_rstrb):
            m.d.sync += self.mem_rdata.eq(self.mem[word_addr])
        with m.If(self.mem_wmask[0]):
            m.d.sync += self.mem[word_addr][0:8].eq(self.mem_wdata[0:8])
        with m.If(self.mem_wmask[1]):
            m.d.sync += self.mem[word_addr][8:16].eq(self.mem_wdata[8:16])
        with m.If(self.mem_wmask[2]):
            m.d.sync += self.mem[word_addr][16:24].eq(self.mem_wdata[16:24])
        with m.If(self.mem_wmask[3]):
            m.d.sync += self.mem[word_addr][24:32].eq(self.mem_wdata[24:32])

        return m
