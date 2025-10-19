import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue
from enum import IntEnum
import random

# Define ALU operation codes as an IntEnum for readability
class AluOp(IntEnum):
    ADD = 0b000
    SUB = 0b001
    AND = 0b010
    OR  = 0b011
    XOR = 0b100
    SLT = 0b101
    SLL = 0b110
    SRL = 0b111

def to_signed(val, width):
    """
    Converts an unsigned integer (as represented in hardware) to a signed Python integer.
    Assumes two's complement representation.
    """
    if val >= (1 << (width - 1)):
        return val - (1 << width)
    return val

def to_unsigned(val, width):
    """
    Converts a signed Python integer to its unsigned hardware representation.
    Assumes two's complement representation.
    """
    if val < 0:
        return val + (1 << width)
    return val
    # Ensure the result fits within the width
    # return val & ((1 << width) - 1) # This is implicitly handled by Python's int behavior for positive numbers

async def drive_and_check(dut, operand_a, operand_b, alu_op, expected_result, expected_zero, data_width):
    """
    Drives inputs to the DUT, waits for combinational logic propagation,
    and asserts the correctness of the outputs.
    """
    dut.operand_a.value = operand_a
    dut.operand_b.value = operand_b
    dut.alu_op.value = alu_op

    # Wait for combinational logic to propagate. A small delay is usually sufficient.
    await Timer(1, units="ns")

    actual_result = dut.result.value.integer
    actual_zero = dut.zero.value.integer

    cocotb.log.info(f"Test: A={operand_a:#x}, B={operand_b:#x}, Op={AluOp(alu_op).name}")
    cocotb.log.info(f"Expected: Result={expected_result:#x}, Zero={expected_zero}")
    cocotb.log.info(f"Actual:   Result={actual_result:#x}, Zero={actual_zero}")

    assert actual_result == expected_result, \
        f"Result mismatch for A={operand_a:#x}, B={operand_b:#x}, Op={AluOp(alu_op).name}. " \
        f"Expected {expected_result:#x}, got {actual_result:#x}"
    assert actual_zero == expected_zero, \
        f"Zero flag mismatch for A={operand_a:#x}, B={operand_b:#x}, Op={AluOp(alu_op).name}. " \
        f"Expected {expected_zero}, got {actual_zero}"

@cocotb.test()
async def test_alu(dut):
    """
    Thorough testbench for the ALU module, covering various operations,
    edge cases, and randomized inputs.
    """

    # Get DATA_WIDTH from the DUT's parameter
    DATA_WIDTH = int(dut.DATA_WIDTH.value)
    cocotb.log.info(f"Testing ALU with DATA_WIDTH = {DATA_WIDTH}")

    # Constants derived from DATA_WIDTH
    MAX_UNSIGNED = (1 << DATA_WIDTH) - 1
    MAX_SIGNED = (1 << (DATA_WIDTH - 1)) - 1
    MIN_SIGNED = -(1 << (DATA_WIDTH - 1))
    SHIFT_MASK = (1 << (DATA_WIDTH.bit_length() - 1)) - 1 # For 32-bit, this is 0x1F (5 bits)

    # Initial values for all inputs
    dut.operand_a.value = 0
    dut.operand_b.value = 0
    dut.alu_op.value = AluOp.ADD
    await Timer(1, units="ns") # Allow initial propagation

    cocotb.log.info("--- Basic Arithmetic Tests (ADD, SUB) ---")
    # ADD
    await drive_and_check(dut, 5, 3, AluOp.ADD, 8, 0, DATA_WIDTH)
    await drive_and_check(dut, 0, 0, AluOp.ADD, 0, 1, DATA_WIDTH)
    await drive_and_check(dut, MAX_UNSIGNED, 1, AluOp.ADD, 0, 1, DATA_WIDTH) # Wrap around (MAX_UNSIGNED + 1 = 0)
    await drive_and_check(dut, 10, MAX_UNSIGNED, AluOp.ADD, 9, 0, DATA_WIDTH) # Wrap around (10 + (-1) = 9)
    await drive_and_check(dut, to_unsigned(MIN_SIGNED, DATA_WIDTH), to_unsigned(-1, DATA_WIDTH), AluOp.ADD, to_unsigned(MIN_SIGNED - 1, DATA_WIDTH), 0, DATA_WIDTH)

    # SUB
    await drive_and_check(dut, 5, 3, AluOp.SUB, 2, 0, DATA_WIDTH)
    await drive_and_check(dut, 3, 5, AluOp.SUB, to_unsigned(-2, DATA_WIDTH), 0, DATA_WIDTH) # 3 - 5 = -2 (unsigned representation)
    await drive_and_check(dut, 0, 0, AluOp.SUB, 0, 1, DATA_WIDTH)
    await drive_and_check(dut, 0, 1, AluOp.SUB, MAX_UNSIGNED, 0, DATA_WIDTH) # 0 - 1 = -1 (unsigned representation)
    await drive_and_check(dut, to_unsigned(MIN_SIGNED, DATA_WIDTH), 1, AluOp.SUB, to_unsigned(MIN_SIGNED - 1, DATA_WIDTH), 0, DATA_WIDTH)
    await drive_and_check(dut, to_unsigned(MAX_SIGNED, DATA_WIDTH), to_unsigned(MIN_SIGNED, DATA_WIDTH), AluOp.SUB, to_unsigned(MAX_SIGNED - MIN_SIGNED, DATA_WIDTH), 0, DATA_WIDTH)

    cocotb.log.info("--- Basic Logical Tests (AND, OR, XOR) ---")
    # AND
    await drive_and_check(dut, 0xF0F0F0F0 & MAX_UNSIGNED, 0x0F0F0F0F & MAX_UNSIGNED, AluOp.AND, 0x00000000, 1, DATA_WIDTH)
    await drive_and_check(dut, MAX_UNSIGNED, 0x00000000, AluOp.AND, 0x00000000, 1, DATA_WIDTH)
    await drive_and_check(dut, 0xABCDEF01 & MAX_UNSIGNED, 0x12345678 & MAX_UNSIGNED, AluOp.AND, (0xABCDEF01 & 0x12345678) & MAX_UNSIGNED, 0, DATA_WIDTH)

    # OR
    await drive_and_check(dut, 0xF0F0F0F0 & MAX_UNSIGNED, 0x0F0F0F0F & MAX_UNSIGNED, AluOp.OR, MAX_UNSIGNED, 0, DATA_WIDTH)
    await drive_and_check(dut, 0x00000000, 0x00000000, AluOp.OR, 0x00000000, 1, DATA_WIDTH)
    await drive_and_check(dut, 0xABCDEF01 & MAX_UNSIGNED, 0x12345678 & MAX_UNSIGNED, AluOp.OR, (0xABCDEF01 | 0x12345678) & MAX_UNSIGNED, 0, DATA_WIDTH)

    # XOR
    await drive_and_check(dut, 0xF0F0F0F0 & MAX_UNSIGNED, 0x0F0F0F0F & MAX_UNSIGNED, AluOp.XOR, MAX_UNSIGNED, 0, DATA_WIDTH)
    await drive_and_check(dut, 0x00000000, 0x00000000, AluOp.XOR, 0x00000000, 1, DATA_WIDTH)
    await drive_and_check(dut, 0xABCDEF01 & MAX_UNSIGNED, 0x12345678 & MAX_UNSIGNED, AluOp.XOR, (0xABCDEF01 ^ 0x12345678) & MAX_UNSIGNED, 0, DATA_WIDTH)

    cocotb.log.info("--- Signed Less Than (SLT) Tests ---")
    # SLT (Set Less Than - signed comparison)
    # The result is 1 if operand_a < operand_b (signed), else 0.
    test_cases_slt = [
        (5, 3, 0),      # 5 < 3 is false
        (3, 5, 1),      # 3 < 5 is true
        (-5, -3, 1),    # -5 < -3 is true
        (-3, -5, 0),    # -3 < -5 is false
        (-5, 3, 1),     # -5 < 3 is true
        (3, -5, 0),     # 3 < -5 is false
        (0, 0, 0),      # 0 < 0 is false
        (MIN_SIGNED, MAX_SIGNED, 1), # MIN_SIGNED < MAX_SIGNED is true
        (MAX_SIGNED, MIN_SIGNED, 0), # MAX_SIGNED < MIN_SIGNED is false
        (MIN_SIGNED, MIN_SIGNED + 1, 1),
        (MAX_SIGNED, MAX_SIGNED - 1, 0),
    ]
    for a_signed, b_signed, expected_val in test_cases_slt:
        expected_result = 1 if expected_val else 0
        expected_zero = 1 if expected_result == 0 else 0
        await drive_and_check(dut, to_unsigned(a_signed, DATA_WIDTH), to_unsigned(b_signed, DATA_WIDTH), AluOp.SLT, expected_result, expected_zero, DATA_WIDTH)

    cocotb.log.info("--- Shift Left Logical (SLL) Tests ---")
    # SLL (Shift Left Logical) - Shift amount is operand_b[4:0]
    await drive_and_check(dut, 1, 1, AluOp.SLL, 2, 0, DATA_WIDTH)
    await drive_and_check(dut, 0x1, DATA_WIDTH - 1, AluOp.SLL, (1 << (DATA_WIDTH - 1)) & MAX_UNSIGNED, 0, DATA_WIDTH) # Shift to MSB
    await drive_and_check(dut, (1 << (DATA_WIDTH - 1)) & MAX_UNSIGNED, 1, AluOp.SLL, 0, 1, DATA_WIDTH) # Shift MSB out
    await drive_and_check(dut, 0x12345678 & MAX_UNSIGNED, 4, AluOp.SLL, (0x12345678 << 4) & MAX_UNSIGNED, 0, DATA_WIDTH)
    await drive_and_check(dut, 0x12345678 & MAX_UNSIGNED, 0, AluOp.SLL, 0x12345678 & MAX_UNSIGNED, 0, DATA_WIDTH)
    await drive_and_check(dut, 0, 5, AluOp.SLL, 0, 1, DATA_WIDTH)
    await drive_and_check(dut, MAX_UNSIGNED, DATA_WIDTH - 1, AluOp.SLL, (MAX_UNSIGNED << (DATA_WIDTH - 1)) & MAX_UNSIGNED, 0, DATA_WIDTH)

    cocotb.log.info("--- Shift Right Logical (SRL) Tests ---")
    # SRL (Shift Right Logical) - Shift amount is operand_b[4:0]
    await drive_and_check(dut, 2, 1, AluOp.SRL, 1, 0, DATA_WIDTH)
    await drive_and_check(dut, (1 << (DATA_WIDTH - 1)) & MAX_UNSIGNED, DATA_WIDTH - 1, AluOp.SRL, 1, 0, DATA_WIDTH) # Shift MSB to LSB
    await drive_and_check(dut, 0x00000001, 1, AluOp.SRL, 0, 1, DATA_WIDTH) # Shift LSB out
    await drive_and_check(dut, 0x12345678 & MAX_UNSIGNED, 4, AluOp.SRL, (0x12345678 >> 4) & MAX_UNSIGNED, 0, DATA_WIDTH)
    await drive_and_check(dut, 0x12345678 & MAX_UNSIGNED, 0, AluOp.SRL, 0x12345678 & MAX_UNSIGNED, 0, DATA_WIDTH)
    await drive_and_check(dut, 0, 5, AluOp.SRL, 0, 1, DATA_WIDTH)
    await drive_and_check(dut, MAX_UNSIGNED, DATA_WIDTH - 1, AluOp.SRL, (MAX_UNSIGNED >> (DATA_WIDTH - 1)) & MAX_UNSIGNED, 0, DATA_WIDTH)

    cocotb.log.info("--- Random Tests ---")
    for i in range(200): # Run 200 random tests
        op_a = random.randint(0, MAX_UNSIGNED)
        op_b = random.randint(0, MAX_UNSIGNED)
        op_code = random.choice(list(AluOp))

        expected_res = 0
        expected_zero = 0

        if op_code == AluOp.ADD:
            expected_res = (op_a + op_b) & MAX_UNSIGNED
        elif op_code == AluOp.SUB:
            expected_res = (op_a - op_b) & MAX_UNSIGNED
        elif op_code == AluOp.AND:
            expected_res = (op_a & op_b) & MAX_UNSIGNED
        elif op_code == AluOp.OR:
            expected_res = (op_a | op_b) & MAX_UNSIGNED
        elif op_code == AluOp.XOR:
            expected_res = (op_a ^ op_b) & MAX_UNSIGNED
        elif op_code == AluOp.SLT:
            # Convert operands to signed for comparison
            signed_a = to_signed(op_a, DATA_WIDTH)
            signed_b = to_signed(op_b, DATA_WIDTH)
            expected_res = 1 if signed_a < signed_b else 0
        elif op_code == AluOp.SLL:
            # Shift amount is lower 5 bits for 32-bit data, or DATA_WIDTH.bit_length() - 1 for generic width
            shift_amount = op_b & SHIFT_MASK
            expected_res = (op_a << shift_amount) & MAX_UNSIGNED
        elif op_code == AluOp.SRL:
            # Shift amount is lower 5 bits for 32-bit data, or DATA_WIDTH.bit_length() - 1 for generic width
            shift_amount = op_b & SHIFT_MASK
            expected_res = (op_a >> shift_amount) & MAX_UNSIGNED
        else:
            # Default case in Verilog is result_int = '0;
            expected_res = 0

        expected_zero = 1 if expected_res == 0 else 0

        await drive_and_check(dut, op_a, op_b, op_code, expected_res, expected_zero, DATA_WIDTH)

    cocotb.log.info("All ALU tests passed successfully!")