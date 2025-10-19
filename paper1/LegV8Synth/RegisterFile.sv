// File: register_file.sv
module RegisterFile (
  input logic clk,
  input logic rst,
  input logic [2:0] read_addr1,
  input logic [2:0] read_addr2,
  input logic [2:0] write_addr,
  input logic [7:0] write_data,
  input logic write_en,
  output logic [7:0] read_data1,
  output logic [7:0] read_data2
);

  localparam DATA_WIDTH = 8;
  localparam REG_ADDR_WIDTH = 3;
  localparam NUM_REGISTERS = (1 << REG_ADDR_WIDTH);

  logic [DATA_WIDTH-1:0] registers [NUM_REGISTERS-1:0];

  // Synchronous write, preventing writes to R0
  always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
      for (int i = 0; i < NUM_REGISTERS; i++) begin
        registers[i] <= {DATA_WIDTH{1'b0}};
      end
    end else begin
      // FIX: Only write if write_en is high AND the destination is not R0
      if (write_en && (write_addr != 0)) begin
        registers[write_addr] <= write_data;
      end
    end
  end

  // Asynchronous read, forcing R0 to be 0
  // FIX: If reading address 0, output 0, otherwise output the register value.
  assign read_data1 = (read_addr1 == 0) ? {DATA_WIDTH{1'b0}} : registers[read_addr1];
  assign read_data2 = (read_addr2 == 0) ? {DATA_WIDTH{1'b0}} : registers[read_addr2];

endmodule
