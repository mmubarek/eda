module LEGv8_Datapath (
    input  logic clk,
    input  logic rst,

    // From Controller
    input  logic [31:0] current_instr,
    input  logic [31:0] pc_latched,
    input  logic        pc_write_en,
    input  logic        reg_write_en,
    input  logic [31:0] reg_write_data,
    input  logic        branch_link_latched,
    input  logic        is_stur,
    input  logic        is_cbz,
    input  logic        is_cbnz,
    input  logic        alu_src,
    input  logic [3:0]  alu_op,
    input  logic        mem_write,
    input  logic        mem_read,
    input  logic        uncond_branch, // Now from register
    input  logic        cond_branch,   // Now from register
    input  logic        branch_reg,    // Now from register

    // From Bootloader (via Core)
    input  logic        imem_write_en_in,
    input  logic [31:0] imem_write_data_in,
    input  logic [5:0]  imem_write_addr_in,

    // To Controller
    output logic [31:0] pc_out,
    output logic [31:0] instr_word,
    output logic        zero_flag,
    output logic [31:0] alu_result,
    output logic [31:0] mem_read_data
);

    logic [31:0] read_data1;
    logic [31:0] read_data2;
    logic [31:0] imm_gen_out;

    // Program Counter
    logic [31:0] pc_next;

    ProgramCounter pc_inst (
        .clk            (clk),
        .rst            (rst),
        .pc_write_en_in (pc_write_en),
        .pc_next_in     (pc_next),
        .pc_out         (pc_out)
    );

    // Branch logic
    logic branch_taken;
    assign branch_taken = (uncond_branch) ||
                          (cond_branch && is_cbz && zero_flag) ||
                          (cond_branch && is_cbnz && !zero_flag);

    assign pc_next = branch_reg ? read_data1 : (branch_taken ? (pc_latched + imm_gen_out) : (pc_out + 4));

    // Instruction Memory
    logic [5:0] imem_addr;
    assign imem_addr = imem_write_en_in ? imem_write_addr_in : pc_out[7:2];

    InstructionMemory #(.INST_WIDTH(32), .ADDR_WIDTH(6))
    imem_inst (
        .clk(clk),
        .addr_in(imem_addr),
        .write_data_in(imem_write_data_in),
        .write_en_in(imem_write_en_in),
        .instr_out(instr_word)
    );

    // Immediate Generator
    ImmediateGenerator imm_inst (
        .instr_in(current_instr),
        .imm_out (imm_gen_out)
    );

    // Register File
    logic [4:0]  rd, rn, rm;
    assign rd = current_instr[4:0];
    assign rn = current_instr[9:5];
    assign rm = current_instr[20:16];

    logic [4:0] rf_write_addr;
    assign rf_write_addr = branch_link_latched ? 5'd30 : rd;
    logic [4:0] rf_read_addr2;
    assign rf_read_addr2 = (is_stur || is_cbz || is_cbnz) ? rd : rm;

    RegisterFile rf_inst (
        .clk            (clk),
        .rst            (rst),
        .write_en_in    (reg_write_en),
        .read_addr1_in  (rn),
        .read_addr2_in  (rf_read_addr2),
        .write_addr_in  (rf_write_addr),
        .write_data_in  (reg_write_data),
        .read_data1_out (read_data1),
        .read_data2_out (read_data2),
        .x1_val_out     () // This was x1_val, unused in the FSM logic
    );

    // ALU
    logic [5:0] shamt;
    assign shamt = current_instr[15:10];
    logic is_shift;
    assign is_shift = (alu_op == 4'b0101) || (alu_op == 4'b0110) || (alu_op == 4'b1000) || (alu_op == 4'b1001);

    logic [31:0] operand_b;
    assign operand_b = alu_src ? imm_gen_out : (is_shift ? {26'b0, shamt} : read_data2);

    logic [31:0] alu_operand_a;
    assign alu_operand_a = (is_cbz || is_cbnz) ? read_data2 : read_data1;

    ALU alu_inst (
        .operand_a_in (alu_operand_a),
        .operand_b_in (operand_b),
        .alu_op_in    (alu_op),
        .result_out   (alu_result),
        .zero_flag_out(zero_flag)
    );

    // Data Memory
    DataMemory data_mem (
        .clk(clk),
        .rst(rst),
        .addr_in(alu_result[5:0]),
        .write_data_in(read_data2),
        .mem_write_en_in(mem_write),
        .mem_read_en_in(mem_read),
        .read_data_out(mem_read_data)
    );

endmodule
