from amaranth import *
from amaranth.sim import *

from soc import SOC

soc = SOC()

sim = Simulator(soc)

def proc():
    cpu = soc.cpu
    mem = soc.memory
    while True:
        uart_valid = (yield soc.uart_valid)
        if uart_valid:
            print("out: '{}'".format(chr((yield soc.mem_wdata[0:8]))))
        yield

sim.add_clock(1e-6)
sim.add_sync_process(proc)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    # Let's run for a quite long time
    sim.run_until(2, )
