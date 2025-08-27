module ALU
(
  input logic [7:0] src1,
  input logic [7:0] src2,
  input logic [2:0] alu_op,
  output logic [7:0] result,
  output logic zero
);

  logic [7:0] alu_result_internal;

  always_comb begin
    alu_result_internal = '0; // Default value

    case (alu_op)
      3'b000: alu_result_internal = src1 + src2; // ADD
      3'b001: alu_result_internal = src1 - src2; // SUB
      3'b010: alu_result_internal = src1 & src2; // AND
      3'b011: alu_result_internal = src1 | src2; // OR
      3'b100: alu_result_internal = src1 ^ src2; // XOR
      3'b101: alu_result_internal = (src1 < src2) ? 8'd1 : 8'd0; // SLT (Set Less Than)
      3'b110: alu_result_internal = src1 << src2; // SLL (Shift Left Logical)
      3'b111: alu_result_internal = src1 >> src2; // SRL (Shift Right Logical)
      default: alu_result_internal = '0; // Should not be reached for 3-bit alu_op
    endcase
  end

  assign result = alu_result_internal;
  assign zero = (alu_result_internal == '0);

endmodule