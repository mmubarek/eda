import cocotb
from cocotb.triggers import Timer
from cocotb.result import TestFailure
import random

@cocotb.test()
async def adder_basic_test(dut):
    """Test the Adder with basic addition cases."""

    dut._log.info("Starting basic adder test")

    test_cases = [
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 1),
        (5, 10, 15),
        (100, 50, 150),
        (255, 0, 255),  # Max value + 0
        (0, 255, 255),  # 0 + Max value
        (127, 128, 255), # Max positive sum
    ]

    for in1_val, in2_val, expected_sum in test_cases:
        dut.in1.value = in1_val
        dut.in2.value = in2_val

        await Timer(1, units="ns") # Wait for combinational logic to settle

        actual_sum = dut.sum.value.integer
        dut._log.info(f"Input: {in1_val} + {in2_val}, Expected: {expected_sum}, Actual: {actual_sum}")
        assert actual_sum == expected_sum, \
            f"Test failed for {in1_val} + {in2_val}: Expected {expected_sum}, Got {actual_sum}"

    dut._log.info("Basic adder test completed successfully")

@cocotb.test()
async def adder_overflow_test(dut):
    """Test the Adder with cases that cause 8-bit overflow (wrap-around)."""

    dut._log.info("Starting overflow adder test")

    test_cases = [
        (255, 1, 0),    # 255 + 1 = 256, wraps to 0 (0x100 & 0xFF = 0x00)
        (250, 10, 4),   # 250 + 10 = 260, wraps to 4 (0x104 & 0xFF = 0x04)
        (128, 128, 0),  # 128 + 128 = 256, wraps to 0
        (1, 255, 0),    # 1 + 255 = 256, wraps to 0
        (200, 200, 144), # 200 + 200 = 400, wraps to 144 (0x190 & 0xFF = 0x90)
    ]

    for in1_val, in2_val, expected_sum_wrapped in test_cases:
        dut.in1.value = in1_val
        dut.in2.value = in2_val

        await Timer(1, units="ns") # Wait for combinational logic to settle

        actual_sum = dut.sum.value.integer
        # Calculate expected sum with 8-bit wrap-around
        expected_sum_calc = (in1_val + in2_val) & 0xFF
        dut._log.info(f"Input: {in1_val} + {in2_val}, Expected (wrapped): {expected_sum_wrapped}, Actual: {actual_sum}")
        assert actual_sum == expected_sum_wrapped, \
            f"Test failed for {in1_val} + {in2_val} (overflow): Expected {expected_sum_wrapped}, Got {actual_sum}"
        assert actual_sum == expected_sum_calc, \
            f"Internal calculation mismatch for {in1_val} + {in2_val}: Expected {expected_sum_calc}, Got {actual_sum}"

    dut._log.info("Overflow adder test completed successfully")

@cocotb.test()
async def adder_random_test(dut):
    """Test the Adder with a large number of random inputs."""

    dut._log.info("Starting random adder test")

    num_tests = 1000
    for i in range(num_tests):
        in1_val = random.randint(0, 255)
        in2_val = random.randint(0, 255)

        dut.in1.value = in1_val
        dut.in2.value = in2_val

        await Timer(1, units="ns") # Wait for combinational logic to settle

        actual_sum = dut.sum.value.integer
        expected_sum = (in1_val + in2_val) & 0xFF # Expected sum with 8-bit wrap-around

        dut._log.debug(f"Random Test {i+1}: {in1_val} + {in2_val}, Expected: {expected_sum}, Actual: {actual_sum}")
        assert actual_sum == expected_sum, \
            f"Random test failed for {in1_val} + {in2_val}: Expected {expected_sum}, Got {actual_sum}"

    dut._log.info(f"Random adder test completed successfully with {num_tests} cases.")