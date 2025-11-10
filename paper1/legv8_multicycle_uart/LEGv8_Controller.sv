module LEGv8_Controller (
    input  logic clk,
    input  logic rst,
    input  logic fsm_start,

    // From Datapath
    input  logic [31:0] instr_word,
    input  logic        zero_flag,
    input  logic [31:0] alu_result,
    input  logic [31:0] mem_read_data,
    input  logic [31:0] pc_out,

    // From Top Level (UART)
    input  logic tx_active,

    // To Datapath
    output logic [31:0] current_instr,
    output logic [31:0] pc_latched,
    output logic        pc_write_en,
    output logic        reg_write_en,
    output logic [31:0] reg_write_data,
    output logic        branch_link_latched,
    output logic        is_stur,
    output logic        is_cbz,
    output logic        is_cbnz,
    output logic        alu_src,
    output logic [3:0]  alu_op,
    output logic        mem_write,
    output logic        mem_read,
    output logic        uncond_branch,
    output logic        cond_branch,
    output logic        branch_reg,

    // To Top Level
    output logic [7:0]  tx_data,
    output logic        tx_start,
    output logic        fsm_sequence_active
);

    // Control Unit
    logic        reg_write;
    logic        mem_to_reg;
    logic        halt_signal;
    logic        branch_link;

    ControlUnit cu_inst (
        .instr_in        (current_instr),
        .zero_flag_in    (zero_flag),
        .reg_write_out   (reg_write),
        .mem_to_reg_out  (mem_to_reg),
        .mem_read_out    (mem_read),
        .mem_write_out   (mem_write),
        .alu_src_out     (alu_src),
        .uncond_branch_out(uncond_branch),
        .cond_branch_out (cond_branch),
        .alu_op_out      (alu_op),
        .halt_signal_out (halt_signal),
        .is_cbz_out      (is_cbz),
        .is_cbnz_out     (is_cbnz),
        .is_stur_out     (is_stur),
        .branch_reg_out  (branch_reg),
        .branch_link_out (branch_link)
    );

    typedef enum logic [3:0] { IDLE, FETCH, DECODE, EXECUTE, MEM_WAIT, CAPTURE_RESULT, SEND_RESULT, NEXT_INSTR, RESET_STATE } state_t;
    state_t state = RESET_STATE;

    logic [31:0] result_value;
    logic [1:0]  byte_idx;
    logic        sequence_active;
    logic        halt_detected;
    logic        tx_request;
    logic [2:0]  reset_counter;
    logic [1:0]  stall_counter; // Added for hazard stall

    logic reg_write_latched;
    logic mem_to_reg_latched;
    logic mem_read_latched;
    logic mem_write_latched;
    logic [31:0] alu_result_latched;

    assign fsm_sequence_active = sequence_active;

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= RESET_STATE;
            reset_counter <= 3'b0;
            stall_counter <= 2'b0; // Added for hazard stall
            tx_start <= 1'b0;
            tx_data <= 8'h00;
            byte_idx <= 2'b0;
            pc_write_en <= 1'b0;
            reg_write_en <= 1'b0;
            reg_write_data <= 32'b0;
            sequence_active <= 1'b0;
            halt_detected <= 1'b0;
            result_value <= 32'b0;
            tx_request <= 1'b0;
            current_instr <= 32'b0;
            pc_latched <= 32'b0;
            reg_write_latched <= 1'b0;
            mem_to_reg_latched <= 1'b0;
            mem_read_latched <= 1'b0;
            mem_write_latched <= 1'b0;
            branch_link_latched <= 1'b0;
            alu_result_latched <= 32'b0;
        end else begin
            tx_start <= 1'b0;
            pc_write_en <= 1'b0;
            reg_write_en <= 1'b0;
            tx_request <= 1'b0;

            case (state)
                RESET_STATE:
                    if (reset_counter == 3'd4) state <= IDLE;
                    else reset_counter <= reset_counter + 1;

                IDLE:
                    if (fsm_start && !sequence_active) begin
                        sequence_active <= 1'b1;
                        halt_detected <= 1'b0;
                        state <= FETCH;
                    end

                FETCH:
                    if (sequence_active && !halt_detected) begin
                        current_instr <= instr_word;
                        pc_latched <= pc_out;
                        pc_write_en <= 1'b1;
                        state <= DECODE;
                    end else begin
                        state <= IDLE;
                    end

                DECODE:
                    begin
                        if (halt_signal) begin
                            halt_detected <= 1'b1;
                            sequence_active <= 1'b0;
                            state <= IDLE;
                        end else begin
                            reg_write_latched <= reg_write;
                            mem_to_reg_latched <= mem_to_reg;
                            mem_read_latched <= mem_read;
                            mem_write_latched <= mem_write;
                            branch_link_latched <= branch_link;
                            state <= EXECUTE;
                        end
                    end

                EXECUTE:
                    begin
                        alu_result_latched <= alu_result;
                        if (mem_read_latched || mem_write_latched) state <= MEM_WAIT;
                        else state <= CAPTURE_RESULT;
                    end

                MEM_WAIT:
                    state <= CAPTURE_RESULT;

                CAPTURE_RESULT:
                    begin
                        if (mem_to_reg_latched) result_value <= mem_read_data;
                        else if (reg_write_latched) result_value <= alu_result_latched;
                        else result_value <= alu_result_latched;

                        if (reg_write_latched) begin
                            if (branch_link_latched) reg_write_data <= pc_latched + 4;
                            else if (mem_to_reg_latched) reg_write_data <= mem_read_data;
                            else reg_write_data <= alu_result_latched;
                            reg_write_en <= 1'b1;
                        end

                        byte_idx <= 2'b00;
                        state <= SEND_RESULT;
                    end

                SEND_RESULT:
                    if (!tx_active && !tx_request) begin
                        tx_request <= 1'b1;
                        case (byte_idx)
                            2'b00: tx_data <= result_value[7:0];
                            2'b01: tx_data <= result_value[15:8];
                            2'b10: tx_data <= result_value[23:16];
                            2'b11: tx_data <= result_value[31:24];
                        endcase
                    end else if (tx_request) begin
                        tx_start <= 1'b1;
                        if (tx_active) begin
                            tx_request <= 1'b0;
                            if (byte_idx == 2'b11) begin
                                state <= NEXT_INSTR;
                                stall_counter <= 2'b0;
                            end else begin
                                byte_idx <= byte_idx + 1;
                            end
                        end
                    end

                NEXT_INSTR:
                    if (stall_counter == 2'd2) begin
                        state <= FETCH;
                    end else begin
                        stall_counter <= stall_counter + 1;
                    end

                default: state <= IDLE;
            endcase
        end
    end
endmodule