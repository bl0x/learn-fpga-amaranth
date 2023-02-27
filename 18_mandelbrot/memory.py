from amaranth import *
from riscv_assembler import RiscvAssembler

class Mem(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:

        mandel_shift    equ 10
        mandel_mul      equ 1024    ; (1 << mandel_shift)
        xmin            equ -2048   ; (-2 * mandel_mul)
        xmax            equ 2028    ; ( 2 * mandel_mul)
        ymin            equ -2048   ; (-2 * mandel_mul)
        ymax            equ 2028    ; ( 2 * mandel_mul)
        dx              equ 136     ; (xmax - xmin) / 30
        dy              equ 136     ; (ymax - ymin) / 30
        norm_max        equ 4096    ; (4 << mandel_shift)

        LI      gp, 0x400000        ; IO page

        LI      s1, 0
        LI      s3, xmin
        LI      s11, 80
        LI      s10, norm_max

        loop_y:
        LI      s0, 0
        LI      s2, ymin

        loop_x:
        MV      a0, s2
        MV      a1, s2
        CALL    mulsi3
        SRLI    s4, a0, mandel_shift    ; s4 = x*x
        MV      a0, s3
        MV      a1, s3
        CALL    mulsi3
        SRLI    s5, a0, mandel_shift    ; s5 = y*y
        ADD     s6, s4, s5              ; s6 = x*x + y*y
        LI      a0, "*"
        BLT     s6, s10, in_disk        ; if (x*x + y*y) < 4
        LI      a0, " "

        in_disk:
        CALL    putc

        ADDI    s0, s0, 1       ; Increase x-counter
        ADDI    s2, s2, dx
        BNE     s0, s11, loop_x

        LI      a0, 13          ; Send line ending
        CALL    putc
        LI      a0, 10
        CALL    putc

        ADDI    s1, s1, 1       ; Increase y-counter
        ADDI    s3, s3, dy
        BNE     s1, s11, loop_y

        EBREAK

        mulsi3:                 ; integer multiplication
        MV      a2, a0
        LI      a0, 0
        mulsi3_l0:
        ANDI    a3, a1, 1
        BEQZ    a3, mulsi3_l1
        ADD     a0, a0, a2
        mulsi3_l1:
        SRLI    a1, a1, 1
        SLLI    a2, a2, 1
        BNEZ    a1, mulsi3_l0
        RET

        putc:                   ; Send one character
        SW      a0, gp, 8       ; (1 << IO_UART_DAT_bit + 2)
        LI      t0, 0x200       ; Test bit 9 (status bit) below
        putc_loop:
        LW      t1, gp, 0x10    ; (1 << IO_UART_CNTL_bit + 2)
        AND     t1, t1, t0      ; Test
        BNEZ    t1, putc_loop
        RET
        """)

        a.assemble()
        self.instructions = a.mem

        # Add 0 memory up to offset 1024 / word 256
        while len(self.instructions) < (1024 * 6 / 4):
            self.instructions.append(0)

        print("memory = {}".format(self.instructions))

        # Instruction memory initialised with above instructions
        self.mem = Memory(width=32, depth=len(self.instructions),
                          init=self.instructions, name="mem")

        self.mem_addr = Signal(32)
        self.mem_rdata = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_wdata = Signal(32)
        self.mem_wmask = Signal(4)

    def elaborate(self, platform):
        m = Module()

        # Using the memory module from amaranth library,
        # we can use write_port and read_port to easily instantiate
        # platform specific primitives to access memory efficiently.
        w_port = m.submodules.w_port = self.mem.write_port(
            domain="sync", granularity=8
        )
        r_port = m.submodules.r_port = self.mem.read_port(
            domain="sync", transparent=False
        )

        word_addr = self.mem_addr[2:32]

        # Hook up read port
        m.d.comb += [
            r_port.addr.eq(word_addr),
            r_port.en.eq(self.mem_rstrb),
            self.mem_rdata.eq(r_port.data)
        ]

        # Hook up write port
        m.d.comb += [
            w_port.addr.eq(word_addr),
            w_port.en.eq(self.mem_wmask),
            w_port.data.eq(self.mem_wdata)
        ]

        return m
