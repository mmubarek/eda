// Corrected and Parameterized RegisterFile.sv
module RegisterFile
#(
  // These parameters can now be set during instantiation
  parameter DATA_WIDTH      = 32,
  parameter REG_COUNT       = 32
)
(
  // The address width is now derived from the parameter
  input logic [$clog2(REG_COUNT)-1:0] rs1_addr,
  input logic [$clog2(REG_COUNT)-1:0] rs2_addr,
  input logic [$clog2(REG_COUNT)-1:0] rd_addr,
  
  input logic clk,
  input logic rst_n,
  input logic [DATA_WIDTH-1:0] rd_data,
  input logic reg_write_en,
  output logic [DATA_WIDTH-1:0] rs1_data,
  output logic [DATA_WIDTH-1:0] rs2_data
);

  // Internal storage for the general-purpose registers
  // The size of this array is now based on the REG_COUNT parameter
  logic [DATA_WIDTH-1:0] registers [REG_COUNT-1:0];

  // Synchronous write port logic
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // On active-low reset, initialize all registers to 0
      for (int i = 0; i < REG_COUNT; i++) begin
        registers[i] <= '0;
      end
    end else if (reg_write_en) begin
      // If write enable is high, write data to the specified register.
      // Register 0 (x0) is typically hardwired to 0 and cannot be written.
      if (rd_addr != '0) begin
        registers[rd_addr] <= rd_data;
      end
    end
  end

  // Asynchronous read ports logic
  // Read data from rs1_addr. If rs1_addr is 0, output 0 (x0 behavior).
  assign rs1_data = (rs1_addr == '0) ? '0 : registers[rs1_addr];

  // Read data from rs2_addr. If rs2_addr is 0, output 0 (x0 behavior).
  assign rs2_data = (rs2_addr == '0) ? '0 : registers[rs2_addr];

endmodule