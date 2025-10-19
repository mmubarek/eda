import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.binary import BinaryValue
import random

# Helper function for a robust, synchronous reset
async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.mem_write_en.value = 0
    dut.addr.value = 0
    dut.write_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)
    dut._log.info("DUT reset.")

@cocotb.test()
async def test_data_memory_combinational_read(dut):
    """
    Test for a DataMemory module with a combinational (asynchronous) read
    and a synchronous write. This is the correct model for a single-cycle CPU.
    """
    
    # Start the clock
    cocotb.start_soon(cocotb.clock.Clock(dut.clk, 10, units="ns").start())

    # Reset the DUT
    await reset_dut(dut)

    # --- Test 1: Write a value and verify it was written ---
    dut._log.info("--- Test 1: Synchronous Write ---")
    test_addr = 5
    test_data = 0xDEADBEEF

    # Set up the write operation
    dut.addr.value = test_addr
    dut.write_data.value = test_data
    dut.mem_write_en.value = 1

    # Wait for the clock edge to perform the write
    await RisingEdge(dut.clk)

    # De-assert write enable to prevent accidental future writes
    dut.mem_write_en.value = 0
    await FallingEdge(dut.clk) # Allow signals to settle

    # --- Test 2: Verify Combinational Read ---
    dut._log.info("--- Test 2: Combinational Read Verification ---")
    
    # Set the address to the location we just wrote to
    dut.addr.value = test_addr
    
    # Because the read is combinational, the data should appear immediately
    # after a very short delay for propagation.
    await Timer(1, units="ns")

    assert dut.read_data.value == test_data, \
        f"Read verification failed! Expected {hex(test_data)}, got {hex(dut.read_data.value)}"
    dut._log.info("Read of written data successful.")

    # --- Test 3: Write Inhibit Test ---
    dut._log.info("--- Test 3: Write Inhibit ---")
    
    # Try to write new data to the same address with write enable LOW
    inhibit_data = 0xAAAAAAAA
    dut.addr.value = test_addr
    dut.write_data.value = inhibit_data
    dut.mem_write_en.value = 0 # Ensure write enable is off

    await RisingEdge(dut.clk) # Clock it

    # Check the data at the address. It should NOT have changed.
    dut.addr.value = test_addr
    await Timer(1, units="ns")
    
    assert dut.read_data.value == test_data, \
        f"Write inhibit failed! Data changed when mem_write_en was low."
    dut._log.info("Write inhibit test successful.")

    # --- Test 4: Back-to-back Combinational Reads ---
    dut._log.info("--- Test 4: Back-to-Back Reads ---")

    # Write a second value to a different address
    addr2 = 10
    data2 = 0x12345678
    dut.addr.value = addr2
    dut.write_data.value = data2
    dut.mem_write_en.value = 1
    await RisingEdge(dut.clk)
    dut.mem_write_en.value = 0
    await FallingEdge(dut.clk)

    # Read from the second address
    dut.addr.value = addr2
    await Timer(1, units="ns")
    assert dut.read_data.value == data2, "Read from second address failed"
    dut._log.info(f"Read from addr {addr2} successful.")

    # Immediately switch address and read from the first address
    dut.addr.value = test_addr
    await Timer(1, units="ns")
    assert dut.read_data.value == test_data, "Read from first address failed"
    dut._log.info(f"Immediate read from addr {test_addr} successful.")
    
    dut._log.info("All DataMemory tests passed successfully!")