from amaranth import *
from riscv_assembler import RiscvAssembler

class Memory(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        LI sp, 0x1800
        LI gp, 0x400000

        l0:
        LI s0, 16
        LI a0, 0

        l1:
        SW a0, gp, 4
        CALL wait
        ADDI a0, a0, 1
        BNE a0, s0, l1

        LI s0, 26
        LI a0, "a"
        LI s1, 0

        l2:
        CALL putc
        ADDI a0, a0, 1
        ADDI s1, s1, 1
        BNE s1, s0, l2

        LI a0, 13
        CALL putc
        LI a0, 10
        CALL putc

        J l0

        EBREAK

        wait:
        LI t0, 1
        SLLI t0, t0, 20

        wait_loop:
        ADDI t0, t0, -1
        BNEZ t0, wait_loop
        RET

        putc:
        SW a0, gp, 8
        LI t0, 0x200
        putc_loop:
        LW t1, gp, 0x10
        AND t1, t1, t0
        BNEZ t1, putc_loop
        RET
        """)

        a.assemble()
        self.instructions = a.mem

        # Add 0 memory up to offset 1024 / word 256
        while len(self.instructions) < (1024 * 6 / 4):
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
