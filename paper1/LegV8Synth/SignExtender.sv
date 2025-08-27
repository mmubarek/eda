module SignExtender (
  input logic [5:0] in_val,
  output logic [7:0] out_val
);

  // Sign-extend in_val (6 bits) to out_val (8 bits)
  // The MSB of in_val (in_val[5]) is replicated to fill the higher bits of out_val.
  assign out_val = {{2{in_val[5]}}, in_val};

endmodule