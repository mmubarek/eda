module ProgramCounter
#(
  parameter ADDRESS_WIDTH = 8
)
(
  input logic clk,
  input logic rst,
  input logic [ADDRESS_WIDTH-1:0] pc_next_addr,
  output logic [ADDRESS_WIDTH-1:0] pc_out
);

  // Program Counter register
  always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
      pc_out <= {ADDRESS_WIDTH{1'b0}}; // Reset PC to address 0
    end else begin
      pc_out <= pc_next_addr; // Update PC with the next calculated address
    end
  end

endmodule