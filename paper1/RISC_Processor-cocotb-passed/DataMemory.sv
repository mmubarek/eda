// FILE: DataMemory.sv
// Final synthesizable version compatible with Verilator and standard tools.
// The explicit reset of the memory array has been removed.
module DataMemory
#(
  parameter int DATA_WIDTH = 32,
  parameter int DMEM_DEPTH_WORDS = 1024
)
(
  input logic clk,
  // rst_n is no longer used by this module but can be kept for interface consistency
  // if other memories in the system might need it. For a clean design, we can remove it.
  input logic rst_n, 
  input logic [$clog2(DMEM_DEPTH_WORDS)-1:0] addr, // Word address
  input logic [DATA_WIDTH-1:0] write_data,
  input logic mem_read_en, 
  input logic mem_write_en,
  output logic [DATA_WIDTH-1:0] read_data
);

  // Use 'reg' for memory array as it will be assigned in an always block
  // This will be inferred as a Block RAM (BRAM).
  logic [DATA_WIDTH-1:0] mem [DMEM_DEPTH_WORDS-1:0];

  // --- ASYNCHRONOUS (COMBINATIONAL) READ LOGIC ---
  // The output immediately reflects the content at the given address.
  // This is the correct model for a single-cycle CPU's memory.
  assign read_data = mem[addr];


  // --- SYNCHRONOUS WRITE LOGIC ---
  // Writes only happen on the rising edge of the clock.
  // There is NO reset logic for the memory array itself, which is standard practice.
  always_ff @(posedge clk) begin
    if (mem_write_en) begin
      mem[addr] <= write_data;
    end
  end

endmodule