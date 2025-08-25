module ProgramCounter
  #(parameter ADDR_WIDTH = 32) // Assuming 32-bit addresses for a 32-bit RISC processor
  (
    input logic clk,
    input logic rst_n,
    input logic [1:0] pc_next_sel,
    input logic [ADDR_WIDTH-1:0] branch_target_addr,
    output logic [ADDR_WIDTH-1:0] pc_out
  );

  logic [ADDR_WIDTH-1:0] pc_reg;
  logic [ADDR_WIDTH-1:0] pc_next_val;

  // Combinational logic to determine the next PC value based on pc_next_sel
  always_comb begin
    case (pc_next_sel)
      2'b00: pc_next_val = pc_reg + ADDR_WIDTH'(4); // Increment PC by 4 for next sequential instruction (32-bit instructions)
      2'b01: pc_next_val = branch_target_addr;     // Load branch/jump target address
      default: pc_next_val = pc_reg;               // Hold PC for other cases (e.g., stall, unused select values)
    endcase
  end

  // Sequential logic for the Program Counter register
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pc_reg <= {ADDR_WIDTH{1'b0}}; // Asynchronous active-low reset: PC to 0
    end else begin
      pc_reg <= pc_next_val;        // Update PC with the determined next value
    end
  end

  // Assign the internal PC register value to the output port
  assign pc_out = pc_reg;

endmodule