from amaranth import *

# This module is designed after corescore_emitter_uart from Olof Kindgren
# https://gist.github.com/olofk/e91fba2572396f55525f8814f05fb33d

class UartTx(Elaboratable):

    def __init__(self, freq_hz=0, baud_rate=57600):
        self.freq_hz = freq_hz
        self.baud_rate = baud_rate

        # Inputs
        self.data = Signal(8)
        self.valid = Signal()

        # Outputs
        self.ready = Signal()
        self.tx = Signal()

    def elaborate(self, platform):

        start_value = self.freq_hz // self.baud_rate
        width = len(Const(start_value))

        print("UartTx: start_value = {}, width = {}".format(start_value, width))

        cnt = Signal(width+1)
        data = Signal(10)

        ready = self.ready
        valid = self.valid

        m = Module()

        m.d.comb += self.tx.eq(data[0] | ~(data.any()))

        with m.If(cnt[width] & ~(data.any())):
            m.d.sync += ready.eq(1)
        with m.Elif(valid & ready):
            m.d.sync += ready.eq(0)

        with m.If(ready | cnt[width]):
            # Cat needed ?
            m.d.sync += cnt.eq(start_value)
        with m.Else():
            m.d.sync += cnt.eq(cnt - 1)

        with m.If(cnt[width]):
            m.d.sync += data.eq(Cat(data[1:10], C(0, 1)))
        with m.Elif(valid & ready):
            m.d.sync += data.eq(Cat(C(0, 1), self.data, C(1, 1)))

        return m
