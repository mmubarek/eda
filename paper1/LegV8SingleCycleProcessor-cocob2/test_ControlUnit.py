#
# File: test_control_unit.py
# Description: Corrected cocotb testbench for the ControlUnit module.
#
# Changes:
# 1. Removed all references to the 'pc_src_sel' signal, as it has been
#    removed from the ControlUnit design to eliminate unused logic.
# 2. Verified that the expected values for 'mem_to_reg_sel' (0 or 1) align
#    with the new 2-bit output from the DUT.
#
import cocotb
from cocotb.triggers import Timer, ReadOnly

# Define opcodes
OP_R_TYPE = 0b0000
OP_LW     = 0b0001
OP_SW     = 0b0010
OP_BEQ    = 0b0011
OP_JUMP   = 0b0100
OP_ADDI   = 0b0101

# Define ALU operations
ALU_ADD = 0b000
ALU_SUB = 0b001

# FIX: Removed PC_SRC constants as the signal is no longer part of the DUT


async def check_control_signals(dut, expected_signals, test_name=""):
    """
    Check all control signals after combinational logic settles.
    """
    await ReadOnly()  # Wait for outputs to stabilize

    dut._log.info(f"--- Checking {test_name} ---")
    dut._log.info(f"Input Opcode: {dut.opcode.value.binstr}")

    actual_signals = {
        "reg_write_en":   dut.reg_write_en.value.integer,
        "mem_write_en":   dut.mem_write_en.value.integer,
        "mem_read_en":    dut.mem_read_en.value.integer,
        "alu_src_sel":    dut.alu_src_sel.value.integer,
        "mem_to_reg_sel": dut.mem_to_reg_sel.value.integer,
        "branch_en":      dut.branch_en.value.integer,
        "jump_en":        dut.jump_en.value.integer,
        "alu_op":         dut.alu_op.value.integer,
        # FIX: Removed 'pc_src_sel' as it is no longer an output of the ControlUnit
    }

    for signal, expected in expected_signals.items():
        actual = actual_signals[signal]
        assert actual == expected, f"{test_name}: {signal} mismatch. Expected {expected}, got {actual}"
        dut._log.info(f"  {signal}: OK (Expected: {expected}, Actual: {actual})")

    dut._log.info(f"--- {test_name} PASSED ---")

    await Timer(1, units="ns")  # Ensure we exit read-only phase


@cocotb.test()
async def control_unit_test(dut):
    """
    Testbench for the ControlUnit module.
    """
    dut._log.info("Starting ControlUnit testbench")

    # Test cases with 'pc_src_sel' removed
    test_cases = [
        (0b1111, "Undefined Opcode (1111)", {
            "reg_write_en": 0, "mem_write_en": 0, "mem_read_en": 0,
            "alu_src_sel": 0, "mem_to_reg_sel": 0, "branch_en": 0,
            "jump_en": 0, "alu_op": ALU_ADD
        }),
        (OP_R_TYPE, "OP_R_TYPE", {
            "reg_write_en": 1, "mem_write_en": 0, "mem_read_en": 0,
            "alu_src_sel": 0, "mem_to_reg_sel": 0, "branch_en": 0,
            "jump_en": 0, "alu_op": ALU_ADD
        }),
        (OP_LW, "OP_LW", {
            "reg_write_en": 1, "mem_write_en": 0, "mem_read_en": 1,
            "alu_src_sel": 1, "mem_to_reg_sel": 1, "branch_en": 0,
            "jump_en": 0, "alu_op": ALU_ADD
        }),
        (OP_SW, "OP_SW", {
            "reg_write_en": 0, "mem_write_en": 1, "mem_read_en": 0,
            "alu_src_sel": 1, "mem_to_reg_sel": 0, "branch_en": 0,
            "jump_en": 0, "alu_op": ALU_ADD
        }),
        (OP_BEQ, "OP_BEQ", {
            "reg_write_en": 0, "mem_write_en": 0, "mem_read_en": 0,
            "alu_src_sel": 0, "mem_to_reg_sel": 0, "branch_en": 1,
            "jump_en": 0, "alu_op": ALU_SUB
        }),
        (OP_JUMP, "OP_JUMP", {
            "reg_write_en": 0, "mem_write_en": 0, "mem_read_en": 0,
            "alu_src_sel": 0, "mem_to_reg_sel": 0, "branch_en": 0,
            "jump_en": 1, "alu_op": ALU_ADD
        }),
        (OP_ADDI, "OP_ADDI", {
            "reg_write_en": 1, "mem_write_en": 0, "mem_read_en": 0,
            "alu_src_sel": 1, "mem_to_reg_sel": 0, "branch_en": 0,
            "jump_en": 0, "alu_op": ALU_ADD
        }),
        (0b0110, "Undefined Opcode (0110)", {
            "reg_write_en": 0, "mem_write_en": 0, "mem_read_en": 0,
            "alu_src_sel": 0, "mem_to_reg_sel": 0, "branch_en": 0,
            "jump_en": 0, "alu_op": ALU_ADD
        }),
    ]

    for opcode, name, expected in test_cases:
        dut.opcode.value = opcode
        await Timer(1, units="ns")  # Allow combinational logic to settle
        await check_control_signals(dut, expected, name)

    dut._log.info("ControlUnit testbench finished successfully")