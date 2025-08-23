import cocotb
from cocotb.triggers import Timer
import random

@cocotb.test()
async def test_mux3to1(dut):
    """Test the Mux3to1 module thoroughly for all select cases and random data."""

    cocotb.log.info("Starting Mux3to1 testbench")

    # Define the select values to test
    select_values = [0b00, 0b01, 0b10, 0b11] # 0b11 is the default case

    # Run multiple iterations for each select value to test with various data
    for sel_val in select_values:
        cocotb.log.info(f"Testing with sel = {bin(sel_val)}")
        for i in range(10): # Run 10 random data tests for each sel value
            in0_val = random.randint(0, 255)
            in1_val = random.randint(0, 255)
            in2_val = random.randint(0, 255)

            # Assign inputs
            dut.in0.value = in0_val
            dut.in1.value = in1_val
            dut.in2.value = in2_val
            dut.sel.value = sel_val

            # Wait for combinational logic to settle
            await Timer(1, units="ns")

            # Determine expected output based on select value
            expected_out = 0
            if sel_val == 0b00:
                expected_out = in0_val
            elif sel_val == 0b01:
                expected_out = in1_val
            elif sel_val == 0b10:
                expected_out = in2_val
            else: # sel_val == 0b11 or any other unhandled case
                expected_out = 0 # As per the Verilog default: out = '0;

            actual_out = dut.out.value.integer

            cocotb.log.info(
                f"Iteration {i+1}: in0={in0_val}, in1={in1_val}, in2={in2_val}, "
                f"sel={bin(sel_val)}, Expected={expected_out}, Actual={actual_out}"
            )

            # Assert the output
            assert actual_out == expected_out, \
                f"Test failed for sel={bin(sel_val)}: Expected {expected_out}, Got {actual_out}"

    cocotb.log.info("Mux3to1 testbench finished successfully")