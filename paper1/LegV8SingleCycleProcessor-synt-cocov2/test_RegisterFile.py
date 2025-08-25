import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles
import random

@cocotb.test()
async def register_file_test(dut):
    """Test the RegisterFile module thoroughly."""

    # Parameters derived from the HDL module
    DATA_WIDTH = 8
    REG_ADDR_WIDTH = 3
    NUM_REGISTERS = 1 << REG_ADDR_WIDTH # 2^3 = 8 registers

    # Create a clock instance and start it
    clock = Clock(dut.clk, 10, units="ns") # 10ns period = 100MHz clock
    cocotb.start_soon(clock.start())

    # Keep a shadow model of the register file for verification
    # Initialize all shadow registers to 0, matching the reset behavior
    shadow_registers = [0] * NUM_REGISTERS

    cocotb.log.info("Starting RegisterFile test")

    # 1. Reset the DUT
    cocotb.log.info("Applying reset and verifying initial state.")
    dut.rst.value = 1
    dut.write_en.value = 0
    dut.write_addr.value = 0
    dut.write_data.value = 0
    dut.read_addr1.value = 0
    dut.read_addr2.value = 0

    await ClockCycles(dut.clk, 5) # Hold reset for a few clock cycles
    dut.rst.value = 0
    await RisingEdge(dut.clk) # Wait for reset to de-assert and first clock edge

    # Verify all registers are 0 after reset
    for i in range(NUM_REGISTERS):
        dut.read_addr1.value = i
        dut.read_addr2.value = i # Check both read ports
        await Timer(1, units="ns") # Allow combinatorial logic to settle
        assert dut.read_data1.value == 0, \
            f"ERROR: Register {i} (read_data1) not 0 after reset. Got {dut.read_data1.value}"
        assert dut.read_data2.value == 0, \
            f"ERROR: Register {i} (read_data2) not 0 after reset. Got {dut.read_data2.value}"
        shadow_registers[i] = 0 # Ensure shadow model is also reset to 0

    cocotb.log.info("Initial state verified: All registers are 0.")
    
    

    # 2. Basic Write and Read Test
    cocotb.log.info("Performing basic write and read test.")
    test_addr = 1
    test_data = 0xAA
    dut.write_en.value = 1
    dut.write_addr.value = test_addr
    dut.write_data.value = test_data
    await RisingEdge(dut.clk) # Write occurs on this rising edge
    shadow_registers[test_addr] = test_data # Shadow model updated *after* the clock edge

    # Read immediately after write (within the same clock cycle)
    dut.read_addr1.value = test_addr
    dut.read_addr2.value = test_addr
    await Timer(1, units="ns") # Allow combinatorial read outputs to settle
    assert dut.read_data1.value == test_data, \
        f"ERROR: Read data1 mismatch after write. Expected {hex(test_data)}, got {hex(dut.read_data1.value)}"
    assert dut.read_data2.value == test_data, \
        f"ERROR: Read data2 mismatch after write. Expected {hex(test_data)}, got {hex(dut.read_data2.value)}"

    # Read from an unwritten address (should still be 0)
    unwritten_addr = (test_addr + 1) % NUM_REGISTERS
    dut.read_addr1.value = unwritten_addr
    await Timer(1, units="ns")
    assert dut.read_data1.value == shadow_registers[unwritten_addr], \
        f"ERROR: Read data from unwritten register {unwritten_addr} mismatch. Expected {hex(shadow_registers[unwritten_addr])}, got {hex(dut.read_data1.value)}"
    cocotb.log.info(f"Basic write to R{test_addr} ({hex(test_data)}) and read verified.")

    # 3. Concurrent Writes and Reads (different addresses)
    cocotb.log.info("Testing concurrent writes and reads.")
    write_addr1 = 1
    write_data1 = 0x11
    write_addr2 = 2
    write_data2 = 0x22

    # Write to addr1
    dut.write_en.value = 1
    dut.write_addr.value = write_addr1
    dut.write_data.value = write_data1
    await RisingEdge(dut.clk)
    shadow_registers[write_addr1] = write_data1

    # Write to addr2
    dut.write_en.value = 1
    dut.write_addr.value = write_addr2
    dut.write_data.value = write_data2
    await RisingEdge(dut.clk)
    shadow_registers[write_addr2] = write_data2

    # Read both concurrently using different read ports
    dut.read_addr1.value = write_addr1
    dut.read_addr2.value = write_addr2
    await Timer(1, units="ns")
    assert dut.read_data1.value == write_data1, \
        f"ERROR: Concurrent read data1 mismatch. Expected {hex(write_data1)}, got {hex(dut.read_data1.value)}"
    assert dut.read_data2.value == write_data2, \
        f"ERROR: Concurrent read data2 mismatch. Expected {hex(write_data2)}, got {hex(dut.read_data2.value)}"
    cocotb.log.info(f"Concurrent writes to R{write_addr1} ({hex(write_data1)}) and R{write_addr2} ({hex(write_data2)}) and reads verified.")

    # 4. Overwriting a Register
    cocotb.log.info("Testing overwriting a register.")
    overwrite_addr = 2 
    overwrite_data = 0xCC
    dut.write_en.value = 1
    dut.write_addr.value = overwrite_addr
    dut.write_data.value = overwrite_data
    await RisingEdge(dut.clk)
    shadow_registers[overwrite_addr] = overwrite_data

    dut.read_addr1.value = overwrite_addr
    await Timer(1, units="ns")
    assert dut.read_data1.value == overwrite_data, \
        f"ERROR: Overwrite failed for R{overwrite_addr}. Expected {hex(overwrite_data)}, got {hex(dut.read_data1.value)}"
    cocotb.log.info(f"Overwrite of R{overwrite_addr} with {hex(overwrite_data)} verified.")

    # 5. No Write when write_en is low
    cocotb.log.info("Testing no write when write_en is low.")
    no_write_addr = 3
    no_write_data = 0xFF
    original_value = shadow_registers[no_write_addr] # Should be 0 from reset
    dut.write_en.value = 0 # Crucial: write_en is low
    dut.write_addr.value = no_write_addr
    dut.write_data.value = no_write_data
    await RisingEdge(dut.clk) # Clock edge, but no write should occur

    dut.read_addr1.value = no_write_addr
    await Timer(1, units="ns")
    assert dut.read_data1.value == original_value, \
        f"ERROR: Write occurred when write_en was low for R{no_write_addr}. Expected {hex(original_value)}, got {hex(dut.read_data1.value)}"
    assert dut.read_data1.value != no_write_data, \
        "ERROR: Data was written despite write_en being low!"
    cocotb.log.info(f"No write to R{no_write_addr} when write_en is low verified.")

    # 6. Fill all registers and verify
    cocotb.log.info("Filling all registers and verifying their contents.")
    dut.write_en.value = 1
    for i in range(NUM_REGISTERS):
        data_to_write = (i * 17 + 5) & ((1 << DATA_WIDTH) - 1)
        dut.write_addr.value = i
        dut.write_data.value = data_to_write
        dut.write_en.value = 1 if i != 0 else 0  # Don't write to R0
    
        await RisingEdge(dut.clk)
    
        # Update shadow model only if not R0
        if i != 0:
            shadow_registers[i] = data_to_write
        else:
            shadow_registers[i] = 0  # R0 always stays 0

    # Verify all registers by reading them back
    for i in range(NUM_REGISTERS):
        dut.read_addr1.value = i
        dut.read_addr2.value = (i + 1) % NUM_REGISTERS # Read another one concurrently
        await Timer(1, units="ns")
        assert dut.read_data1.value == shadow_registers[i], \
            f"ERROR: Verification failed for R{i} (read_data1). Expected {hex(shadow_registers[i])}, got {hex(dut.read_data1.value)}"
        assert dut.read_data2.value == shadow_registers[(i + 1) % NUM_REGISTERS], \
            f"ERROR: Verification failed for R{(i + 1) % NUM_REGISTERS} (read_data2). Expected {hex(shadow_registers[(i + 1) % NUM_REGISTERS])}, got {hex(dut.read_data2.value)}"
        cocotb.log.debug(f"Verified R{i} ({hex(shadow_registers[i])}) and R{(i + 1) % NUM_REGISTERS} ({hex(shadow_registers[(i + 1) % NUM_REGISTERS])})")
    cocotb.log.info("All registers filled and verified successfully.")

    # 7. Randomized Test
    cocotb.log.info("Starting randomized test (100 cycles).")
    
    for cycle in range(100):
        # 1. Determine write operation for the *upcoming* clock edge
        write_this_cycle = False
        write_addr_val = 1
        write_data_val = 0

        if random.random() < 0.6: # 60% chance to write
            write_this_cycle = True
            write_addr_val = random.randint(1, NUM_REGISTERS - 1)
            write_data_val = random.randint(1, (1 << DATA_WIDTH) - 1)
            dut.write_en.value = 1
            dut.write_addr.value = write_addr_val
            dut.write_data.value = write_data_val
            cocotb.log.debug(f"Cycle {cycle}: Setting inputs for write: addr={write_addr_val}, data={hex(write_data_val)}")
        else:
            dut.write_en.value = 0 # No write this cycle
            cocotb.log.debug(f"Cycle {cycle}: No write this cycle.")

        # 2. Set read addresses for the *current* cycle's verification.
        # These reads will reflect the state *after* the upcoming clock edge.
        read_addr1 = random.randint(0, NUM_REGISTERS - 1)
        read_addr2 = random.randint(0, NUM_REGISTERS - 1)
        dut.read_addr1.value = read_addr1
        dut.read_addr2.value = read_addr2

        # 3. Wait for the clock edge. This is when the DUT's write (if enabled) happens.
        await RisingEdge(dut.clk)

        # 4. Update shadow model *after* the clock edge if a write was enabled
        if write_this_cycle:
            shadow_registers[write_addr_val] = write_data_val

        # 5. Allow combinatorial logic for reads to settle *after* the clock edge
        await Timer(1, units="ns")

        # 6. Now verify the reads
        expected_data1 = shadow_registers[read_addr1]
        expected_data2 = shadow_registers[read_addr2]
        actual_data1 = dut.read_data1.value
        actual_data2 = dut.read_data2.value

        assert actual_data1 == expected_data1, \
            f"ERROR: Cycle {cycle}: Random Read1 mismatch at addr {read_addr1}. Expected {hex(expected_data1)}, got {hex(actual_data1)}"
        assert actual_data2 == expected_data2, \
            f"ERROR: Cycle {cycle}: Random Read2 mismatch at addr {read_addr2}. Expected {hex(expected_data2)}, got {hex(actual_data2)}"
        cocotb.log.debug(f"Cycle {cycle}: Random Read: addr1={read_addr1}, data1={hex(actual_data1)} (expected {hex(expected_data1)}) | "
                          f"addr2={read_addr2}, data2={hex(actual_data2)} (expected {hex(expected_data2)})")

    cocotb.log.info("Randomized test completed.")
    cocotb.log.info("RegisterFile test finished successfully!")

