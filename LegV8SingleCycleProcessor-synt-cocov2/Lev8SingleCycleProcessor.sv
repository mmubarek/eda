//
// File: lev8_single_cycle_processor.sv
// Description: Corrected top-level module.
//
//
module Lev8SingleCycleProcessor
(
  input logic clk,
  input logic rst,
  output logic [3:0] debug_pc_out,   // Was 7:0
  output logic [15:0] debug_instruction_out,
  output logic [7:0] debug_alu_result,
  output logic [7:0] debug_reg_write_data
);

  localparam DATA_WIDTH = 8;
  localparam ADDRESS_WIDTH = 4;  // was 8
  localparam INSTRUCTION_WIDTH = 16;
  localparam REG_ADDR_WIDTH = 3;
  localparam OPCODE_WIDTH = 4;
  localparam ALU_OP_WIDTH = 3;
  localparam IMMEDIATE_WIDTH = 6;
  localparam PC_INCREMENT_VAL = 4'd2;  // 8'd2

  // Wires for connecting sub-modules
  logic [ADDRESS_WIDTH-1:0] pc_out_w;
  logic [ADDRESS_WIDTH-1:0] pc_next_addr_w;
  logic [INSTRUCTION_WIDTH-1:0] instruction_w;
  logic [ADDRESS_WIDTH-1:0] pc_plus_2_w;
  logic [OPCODE_WIDTH-1:0] opcode_w;
  logic [REG_ADDR_WIDTH-1:0] rs1_addr_w;
  logic [REG_ADDR_WIDTH-1:0] rs2_addr_w;
  logic [REG_ADDR_WIDTH-1:0] rd_addr_w;
  logic [IMMEDIATE_WIDTH-1:0] immediate_w;
  logic [ADDRESS_WIDTH-1:0] jump_target_raw_w;
  logic reg_write_en_w;
  logic mem_write_en_w;
  logic mem_read_en_w;
  logic alu_src_sel_w;
  logic [1:0] mem_to_reg_sel_w;
  logic branch_en_w;
  logic jump_en_w;
  logic [ALU_OP_WIDTH-1:0] alu_op_w;
  logic [DATA_WIDTH-1:0] read_data1_w;
  logic [DATA_WIDTH-1:0] read_data2_w;
  logic [DATA_WIDTH-1:0] reg_write_data_w;
  logic [DATA_WIDTH-1:0] sign_extended_immediate_w;
  logic [DATA_WIDTH-1:0] alu_src2_w;
  logic [DATA_WIDTH-1:0] alu_result_w;
  logic alu_zero_w;
  logic [DATA_WIDTH-1:0] mem_read_data_w;
  logic [ADDRESS_WIDTH-1:0] branch_target_addr_w;
  logic branch_condition_w;
  
  
  logic rd_sel_i_type_w;

  // Debug Outputs
  assign debug_pc_out = pc_out_w;
  assign debug_instruction_out = instruction_w;
  assign debug_alu_result = alu_result_w;
  assign debug_reg_write_data = reg_write_data_w;

  // 1. Program Counter
  ProgramCounter #(
  .ADDRESS_WIDTH(4)
  )
  PC_inst (
    .clk(clk),
    .rst(rst),
    .pc_next_addr(pc_next_addr_w),
    .pc_out(pc_out_w)
  );

  // 2. Instruction Memory
  InstructionMemory #(
  .DATA_WIDTH(8),
  .ADDRESS_WIDTH(4),
  .INSTRUCTION_WIDTH(16),
  .REG_ADDR_WIDTH(3),
  .OPCODE_WIDTH(4),
  .ALU_OP_WIDTH(3),
  .IMMEDIATE_WIDTH(6),
  .JUMP_ADDR_WIDTH(12),
  .PC_INCREMENT_VAL(2)
) IM_inst (
  .clk(clk),
  .addr(pc_out_w),
  .instruction(instruction_w)
);
  
  // 3. Instruction Decode (Combinational Assignments)
  assign opcode_w = instruction_w[15:12];
  assign rs1_addr_w = instruction_w[11:9];
  assign rs2_addr_w = instruction_w[8:6];
  // FIX: rd_addr_w is now selected by a mux based on instruction type.
  // The immediate value is now correctly decoupled from the rd address.
  assign rd_addr_w = rd_sel_i_type_w ? instruction_w[8:6] : instruction_w[5:3];
  assign immediate_w = instruction_w[5:0];
  assign jump_target_raw_w = instruction_w[ADDRESS_WIDTH-1:0];  // was 7:0

  // 4. Control Unit
  ControlUnit CU_inst (
    .opcode(opcode_w),
    .reg_write_en(reg_write_en_w),
    .mem_write_en(mem_write_en_w),
    .mem_read_en(mem_read_en_w),
    .alu_src_sel(alu_src_sel_w),
    .mem_to_reg_sel(mem_to_reg_sel_w),
    .branch_en(branch_en_w),
    .jump_en(jump_en_w),
    .alu_op(alu_op_w),
    .rd_sel_i_type(rd_sel_i_type_w) // NEW connection
  );

  // 5. Register File
  RegisterFile RF_inst (
    .clk(clk),
    .rst(rst),
    .read_addr1(rs1_addr_w),
    .read_addr2(rs2_addr_w),
    .write_addr(rd_addr_w),
    .write_data(reg_write_data_w),
    .write_en(reg_write_en_w),
    .read_data1(read_data1_w),
    .read_data2(read_data2_w)
  );

  // 6. Sign Extender
  SignExtender SE_inst (
    .in_val(immediate_w),
    .out_val(sign_extended_immediate_w)
  );

  // 7. ALU Source Mux (Mux2to1)
  Mux2to1 ALU_SRC_MUX_inst (
    .in0(read_data2_w),
    .in1(sign_extended_immediate_w),
    .sel(alu_src_sel_w),
    .out(alu_src2_w)
  );

  // 8. ALU
  ALU ALU_inst (
    .src1(read_data1_w),
    .src2(alu_src2_w),
    .alu_op(alu_op_w),
    .result(alu_result_w),
    .zero(alu_zero_w)
  );

  // 9. Data Memory
  DataMemory DM_inst (
    .clk(clk),
    .addr(alu_result_w),
    .write_data(read_data2_w),
    .write_en(mem_write_en_w),
    .read_en(mem_read_en_w),
    .read_data(mem_read_data_w)
  );

  // 10. Write Back Mux (Mux3to1)
  assign pc_plus_2_w = pc_out_w + PC_INCREMENT_VAL;
  Mux3to1 #(
    .ADDRESS_WIDTH(8)
  )
  WB_MUX_inst (
    .in0(alu_result_w),
    .in1(mem_read_data_w),
    .in2({4'h0, pc_plus_2_w}),   // was .in2(pc_plus_2_w)
    .sel(mem_to_reg_sel_w),
    .out(reg_write_data_w)
  );

  logic [7:0] branch_target_addr_w_raw;
  // 11. Branch Adder
  Adder #(
    .ADDRESS_WIDTH(8)
  )
  BRANCH_ADDER_inst
  (
    .in1({4'h0, pc_plus_2_w}),
    .in2(sign_extended_immediate_w), // Note: Branch offset is added to PC+2
    .sum(branch_target_addr_w_raw)   // was branch_target_addr_w
  );
  
  assign branch_target_addr_w = branch_target_addr_w_raw[3:0]; // added for port compatiblity

  // 12. Branch Condition Logic
  assign branch_condition_w = branch_en_w && alu_zero_w;

  // 13. PC Next Address Logic
  assign pc_next_addr_w = (jump_en_w) ? jump_target_raw_w :
                          ((branch_condition_w) ? branch_target_addr_w : pc_plus_2_w);

endmodule
