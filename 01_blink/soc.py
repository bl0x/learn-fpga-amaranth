from amaranth import *

# Any Elaboratable class is used to generate HDL output
class SOC(Elaboratable):

    def __init__(self):

        # A Signal is usually created with its number of bits (default = 1).
        # Signals declared as instance variables (self.*) are accessible
        # from outside the class (either as input or output).
        # These signals define the external interface of the module.
        self.leds = Signal(5)

    def elaborate(self, platform):

        # Create a new Amaranth module
        m = Module()

        # This is a local signal, which will not be accessible from outside.
        count = Signal(5)

        # In the sync domain all logic is clocked at the positive edge of
        # the implicit clk signal.
        m.d.sync += count.eq(count + 1)

        # The comb domain contains logic that is unclocked and purely
        # combinatorial.
        m.d.comb += self.leds.eq(count)

        return m
