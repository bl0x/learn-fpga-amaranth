from amaranth import *

import sys

class Top(Elaboratable):
    def __init__(self, leds):
        if len(sys.argv) == 1:
            print("Usage: {} step_number".format(sys.argv[0]))
            exit(1)
        step = int(sys.argv[1])
        print("step = {}".format(step))
        self.leds = leds

        if step == 1:
            path = "01_blink"
        if step == 2:
            path = "02_slower_blinky"
        else:
            print("Invalid step_number {}.".format(step))
            exit(1)
        sys.path.append(path)
        from soc import SOC
        self.soc = SOC()

    def elaborate(self, platform):
        m = Module()
        soc = self.soc
        leds = self.leds
        m.submodules.soc = soc

        # We connect the SOC leds signal to the various LEDs on the board.
        m.d.comb += [
            leds[0].o.eq(soc.leds[0]),
            leds[1].o.eq(soc.leds[1]),
            leds[2].o.eq(soc.leds[2]),
            leds[3].o.eq(soc.leds[3]),
            leds[4].o.eq(soc.leds[4]),
        ]

        return m
