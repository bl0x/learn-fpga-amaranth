from amaranth import *
from riscv_assembler import RiscvAssembler

class Mem(Elaboratable):

    def __init__(self, simulation = False):
        self.simulation = simulation

        a = RiscvAssembler(simulation=simulation)
        a.read(a.testCode())
        a.assemble()

        self.instructions = a.mem

        print("memory = {}".format(self.instructions))

        # Instruction memory initialised with above instructions
        self.mem = Memory(width=32, depth=len(self.instructions),
                          init=self.instructions, name="mem")

        self.mem_addr = Signal(32)
        self.mem_rdata = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_wdata = Signal(32)
        self.mem_wmask = Signal(4)

    def elaborate(self, platform):
        m = Module()

        # Using the memory module from amaranth library,
        # we can use write_port and read_port to easily instantiate
        # platform specific primitives to access memory efficiently.
        w_port = m.submodules.w_port = self.mem.write_port(
            domain="sync", granularity=8
        )
        r_port = m.submodules.r_port = self.mem.read_port(
            domain="sync", transparent=False
        )

        word_addr = self.mem_addr[2:32]

        # Hook up read port
        m.d.comb += [
            r_port.addr.eq(word_addr),
            r_port.en.eq(self.mem_rstrb),
            self.mem_rdata.eq(r_port.data)
        ]

        # Hook up write port
        m.d.comb += [
            w_port.addr.eq(word_addr),
            w_port.en.eq(self.mem_wmask),
            w_port.data.eq(self.mem_wdata)
        ]

        return m
