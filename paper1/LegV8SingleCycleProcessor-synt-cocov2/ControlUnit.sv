      
// File: control_unit.sv
module ControlUnit (
  input logic [3:0] opcode,
  output logic reg_write_en,
  output logic mem_write_en,
  output logic mem_read_en,
  output logic alu_src_sel,
  output logic [1:0] mem_to_reg_sel,
  output logic branch_en,
  output logic jump_en,
  output logic [2:0] alu_op,
  output logic rd_sel_i_type // NEW: Selects rd field for I-type instructions
);

  localparam OP_R_TYPE = 4'b0000;
  localparam OP_LW     = 4'b0001;
  localparam OP_SW     = 4'b0010;
  localparam OP_BEQ    = 4'b0011;
  localparam OP_JUMP   = 4'b0100;
  localparam OP_ADDI   = 4'b0101;

  localparam ALU_ADD = 3'b000;
  localparam ALU_SUB = 3'b001;

  always_comb begin
    // Defaults
    reg_write_en   = 1'b0;
    mem_write_en   = 1'b0;
    mem_read_en    = 1'b0;
    alu_src_sel    = 1'b0;
    mem_to_reg_sel = 2'b00;
    branch_en      = 1'b0;
    jump_en        = 1'b0;
    alu_op         = ALU_ADD;
    rd_sel_i_type  = 1'b0; // NEW: Default to R-type rd source

    case (opcode)
      OP_R_TYPE: begin
        reg_write_en   = 1'b1;
      end
      OP_LW: begin
        reg_write_en   = 1'b1;
        mem_read_en    = 1'b1;
        alu_src_sel    = 1'b1;
        mem_to_reg_sel = 2'b01;
        rd_sel_i_type  = 1'b1; // NEW: Use I-type rd field
      end
      OP_SW: begin
        mem_write_en   = 1'b1;
        alu_src_sel    = 1'b1;
      end
      OP_BEQ: begin
        branch_en      = 1'b1;
        alu_op         = ALU_SUB;
      end
      OP_JUMP: begin
        jump_en        = 1'b1;
      end
      OP_ADDI: begin
        reg_write_en   = 1'b1;
        alu_src_sel    = 1'b1;
        rd_sel_i_type  = 1'b1; // NEW: Use I-type rd field
      end
      default: begin
      end
    endcase
  end
endmodule

    
