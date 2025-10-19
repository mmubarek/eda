import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue
import random

@cocotb.test()
async def alu_basic_test(dut):
    """Test ALU with various operations and specific values."""

    # Helper function to apply inputs and check outputs
    async def check_alu(src1_val, src2_val, alu_op_val, expected_result, expected_zero):
        dut.src1.value = src1_val
        dut.src2.value = src2_val
        dut.alu_op.value = alu_op_val

        await Timer(1, units='ns') # Allow combinational logic to settle

        actual_result = dut.result.value.integer
        actual_zero = dut.zero.value.integer

        cocotb.log.info(f"Testing: src1={src1_val:3d}, src2={src2_val:3d}, op={alu_op_val.binstr}")
        cocotb.log.info(f"Expected: result={expected_result:3d}, zero={expected_zero}")
        cocotb.log.info(f"Actual:   result={actual_result:3d}, zero={actual_zero}")

        assert actual_result == expected_result, \
            f"Result mismatch for op {alu_op_val.binstr} (src1={src1_val}, src2={src2_val}): Expected {expected_result}, got {actual_result}"
        assert actual_zero == expected_zero, \
            f"Zero flag mismatch for op {alu_op_val.binstr} (src1={src1_val}, src2={src2_val}): Expected {expected_zero}, got {actual_zero}"
        cocotb.log.info("Assertion PASSED")

    cocotb.log.info("Starting ALU basic test")

    # Test cases for each ALU operation
    # ADD (3'b000)
    cocotb.log.info("--- Testing ADD (000) ---")
    await check_alu(10, 5, BinaryValue("000", bits=3), 15, 0)
    await check_alu(250, 10, BinaryValue("000", bits=3), 4, 0) # Overflow: 250+10 = 260 (0x104), 8-bit -> 4
    await check_alu(0, 0, BinaryValue("000", bits=3), 0, 1)
    await check_alu(127, 1, BinaryValue("000", bits=3), 128, 0)
    await check_alu(255, 1, BinaryValue("000", bits=3), 0, 1) # 255 + 1 = 256 (0x100), 8-bit -> 0

    # SUB (3'b001)
    cocotb.log.info("--- Testing SUB (001) ---")
    await check_alu(10, 5, BinaryValue("001", bits=3), 5, 0)
    await check_alu(5, 10, BinaryValue("001", bits=3), 251, 0) # Underflow: 5-10 = -5 (0xFFFB), 8-bit -> 251
    await check_alu(100, 100, BinaryValue("001", bits=3), 0, 1)
    await check_alu(0, 1, BinaryValue("001", bits=3), 255, 0) # 0 - 1 = -1, 8-bit -> 255

    # AND (3'b010)
    cocotb.log.info("--- Testing AND (010) ---")
    await check_alu(0b11001100, 0b10101010, BinaryValue("010", bits=3), 0b10001000, 0)
    await check_alu(0b11111111, 0b00000000, BinaryValue("010", bits=3), 0b00000000, 1)
    await check_alu(0b01010101, 0b10101010, BinaryValue("010", bits=3), 0b00000000, 1)

    # OR (3'b011)
    cocotb.log.info("--- Testing OR (011) ---")
    await check_alu(0b11001100, 0b10101010, BinaryValue("011", bits=3), 0b11101110, 0)
    await check_alu(0b00000000, 0b00000000, BinaryValue("011", bits=3), 0b00000000, 1)
    await check_alu(0b00000001, 0b00000010, BinaryValue("011", bits=3), 0b00000011, 0)

    # XOR (3'b100)
    cocotb.log.info("--- Testing XOR (100) ---")
    await check_alu(0b11001100, 0b10101010, BinaryValue("100", bits=3), 0b01100110, 0)
    await check_alu(0b11110000, 0b11110000, BinaryValue("100", bits=3), 0b00000000, 1)
    await check_alu(0b00000000, 0b11111111, BinaryValue("100", bits=3), 0b11111111, 0)

    # SLT (3'b101)
    cocotb.log.info("--- Testing SLT (101) ---")
    await check_alu(5, 10, BinaryValue("101", bits=3), 1, 0)
    await check_alu(10, 5, BinaryValue("101", bits=3), 0, 1)
    await check_alu(10, 10, BinaryValue("101", bits=3), 0, 1)
    await check_alu(0, 0, BinaryValue("101", bits=3), 0, 1)
    await check_alu(255, 0, BinaryValue("101", bits=3), 0, 1) # Unsigned comparison

    # SLL (3'b110)
    cocotb.log.info("--- Testing SLL (110) ---")
    await check_alu(0b00000001, 1, BinaryValue("110", bits=3), 0b00000010, 0)
    await check_alu(0b10000000, 1, BinaryValue("110", bits=3), 0b00000000, 1) # Shift out MSB
    await check_alu(0b00000001, 8, BinaryValue("110", bits=3), 0b00000000, 1) # Shift by 8 or more -> 0
    await check_alu(0b00000001, 0, BinaryValue("110", bits=3), 0b00000001, 0)
    await check_alu(0b00001111, 2, BinaryValue("110", bits=3), 0b00111100, 0)

    # SRL (3'b111)
    cocotb.log.info("--- Testing SRL (111) ---")
    await check_alu(0b10000000, 1, BinaryValue("111", bits=3), 0b01000000, 0)
    await check_alu(0b00000001, 1, BinaryValue("111", bits=3), 0b00000000, 1) # Shift out LSB
    await check_alu(0b10000000, 8, BinaryValue("111", bits=3), 0b00000000, 1) # Shift by 8 or more -> 0
    await check_alu(0b10000000, 0, BinaryValue("111", bits=3), 0b10000000, 0)
    await check_alu(0b11110000, 2, BinaryValue("111", bits=3), 0b00111100, 0)

    cocotb.log.info("ALU basic test finished successfully.")

@cocotb.test()
async def alu_random_test(dut):
    """Test ALU with random inputs for various operations."""

    # Helper function to apply inputs and check outputs
    async def check_alu_random(src1_val, src2_val, alu_op_val):
        dut.src1.value = src1_val
        dut.src2.value = src2_val
        dut.alu_op.value = alu_op_val

        await Timer(1, units='ns') # Allow combinational logic to settle

        actual_result = dut.result.value.integer
        actual_zero = dut.zero.value.integer

        # Calculate expected values based on Verilog behavior
        expected_result = 0
        op_code = alu_op_val.integer

        if op_code == 0: # ADD
            expected_result = (src1_val + src2_val) & 0xFF
        elif op_code == 1: # SUB
            expected_result = (src1_val - src2_val) & 0xFF
        elif op_code == 2: # AND
            expected_result = src1_val & src2_val
        elif op_code == 3: # OR
            expected_result = src1_val | src2_val
        elif op_code == 4: # XOR
            expected_result = src1_val ^ src2_val
        elif op_code == 5: # SLT (Set Less Than)
            expected_result = 1 if src1_val < src2_val else 0
        elif op_code == 6: # SLL (Shift Left Logical)
            shift_amount = src2_val
            if shift_amount >= 8: # For 8-bit data, shifting by 8 or more bits results in 0
                expected_result = 0
            else:
                expected_result = (src1_val << shift_amount) & 0xFF
        elif op_code == 7: # SRL (Shift Right Logical)
            shift_amount = src2_val
            if shift_amount >= 8:
                expected_result = 0
            else:
                expected_result = (src1_val >> shift_amount) & 0xFF
        else:
            # This case should not be reached with 3-bit alu_op
            cocotb.log.error(f"Invalid ALU OpCode: {op_code}")
            assert False, "Invalid ALU OpCode generated in test"

        expected_zero = 1 if expected_result == 0 else 0

        cocotb.log.info(f"Random Test: src1={src1_val:3d}, src2={src2_val:3d}, op={alu_op_val.binstr}")
        cocotb.log.info(f"Expected: result={expected_result:3d}, zero={expected_zero}")
        cocotb.log.info(f"Actual:   result={actual_result:3d}, zero={actual_zero}")

        assert actual_result == expected_result, \
            f"Result mismatch for op {alu_op_val.binstr} (src1={src1_val}, src2={src2_val}): Expected {expected_result}, got {actual_result}"
        assert actual_zero == expected_zero, \
            f"Zero flag mismatch for op {alu_op_val.binstr} (src1={src1_val}, src2={src2_val}): Expected {expected_zero}, got {actual_zero}"
        cocotb.log.info("Assertion PASSED")

    cocotb.log.info("Starting ALU random test")

    num_random_tests = 100
    for i in range(num_random_tests):
        cocotb.log.info(f"--- Running random test {i+1}/{num_random_tests} ---")
        src1_rand = random.randint(0, 255)
        src2_rand = random.randint(0, 255)
        alu_op_rand = random.randint(0, 7) # 3-bit opcode, 0 to 7
        await check_alu_random(src1_rand, src2_rand, BinaryValue(alu_op_rand, bits=3))

    cocotb.log.info("ALU random test finished successfully.")