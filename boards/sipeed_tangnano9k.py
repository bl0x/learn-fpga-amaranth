from amaranth_boards.tang_nano_9k import *
from amaranth.build import *

from top import Top

if __name__ == "__main__":
    platform = TangNano9kPlatform(toolchain="Gowin") # toolchain = (Gowin, Apicula)

    gpio = ("gpio", 0)
    platform.add_resources([
        Resource("uart", 1,
            Subsignal("rx", Pins("42", conn=gpio, dir='i')),
            Subsignal("tx", Pins("43", conn=gpio, dir='o')),
            Attrs(IO_TYPE="LVCMOS33")
        )])
    # The platform allows access to the various resources defined by the board
    # definition from amaranth-boards.
    led0 = platform.request('led', 0)
    led1 = platform.request('led', 1)
    led2 = platform.request('led', 2)
    led3 = platform.request('led', 3)
    led4 = platform.request('led', 4)
    leds = [led0, led1, led2, led3, led4]
    uart = platform.request('uart', 1)

    platform.build(Top(leds, uart), do_program=True)

