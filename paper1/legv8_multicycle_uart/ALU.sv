module ALU #(
  parameter DATA_WIDTH = 32,
  parameter ALU_OP_WIDTH = 4,
  parameter ALU_ADD = 4'b0000,
  parameter ALU_SUB = 4'b0001,
  parameter ALU_AND = 4'b0010,
  parameter ALU_ORR = 4'b0011,
  parameter ALU_EOR = 4'b0100,
  parameter ALU_LSL = 4'b0101,
  parameter ALU_LSR = 4'b0110,
  parameter ALU_PASS_B = 4'b0111,
  parameter ALU_ASR = 4'b1000, // New
  parameter ALU_ROR = 4'b1001  // New
)
(
  input logic [DATA_WIDTH-1:0] operand_a_in,
  input logic [DATA_WIDTH-1:0] operand_b_in,
  input logic [ALU_OP_WIDTH-1:0] alu_op_in,
  output logic [DATA_WIDTH-1:0] result_out,
  output logic  zero_flag_out
);

  // Determine number of bits required to encode shift amount
  localparam int SHIFT_AMT_WIDTH = (DATA_WIDTH > 1) ? $clog2(DATA_WIDTH) : 1;
  logic [SHIFT_AMT_WIDTH-1:0] shift_amt;

  always_comb begin
    // extract shift amount from operand_b_in (lower bits)
    shift_amt = operand_b_in[SHIFT_AMT_WIDTH-1:0];

    unique case (alu_op_in)
      ALU_ADD: begin
        result_out = operand_a_in + operand_b_in;
      end

      ALU_SUB: begin
        result_out = operand_a_in - operand_b_in;
      end

      ALU_AND: begin
        result_out = operand_a_in & operand_b_in;
      end

      ALU_ORR: begin
        result_out = operand_a_in | operand_b_in;
      end

      ALU_EOR: begin
        result_out = operand_a_in ^ operand_b_in;
      end

      ALU_LSL: begin
        // logical shift left by amount in lower bits of operand_b_in
        result_out = operand_a_in << shift_amt;
      end

      ALU_LSR: begin
        // logical shift right by amount in lower bits of operand_b_in
        result_out = operand_a_in >> shift_amt;
      end

      ALU_ASR: begin // New
        // Arithmetic Shift Right
        result_out = $signed(operand_a_in) >>> shift_amt;
      end

      ALU_ROR: begin // New
        // Rotate Right
        result_out = (operand_a_in >> shift_amt) | (operand_a_in << (DATA_WIDTH - shift_amt));
      end

      ALU_PASS_B: begin
        // pass-through operand B
        result_out = operand_b_in;
      end

      default: begin
        // for undefined opcodes, drive zero
        result_out = '0;
      end
    endcase

    // zero flag asserted when result is zero
    zero_flag_out = (result_out == {DATA_WIDTH{1'b0}});
  end

endmodule
