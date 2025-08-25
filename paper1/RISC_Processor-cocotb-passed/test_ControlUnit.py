import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

# --- RISC-V ISA Constants (from RISC_ISA_pkg) ---
# Opcodes
OP_R_TYPE = "0110011"
OP_I_TYPE_ARITH = "0010011"
OP_LOAD = "0000011"
OP_STORE = "0100011"
OP_BRANCH = "1100011"
OP_JAL = "1101111"
OP_JALR = "1100111"
OP_LUI = "0110111"
OP_AUIPC = "0010111"

# Funct3
FUNCT3_ADD_SUB_ADDI = "000"
FUNCT3_BNE = "001"
FUNCT3_LW_SW = "010"
FUNCT3_BEQ = "000"
FUNCT3_BLT = "100"

# Funct7
FUNCT7_ADD = "0000000"
FUNCT7_SUB = "0100000"

# ALU Operations
ALU_ADD = BinaryValue("000", n_bits=3)
ALU_SUB = BinaryValue("001", n_bits=3)

# PC Source Selection
PC_SRC_INC = BinaryValue("00", n_bits=2)
PC_SRC_BRANCH = BinaryValue("01", n_bits=2)

# ALU Source Selection
ALU_SRC_A_REG = BinaryValue("0", n_bits=1)
ALU_SRC_B_REG = BinaryValue("0", n_bits=1)
ALU_SRC_B_IMM = BinaryValue("1", n_bits=1)

# Immediate Type Selection
IMM_TYPE_I = BinaryValue("00", n_bits=2)
IMM_TYPE_S = BinaryValue("01", n_bits=2)
IMM_TYPE_B = BinaryValue("10", n_bits=2)

# Write-back Source Selection
WB_SRC_ALU = BinaryValue("00", n_bits=2)
WB_SRC_MEM = BinaryValue("01", n_bits=2)


async def check_control_signals(dut, opcode, funct3, funct7, alu_zero_flag, expected_outputs, test_name):
    """
    Helper function to set inputs, wait, and assert expected outputs.
    """
    dut.opcode.value = BinaryValue(opcode, n_bits=7)
    dut.funct3.value = BinaryValue(funct3, n_bits=3)
    dut.funct7.value = BinaryValue(funct7, n_bits=7)
    dut.alu_zero_flag.value = BinaryValue(str(alu_zero_flag), n_bits=1)

    await Timer(1, units="ns")

    cocotb.log.info(f"--- Test Case: {test_name} ---")
    
    # Assertions
    for signal, expected_value in expected_outputs.items():
        actual_value = getattr(dut, signal).value
        assert actual_value == expected_value, \
            f"{test_name}: {signal} mismatch! Expected {expected_value}, got {actual_value}"

    cocotb.log.info(f"--- Test Case: {test_name} PASSED ---")


@cocotb.test()
async def control_unit_test(dut):
    """Test the ControlUnit module thoroughly based on the corrected HDL."""

    # Default/NOP outputs based on the corrected HDL defaults
    default_outputs = {
        'pc_next_sel':   PC_SRC_INC,
        'alu_op':        ALU_ADD, # Default is now ADD
        'alu_src_a_sel': ALU_SRC_A_REG,
        'alu_src_b_sel': ALU_SRC_B_REG,
        'imm_type_sel':  IMM_TYPE_I,
        'mem_read_en':   BinaryValue("0", n_bits=1),
        'mem_write_en':  BinaryValue("0", n_bits=1),
        'reg_write_en':  BinaryValue("0", n_bits=1),
        'wb_src_sel':    WB_SRC_ALU
    }

    # Test 1: Default/Invalid Opcode
    await check_control_signals(dut, "0000000", "000", "0000000", 0, default_outputs, "Default/Invalid Opcode")

    # Test 2: R-type ADD
    r_type_add_outputs = default_outputs.copy()
    r_type_add_outputs['reg_write_en'] = BinaryValue("1", n_bits=1)
    r_type_add_outputs['alu_op'] = ALU_ADD # Should be ADD
    await check_control_signals(dut, OP_R_TYPE, FUNCT3_ADD_SUB_ADDI, FUNCT7_ADD, 0, r_type_add_outputs, "R-type (ADD)")

    # Test 2.1: R-type SUB
    r_type_sub_outputs = default_outputs.copy()
    r_type_sub_outputs['reg_write_en'] = BinaryValue("1", n_bits=1)
    r_type_sub_outputs['alu_op'] = ALU_SUB # Should be SUB
    await check_control_signals(dut, OP_R_TYPE, FUNCT3_ADD_SUB_ADDI, FUNCT7_SUB, 0, r_type_sub_outputs, "R-type (SUB)")
    
    # Test 3: I-type ADDI
    i_alu_outputs = default_outputs.copy()
    i_alu_outputs['reg_write_en'] = BinaryValue("1", n_bits=1)
    i_alu_outputs['alu_src_b_sel'] = ALU_SRC_B_IMM
    i_alu_outputs['imm_type_sel'] = IMM_TYPE_I
    i_alu_outputs['alu_op'] = ALU_ADD  # <-- FIX: Corrected to expect ADD
    await check_control_signals(dut, OP_I_TYPE_ARITH, FUNCT3_ADD_SUB_ADDI, FUNCT7_ADD, 0, i_alu_outputs, "I-type ALU (ADDI)")

    # Test 4: I-type LW
    i_load_outputs = default_outputs.copy()
    i_load_outputs['mem_read_en'] = BinaryValue("1", n_bits=1)
    i_load_outputs['reg_write_en'] = BinaryValue("1", n_bits=1)
    i_load_outputs['alu_src_b_sel'] = ALU_SRC_B_IMM
    i_load_outputs['imm_type_sel'] = IMM_TYPE_I
    i_load_outputs['alu_op'] = ALU_ADD  # <-- FIX: Address calculation is an ADD
    i_load_outputs['wb_src_sel'] = WB_SRC_MEM
    await check_control_signals(dut, OP_LOAD, FUNCT3_LW_SW, FUNCT7_ADD, 0, i_load_outputs, "I-type Load (LW)")

    # Test 5: S-type SW
    s_store_outputs = default_outputs.copy()
    s_store_outputs['mem_write_en'] = BinaryValue("1", n_bits=1)
    s_store_outputs['alu_src_b_sel'] = ALU_SRC_B_IMM
    s_store_outputs['imm_type_sel'] = IMM_TYPE_S
    s_store_outputs['alu_op'] = ALU_ADD  # <-- FIX: Address calculation is an ADD
    s_store_outputs['reg_write_en'] = BinaryValue("0", n_bits=1) # No reg write for store
    await check_control_signals(dut, OP_STORE, FUNCT3_LW_SW, FUNCT7_ADD, 0, s_store_outputs, "S-type Store (SW)")

    # Test 6: B-type BEQ (branch taken)
    b_beq_taken_outputs = default_outputs.copy()
    b_beq_taken_outputs['imm_type_sel'] = IMM_TYPE_B
    b_beq_taken_outputs['alu_op'] = ALU_SUB # <-- FIX: Branch comparison is SUB
    b_beq_taken_outputs['pc_next_sel'] = PC_SRC_BRANCH
    await check_control_signals(dut, OP_BRANCH, FUNCT3_BEQ, FUNCT7_ADD, 1, b_beq_taken_outputs, "B-type BEQ (taken)")

    # Test 7: B-type BEQ (branch not taken)
    b_beq_not_taken_outputs = default_outputs.copy()
    b_beq_not_taken_outputs['imm_type_sel'] = IMM_TYPE_B
    b_beq_not_taken_outputs['alu_op'] = ALU_SUB # <-- FIX: Branch comparison is SUB
    b_beq_not_taken_outputs['pc_next_sel'] = PC_SRC_INC # Stays PC+4
    await check_control_signals(dut, OP_BRANCH, FUNCT3_BEQ, FUNCT7_ADD, 0, b_beq_not_taken_outputs, "B-type BEQ (not taken)")

    cocotb.log.info("All ControlUnit tests completed successfully!")