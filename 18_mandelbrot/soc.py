import sys
from amaranth import *

from clockworks import Clockworks
from memory import Mem
from cpu import CPU
from uart_tx import UartTx

class SOC(Elaboratable):

    def __init__(self):

        self.leds = Signal(5)
        self.tx = Signal()

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

    def elaborate(self, platform):

        clk_frequency = int(platform.default_clk_constraint.frequency)
        print("clock frequency = {}".format(clk_frequency))

        m = Module()
        cw = Clockworks()
        memory = DomainRenamer("slow")(Mem())
        cpu = DomainRenamer("slow")(CPU())
        uart_tx = DomainRenamer("slow")(
                UartTx(freq_hz=clk_frequency, baud_rate=1000000))

        m.submodules.cw = cw
        m.submodules.cpu = cpu
        m.submodules.memory = memory
        m.submodules.uart_tx = uart_tx

        self.cpu = cpu
        self.memory = memory

        ram_rdata = Signal(32)
        mem_wordaddr = Signal(30)
        isIO = Signal()
        isRAM = Signal()
        mem_wstrb = Signal()
        io_rdata = Signal(32)

        # Memory map bits
        IO_LEDS_bit = 0
        IO_UART_DAT_bit = 1
        IO_UART_CNTL_bit = 2

        m.d.comb += [
            mem_wordaddr.eq(cpu.mem_addr[2:32]),
            isIO.eq(cpu.mem_addr[22]),
            isRAM.eq(~isIO),
            mem_wstrb.eq(cpu.mem_wmask.any())
        ]

        self.mem_wdata = cpu.mem_wdata

        # Connect memory to CPU
        m.d.comb += [
            memory.mem_addr.eq(cpu.mem_addr),
            memory.mem_rstrb.eq(isRAM & cpu.mem_rstrb),
            memory.mem_wdata.eq(cpu.mem_wdata),
            memory.mem_wmask.eq(Repl(isRAM, 4) & cpu.mem_wmask),
            ram_rdata.eq(memory.mem_rdata),
            cpu.mem_rdata.eq(Mux(isRAM, ram_rdata, io_rdata))
        ]

        # LEDs
        with m.If(isIO & mem_wstrb & mem_wordaddr[IO_LEDS_bit]):
            m.d.sync += self.leds.eq(cpu.mem_wdata)

        # UART
        uart_valid = Signal()
        self.uart_valid = uart_valid
        uart_ready = Signal()

        m.d.comb += [
            uart_valid.eq(isIO & mem_wstrb & mem_wordaddr[IO_UART_DAT_bit])
        ]

        # Hook up UART
        m.d.comb += [
            uart_tx.valid.eq(uart_valid),
            uart_tx.data.eq(cpu.mem_wdata[0:8]),
            uart_ready.eq(uart_tx.ready),
            self.tx.eq(uart_tx.tx)
        ]

        # Data from UART
        m.d.comb += [
            io_rdata.eq(Mux(mem_wordaddr[IO_UART_CNTL_bit],
                Cat(C(0, 9), ~uart_ready, C(0, 22)), C(0, 32)))
        ]


        # Export signals for simulation
        def export(signal, name):
            if type(signal) is not Signal:
                newsig = Signal(signal.shape(), name = name)
                m.d.comb += newsig.eq(signal)
            else:
                newsig = signal
            self.ports.append(newsig)
            setattr(self, name, newsig)

        if platform is None:
            export(ClockSignal("slow"), "slow_clk")
            #export(pc, "pc")
            #export(instr, "instr")
            #export(isALUreg, "isALUreg")
            #export(isALUimm, "isALUimm")
            #export(isBranch, "isBranch")
            #export(isJAL, "isJAL")
            #export(isJALR, "isJALR")
            #export(isLoad, "isLoad")
            #export(isStore, "isStore")
            #export(isSystem, "isSystem")
            #export(rdId, "rdId")
            #export(rs1Id, "rs1Id")
            #export(rs2Id, "rs2Id")
            #export(Iimm, "Iimm")
            #export(Bimm, "Bimm")
            #export(Jimm, "Jimm")
            #export(funct3, "funct3")
            #export(rdId, "rdId")
            #export(rs1, "rs1")
            #export(rs2, "rs2")
            #export(writeBackData, "writeBackData")
            #export(writeBackEn, "writeBackEn")
            #export(aluOut, "aluOut")
            #export((1 << cpu.fsm.state), "state")

        return m
