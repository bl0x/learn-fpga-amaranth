from amaranth import *
from riscv_assembler import RiscvAssembler

class Memory(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        LI  a0, 0

        l0:
        ADDI a0, a0, 1
        CALL wait
        J    l0
        EBREAK

        wait:
        LI   a1, 1
        SLLI a1, a1, 20

        l1:
        ADDI a1, a1, -1
        BNEZ a1, l1
        RET
        """)

        a.assemble()
        self.instructions = a.mem
        print("memory = {}".format(self.instructions))

        # Instruction memory initialised with above instructions
        self.mem = Array([Signal(32, reset=x, name="mem")
                          for x in self.instructions])

        self.mem_addr = Signal(32)
        self.mem_rdata = Signal(32)
        self.mem_rstrb = Signal()

    def elaborate(self, platform):
        m = Module()

        with m.If(self.mem_rstrb):
            m.d.sync += self.mem_rdata.eq(self.mem[self.mem_addr[2:32]])

        return m
