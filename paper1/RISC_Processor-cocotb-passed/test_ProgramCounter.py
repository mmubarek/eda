import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

@cocotb.test()
async def test_program_counter(dut):
    """Robust test for ProgramCounter."""

    # Start 10ns period clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # 1. APPLY AND VERIFY RESET
    dut._log.info("Applying reset")
    dut.rst_n.value = 0
    dut.pc_next_sel.value = 0b10  # Hold during reset
    dut.branch_target_addr.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.pc_out.value) == 0, f"FAIL: PC should be 0 after reset, got {int(dut.pc_out.value)}"
    dut._log.info("✅ PC is 0 in reset")

    # 2. DEASSERT RESET
    # We will keep the inputs on 'Hold' and just deassert reset.
    dut._log.info("Deasserting reset")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    # The first clock edge after reset deassertion, the PC latches the value determined
    # by the inputs during reset ('Hold' from 0 -> 0).
    assert int(dut.pc_out.value) == 0, f"FAIL: PC should still be 0 on first cycle out of reset, got {int(dut.pc_out.value)}"
    dut._log.info(f"✅ PC is stable at {int(dut.pc_out.value)} after leaving reset")

    # 3. TEST FIRST INCREMENT using the ROBUST PATTERN
    dut._log.info("Testing first increment")
    
    # THE CRITICAL FIX:
    await FallingEdge(dut.clk)  # a) Wait for falling edge (middle of clock cycle)

    dut.pc_next_sel.value = 0b00  # b) Apply stimulus (set to Increment)
    
    await Timer(1, units="ns")  # <--- c) Let the combinational logic settle

    await RisingEdge(dut.clk)   # d) Wait for the latching edge
    await RisingEdge(dut.clk)

    # e) Now check the result
    assert int(dut.pc_out.value) == 4, f"FAIL: Expected PC=4, got {int(dut.pc_out.value)}"


    # Next increment: PC = 8
    # Since the input is already 'Increment', we just need to wait for the next edge.
    await RisingEdge(dut.clk)
    assert int(dut.pc_out.value) == 8, f"FAIL: Expected PC=8, got {int(dut.pc_out.value)}"
    dut._log.info("✅ Second increment successful: PC = 8")

    # Branch test (robust)
    dut._log.info("Testing branch")
    await FallingEdge(dut.clk)  # Mid-cycle to apply input changes
    dut.pc_next_sel.value = 0b01
    dut.branch_target_addr.value = 0x40
    await Timer(1, units="ns")  # Let combinational logic settle
    
    await RisingEdge(dut.clk)   # 1st edge: signal sampled
    await RisingEdge(dut.clk)   # 2nd edge: output should now reflect the new PC
    
    assert int(dut.pc_out.value) == 0x40, f"FAIL: Expected PC=0x40, got {hex(int(dut.pc_out.value))}"
    dut._log.info("✅ Branch successful")

    # Hold test (using the same robust pattern)
    dut._log.info("Testing hold")
    current_pc = int(dut.pc_out.value)
    await FallingEdge(dut.clk)
    dut.pc_next_sel.value = 0b10
    await RisingEdge(dut.clk)
    assert int(dut.pc_out.value) == current_pc, "FAIL: Hold failed, PC changed"
    dut._log.info("✅ Hold successful")

    dut._log.info("🎉 All ProgramCounter tests passed!")
