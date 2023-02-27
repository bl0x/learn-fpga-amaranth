from amaranth import *
from riscv_assembler import RiscvAssembler

class Mem(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:

        mandel_shift    equ 10
        mandel_shift_m1 equ  9
        mandel_mul      equ 1024    ; (1 << mandel_shift)
        xmin            equ -2048   ; (-2 * mandel_mul)
        xmax            equ 2028    ; ( 2 * mandel_mul)
        ymin            equ -2048   ; (-2 * mandel_mul)
        ymax            equ 2028    ; ( 2 * mandel_mul)
        dx              equ 51      ; (xmax - xmin) / 80
        dy              equ 51      ; (ymax - ymin) / 80
        norm_max        equ 4096    ; (4 << mandel_shift)
        io_leds         equ 4       ; (2 + 2)
        slow_bit        equ 18      ; wait (1 << 18) clocks

        LI      sp, 0x1800          ; end of RAM, 6 kB
        LI      gp, 0x400000        ; IO page

        J       mandelstart

        colormap:
        DATAB   " ", ".", ",", ":"
        DATAB   ";", "o", "x", "%"
        DATAB   "#", "@", 0, 0

        mandelstart:

        LI      s0, 5               ; blink 5 times
        blink:
        LI      a0, 5
        SW      a0, gp, io_leds
        CALL    wait
        LI      a0, 10
        SW      a0, gp, io_leds
        CALL    wait
        ADDI    s0, s0, -1
        BNEZ    s0, blink
        LI      a0, 0
        SW      a0, gp, io_leds

        LI      s1, 0
        LI      s3, xmin
        LI      s11, 80

        loop_y:
        LI      s0, 0
        LI      s2, ymin ; (bug in LI?)

        loop_x:
        MV      s4, s2                  ; z <- c
        MV      s5, s3

        LI      s10, 9                  ; iter <- 9


        loop_z:
        MV      a0, s4
        MV      a1, s4
        CALL    mulsi3
        SRLI    s6, a0, mandel_shift    ; Zrr <- (Zr*Zr) >> mandel_shift
        MV      a0, s4
        MV      a1, s5
        CALL    mulsi3
        SRLI    s7, a0, mandel_shift_m1 ; Zri <- (Zr*Zi) >> (mandelshift-1)
        MV      a0, s5
        MV      a1, s5
        CALL    mulsi3
        SRLI    s8, a0, mandel_shift    ; Zii <- (Zi*Zi) >> mandelshift
        SUB     s4, s6, s8              ; Zr <- Zrr - Zii + Cr
        ADD     s4, s4, s2
        ADD     s5, s7, s3              ; Zi <- 2*Zri + cr

        ADD     s6, s6, s8              ; Exit, if norm > norm_max
        LI      s7, norm_max
        BGT     s6, s7, exit_z

        ADDI    s10, s10, -1            ; iter--
        BNEZ    s10, loop_z


        exit_z:
        LI      a0, colormap            ; choose color
        ADD     a0, a0, s10
        LBU     a0, a0, 0
        CALL    putc

        ADDI    s0, s0, 1               ; Increase x-counter
        ADDI    s2, s2, dx
        BNE     s0, s11, loop_x

        LI      a0, 13                  ; Send line ending
        CALL    putc
        LI      a0, 10
        CALL    putc

        ADDI    s1, s1, 1               ; Increase y-counter
        ADDI    s3, s3, dy
        BNE     s1, s11, loop_y

        J       mandelstart

        EBREAK

        wait:
        LI      t0, 1
        SLLI    t0, t0, slow_bit
        wait_loop:
        ADDI    t0, t0, -1
        BNEZ    t0, wait_loop
        RET

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
