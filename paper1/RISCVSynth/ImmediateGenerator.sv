module ImmediateGenerator
#(
  parameter int INSTR_WIDTH = 32,
  parameter int DATA_WIDTH = 32
)
(
  input logic [INSTR_WIDTH-1:0] instr,
  input logic [1:0] imm_type_sel, // From ControlUnit
  output logic [DATA_WIDTH-1:0] immediate
);

  import RISC_ISA_pkg::*; // Use constants for the type selector

  always_comb begin
    // Default to 0
    immediate = '0;

    case (imm_type_sel)
      // For ADDI, LW, JALR
      IMM_TYPE_I: begin
        // Sign-extend from the MSB of the immediate field (instr[31])
        immediate = {{20{instr[31]}}, instr[31:20]};
      end

      // For SW
      IMM_TYPE_S: begin
        // Reassemble from two parts and sign-extend from instr[31]
        immediate = {{20{instr[31]}}, instr[31:25], instr[11:7]};
      end

      // For BEQ
      IMM_TYPE_B: begin
        // Reassemble from multiple parts and sign-extend from instr[31]
        // The immediate is 13 bits and represents a byte offset.
        immediate = {{20{instr[31]}}, instr[7], instr[30:25], instr[11:8], 1'b0};
      end
      
      // Default case handles other types (U, J) if they were added
      default: immediate = '0;
    endcase
  end

endmodule