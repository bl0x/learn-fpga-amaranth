from amaranth import *
from amaranth.sim import *

from soc import SOC

soc = SOC()

sim = Simulator(soc)

prev_clk = 0

def proc():
    while True:
        global prev_clk
        clk = yield soc.slow_clk
        if prev_clk == 0 and prev_clk != clk:
            print("pc={}".format((yield soc.pc)))
            print("instr={:#032b}".format((yield soc.instr)))
            print("LEDS = {:05b}".format((yield soc.leds)))
            if (yield soc.isALUreg):
                print("ALUreg rd={} rs1={} rs2={} funct3={}".format(
                    (yield soc.rdId), (yield soc.rs1Id), (yield soc.rs2Id),
                    (yield soc.funct3)))
            if (yield soc.isALUimm):
                print("ALUimm rd={} rs1={} imm={} funct3={}".format(
                    (yield soc.rdId), (yield soc.rs1Id), (yield soc.Iimm),
                    (yield soc.funct3)))
            if (yield soc.isLoad):
                print("LOAD")
            if (yield soc.isStore):
                print("STORE")
            if (yield soc.isSystem):
                print("SYSTEM")
                break
        yield
        prev_clk = clk

sim.add_clock(1e-6)
sim.add_sync_process(proc)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    # Let's run for a quite long time
    sim.run_until(2, )
