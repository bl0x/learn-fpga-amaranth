from amaranth import *
from riscv_assembler import RiscvAssembler

class Memory(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        ADD x1, x0, x0
        ADDI x2, x0, 31
        l0:
        ADDI x1, x1, 1
        BNE x1, x2, l0
        EBREAK
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
