module Adder #(
    parameter ADDRESS_WIDTH = 8
)
(
  input logic [ADDRESS_WIDTH-1:0] in1,
  input logic [ADDRESS_WIDTH-1:0] in2,
  output logic [ADDRESS_WIDTH-1:0] sum
);

  assign sum = in1 + in2;

endmodule