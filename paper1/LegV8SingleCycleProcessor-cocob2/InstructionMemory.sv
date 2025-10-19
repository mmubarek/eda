module InstructionMemory
#(
  parameter DATA_WIDTH = 8,
  parameter ADDRESS_WIDTH = 8,
  parameter INSTRUCTION_WIDTH = 16,
  parameter REG_ADDR_WIDTH = 3,
  parameter OPCODE_WIDTH = 4,
  parameter ALU_OP_WIDTH = 3,
  parameter IMMEDIATE_WIDTH = 6,
  parameter JUMP_ADDR_WIDTH = 12,
  parameter PC_INCREMENT_VAL = 2
)
(
  input logic clk,
  input logic [ADDRESS_WIDTH-1:0] addr,
  output logic [INSTRUCTION_WIDTH-1:0] instruction
);

  // Declare the instruction memory array
logic [INSTRUCTION_WIDTH-1:0] mem [2**ADDRESS_WIDTH-1:0];

assign instruction = {mem[addr][7:0], mem[addr+1][7:0]};


  // Read operation moved into an always_comb block.
  // This makes the read path truly combinational and resolves the simulator race condition
  // that was causing an 'x' to be read during the fetch stage of Cycle 3.
  initial  begin
$readmemh("memfile.dat", mem);
    // Unlike DataMemory, InstructionMemory is always "read enabled".
    // It's a ROM from the processor's perspective.
   
  end
 

endmodule

