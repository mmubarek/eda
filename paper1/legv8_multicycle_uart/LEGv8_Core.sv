module LEGv8_Core (
    input  logic clk,
    input  logic rst,
    input  logic start,

    // IMEM Write Interface from Bootloader
    input  logic        imem_write_en_in,
    input  logic [31:0] imem_write_data_in,
    input  logic [5:0]  imem_write_addr_in,

    // UART Interface
    input  logic tx_active,
    output logic [7:0] tx_data,
    output logic tx_start,

    // Status
    output logic core_active
);

    // Controller -> Datapath Signals
    logic [31:0] current_instr;
    logic [31:0] pc_latched;
    logic        pc_write_en;
    logic        reg_write_en;
    logic [31:0] reg_write_data;
    logic        branch_link_latched;
    logic        is_stur;
    logic        is_cbz;
    logic        is_cbnz;
    logic        alu_src;
    logic [3:0]  alu_op;
    logic        mem_write;
    logic        mem_read;
    logic        uncond_branch;
    logic        cond_branch;
    logic        branch_reg;

    // Datapath -> Controller Signals
    logic [31:0] instr_word;
    logic        zero_flag;
    logic [31:0] alu_result;
    logic [31:0] mem_read_data;
    logic [31:0] pc_out;

    LEGv8_Datapath datapath_inst (
        .clk(clk),
        .rst(rst),
        .current_instr(current_instr),
        .pc_latched(pc_latched),
        .pc_write_en(pc_write_en),
        .reg_write_en(reg_write_en),
        .reg_write_data(reg_write_data),
        .branch_link_latched(branch_link_latched),
        .is_stur(is_stur),
        .is_cbz(is_cbz),
        .is_cbnz(is_cbnz),
        .alu_src(alu_src),
        .alu_op(alu_op),
        .mem_write(mem_write),
        .mem_read(mem_read),
        .uncond_branch(uncond_branch),
        .cond_branch(cond_branch),
        .branch_reg(branch_reg),
        .imem_write_en_in(imem_write_en_in),
        .imem_write_data_in(imem_write_data_in),
        .imem_write_addr_in(imem_write_addr_in),
        .pc_out(pc_out),
        .instr_word(instr_word),
        .zero_flag(zero_flag),
        .alu_result(alu_result),
        .mem_read_data(mem_read_data)
    );

    LEGv8_Controller controller_inst (
        .clk(clk),
        .rst(rst),
        .fsm_start(start),
        .instr_word(instr_word),
        .zero_flag(zero_flag),
        .alu_result(alu_result),
        .mem_read_data(mem_read_data),
        .pc_out(pc_out),
        .tx_active(tx_active),
        .current_instr(current_instr),
        .pc_latched(pc_latched),
        .pc_write_en(pc_write_en),
        .reg_write_en(reg_write_en),
        .reg_write_data(reg_write_data),
        .branch_link_latched(branch_link_latched),
        .is_stur(is_stur),
        .is_cbz(is_cbz),
        .is_cbnz(is_cbnz),
        .alu_src(alu_src),
        .alu_op(alu_op),
        .mem_write(mem_write),
        .mem_read(mem_read),
        .uncond_branch(uncond_branch),
        .cond_branch(cond_branch),
        .branch_reg(branch_reg),
        .tx_data(tx_data),
        .tx_start(tx_start),
        .fsm_sequence_active(core_active)
    );

endmodule
