import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
import os
import random

@cocotb.test()
async def test_instruction_memory(dut):
    """
    Testbench for the InstructionMemory module.
    Verifies that the module correctly reads instructions from memory
    based on the provided address, matching the content of a dynamically
    generated instruction_memory.hex file.
    """

    # --- Testbench Parameters (must match design's derived parameters) ---
    # These parameters are derived from the design's default IMEM_DEPTH_WORDS=1024
    IMEM_DEPTH_WORDS = 1024
    INSTR_WIDTH = 32
    # ADDR_WIDTH is $clog2(IMEM_DEPTH_WORDS). For 1024, it's 10.
    # In Python, (N-1).bit_length() is equivalent to ceil(log2(N)) for N > 0.
    ADDR_WIDTH = (IMEM_DEPTH_WORDS - 1).bit_length() if IMEM_DEPTH_WORDS > 0 else 0

    dut._log.info(f"Testbench parameters: IMEM_DEPTH_WORDS={IMEM_DEPTH_WORDS}, "
                  f"INSTR_WIDTH={INSTR_WIDTH}, ADDR_WIDTH={ADDR_WIDTH}")

    # --- Generate instruction_memory.hex file ---
    # This file is read by the Verilog $readmemh function.
    hex_filename = "instruction_memory.hex"
    instruction_map = {} # Store expected values for verification

    dut._log.info(f"Generating {hex_filename} with {IMEM_DEPTH_WORDS} entries...")
    try:
        with open(hex_filename, "w") as f:
            for i in range(IMEM_DEPTH_WORDS):
                # Create a predictable instruction pattern
                # Ensure the instruction fits within INSTR_WIDTH bits
                instruction = (i * 0xDEADBEEF + 0xCAFEF00D) & ((1 << INSTR_WIDTH) - 1)
                f.write(f"{instruction:0{INSTR_WIDTH//4}x}\n")
                instruction_map[i] = instruction
        dut._log.info(f"Successfully generated {hex_filename}.")
    except IOError as e:
        dut._log.error(f"Failed to create {hex_filename}: {e}")
        raise

    # --- Start Clock (even if not strictly used by combinational ROM) ---
    # Cocotb simulations often benefit from a clock, and it's good practice.
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # --- Initial Reset/Wait for $readmemh to complete ---
    # Give the simulation some time for the initial block ($readmemh) to execute
    # and for the memory to be populated.
    await Timer(100, units="ns")
    dut._log.info("Simulation initialized. Starting memory reads.")

    # --- Test Scenarios ---

    # 1. Test specific, important addresses
    test_addresses = [
        0,                                  # First address
        1,                                  # Second address
        IMEM_DEPTH_WORDS // 2,              # Middle address
        IMEM_DEPTH_WORDS - 1,               # Last address
        IMEM_DEPTH_WORDS // 4,              # Quarter address
        IMEM_DEPTH_WORDS * 3 // 4           # Three-quarter address
    ]

    for addr in test_addresses:
        if addr >= IMEM_DEPTH_WORDS: # Skip if depth is too small for some test addresses
            continue

        dut._log.info(f"Testing specific address: {addr}")
        dut.addr.value = addr
        await Timer(1, units="ns") # Allow combinational logic to propagate

        expected_instr = instruction_map[addr]
        actual_instr = dut.instr_out.value.integer

        dut._log.info(f"  Address: {addr}, Expected: 0x{expected_instr:0{INSTR_WIDTH//4}x}, "
                      f"Actual: 0x{actual_instr:0{INSTR_WIDTH//4}x}")
        assert actual_instr == expected_instr, \
            f"Mismatch at address {addr}: Expected 0x{expected_instr:x}, Got 0x{actual_instr:x}"

    # 2. Test a selection of random addresses
    dut._log.info("Testing a selection of random addresses...")
    random.seed(42) # For reproducibility of random tests
    num_random_tests = min(50, IMEM_DEPTH_WORDS) # Test up to 50 random addresses

    for _ in range(num_random_tests):
        addr = random.randint(0, IMEM_DEPTH_WORDS - 1)

        dut._log.info(f"Testing random address: {addr}")
        dut.addr.value = addr
        await Timer(1, units="ns") # Allow combinational logic to propagate

        expected_instr = instruction_map[addr]
        actual_instr = dut.instr_out.value.integer

        dut._log.info(f"  Address: {addr}, Expected: 0x{expected_instr:0{INSTR_WIDTH//4}x}, "
                      f"Actual: 0x{actual_instr:0{INSTR_WIDTH//4}x}")
        assert actual_instr == expected_instr, \
            f"Mismatch at random address {addr}: Expected 0x{expected_instr:x}, Got 0x{actual_instr:x}"

    dut._log.info("All instruction memory read tests passed!")

    # --- Cleanup ---
    # Remove the generated hex file after the test
    try:
        os.remove(hex_filename)
        dut._log.info(f"Cleaned up {hex_filename}.")
    except OSError as e:
        dut._log.warning(f"Could not remove {hex_filename}: {e}")