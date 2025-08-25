module DataMemory (
  input logic clk,
  input logic [7:0] addr,
  input logic [7:0] write_data,
  input logic write_en,
  input logic read_en,
  output logic [7:0] read_data
);

  // Memory declaration: 2^8 = 256 locations, each 8 bits wide
  logic [7:0] mem [255:0];

  // Write operation: Synchronous write on positive clock edge
  always_ff @(posedge clk) begin
    if (write_en) begin
      mem[addr] <= write_data;
    end
  end

  // FIX: Read operation moved into an always_comb block.
  // This makes the read path truly combinational and prevents simulator race conditions,
  // ensuring data is available within the same cycle for the LW instruction.
  always_comb begin
    if (read_en) begin
      read_data = mem[addr];
    end else begin
      read_data = 8'b0; // Output 0 if read is not enabled
    end
  end

endmodule


