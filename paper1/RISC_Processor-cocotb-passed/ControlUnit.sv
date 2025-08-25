module ControlUnit (
  input logic [6:0] opcode,
  input logic [2:0] funct3,
  input logic [6:0] funct7,
  input logic alu_zero_flag,
  output logic [1:0] pc_next_sel,
  output logic [2:0] alu_op,
  output logic alu_src_a_sel,
  output logic alu_src_b_sel,
  output logic [1:0] imm_type_sel,
  output logic mem_read_en,
  output logic mem_write_en,
  output logic reg_write_en,
  output logic [1:0] wb_src_sel
);

  import RISC_ISA_pkg::*;

  always_comb begin
    // --- Start with safe, default NOP values ---
    pc_next_sel   = PC_SRC_INC;
    alu_op        = ALU_ADD;
    alu_src_a_sel = ALU_SRC_A_REG;
    alu_src_b_sel = ALU_SRC_B_REG;
    imm_type_sel  = IMM_TYPE_I; // Default to I-type
    mem_read_en   = 1'b0;
    mem_write_en  = 1'b0;
    reg_write_en  = 1'b0;
    wb_src_sel    = WB_SRC_ALU;

    // --- Decode opcode to set control signals ---
    case (opcode)
      OP_R_TYPE: begin
        reg_write_en  = 1'b1;
        if (funct7 == FUNCT7_SUB) begin
          alu_op = ALU_SUB;
        end else begin
          alu_op = ALU_ADD;
        end
      end

      OP_I_TYPE_ARITH: begin // ADDI
        reg_write_en  = 1'b1;
        alu_src_b_sel = ALU_SRC_B_IMM;
        imm_type_sel  = IMM_TYPE_I; // Explicitly set
        alu_op        = ALU_ADD;
      end

      OP_LOAD: begin // LW
        mem_read_en   = 1'b1;
        reg_write_en  = 1'b1;
        alu_src_b_sel = ALU_SRC_B_IMM;
        imm_type_sel  = IMM_TYPE_I; // Explicitly set
        wb_src_sel    = WB_SRC_MEM;
        alu_op        = ALU_ADD;
      end

      OP_STORE: begin // SW
        mem_write_en  = 1'b1;
        alu_src_b_sel = ALU_SRC_B_IMM;
        imm_type_sel  = IMM_TYPE_S; // S-type immediate
        alu_op        = ALU_ADD;
      end

      OP_BRANCH: begin // BEQ
        imm_type_sel  = IMM_TYPE_B; // B-type immediate
        alu_op        = ALU_SUB;
        if (alu_zero_flag) begin
          pc_next_sel = PC_SRC_BRANCH;
        end
      end


      // J-type JAL instruction
      7'b1101111: begin // JAL
        reg_write_en  = 1'b1;
        alu_src_a_sel = 1'b1; // ALU operand A is PC
        alu_src_b_sel = 1'b1; // ALU operand B is immediate
        imm_type_sel  = 2'b11; // J-type immediate (shares encoding with U-type, immediate generator distinguishes by opcode)
        alu_op        = 3'b100; // PC-relative/Immediate to Reg (ADD)
        pc_next_sel   = 2'b10; // Next PC is jump target (PC + J-immediate)
        wb_src_sel    = 2'b10; // Write-back source is PC + 4 (link address)
      end

      // I-type JALR instruction
      7'b1100111: begin // JALR
        reg_write_en  = 1'b1;
        alu_src_b_sel = 1'b1; // ALU operand B is immediate
        imm_type_sel  = 2'b00; // I-type immediate
        alu_op        = 3'b100; // PC-relative/Immediate to Reg (ADD)
        pc_next_sel   = 2'b11; // Next PC is ALU result (rs1 + I-immediate)
        wb_src_sel    = 2'b10; // Write-back source is PC + 4 (link address)
      end

      // U-type LUI instruction
      7'b0110111: begin // LUI
        reg_write_en  = 1'b1;
        alu_src_a_sel = 1'b0; // ALU operand A is Read data 1 (unused for LUI)
        alu_src_b_sel = 1'b1; // ALU operand B is immediate
        imm_type_sel  = 2'b11; // U-type immediate
        alu_op        = 3'b100; // PC-relative/Immediate to Reg (ADD, effectively passes immediate)
        wb_src_sel    = 2'b00; // Write-back source is ALU result
      end

      // U-type AUIPC instruction
      7'b0010111: begin // AUIPC
        reg_write_en  = 1'b1;
        alu_src_a_sel = 1'b1; // ALU operand A is PC
        alu_src_b_sel = 1'b1; // ALU operand B is immediate
        imm_type_sel  = 2'b11; // U-type immediate
        alu_op        = 3'b100; // PC-relative/Immediate to Reg (ADD)
        wb_src_sel    = 2'b00; // Write-back source is ALU result
      end

      default: begin
        // For unsupported or invalid opcodes, outputs remain at their default (NOP) values.
      end
    endcase
  end

endmodule