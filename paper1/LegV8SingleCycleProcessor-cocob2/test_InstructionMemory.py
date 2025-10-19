import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
import random


@cocotb.test()
async def test_instruction_memory(dut):
    """
    Test the InstructionMemory module (byte-addressable version).
    Memory is pre-initialized in the testbench by writing two 8-bit halves per instruction.
    """

    # Start a dummy clock for consistency with the design
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    dut._log.info("Clock started.")

    # Initialize memory: write byte-by-byte (LSB and MSB stored separately)
    dut._log.info("Initializing byte-addressable instruction memory...")

    # Helper: write a 16-bit instruction as two bytes at address and address+1
    def write_instruction(addr, value16):
        high_byte = (value16 >> 8) & 0xFF
        low_byte = value16 & 0xFF
        dut.mem[addr].value = high_byte
        dut.mem[addr + 1].value = low_byte

    # Fill memory with pattern
    for i in range(0, 256, 2):  # Step 2 to avoid overlap of instruction bytes
        if i == 0:
            write_instruction(i, 0xAAAA)
        elif i == 10:
            write_instruction(i, 0xCCCC)
        elif i == 254:
            write_instruction(i, 0xDDDD)  # Edge case: 254 and 255
        else:
            write_instruction(i, i + 0x1000)

    dut._log.info("Memory initialized.")

    # Test cases: only even addresses (since each instruction uses 2 bytes)
    test_cases = [
        (0, 0xAAAA),
        (10, 0xCCCC),
        (100, 0x1064),   # 100 + 0x1000 = 0x1064
        (200, 0x10C8),
        (254, 0xDDDD),
    ]

    for addr_val, expected_instr in test_cases:
        dut.addr.value = addr_val
        await Timer(1, units="ns")  # settle combinational path
        actual_instr = dut.instruction.value.integer

        dut._log.info(
            f"ADDR={addr_val}: Expected=0x{expected_instr:04X}, Actual=0x{actual_instr:04X}"
        )
        assert actual_instr == expected_instr, \
            f"Mismatch at addr {addr_val}: expected 0x{expected_instr:04X}, got 0x{actual_instr:04X}"

    # Test 5 random even addresses (excluding special ones)
    for _ in range(5):
        while True:
            rand_addr = random.randrange(0, 254, 2)
            if rand_addr not in [0, 10, 254]:
                break
        expected = rand_addr + 0x1000
        dut.addr.value = rand_addr
        await Timer(1, units="ns")
        actual = dut.instruction.value.integer

        dut._log.info(
            f"Random ADDR={rand_addr}: Expected=0x{expected:04X}, Actual=0x{actual:04X}"
        )
        assert actual == expected, \
            f"Random mismatch at addr {rand_addr}: expected 0x{expected:04X}, got 0x{actual:04X}"

    dut._log.info("✅ All byte-addressable instruction memory tests passed.")
