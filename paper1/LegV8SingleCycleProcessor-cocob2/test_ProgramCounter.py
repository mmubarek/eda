import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

@cocotb.test()
async def test_program_counter(dut):
    """Test the ProgramCounter module."""

    # Create a 10 ns period clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Initial values
    dut.rst.value = 0
    dut.pc_next_addr.value = 0

    # Wait a few clock cycles for initial settling
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    cocotb.log.info("--- Test Reset ---")
    # Assert reset
    dut.rst.value = 1
    dut.pc_next_addr.value = 0xAA # Should be ignored during reset, but will be latched on de-assertion if not changed
    await RisingEdge(dut.clk)
    assert dut.pc_out.value == 0, f"Reset failed: pc_out is {dut.pc_out.value}, expected 0"
    cocotb.log.info(f"After reset: pc_out = {dut.pc_out.value}")

    # De-assert reset
    dut.rst.value = 0
    # To ensure pc_out is 0 after reset de-assertion, pc_next_addr must be 0
    # when the first clock edge occurs after reset is de-asserted.
    # It was previously set to 0xAA, so set it back to 0.
    dut.pc_next_addr.value = 0 # FIX: Ensure pc_next_addr is 0 for a clean reset state
    await RisingEdge(dut.clk) # Wait one cycle after de-asserting reset
    assert dut.pc_out.value == 0, f"pc_out should be 0 after reset de-assertion: {dut.pc_out.value}"
    cocotb.log.info(f"After de-asserting reset: pc_out = {dut.pc_out.value}")

    cocotb.log.info("--- Test Basic Counting ---")
    # Test basic counting
    for i in range(1, 10):
        dut.pc_next_addr.value = i
        await RisingEdge(dut.clk)  # Value is sampled on this rising edge
        await RisingEdge(dut.clk)  # Now the output is updated
        assert dut.pc_out.value == i, f"Count failed: pc_out is {dut.pc_out.value}, expected {i}"
    
    cocotb.log.info("--- Test Specific Addresses ---")
    test_addresses = [0x10, 0x55, 0x00, 0xFF, 0x7F, 0x01]
    
    for addr in test_addresses:
        dut.pc_next_addr.value = addr
        await RisingEdge(dut.clk)  # Apply input
        await RisingEdge(dut.clk)  # Wait for output to update
        assert dut.pc_out.value == addr, f"Address {hex(addr)} failed: pc_out is {dut.pc_out.value}, expected {addr}"
        cocotb.log.info(f"pc_next_addr = {hex(addr)}, pc_out = {hex(dut.pc_out.value)}")


    cocotb.log.info("--- Test Reset during operation ---")
    # Test reset during operation
    dut.pc_next_addr.value = 0xBE
    await RisingEdge(dut.clk)  # 1st edge: latch value
    await RisingEdge(dut.clk)  # 2nd edge: output stable
    assert dut.pc_out.value == 0xBE, f"pc_out is {dut.pc_out.value}, expected 0xBE before reset"
    cocotb.log.info(f"pc_out before reset: {dut.pc_out.value}")

    dut.rst.value = 1
    await RisingEdge(dut.clk)
    assert dut.pc_out.value == 0, f"Reset during operation failed: pc_out is {dut.pc_out.value}, expected 0"
    cocotb.log.info(f"pc_out after reset during operation: {dut.pc_out.value}")

    dut.rst.value = 0
    dut.pc_next_addr.value = 0xDE
    await RisingEdge(dut.clk)  # 1st clock edge: pc_next_addr is latched
    await RisingEdge(dut.clk)  # 2nd clock edge: pc_out is updated
    assert dut.pc_out.value == 0xDE, f"pc_out is {dut.pc_out.value}, expected 0xDE after reset de-assertion"
    cocotb.log.info(f"pc_out after de-asserting reset: {dut.pc_out.value}")

    cocotb.log.info("--- Test Max Address ---")
    # Test max address
    dut.pc_next_addr.value = 0xFF
    await RisingEdge(dut.clk)  # Latch input
    await RisingEdge(dut.clk)  # Output updates
    assert dut.pc_out.value == 0xFF, f"Max address failed: pc_out is {dut.pc_out.value}, expected 0xFF"
    cocotb.log.info(f"pc_next_addr = 0xFF, pc_out = {dut.pc_out.value}")

    cocotb.log.info("--- Test Min Address ---")
    # Test min address (0 after a non-zero value)
    dut.pc_next_addr.value = 0x00
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk) 
    assert dut.pc_out.value == 0x00, f"Min address failed: pc_out is {dut.pc_out.value}, expected 0x00"
    cocotb.log.info(f"pc_next_addr = 0x00, pc_out = {dut.pc_out.value}")

    cocotb.log.info("--- Test Complete ---")
