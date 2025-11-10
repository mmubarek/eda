module uart_rx #(
    parameter CLKS_PER_BIT = 434,
    parameter DEBUG_UART = 0,
    parameter SYNC_DELAY_CLKS = 2
)
(
    input  logic clk,
    input  logic rst,
    input  logic i_rx_serial,
    output logic [7:0] o_rx_data,
    output logic o_rx_dv
);

    // FIXED: Proper calculations for half and full bit periods
    localparam HALF_BIT_WAIT = CLKS_PER_BIT / 2;  // Middle of bit period
    localparam FULL_BIT_WAIT = CLKS_PER_BIT - 1;  // Full bit period

    typedef enum logic [1:0] { IDLE, SYNC, DATA, STOP } state_t;
    state_t state_r, prev_state_r;

    logic [15:0] clk_count_r;
    logic [2:0]  bit_count_r;
    logic [7:0]  data_r;
    logic        o_rx_dv_reg;

    assign o_rx_data = data_r;
    assign o_rx_dv = o_rx_dv_reg;

    always_ff @(posedge clk) begin
        if (rst) begin
            state_r <= IDLE;
            prev_state_r <= IDLE;
            clk_count_r <= 0;
            bit_count_r <= 0;
            data_r <= 0;
            o_rx_dv_reg <= 0;
        end else begin
            prev_state_r <= state_r;
            o_rx_dv_reg <= 0;  // Default to 0, set only when we have valid data

            case (state_r)
                IDLE: begin
                    if (~i_rx_serial) begin  // Start bit detected (low)
                        state_r <= SYNC;
                        clk_count_r <= 0;
                        data_r <= 0;  // Clear previous data
                    end
                end

                SYNC: begin
                    if (clk_count_r == (HALF_BIT_WAIT - 1)) begin
                        // Verify we're still in start bit (should be low)
                        if (~i_rx_serial) begin
                            state_r <= DATA;
                            clk_count_r <= 0;
                            bit_count_r <= 0;
                        end else begin
                            // False start, go back to IDLE
                            state_r <= IDLE;
                        end
                    end else begin
                        clk_count_r <= clk_count_r + 1'b1;
                    end
                end

                DATA: begin
                    if (clk_count_r == (FULL_BIT_WAIT)) begin
                        // Sample the bit at the end of the bit period
                        data_r[bit_count_r] <= i_rx_serial;
                        clk_count_r <= 0;
                        
                        if (bit_count_r == 3'd7) begin
                            state_r <= STOP;
                        end else begin
                            bit_count_r <= bit_count_r + 1'b1;
                        end
                        
                        if (DEBUG_UART) begin
                            $display("[%0t] RX: Sampled bit %0d = %0b (data_r=0x%0h)", 
                                     $time, bit_count_r, i_rx_serial, data_r);
                        end
                    end else begin
                        clk_count_r <= clk_count_r + 1'b1;
                    end
                end

                STOP: begin
                    if (clk_count_r == (FULL_BIT_WAIT)) begin
                        clk_count_r <= 0;
                        o_rx_dv_reg <= 1;  // Assert data valid for one cycle
                        state_r <= IDLE;
                        if (DEBUG_UART) begin
                            $display("[%0t] RX: STOP state, o_rx_dv_reg asserted, data=0x%h", 
                                     $time, data_r);
                        end
                    end else begin
                        clk_count_r <= clk_count_r + 1'b1;
                    end
                end

                default: state_r <= IDLE;
            endcase

        end
    end

endmodule