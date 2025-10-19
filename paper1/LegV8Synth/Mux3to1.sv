module Mux3to1
(
  input logic [7:0] in0,
  input logic [7:0] in1,
  input logic [7:0] in2,
  input logic [1:0] sel,
  output logic [7:0] out
);

  always_comb begin
    case (sel)
      2'b00: out = in0;
      2'b01: out = in1;
      2'b10: out = in2;
      default: out = '0; // Default to 0 for unselected cases
    endcase
  end

endmodule