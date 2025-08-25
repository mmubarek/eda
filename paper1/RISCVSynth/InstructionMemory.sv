
module InstructionMemory
#(
  parameter logic [1023:0] IMEM_DEPTH_WORDS = 1024 // Default value for synthesis/simulation if not overridden
)
(
  input logic clk,
  input logic [ADDR_WIDTH-1:0] addr,
  output logic [INSTR_WIDTH-1:0] instr_out
);

  // Local parameters derived from project specifications and module parameters
  localparam int INSTR_WIDTH = 32; // Derived from "32-bit RISC" processor type
  
  // ADDR_WIDTH is derived from IMEM_DEPTH_WORDS.
  // SystemVerilog's $clog2 function expects an integer argument.
  // When IMEM_DEPTH_WORDS (defined as logic [1023:0]) is passed,
  // it is implicitly treated as an integer value for the calculation.
  localparam int ADDR_WIDTH = $clog2(IMEM_DEPTH_WORDS);

  // Declare the memory array.
  // The size of the array (IMEM_DEPTH_WORDS) is implicitly treated as an integer.
      /* synthesis ramstyle = "M9K" */
  
  logic [INSTR_WIDTH-1:0] mem [IMEM_DEPTH_WORDS-1:0];

  // Initialize the memory from a hex file.
  // This initial block is used by synthesis tools to infer a ROM with pre-loaded contents.
  // It is not for simulation test setup, but for defining the hardware's initial state.
  initial begin
    $readmemh("instruction_memory.hex", mem);
  end

   always_ff @(posedge clk) begin
    instr_out <= mem[addr];
  end
  // Combinational read from memory.
  // The 'clk' input is part of the port list but is not used for this combinational ROM.
  //assign instr_out = mem[addr];
 
endmodule

//
// InstructionMemory.sv - "Golden Template" for ROM Inference
//

