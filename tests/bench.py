from amaranth import *
from amaranth.sim import *
from ctypes import c_int32 as int32

from soc import SOC

soc = SOC()

sim = Simulator(soc)

def proc():
    cpu = soc.cpu
    mem = soc.memory
    prev_pc = 0
    while True:
        pc = yield cpu.pc
        uart_valid = (yield soc.uart_valid)
        if uart_valid:
            print("out: '{}'".format(chr((yield soc.mem_wdata[0:8]))))
        rdata = (yield mem.mem_rdata)
        if prev_pc != pc:
            prev_pc = pc
            if rdata == 0b00000000000000000000000000110011:
                print("pc=0x{:04x}={:4d} NOP!".format(pc, pc))
                for i in range(5):
                    reg = (yield cpu.regs[10 + i])
                    regi = int32(reg).value
                    print("   a{} = {}={}".format(i, regi, hex(reg)))

        yield

sim.add_clock(1e-6)
sim.add_sync_process(proc)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    # Let's run for a quite long time
    sim.run_until(2, )
