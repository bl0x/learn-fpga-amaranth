from amaranth_boards.arty_a7 import *

from top import Top

if __name__ == "__main__":
    platform = ArtyA7_35Platform(toolchain="Symbiflow")

    # The platform allows access to the various resources defined by the board
    # definition from amaranth-boards.
    led0 = platform.request('led', 0)
    led1 = platform.request('led', 1)
    led2 = platform.request('led', 2)
    led3 = platform.request('led', 3)
    rgb = platform.request('rgb_led')
    leds = [led0, led1, led2, led3, rgb.r]

    platform.build(Top(leds), do_program=True)

