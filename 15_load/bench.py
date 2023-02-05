from amaranth import *
from amaranth.sim import *

from soc import SOC

soc = SOC()

sim = Simulator(soc)

prev_clk = 0

def proc():
    cpu = soc.cpu
    mem = soc.memory
    while True:
        global prev_clk
        clk = yield soc.slow_clk
        if prev_clk == 0 and prev_clk != clk:
            state = (yield soc.cpu.fsm.state)
            if state == 2:
                print("-- NEW CYCLE -----------------------")
                print("  F: LEDS = {:05b}".format((yield soc.leds)))
                print("  F: pc={}".format((yield cpu.pc)))
                print("  F: instr={:#032b}".format((yield cpu.instr)))
                if (yield cpu.isALUreg):
                    print("     ALUreg rd={} rs1={} rs2={} funct3={}".format(
                        (yield cpu.rdId), (yield cpu.rs1Id), (yield cpu.rs2Id),
                        (yield cpu.funct3)))
                if (yield cpu.isALUimm):
                    print("     ALUimm rd={} rs1={} imm={} funct3={}".format(
                        (yield cpu.rdId), (yield cpu.rs1Id), (yield cpu.Iimm),
                        (yield cpu.funct3)))
                if (yield cpu.isBranch):
                    print("    BRANCH rs1={} rs2={}".format(
                        (yield cpu.rs1Id), (yield cpu.rs2Id)))
                if (yield cpu.isLoad):
                    print("    LOAD")
                if (yield cpu.isStore):
                    print("    STORE")
                if (yield cpu.isSystem):
                    print("    SYSTEM")
                    break
            if state == 4:
                print("  R: LEDS = {:05b}".format((yield soc.leds)))
                print("  R: rs1={}".format((yield cpu.rs1)))
                print("  R: rs2={}".format((yield cpu.rs2)))
            if state == 1:
                print("  E: LEDS = {:05b}".format((yield soc.leds)))
                print("  E: Writeback x{} = {:032b}".format((yield cpu.rdId),
                                             (yield cpu.writeBackData)))
            if state == 8:
                print("  NEW")
        yield
        prev_clk = clk

sim.add_clock(1e-6)
sim.add_sync_process(proc)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    # Let's run for a quite long time
    sim.run_until(2, )
