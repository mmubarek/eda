import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Opcodes MATCHING the ControlUnit.sv
OPCODE_R_TYPE = 0b0000
OPCODE_LW     = 0b0001
OPCODE_SW     = 0b0010
OPCODE_BEQ    = 0b0011
OPCODE_JUMP   = 0b0100
OPCODE_ADDI   = 0b0101

# Lists to identify instruction formats for the decoder
I_TYPE_OPCODES = [OPCODE_ADDI, OPCODE_LW]
R_TYPE_OPCODES = [OPCODE_R_TYPE]
B_TYPE_OPCODES = [OPCODE_BEQ, OPCODE_SW]
J_TYPE_OPCODES = [OPCODE_JUMP]
WRITE_BACK_OPCODES = [OPCODE_R_TYPE, OPCODE_ADDI, OPCODE_LW]

# Instruction Encodings
IM_CONTENT = {
    # PC: Instruction,        # Decoded Instruction
    0:  0b0101_000_001_000101, # ADDI R1, R0, 5
    2:  0b0101_000_010_001010, # ADDI R2, R0, 10
    4:  0b0000_001_010_011_000, # ADD  R3, R1, R2
    6:  0b0001_000_100_010100, # LW   R4, R0, 20
    8:  0b0010_000_011_011001, # SW   R3, R0, 25
    10: 0b0011_001_010_000100, # BEQ  R1, R2, +4
    12: 0b0100_00000000_0000,   # JUMP 0
    14: 0x0000                  # NOP
}

def decode_instruction(instruction_val):
    opcode = (instruction_val >> 12) & 0xF
    rs1_addr, rs2_addr, rd_addr, immediate, jump_addr_8bit = 0, 0, 0, 0, 0
    if opcode in R_TYPE_OPCODES:
        rs1_addr, rs2_addr, rd_addr = (instruction_val >> 9) & 0x7, (instruction_val >> 6) & 0x7, (instruction_val >> 3) & 0x7
    elif opcode in I_TYPE_OPCODES:
        rs1_addr, rd_addr, immediate = (instruction_val >> 9) & 0x7, (instruction_val >> 6) & 0x7, instruction_val & 0x3F
    elif opcode in B_TYPE_OPCODES:
        rs1_addr, rs2_addr, immediate = (instruction_val >> 9) & 0x7, (instruction_val >> 6) & 0x7, instruction_val & 0x3F
    elif opcode in J_TYPE_OPCODES:
        jump_addr_8bit = instruction_val & 0xFF
    sign_extended_immediate = immediate | (0b11000000 if (immediate & 0b00100000) else 0)
    return opcode, rs1_addr, rs2_addr, rd_addr, immediate, sign_extended_immediate, jump_addr_8bit

@cocotb.test()
async def lev8_processor_test(dut):
    """Test the Lev8 Single Cycle Processor with a simple program."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    expected_regs = {i: 0 for i in range(8)}
    expected_mem = {i: 0 for i in range(256)}
    expected_mem[20] = 0xAA # Pre-load data for the LW test
    current_pc = 0

    dut.rst.value = 1
    
    # Initialize Instruction Memory
    dut._log.info("--- Initializing DUT Instruction Memory (during reset) ---")
    for addr, instr in IM_CONTENT.items():
        high_byte = (instr >> 8) & 0xFF
        low_byte = instr & 0xFF
        dut.IM_inst.mem[addr].value = high_byte     # mem[addr]   = MSB
        dut.IM_inst.mem[addr + 1].value = low_byte  # mem[addr+1] = LSB

    # FIX: Initialize Data Memory in the DUT to match the test's golden model
    dut._log.info("--- Initializing DUT Data Memory (during reset) ---")
    for addr, data in expected_mem.items():
        if data != 0:
            dut.DM_inst.mem[addr].value = data
            dut._log.info(f"  DUT.DM_inst.mem[{addr}] = 0x{data:02X}")

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    
    dut._log.info("--- Reset complete, starting program execution ---")

    for cycle in range(15):
        dut._log.info(f"\n--- Cycle {cycle} ---")
        
        await Timer(1, units="ns") 

        assert dut.debug_pc_out.value.integer == current_pc
        dut._log.info(f"assert equality")
        expected_instruction = IM_CONTENT.get(current_pc, 0x0000)
        assert dut.debug_instruction_out.value.integer == expected_instruction

        dut._log.info(f"  PC: {current_pc} | Instruction: 0x{dut.debug_instruction_out.value.integer:04X}")

        opcode, rs1_addr, rs2_addr, rd_addr, immediate, sign_extended_immediate, jump_addr_8bit = \
            decode_instruction(expected_instruction)

        src1_val = expected_regs.get(rs1_addr, 0)
        expected_alu_result = 0
        predicted_reg_write_data = 0
        next_pc = (current_pc + 2) & 0xFF

        if opcode == OPCODE_ADDI:
            alu_src2 = sign_extended_immediate
            expected_alu_result = (src1_val + alu_src2) & 0xFF
            predicted_reg_write_data = expected_alu_result
            if rd_addr != 0: expected_regs[rd_addr] = predicted_reg_write_data
        elif opcode == OPCODE_R_TYPE:
            alu_src2 = expected_regs.get(rs2_addr, 0)
            expected_alu_result = (src1_val + alu_src2) & 0xFF
            predicted_reg_write_data = expected_alu_result
            if rd_addr != 0: expected_regs[rd_addr] = predicted_reg_write_data
        elif opcode == OPCODE_LW:
            dut._log.info(f"Beginning of LW ... ")
            alu_src2 = sign_extended_immediate
            mem_addr = (src1_val + alu_src2) & 0xFF
            expected_alu_result = mem_addr
            predicted_reg_write_data = expected_mem.get(mem_addr, 0)
            if rd_addr != 0: expected_regs[rd_addr] = predicted_reg_write_data
            dut._log.info(f"End of LW ... ")
        elif opcode == OPCODE_SW:
            alu_src2 = sign_extended_immediate
            mem_addr = (src1_val + alu_src2) & 0xFF
            data_to_write = expected_regs.get(rs2_addr, 0)
            expected_mem[mem_addr] = data_to_write
            expected_alu_result = mem_addr
        elif opcode == OPCODE_BEQ:
            src2_val = expected_regs.get(rs2_addr, 0)
            expected_alu_result = (src1_val - src2_val) & 0xFF
            if expected_alu_result == 0:
                next_pc = (current_pc + 2 + sign_extended_immediate) & 0xFF
        elif opcode == OPCODE_JUMP:
            next_pc = jump_addr_8bit
        
        # Log the prediction AFTER it's been calculated
        dut._log.info(f"  PREDICT: ALU_res={expected_alu_result}, RegWriteData={predicted_reg_write_data}, NextPC={next_pc}")

        assert dut.debug_alu_result.value.integer == expected_alu_result
        if opcode in WRITE_BACK_OPCODES:
            assert dut.debug_reg_write_data.value.integer == predicted_reg_write_data

        dut._log.info(f"  ASSERT: OK")
        
        dut._log.info(f"Just before RisingEdge")
        await RisingEdge(dut.clk)
        dut._log.info(f"Just After RisingEdge")
       
        current_pc = next_pc
        
        if cycle > 8 and current_pc == 0:
            dut._log.info("\n--- Program has looped back to PC 0, ending test. ---")
            break

    dut._log.info("\n--- Test Finished ---")
    assert current_pc == 0
    assert expected_regs[1] == 5
    assert expected_regs[2] == 10
    assert expected_regs[3] == 15
    assert expected_regs[4] == 0xAA
    assert expected_mem[25] == 15
    dut._log.info(f"Final Regs OK: R1={expected_regs[1]}, R2={expected_regs[2]}, R3={expected_regs[3]}, R4={expected_regs[4]}")
    dut._log.info(f"Final Mem OK: Mem[25]={expected_mem[25]}")
    dut._log.info("Testbench passed successfully!")
