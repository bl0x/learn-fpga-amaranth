from amaranth import Signal, Module
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

# Any wiring.Component class is used to generate HDL output
class SOC(wiring.Component):

    # Inputs and outputs are Signals that constitute the interface of a
    # Component. They are usually created with their number of bits
    # (default = 1).
    # Signals declared as In or Out are accessible via self.<name>
    # from inside the class.
    leds: Out(5)

    def __init__(self):
        # Call the parent constructor
        super().__init__()

    def elaborate(self, platform):

        # Create a new Amaranth module
        m = Module()

        # This is a local signal, which is not accessible from outside.
        count = Signal(5)

        # In the sync domain all logic is clocked at the positive edge of
        # the implicit clk signal.
        m.d.sync += count.eq(count + 1)

        # The comb domain contains logic that is unclocked and purely
        # combinational.
        m.d.comb += self.leds.eq(count)

        return m
