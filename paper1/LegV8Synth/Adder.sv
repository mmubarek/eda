module Adder
(
  input logic [7:0] in1,
  input logic [7:0] in2,
  output logic [7:0] sum
);

  assign sum = in1 + in2;

endmodule