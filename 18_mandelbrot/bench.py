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
    n_nops = 0
    while True:
        pc = yield cpu.pc
        uart_valid = (yield soc.uart_valid)
        if uart_valid:
            print("out: '{}'".format(chr((yield soc.mem_wdata[0:8]))))
        rdata = (yield mem.mem_rdata)
        if prev_pc != pc:
            prev_pc = pc
            if rdata == 0b00000000000000000000000000110011:
                print("NOP {:03d}: pc=0x{:04x}={:4d}".format(n_nops, pc, pc))
                n_nops += 1
                for i in range(5):
                    reg = (yield cpu.regs[10 + i])
                    regi = int32(reg).value
                    print("   a{} = {}={}".format(i, regi, hex(reg)))
                for i in range(2):
                    reg = (yield cpu.regs[8 + i])
                    regi = int32(reg).value
                    print("   s{} = {}={}".format(i, regi, hex(reg)))
                for i in range(0,10):
                    reg = (yield cpu.regs[18 + i])
                    regi = int32(reg).value
                    print("   s{} = {}={}".format(i+2, regi, hex(reg)))

        yield

sim.add_clock(1e-6)
sim.add_sync_process(proc)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    # Let's run for a quite long time
    sim.run_until(2, )
