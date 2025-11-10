module fpga_top (
    input  logic clk_50MHz,
    input  logic rst_n,
    input  logic start,
    input  logic uart_rx_in,
    output logic uart_tx,
    output logic led_act
);

    logic rst;
    assign rst = ~rst_n;

    // Core Instance & UART signals
    logic [7:0] core_tx_data;
    logic       core_tx_start;
    logic       uart_tx_active;

    // IMEM Write Interface (for bootloader)
    logic imem_write_en;
    logic [31:0] imem_write_data;
    logic [5:0] imem_write_addr;

    // --- Handshake & UART Muxing Logic ---
    logic [7:0] handshake_tx_data;
    logic       handshake_tx_start;
    logic [7:0] uart_mux_tx_data;
    logic       uart_mux_tx_dv;

    // New Master FSM States
    typedef enum logic [4:0] {
        S_RESET_WAIT,
        S_HS1_B0, S_HS1_B1, S_HS1_B2, S_HS1_B3,
        S_IDLE,
        S_HS2_B0, S_HS2_B1, S_HS2_B2, S_HS2_B3,
        S_LOAD,
        S_HS3_B0, S_HS3_B1, S_HS3_B2, S_HS3_B3,
        S_RUN
    } master_state_t;
    master_state_t master_state;

    logic is_load_mode;
    logic is_run_mode;
    assign is_load_mode = (master_state == S_LOAD);
    assign is_run_mode  = (master_state == S_RUN);

    master_state_t master_state_d1;
    always_ff @(posedge clk_50MHz or posedge rst) begin
        if (rst) master_state_d1 <= S_RESET_WAIT;
        else master_state_d1 <= master_state;
    end
    logic core_start_pulse;
    assign core_start_pulse = (master_state == S_RUN) && (master_state_d1 != S_RUN);

    assign uart_mux_tx_data = is_run_mode ? core_tx_data : handshake_tx_data;
    assign uart_mux_tx_dv   = is_run_mode ? core_tx_start : handshake_tx_start;

    LEGv8_Core core_inst (
        .clk(clk_50MHz), .rst(rst), .start(core_start_pulse), 
        .imem_write_en_in(imem_write_en), .imem_write_data_in(imem_write_data), .imem_write_addr_in(imem_write_addr),
        .tx_active(uart_tx_active), .tx_data(core_tx_data), .tx_start(core_tx_start), .core_active(led_act)
    );

    parameter CLKS_PER_BIT = 434;
    logic [7:0] rx_data; logic rx_dv;

    uart_tx #( .CLKS_PER_BIT(CLKS_PER_BIT) ) uart_tx_inst (
        .clk(clk_50MHz), .rst(rst), .i_tx_data(uart_mux_tx_data), .i_tx_dv(uart_mux_tx_dv), .o_tx_active(uart_tx_active), .o_tx_serial(uart_tx)
    );
    uart_rx #( .CLKS_PER_BIT(CLKS_PER_BIT) ) uart_rx_inst (
        .clk(clk_50MHz), .rst(rst), .i_rx_serial(uart_rx_in), .o_rx_data(rx_data), .o_rx_dv(rx_dv)
    );

    logic start_edge, start_sync_0, start_sync_1;
    always_ff @(posedge clk_50MHz or posedge rst) begin
        if (rst) {start_sync_0, start_sync_1} <= 2'b0; else {start_sync_0, start_sync_1} <= {start, start_sync_0};
    end
    assign start_edge = start_sync_0 & ~start_sync_1;

    logic start_released; logic [3:0] reset_counter; logic hs_tx_req;
    always_ff @(posedge clk_50MHz or posedge rst) begin
        if (rst) begin
            master_state <= S_RESET_WAIT; reset_counter <= 4'b0; start_released <= 1'b0; handshake_tx_start <= 1'b0; hs_tx_req <= 1'b0;
        end else begin
            handshake_tx_start <= 1'b0;
            case (master_state)
                S_RESET_WAIT:       if (reset_counter == 4'd9) master_state <= S_HS1_B0; else reset_counter <= reset_counter + 1;
                
                S_HS1_B0: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h01; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS1_B1; end end
                S_HS1_B1: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS1_B2; end end
                S_HS1_B2: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS1_B3; end end
                S_HS1_B3: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_IDLE;   end end

                S_IDLE:   if (start_edge) begin master_state <= S_HS2_B0; start_released <= 1'b0; end

                S_HS2_B0: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h02; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS2_B1; end end
                S_HS2_B1: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS2_B2; end end
                S_HS2_B2: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS2_B3; end end
                S_HS2_B3: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_LOAD;   end end

                S_LOAD:   begin if (!start) start_released <= 1'b1; if (start_edge && start_released) master_state <= S_HS3_B0; end

                S_HS3_B0: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h03; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS3_B1; end end
                S_HS3_B1: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS3_B2; end end
                S_HS3_B2: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_HS3_B3; end end
                S_HS3_B3: if (!uart_tx_active && !hs_tx_req) begin hs_tx_req <= 1'b1; handshake_tx_data <= 8'h00; end else if (hs_tx_req) begin handshake_tx_start <= 1'b1; if (uart_tx_active) begin hs_tx_req <= 1'b0; master_state <= S_RUN;    end end

                S_RUN:    master_state <= S_RUN;
                default:  master_state <= S_RESET_WAIT;
            endcase
        end
    end

    logic [1:0]  byte_count_r; logic [31:0] imem_write_data_reg; logic [5:0]  imem_write_addr_reg; logic write_pulse;
    always_ff @(posedge clk_50MHz or posedge rst) begin
        if (rst) write_pulse <= 1'b0; else write_pulse <= (rx_dv && (byte_count_r == 2'b11) && is_load_mode);
    end
    assign imem_write_en   = write_pulse; assign imem_write_data = imem_write_data_reg; assign imem_write_addr = imem_write_addr_reg;
    always_ff @(posedge clk_50MHz or posedge rst) begin
        if (rst) {byte_count_r, imem_write_addr_reg, imem_write_data_reg} <= {'0, '0, '0};
        else if (is_load_mode) begin
            if (rx_dv) if (byte_count_r == 2'b11) byte_count_r <= 2'b00; else byte_count_r <= byte_count_r + 1;
            if (write_pulse) imem_write_addr_reg <= imem_write_addr_reg + 1;
            if (rx_dv) case (byte_count_r) 2'b00: imem_write_data_reg[7:0]<=rx_data; 2'b01: imem_write_data_reg[15:8]<=rx_data; 2'b10: imem_write_data_reg[23:16]<=rx_data; 2'b11: imem_write_data_reg[31:24]<=rx_data; endcase
        end
    end

endmodule