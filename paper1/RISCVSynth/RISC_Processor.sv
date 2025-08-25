module RISC_Processor2
(
  input logic  clk,
  input logic  rst_n,
  output logic [ADDR_WIDTH-1:0] debug_pc,
  output logic [INSTR_WIDTH-1:0] debug_instr,
  //output logic [DATA_WIDTH-1:0] debug_reg_x10,
  //output logic [DATA_WIDTH-1:0] debug_reg_x11,
  // Debug
  output logic debug_reg_write_en,
  output logic [2:0] debug_alu_op,
  output logic [DATA_WIDTH-1:0] debug_immediate
);

  // STEP 1: USE THE PACKAGE FOR CONSTANTS
  import RISC_ISA_pkg::*; // <-- CORRECT WAY to use the package

  // These localparams are used to parameterize the sub-modules
  localparam IMEM_DEPTH_WORDS = 1024;
  localparam DMEM_DEPTH_WORDS = 1024;
  
  // Calculate memory address width from depth
  localparam IMEM_ADDR_WIDTH = $clog2(IMEM_DEPTH_WORDS);
  localparam DMEM_ADDR_WIDTH = $clog2(DMEM_DEPTH_WORDS);


  // STEP 2: DECLARE INTERNAL WIRES (No longer need wires for constants)

  // Wires for Program Counter and Instruction Memory
  logic [ADDR_WIDTH-1:0] pc_w;
  logic [INSTR_WIDTH-1:0] instr_w;

  // Wires for Instruction Decode
  logic [6:0] opcode_w;
  logic [2:0] funct3_w;
  logic [6:0] funct7_w;
  logic [REG_ADDR_WIDTH-1:0] rs1_addr_w;
  logic [REG_ADDR_WIDTH-1:0] rs2_addr_w;
  logic [REG_ADDR_WIDTH-1:0] rd_addr_w;

  // Wires for Register File
  logic [DATA_WIDTH-1:0] rs1_data_w;
  logic [DATA_WIDTH-1:0] rs2_data_w;
  logic [DATA_WIDTH-1:0] wb_data_w; 

  // Wires for Immediate Generator
  logic [DATA_WIDTH-1:0] immediate_w;

  // Wires for ALU
  logic [DATA_WIDTH-1:0] alu_operand_a_w;
  logic [DATA_WIDTH-1:0] alu_operand_b_w;
  logic [DATA_WIDTH-1:0] alu_result_w;
  logic zero_flag_w; 

  // Wires for Data Memory
  logic [DATA_WIDTH-1:0] mem_read_data_w;
  
  // Brach address calc
  logic [ADDR_WIDTH-1:0] branch_addr_w;

  // Wires for Control Unit outputs
  logic [1:0] pc_next_sel_w;
  logic [2:0] alu_op_w;
  logic alu_src_a_sel_w;
  logic alu_src_b_sel_w;
  logic [1:0] imm_type_sel_w;
  logic mem_read_en_w;
  logic mem_write_en_w;
  logic reg_write_en_w;
  logic [1:0] wb_src_sel_w;


  // STEP 3: COMPLETE THE INSTANTIATIONS

  // THE INCORRECT INSTANTIATION OF THE PACKAGE IS REMOVED.

  // Instantiation for ProgramCounter
  ProgramCounter #(
      .ADDR_WIDTH(ADDR_WIDTH)
  ) programcounter_inst (
      .clk( clk ),
      .rst_n( rst_n ),
      .pc_next_sel( pc_next_sel_w ),
      //.branch_target_addr( alu_result_w ), 
      .branch_target_addr( branch_addr_w ), 
      .pc_out( pc_w )
    );

  // Instantiation for InstructionMemory
  InstructionMemory #(
      .IMEM_DEPTH_WORDS( IMEM_DEPTH_WORDS )
  ) instructionmemory_inst (
      .clk( clk ),
      .addr( pc_w[IMEM_ADDR_WIDTH+1:2] ), // <-- FIX: Use correct address bits
      .instr_out( instr_w )
    );

  // Instantiation for RegisterFile
  RegisterFile #(
    .DATA_WIDTH(DATA_WIDTH),
    // .REG_ADDR_WIDTH(REG_ADDR_WIDTH), // This parameter doesn't exist anymore
    .REG_COUNT(REG_COUNT)           // This parameter now exists
) registerfile_inst (
    .clk( clk ),
    .rst_n( rst_n ),
    .rs1_addr( rs1_addr_w ), 
    .rs2_addr( rs2_addr_w ), 
    .rd_addr( rd_addr_w ),
    .rd_data( wb_data_w ),
    .reg_write_en( reg_write_en_w ), 
    .rs1_data( rs1_data_w ),
    .rs2_data( rs2_data_w )
);
  // Instantiation for ImmediateGenerator
  ImmediateGenerator #(
      .INSTR_WIDTH(INSTR_WIDTH),
      .DATA_WIDTH(DATA_WIDTH)
  ) immediategenerator_inst (
      .instr( instr_w ), 
      .imm_type_sel( imm_type_sel_w ),
      .immediate( immediate_w )
    );

  // Instantiation for ALU
  ALU #(
      .DATA_WIDTH(DATA_WIDTH)
  ) alu_inst (
      .operand_a( alu_operand_a_w ),
      .operand_b( alu_operand_b_w ), 
      .alu_op( alu_op_w ), 
      .result( alu_result_w ), 
      .zero( zero_flag_w ) 
    );

  // Instantiation for DataMemory
  DataMemory #(
      .DMEM_DEPTH_WORDS( DMEM_DEPTH_WORDS )
  ) datamemory_inst (
      .clk( clk ),
      .rst_n( rst_n ),
      .addr( alu_result_w[DMEM_ADDR_WIDTH+1:2] ), // <-- FIX: Use correct address bits
      .write_data( rs2_data_w ),
      .mem_read_en( mem_read_en_w ),
      .mem_write_en( mem_write_en_w ),
      .read_data( mem_read_data_w )
    );

  // Instantiation for ControlUnit
  ControlUnit controlunit_inst (
      .opcode( opcode_w ), 
      .funct3( funct3_w ), 
      .funct7( funct7_w ), 
      .alu_zero_flag( zero_flag_w ), 
      .pc_next_sel( pc_next_sel_w ), 
      .alu_op( alu_op_w ),
      .alu_src_a_sel( alu_src_a_sel_w ),
      .alu_src_b_sel( alu_src_b_sel_w ),
      .imm_type_sel( imm_type_sel_w ),
      .mem_read_en( mem_read_en_w ),
      .mem_write_en( mem_write_en_w ),
      .reg_write_en( reg_write_en_w ),
      .wb_src_sel( wb_src_sel_w )
    );

  // STEP 4: ADD GLUE LOGIC

  // Instruction Decoding
  assign opcode_w = instr_w[6:0];
  assign funct3_w = instr_w[14:12];
  assign funct7_w = instr_w[31:25];
  assign rs1_addr_w = instr_w[19:15];
  assign rs2_addr_w = instr_w[24:20];
  assign rd_addr_w = instr_w[11:7];

  // ALU Operand A Mux - Uses constants directly from package
  assign alu_operand_a_w = (alu_src_a_sel_w == ALU_SRC_A_PC) ? pc_w : rs1_data_w;

  // ALU Operand B Mux - Uses constants directly from package
  assign alu_operand_b_w = (alu_src_b_sel_w == ALU_SRC_B_IMM) ? immediate_w : rs2_data_w;
  
  // This adder calculates the branch target address in parallel with the ALU's comparison.
  // The target is the current PC plus the sign-extended immediate from the instruction.
  assign branch_addr_w = pc_w + immediate_w;

  // Write-back Mux - Uses constants directly from package
  assign wb_data_w = (wb_src_sel_w == WB_SRC_MEM) ? mem_read_data_w : alu_result_w;

  // Debug Outputs
  assign debug_pc = pc_w;
  assign debug_instr = instr_w;
  // This hierarchical access might require a simulator flag (like --public-flat-rw in Verilator)
  // but it is syntactically correct for simulation.
  //assign debug_reg_x10 = registerfile_inst.registers[10]; 
  //assign debug_reg_x11 = registerfile_inst.registers[11]; 
  
  // Debug 
  assign debug_reg_write_en = reg_write_en_w;
  assign debug_alu_op = alu_op_w;
  assign debug_immediate = immediate_w;

endmodule