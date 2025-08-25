module ALU
#(
  parameter int DATA_WIDTH = 32
)
(
  input logic [DATA_WIDTH-1:0] operand_a,
  input logic [DATA_WIDTH-1:0] operand_b,
  input logic [2:0] alu_op,
  output logic [DATA_WIDTH-1:0] result,
  output logic zero
);

  logic [DATA_WIDTH-1:0] result_int;

  // ALU operations based on alu_op
  always_comb begin
    result_int = '0; // Default value for result_int

    case (alu_op)
      3'b000: begin // ADD: operand_a + operand_b
        result_int = operand_a + operand_b;
      end
      3'b001: begin // SUB: operand_a - operand_b
        result_int = operand_a - operand_b;
      end
      3'b010: begin // AND: operand_a & operand_b
        result_int = operand_a & operand_b;
      end
      3'b011: begin // OR: operand_a | operand_b
        result_int = operand_a | operand_b;
      end
      3'b100: begin // XOR: operand_a ^ operand_b
        result_int = operand_a ^ operand_b;
      end
      3'b101: begin // SLT (Set Less Than - signed comparison)
        // If operand_a is less than operand_b (signed), result is 1, else 0
        result_int = ($signed(operand_a) < $signed(operand_b)) ? 1 : 0;
      end
      3'b110: begin // SLL (Shift Left Logical)
        // Shift amount is typically the lower 5 bits for 32-bit data
        result_int = operand_a << operand_b[4:0];
      end
      3'b111: begin // SRL (Shift Right Logical)
        // Shift amount is typically the lower 5 bits for 32-bit data
        result_int = operand_a >> operand_b[4:0];
      end
      default: begin // Default case for any unhandled alu_op values
        result_int = '0;
      end
    endcase
  end

  // Assign the calculated internal result to the output port
  assign result = result_int;

  // Zero flag is high if the result is all zeros
  assign zero = (result_int == '0);

endmodule