module RegisterFile #(
  parameter DATA_WIDTH = 32,
  parameter REG_COUNT = 32,
  parameter REG_ADDR_WIDTH = 5
)
(
  input logic  clk,
  input logic  rst,
  input logic  write_en_in,
  input logic [REG_ADDR_WIDTH-1:0] read_addr1_in,
  input logic [REG_ADDR_WIDTH-1:0] read_addr2_in,
  input logic [REG_ADDR_WIDTH-1:0] write_addr_in,
  input logic [DATA_WIDTH-1:0] write_data_in,
  output logic [DATA_WIDTH-1:0] read_data1_out,
  output logic [DATA_WIDTH-1:0] read_data2_out,
  output logic [DATA_WIDTH-1:0] x1_val_out
);

  // Address of the hardwired zero register (XZR / R31 by default)
  // FIX: Explicitly cast to correct width to resolve Verilator width warning - Pitfall 5
  localparam [REG_ADDR_WIDTH-1:0] XZR_ADDR = REG_ADDR_WIDTH'(REG_COUNT - 1);

  // Register storage. Note: writes to XZR are ignored and reads from XZR return zero.
  logic [DATA_WIDTH-1:0] regs [0:REG_COUNT-1];

  // Synchronous write: on posedge clk, write if enabled and not targeting XZR
  always_ff @(posedge clk) begin
    if (rst) begin
      for (int i = 0; i < REG_COUNT; i++) begin
        regs[i] <= '0;
      end
    end else if (write_en_in) begin
      if (write_addr_in != XZR_ADDR) begin
        regs[write_addr_in] <= write_data_in;
      end
    end
  end

  // Combinational read ports with write-through bypass:
  // If reading the XZR address, return zero.
  // If a write to the same address is requested this cycle, reflect write_data_in (bypass).
  always_comb begin
    // Default outputs
    if (read_addr1_in == XZR_ADDR) begin
      read_data1_out = '0;
    end else begin
      read_data1_out = regs[read_addr1_in];
    end

    if (read_addr2_in == XZR_ADDR) begin
      read_data2_out = '0;
    end else begin
      read_data2_out = regs[read_addr2_in];
    end

    // Bypass logic (write-through) - show new data immediately if writing same address
    if (write_en_in && (write_addr_in != XZR_ADDR)) begin
      if (write_addr_in == read_addr1_in) begin
        read_data1_out = write_data_in;
      end
      if (write_addr_in == read_addr2_in) begin
        read_data2_out = write_data_in;
      end
    end

    // Assign X1 to x1_val_out
    x1_val_out = regs[1];
  end

endmodule