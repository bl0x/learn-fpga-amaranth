from amaranth import *
from amaranth.sim import *

from soc import SOC

soc = SOC()

prev_clk = 0

async def testbench(ctx):
    while True:
        global prev_clk
        clk = ctx.get(soc.slow_clk)
        if prev_clk == 0 and prev_clk != clk:
            print("pc={}".format(ctx.get(soc.pc)))
            print("instr={:#032b}".format(ctx.get(soc.instr)))
            print("LEDS = {:05b}".format(ctx.get(soc.leds)))
            if ctx.get(soc.isALUreg):
                print("ALUreg rd={} rs1={} rs2={} funct3={}".format(
                    ctx.get(soc.rdId), ctx.get(soc.rs1Id), ctx.get(soc.rs2Id),
                    ctx.get(soc.funct3)))
            if ctx.get(soc.isALUimm):
                print("ALUimm rd={} rs1={} imm={} funct3={}".format(
                    ctx.get(soc.rdId), ctx.get(soc.rs1Id), ctx.get(soc.Iimm),
                    ctx.get(soc.funct3)))
            if ctx.get(soc.isLoad):
                print("LOAD")
            if ctx.get(soc.isStore):
                print("STORE")
            if ctx.get(soc.isSystem):
                print("SYSTEM")
                break
        await ctx.tick()
        prev_clk = clk

sim = Simulator(soc)
sim.add_clock(1e-6)
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    # Let's run for a quite long time
    sim.run_until(2, )
