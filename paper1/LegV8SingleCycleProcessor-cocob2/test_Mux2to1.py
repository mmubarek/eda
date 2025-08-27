import cocotb
from cocotb.triggers import Timer
import random

@cocotb.test()
async def test_mux2to1(dut):
    """Test the Mux2to1 module thoroughly for all selection and data cases."""

    cocotb.log.info("Starting Mux2to1 testbench")

    # 1. Initialize inputs to a known state
    dut.in0.value = 0x00
    dut.in1.value = 0x00
    dut.sel.value = 0
    await Timer(1, units="ns") # Allow initial values to propagate

    cocotb.log.info("--- Test Case 1: sel = 0 (select in0) ---")
    # Test various data values when sel is 0
    test_cases_sel0 = [
        (0x00, 0xFF, 0x00),  # in0, in1, expected_out
        (0xFF, 0x00, 0xFF),
        (0x5A, 0xA5, 0x5A),
        (0x12, 0x34, 0x12),
        (0xCD, 0xAB, 0xCD),
        (0x7F, 0x80, 0x7F),  # Edge case around mid-range
        (0xAA, 0xAA, 0xAA),  # in0 == in1
    ]

    for in0_val, in1_val, expected_out in test_cases_sel0:
        dut.in0.value = in0_val
        dut.in1.value = in1_val
        dut.sel.value = 0
        await Timer(1, units="ns") # Wait for combinational logic to settle

        actual_out = dut.out.value.integer
        cocotb.log.info(f"sel=0: in0={hex(in0_val)}, in1={hex(in1_val)} -> out={hex(actual_out)}")
        assert actual_out == expected_out, \
            f"ERROR: sel=0, in0={hex(in0_val)}, in1={hex(in1_val)}. Expected {hex(expected_out)}, got {hex(actual_out)}"

    cocotb.log.info("--- Test Case 2: sel = 1 (select in1) ---")
    # Test various data values when sel is 1
    test_cases_sel1 = [
        (0x00, 0xFF, 0xFF),  # in0, in1, expected_out
        (0xFF, 0x00, 0x00),
        (0x5A, 0xA5, 0xA5),
        (0x12, 0x34, 0x34),
        (0xCD, 0xAB, 0xAB),
        (0x7F, 0x80, 0x80),  # Edge case around mid-range
        (0xAA, 0xAA, 0xAA),  # in0 == in1
    ]

    for in0_val, in1_val, expected_out in test_cases_sel1:
        dut.in0.value = in0_val
        dut.in1.value = in1_val
        dut.sel.value = 1
        await Timer(1, units="ns") # Wait for combinational logic to settle

        actual_out = dut.out.value.integer
        cocotb.log.info(f"sel=1: in0={hex(in0_val)}, in1={hex(in1_val)} -> out={hex(actual_out)}")
        assert actual_out == expected_out, \
            f"ERROR: sel=1, in0={hex(in0_val)}, in1={hex(in1_val)}. Expected {hex(expected_out)}, got {hex(actual_out)}"

    cocotb.log.info("--- Test Case 3: Random Value Tests ---")
    # Run a series of random tests to increase coverage
    num_random_tests = 100
    for i in range(num_random_tests):
        in0_val = random.randint(0, 255) # 8-bit value
        in1_val = random.randint(0, 255) # 8-bit value
        sel_val = random.randint(0, 1)   # 1-bit value

        dut.in0.value = in0_val
        dut.in1.value = in1_val
        dut.sel.value = sel_val
        await Timer(1, units="ns") # Wait for combinational logic to settle

        expected_out = in1_val if sel_val == 1 else in0_val
        actual_out = dut.out.value.integer

        cocotb.log.info(f"Random test {i+1}/{num_random_tests}: in0={hex(in0_val)}, in1={hex(in1_val)}, sel={sel_val} -> out={hex(actual_out)}")
        assert actual_out == expected_out, \
            f"ERROR: Random test {i+1}: in0={hex(in0_val)}, in1={hex(in1_val)}, sel={sel_val}. Expected {hex(expected_out)}, got {hex(actual_out)}"

    cocotb.log.info("Mux2to1 testbench finished successfully!")