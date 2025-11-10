module ProgramCounter #(
    parameter WIDTH = 32
) (
    input  logic              clk,
    input  logic              rst,     // active high reset
    input  logic              pc_write_en_in,   // enable PC write
    input  logic [WIDTH-1:0]  pc_next_in,      // next PC value
    output logic [WIDTH-1:0]  pc_out
);

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            pc_out <= '0;
        else if (pc_write_en_in)
            pc_out <= pc_next_in;
    end

endmodule
