from amaranth import *
from amaranth.sim import *

from soc import SOC

soc = SOC()

prev_leds = 0

async def testbench(ctx):
    global prev_leds
    while True:
        leds = ctx.get(soc.leds)
        if leds != prev_leds:
            print("LEDS = {:05b}".format(leds))
            prev_leds = leds
        await ctx.tick()

sim = Simulator(soc)
sim.add_clock(1e-6)
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd'):
    sim.run_until(2e-5)
