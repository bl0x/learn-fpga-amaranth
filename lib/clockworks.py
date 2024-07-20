from amaranth import Signal, Module, ClockDomain, ClockSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

# This module handles clock division and provides a new 'slow' clock domain

clockworks_domain_name = "slow"

class Clockworks(wiring.Component):

    o_slow: Out(1)

    def __init__(self, module, slow=0, sim_slow=None):

        # Since amaranth 0.6 clock domains do not propagate upwards (RFC59)
        module.domains += ClockDomain(clockworks_domain_name)

        # Since the module provides a new clock domain, which is accessible
        # via the top level module, we don't need to explicitly provide the
        # slow clock signal as an output.

        self.slow = slow
        if sim_slow is None:
            self.sim_slow = slow
        else:
            self.sim_slow = sim_slow

        super().__init__()

    def elaborate(self, platform):

        o_clk = Signal()
        m = Module()

        if self.slow != 0:
            # When the design is simulated, platform is None
            if platform is None:
                # Have the simulation run at a different speed than the
                # actual hardware (usually faster).
                slow_bit = self.sim_slow
            else:
                slow_bit = self.slow

            slow_clk = Signal(slow_bit + 1)
            m.d.sync += slow_clk.eq(slow_clk + 1)
            m.d.comb += o_clk.eq(slow_clk[slow_bit])

        else:
            # When no division is requested, just use the clock signal of
            # the default 'sync' domain.
            m.d.comb += o_clk.eq(ClockSignal("sync"))

        # Create the new clock domain
        m.domains += ClockDomain("slow")

        # Assign the slow clock to the clock signal of the new domain
        m.d.comb += ClockSignal("slow").eq(o_clk)

        return m
