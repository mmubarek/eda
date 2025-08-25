module Mux2to1
(
  input logic [7:0] in0,
  input logic [7:0] in1,
  input logic sel,
  output logic [7:0] out
);

  assign out = sel ? in1 : in0;

endmodule