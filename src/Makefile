all: blinker.bram.elf

AS := riscv64-unknown-elf-as
LD := riscv64-unknown-elf-ld
ASFLAGS := -march=rv32i -mabi=ilp32 -mno-relax
LDFLAGS := -T bram.ld -m elf32lriscv -nostdlib -norelax

%.o: %.S
	$(AS) $(ASFLAGS) $< -o $@

blinker.bram.elf: start.o blinker.o wait.o
	$(LD) $(LDFLAGS) $^ -o $@

clean:
	rm *.o
	rm *.bram.elf
