module DataMemory #(
  parameter DATA_WIDTH = 32,
  parameter ADDR_WIDTH = 6
)(
  input  logic                    clk,
  input  logic                    rst,
  input  logic [ADDR_WIDTH-1:0]   addr_in,      // Byte address
  input  logic [DATA_WIDTH-1:0]   write_data_in,
  input  logic                    mem_write_en_in,
  input  logic                    mem_read_en_in,
  output logic [DATA_WIDTH-1:0]   read_data_out
);

  localparam integer WORD_ADDR_WIDTH = ADDR_WIDTH - 2;
  localparam integer MEM_DEPTH = (1 << WORD_ADDR_WIDTH);

  (* ramstyle = "M9K" *) logic [DATA_WIDTH-1:0] mem [0:MEM_DEPTH-1];

  // Convert byte address to word address
  logic [WORD_ADDR_WIDTH-1:0] word_addr;
  assign word_addr = addr_in[ADDR_WIDTH-1:2];

  // Single cycle read (combinatorial) for simplicity
  assign read_data_out = (mem_read_en_in && !mem_write_en_in) ? mem[word_addr] : '0;

  // Synchronous write
  always_ff @(posedge clk) begin
    if (mem_write_en_in) begin
      mem[word_addr] <= write_data_in;
    end
  end

endmodule