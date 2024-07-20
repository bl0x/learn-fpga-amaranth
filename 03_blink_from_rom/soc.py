from amaranth import *

from clockworks import Clockworks

class SOC(Elaboratable):

    def __init__(self):

        self.leds = Signal(5)

    def elaborate(self, platform):

        m = Module()

        cw = Clockworks(m, slow=21)
        m.submodules.cw = cw

        sequence = [
                0b00000,
                0b00001,
                0b00010,
                0b00100,
                0b01000,
                0b10000,
                0b10001,
                0b10010,
                0b10100,
                0b11000,
        ]

        pc = Signal(5)
        mem = Array([Signal(5, reset=x) for x in sequence])

        m.d.slow += pc.eq(Mux(pc == len(sequence), 0, pc + 1))
        m.d.comb += self.leds.eq(mem[pc])

        return m
