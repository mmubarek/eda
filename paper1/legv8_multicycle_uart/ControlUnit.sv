module ControlUnit #(
  parameter INST_WIDTH = 32,
  parameter ALU_OP_WIDTH = 4,
  parameter OPCODE_ADD_R = 11'b10001011000,
  parameter OPCODE_SUB_R = 11'b11001011000,
  parameter OPCODE_AND_R = 11'b10001010000,
  parameter OPCODE_ORR_R = 11'b10101010000,
  parameter OPCODE_EOR_R = 11'b01001010000,
  parameter OPCODE_LSL_R = 11'b11010011011,
  parameter OPCODE_LSR_R = 11'b11010011010,
  parameter OPCODE_ASR_R = 11'b11010011110,
  parameter OPCODE_ROR_R = 11'b11010011111,
  parameter OPCODE_BR_R = 11'b11010110000,
  parameter OPCODE_ADDI_I = 10'b1001000100,
  parameter OPCODE_SUBI_I = 10'b1101000100,
  parameter OPCODE_LDUR_D = 11'b11111000010,
  parameter OPCODE_STUR_D = 11'b11111000000,
  parameter OPCODE_CBZ_CB = 8'b10110100,
  parameter OPCODE_CBNZ_CB = 8'b10110101,
  parameter OPCODE_B_B = 6'b000101,
  parameter OPCODE_BL_B = 6'b100101,
  parameter OPCODE_HALT_S = 11'b11111111111,
  parameter ALU_ADD = 4'b0000,
  parameter ALU_SUB = 4'b0001,
  parameter ALU_AND = 4'b0010,
  parameter ALU_ORR = 4'b0011,
  parameter ALU_EOR = 4'b0100,
  parameter ALU_LSL = 4'b0101,
  parameter ALU_LSR = 4'b0110,
  parameter ALU_PASS_B = 4'b0111,
  parameter ALU_ASR = 4'b1000,
  parameter ALU_ROR = 4'b1001
)
(
  input logic [INST_WIDTH-1:0] instr_in,
  input logic  zero_flag_in,
  output logic  reg_write_out,
  output logic  mem_to_reg_out,
  output logic  mem_read_out,
  output logic  mem_write_out,
  output logic  alu_src_out,
  output logic  uncond_branch_out,
  output logic  cond_branch_out,
  output logic [ALU_OP_WIDTH-1:0] alu_op_out,
  output logic  halt_signal_out,
  output logic  is_cbz_out,
  output logic  is_cbnz_out,
  output logic  is_stur_out,
  output logic  branch_reg_out,
  output logic  branch_link_out
);

  logic [10:0] opcode11;
  logic [9:0]  opcode10;
  logic [7:0]  opcode8;
  logic [5:0]  opcode6;

  always_comb begin
    reg_write_out      = 1'b0;
    mem_to_reg_out     = 1'b0;
    mem_read_out       = 1'b0;
    mem_write_out      = 1'b0;
    alu_src_out        = 1'b0;
    uncond_branch_out  = 1'b0;
    cond_branch_out    = 1'b0;
    alu_op_out         = '0;
    halt_signal_out    = 1'b0;
    is_cbz_out         = 1'b0;
    is_cbnz_out        = 1'b0;
    is_stur_out        = 1'b0;
    branch_reg_out     = 1'b0;
    branch_link_out    = 1'b0;

    opcode11 = instr_in[31:21];
    opcode10 = instr_in[31:22];
    opcode8  = instr_in[31:24];
    opcode6  = instr_in[31:26];

    // Use a single, prioritized case structure to prevent conflicts
    case (opcode6)
      OPCODE_B_B: begin
        uncond_branch_out = 1'b1;
        alu_op_out        = ALU_PASS_B;
      end
      OPCODE_BL_B: begin
        reg_write_out      = 1'b1;
        uncond_branch_out  = 1'b1;
        branch_link_out    = 1'b1;
        alu_op_out         = ALU_PASS_B;
      end
      default: begin
        case (opcode8)
          OPCODE_CBZ_CB: begin
            is_cbz_out        = 1'b1;
            cond_branch_out   = 1'b1;
            alu_op_out        = ALU_PASS_B;
          end
          OPCODE_CBNZ_CB: begin
            is_cbnz_out       = 1'b1;
            cond_branch_out   = 1'b1;
            alu_op_out        = ALU_PASS_B;
          end
          default: begin
            case(opcode10)
              OPCODE_ADDI_I: begin
                reg_write_out  = 1'b1;
                alu_src_out    = 1'b1;
                alu_op_out     = ALU_ADD;
              end
              OPCODE_SUBI_I: begin
                reg_write_out  = 1'b1;
                alu_src_out    = 1'b1;
                alu_op_out     = ALU_SUB;
              end
              default: begin
                case(opcode11)
                  OPCODE_ADD_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_ADD;
                  end
                  OPCODE_SUB_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_SUB;
                  end
                  OPCODE_AND_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_AND;
                  end
                  OPCODE_ORR_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_ORR;
                  end
                  OPCODE_EOR_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_EOR;
                  end
                  OPCODE_LSL_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_LSL;
                  end
                  OPCODE_LSR_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_LSR;
                  end
                  OPCODE_ASR_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_ASR;
                  end
                  OPCODE_ROR_R: begin
                    reg_write_out  = 1'b1;
                    alu_src_out    = 1'b0;
                    alu_op_out     = ALU_ROR;
                  end
                  OPCODE_BR_R: begin
                    uncond_branch_out  = 1'b1;
                    branch_reg_out     = 1'b1;
                    alu_op_out         = ALU_PASS_B;
                  end
                  OPCODE_LDUR_D: begin
                    reg_write_out  = 1'b1;
                    mem_to_reg_out = 1'b1;
                    mem_read_out   = 1'b1;
                    alu_src_out    = 1'b1;
                    alu_op_out     = ALU_ADD;
                  end
                  OPCODE_STUR_D: begin
                    is_stur_out    = 1'b1;
                    mem_write_out  = 1'b1;
                    alu_src_out    = 1'b1;
                    alu_op_out     = ALU_ADD;
                  end
                  OPCODE_HALT_S: begin
                    halt_signal_out = 1'b1;
                  end
                  default: begin
                  end
                endcase
              end
            endcase
          end
        endcase
      end
    endcase
  end

endmodule
