from amaranth import *
from amaranth.sim import *

from soc import SOC

soc = SOC()

sim = Simulator(soc)

prev_pc = 0

def proc():
    while True:
        global prev_pc
        pc = yield soc.pc
        if prev_pc != pc:
            print("pc={}".format(pc))
            print("instr={:#032b}".format((yield soc.instr)))
            print("LEDS = {:05b}".format((yield soc.leds)))
            if (yield soc.isALUreg):
                print("ALUreg rd={} rs1={} rs2={} funct3={}".format(
                    (yield soc.rdId), (yield soc.rs1Id), (yield soc.Iimm),
                    (yield soc.funct3)))
            if (yield soc.isSystem):
                print("SYSTEM")
                break
        yield
        prev_pc = pc

sim.add_clock(1e-6)
sim.add_sync_process(proc)

with sim.write_vcd('bench.vcd'):
    # Let's run for a quite long time
    sim.run_until(2)
