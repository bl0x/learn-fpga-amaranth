from amaranth_boards.cmod_a7 import *

from top import Top

if __name__ == "__main__":
    platform = CmodA7_35Platform(toolchain="Symbiflow")

    # The platform allows access to the various resources defined
    # by the board definition from amaranth-boards.
    led0 = platform.request('led', 0)
    led1 = platform.request('led', 1)
    rgb = platform.request('rgb_led')
    leds = [led0, led1, rgb.r, rgb.g, rgb.b]

    platform.build(Top(leds), do_program=True)
