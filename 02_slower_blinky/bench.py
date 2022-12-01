from amaranth import *
from amaranth.sim import *

from soc import SOC

soc = SOC()

sim = Simulator(soc)

prev_leds = 0

def proc():
    global prev_leds
    while True:
        leds = yield soc.leds
        if leds != prev_leds:
            print("LEDS = {:05b}".format(leds))
            prev_leds = leds
        yield

sim.add_clock(1e-6)
sim.add_sync_process(proc)

with sim.write_vcd('bench.vcd'):
    # Let's run for a quite long time
    sim.run_until(2)
