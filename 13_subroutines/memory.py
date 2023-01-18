from amaranth import *
from riscv_assembler import RiscvAssembler

class Memory(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        ADD x10, x0, x0

        l0:
        ADDI x10, x10, 1
        JAL x1, wait
        JAL zero, l0
        EBREAK

        wait:
        ADDI x11, x0, 1
        SLLI x11, x11, 15

        l1:
        ADDI x11, x11, -1
        BNE x11, x0, l1
        JALR x0, x1, 0
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
