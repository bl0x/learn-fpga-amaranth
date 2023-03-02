from amaranth_boards.arty_a7 import *
from amaranth.build import *

from top import Top

if __name__ == "__main__":
    platform = ArtyA7_35Platform(toolchain="Symbiflow")
    gpio = ("gpio", 0)
    platform.add_resources([
        Resource("uart", 1,
             Subsignal("tx", Pins("1", conn=gpio, dir='o')),
             Subsignal("rx", Pins("2", conn=gpio, dir='i')),
             Attrs(IOSTANDARD="LVCMOS33")
        )
    ])

    # The platform allows access to the various resources defined by the board
    # definition from amaranth-boards.
    led0 = platform.request('led', 0)
    led1 = platform.request('led', 1)
    led2 = platform.request('led', 2)
    led3 = platform.request('led', 3)
    rgb = platform.request('rgb_led')
    leds = [led0, led1, led2, led3, rgb.r]
    uart = platform.request('uart', 1)

    platform.build(Top(leds, uart), do_program=True)

