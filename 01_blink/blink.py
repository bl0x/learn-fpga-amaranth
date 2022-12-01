from amaranth import *
from amaranth_boards.arty_a7 import *

# Any Elaboratable class is used to generate HDL output
class Blink(Elaboratable):

    def elaborate(self, platform):

        # Get access to the 'led' resource defined by the board definition
        # from amaranth-boards.
        led0 = platform.request('led', 0)

        # Create a new module
        m = Module()

        # A Signal is usually created with its number of bits (default = 1).
        count = Signal(5)

        # In the sync domain all logic is clocked at the positive edge of
        # the implicit clk signal.
        m.d.sync += count.eq(count + 1)

        # The comb domain contains logic that is unclocked and purely
        # combinatorial.
        m.d.comb += led0.o.eq(count)

        return m

if __name__ == "__main__":
    platform = ArtyA7_35Platform(toolchain="Symbiflow")
    platform.build(Blink(), do_program=False)
