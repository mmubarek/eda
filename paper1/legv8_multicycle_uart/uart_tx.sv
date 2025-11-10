module uart_tx #(
    parameter CLKS_PER_BIT = 434, // 115200 baud for 50MHz clock
    parameter DEBUG_UART = 0      // Uncomment this line
)
(
    input  logic clk,
    input  logic rst,
    input  logic [7:0] i_tx_data,
    input  logic i_tx_dv,
    output logic o_tx_active,
    output logic o_tx_serial
);

    typedef enum logic [3:0] {
        IDLE,
        TX_START_BIT,
        TX_DATA_BITS,
        TX_STOP_BIT
    } state_t;

    state_t state_r, state_n;

    logic [9:0] clk_counter_r, clk_counter_n; // Reduced width
    logic [2:0] bit_index_r, bit_index_n;
    logic [7:0] tx_data_r, tx_data_n;

    // TX state machine
    always_ff @(posedge clk) begin
        if (rst) begin
            state_r <= IDLE;
            clk_counter_r <= '0;
            bit_index_r <= '0;
            tx_data_r <= '0;
        end else begin
            state_r <= state_n;
            clk_counter_r <= clk_counter_n;
            bit_index_r <= bit_index_n;
            tx_data_r <= tx_data_n;
        end
    end

    always_comb begin
        state_n = state_r;
        clk_counter_n = clk_counter_r;
        bit_index_n = bit_index_r;
        tx_data_n = tx_data_r;
        o_tx_active = (state_r != IDLE);
        o_tx_serial = 1'b1; // Default to high

        case (state_r)
            IDLE: begin
                if (i_tx_dv) begin
                    state_n = TX_START_BIT;
                    clk_counter_n = '0;
                    tx_data_n = i_tx_data;
                end
            end

            TX_START_BIT: begin
                o_tx_serial = 1'b0;
                if (clk_counter_r == (CLKS_PER_BIT - 1)) begin
                    state_n = TX_DATA_BITS;
                    clk_counter_n = '0;
                    bit_index_n = '0;
                end else begin
                    clk_counter_n = clk_counter_r + 1'b1;
                end
            end

            TX_DATA_BITS: begin
                o_tx_serial = tx_data_r[bit_index_r];
                if (clk_counter_r == (CLKS_PER_BIT - 1)) begin
                    if (DEBUG_UART) $display("[%0t] TX: Sending bit %d, value %b from tx_data_r=0x%h", $time, bit_index_r, tx_data_r[bit_index_r], tx_data_r);
                    clk_counter_n = '0;
                    if (bit_index_r == 3'd7) begin
                        state_n = TX_STOP_BIT;
                    end else begin
                        state_n = TX_DATA_BITS;
                        bit_index_n = bit_index_r + 1'b1;
                    end
                end else begin
                    clk_counter_n = clk_counter_r + 1'b1;
                end
            end

            TX_STOP_BIT: begin
                o_tx_serial = 1'b1;
                if (clk_counter_r == (CLKS_PER_BIT - 1)) begin
                    state_n = IDLE;
                end else begin
                    clk_counter_n = clk_counter_r + 1'b1;
                end
            end

            default: begin
                state_n = IDLE;
            end
        endcase

    end

endmodule
