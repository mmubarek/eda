module ClockDivider #(
    parameter int WIDTH = 32
)(
    input  logic                  clk_in,      // 50 MHz input clock
    input  logic                  rst_n,       // active-low reset
    input  logic [WIDTH-1:0]      div_value,   // divide factor (>= 2)
    output logic                  clk_out      // divided output clock
);

    logic [WIDTH-1:0] counter;

    always_ff @(posedge clk_in or negedge rst_n) begin
        if (!rst_n) begin
            counter <= '0;
            clk_out <= 1'b0;
        end else begin
            if (counter >= (div_value >> 1) - 1) begin
                clk_out <= ~clk_out;
                counter <= '0;
            end else begin
                counter <= counter + 1'b1;
            end
        end
    end

endmodule
