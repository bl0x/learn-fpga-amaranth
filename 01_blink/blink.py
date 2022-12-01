from amaranth import *
from amaranth_boards.arty_a7 import *

from soc import SOC

# A platform contains board specific information about FPGA pin assignments,
# toolchain and specific information for uploading the bitfile.
platform = ArtyA7_35Platform(toolchain="Symbiflow")

# We need a top level module
m = Module()

# This is the instance of our SOC
soc = SOC()

# The SOC is turned into a submodule (fragment) of our top level module.
m.submodules.soc = soc

# The platform allows access to the various resources defined by the board
# definition from amaranth-boards.
led0 = platform.request('led', 0)
led1 = platform.request('led', 1)
led2 = platform.request('led', 2)
led3 = platform.request('led', 3)
rgb = platform.request('rgb_led')

# We connect the SOC leds signal to the various LEDs on the board.
m.d.comb += [
    led0.o.eq(soc.leds[0]),
    led1.o.eq(soc.leds[1]),
    led1.o.eq(soc.leds[2]),
    led1.o.eq(soc.leds[3]),
    rgb.r.o.eq(soc.leds[4]),
]

# To generate the bitstream, we build() the platform using our top level
# module m.
platform.build(m, do_program=False)
