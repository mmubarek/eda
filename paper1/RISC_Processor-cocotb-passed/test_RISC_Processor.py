import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

# --- RISC-V ISA Constants (for instruction encoding) ---
OP_R_TYPE = 0b0110011
OP_I_TYPE_ARITH = 0b0010011
OP_LOAD = 0b0000011
OP_STORE = 0b0100011
OP_BRANCH = 0b1100011
FUNCT3_ADD_SUB_ADDI = 0b000
FUNCT3_LW_SW = 0b010  # Correct funct3 for 32-bit LW/SW
FUNCT3_BEQ = 0b000
FUNCT7_ADD = 0b0000000
FUNCT7_SUB = 0b0100000
X0 = 0

# --- Instruction Encoding Helper Functions ---
def encode_r_type(opcode, rd, funct3, rs1, rs2, funct7):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def encode_i_type(opcode, rd, funct3, rs1, imm):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def encode_s_type(opcode, imm, funct3, rs1, rs2):
    imm_11_5 = (imm >> 5) & 0x7F
    imm_4_0 = imm & 0x1F
    return (imm_11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm_4_0 << 7) | opcode

def encode_b_type(opcode, imm, funct3, rs1, rs2):
    imm_val = imm & 0x1FFF # 13-bit immediate
    imm_12 = (imm_val >> 12) & 0x1
    imm_11 = (imm_val >> 11) & 0x1
    imm_10_5 = (imm_val >> 5) & 0x3F
    imm_4_1 = (imm_val >> 1) & 0xF
    return (imm_12 << 31) | (imm_10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm_4_1 << 8) | (imm_11 << 7) | opcode

async def reset_dut(dut):
    """
    A robust, synchronous reset sequence.
    """
    dut._log.info("Applying reset...")
    
    # Ensure clock is running before we start
    await RisingEdge(dut.clk)
    
    # 1. Assert reset
    dut.rst_n.value = 0
    
    # 2. Wait for a couple of clock edges for reset to propagate
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # At this point, PC is guaranteed to be 0 from the async reset
    # Now, de-assert reset cleanly between clock edges
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    
    dut._log.info("DUT reset complete.")


@cocotb.test()
async def test_risc_processor_full(dut):
    """Test the single-cycle RISC processor with a full program."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut._log.info("--- Starting Full RISC Processor Test ---")

    # 1. Reset and check initial state
    await reset_dut(dut)
    assert dut.debug_pc.value == 0, f"PC not 0 after reset: {dut.debug_pc.value}"
    assert dut.debug_reg_x10.value == 0, f"x10 not 0 after reset: {dut.debug_reg_x10.value}"
    assert dut.debug_reg_x11.value == 0, f"x11 not 0 after reset: {dut.debug_reg_x11.value}"

    # 2. Load program that uses observable registers (x10, x11)
    imem = dut.instructionmemory_inst.mem
    dmem = dut.datamemory_inst.mem

    program = [
        # 0x00: ADDI x10, x0, 50   (x10 = 50)
        encode_i_type(OP_I_TYPE_ARITH, 10, FUNCT3_ADD_SUB_ADDI, X0, 50),
        # 0x04: ADDI x11, x0, 60   (x11 = 60)
        encode_i_type(OP_I_TYPE_ARITH, 11, FUNCT3_ADD_SUB_ADDI, X0, 60),
        # 0x08: ADD  x10, x10, x11 (x10 = 50 + 60 = 110)
        encode_r_type(OP_R_TYPE, 10, FUNCT3_ADD_SUB_ADDI, 10, 11, FUNCT7_ADD),
        # 0x0C: SW   x10, 8(x0)    (Store 110 to memory address 8)
        encode_s_type(OP_STORE, 8, FUNCT3_LW_SW, X0, 10),
        # 0x10: LW   x11, 8(x0)    (Load from memory address 8 into x11. x11 should be 110)
        encode_i_type(OP_LOAD, 11, FUNCT3_LW_SW, X0, 8),
        # 0x14: BEQ  x10, x0, +8   (Branch not taken, 110 != 0. Target: 0x14 + 8 = 0x1C)
        encode_b_type(OP_BRANCH, 8, FUNCT3_BEQ, 10, X0),
        # 0x18: BEQ  x10, x11, +8  (Branch taken, 110 == 110. Jumps to 0x18 + 8 = 0x20)
        encode_b_type(OP_BRANCH, 8, FUNCT3_BEQ, 10, 11),
        # 0x1C: ADDI x10, x0, 999   (This instruction is skipped)
        encode_i_type(OP_I_TYPE_ARITH, 10, FUNCT3_ADD_SUB_ADDI, X0, 999),
        # 0x20: ADDI x11, x0, 777   (Landed here after branch)
        encode_i_type(OP_I_TYPE_ARITH, 11, FUNCT3_ADD_SUB_ADDI, X0, 777)
    ]

    dut._log.info("Loading program into instruction memory...")
    for i, instr_val in enumerate(program):
        imem[i].value = instr_val
        
    # Wait for memory to load before starting execution
    await FallingEdge(dut.clk)
    dut._log.info("Program loaded. Starting execution.")


    # 3. Execute and verify cycle-by-cycle
    dut._log.info("--- Cycle 1: Executing ADDI x10, x0, 50 ---")
    await RisingEdge(dut.clk)
    assert dut.debug_pc.value == 4, "PC should be 4 after first instruction"
    assert dut.debug_reg_x10.value == 50, "x10 should be 50"

    dut._log.info("--- Cycle 2: Executing ADDI x11, x0, 60 ---")
    await RisingEdge(dut.clk)
    assert dut.debug_pc.value == 8, "PC should be 8"
    assert dut.debug_reg_x11.value == 60, "x11 should be 60"
    assert dut.debug_reg_x10.value == 50, "x10 should remain 50"

    dut._log.info("--- Cycle 3: Executing ADD x10, x10, x11 ---")
    await RisingEdge(dut.clk)
    assert dut.debug_pc.value == 12, "PC should be 12"
    assert dut.debug_reg_x10.value == 110, "x10 should be 110 (50+60)"

    dut._log.info("--- Cycle 4: Executing SW x10, 8(x0) ---")
    await RisingEdge(dut.clk)
    assert dut.debug_pc.value == 16, "PC should be 16"
    # Verify memory content. Address 8 is word 2 (8 / 4 = 2).
    dmem_word_addr = 8 // 4
    assert dmem[dmem_word_addr].value == 110, f"Memory at word addr {dmem_word_addr} should be 110"
    assert dut.debug_reg_x10.value == 110, "x10 should not change on a store"

    dut._log.info("--- Cycle 5: Executing LW x11, 8(x0) ---")
    await RisingEdge(dut.clk)
    assert dut.debug_pc.value == 20, "PC should be 20"
    assert dut.debug_reg_x11.value == 110, "x11 should be 110 after LW"

    dut._log.info("--- Cycle 6: Executing BEQ x10, x0, +8 (Branch NOT taken) ---")
    await RisingEdge(dut.clk)
    # Branch is not taken, so PC increments normally from 0x14 to 0x18 (20 -> 24)
    assert dut.debug_pc.value == 24, "PC should be 24 (branch not taken)"
    assert dut.debug_reg_x10.value == 110, "x10 should be unchanged"

    dut._log.info("--- Cycle 7: Executing BEQ x10, x11, +8 (Branch TAKEN) ---")
    await RisingEdge(dut.clk)
    # Branch is taken (110 == 110). Target is 0x18 + 8 = 0x20 (24 + 8 = 32)
    assert dut.debug_pc.value == 32, "PC should be 32 (branch taken)"
    # The instruction at 0x1C (ADDI x10, x0, 999) was skipped, so x10 is still 110
    assert dut.debug_reg_x10.value == 110, "x10 should not have changed"

    dut._log.info("--- Cycle 8: Executing ADDI x11, x0, 777 (Landed after branch) ---")
    await RisingEdge(dut.clk)
    assert dut.debug_pc.value == 36, "PC should be 36"
    assert dut.debug_reg_x11.value == 777, "x11 should be 777"
    assert dut.debug_reg_x10.value == 110, "x10 should still be 110"

    dut._log.info("🎉 Full RISC Processor test passed successfully! 🎉")