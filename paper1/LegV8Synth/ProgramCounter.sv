module ProgramCounter
(
  input logic clk,
  input logic rst,
  input logic [7:0] pc_next_addr,
  output logic [7:0] pc_out
);

  // Program Counter register
  always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
      pc_out <= 8'h00; // Reset PC to address 0
    end else begin
      pc_out <= pc_next_addr; // Update PC with the next calculated address
    end
  end

endmodule