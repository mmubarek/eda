module InstructionMemory #(
    parameter ADDR_WIDTH = 6,
    parameter INST_WIDTH = 32
)(
    input  logic [ADDR_WIDTH-1:0] addr_in,
    input  logic [INST_WIDTH-1:0] write_data_in,
    input  logic                  write_en_in,
    input  logic                  clk,
    output logic [INST_WIDTH-1:0] instr_out
);

    // RAM block
    (* ramstyle = "M9K" *) logic [INST_WIDTH-1:0] IMEM [0:(1<<ADDR_WIDTH)-1];

    // Combinatorial read
    assign instr_out = IMEM[addr_in];

    // Synchronous write
    always_ff @(posedge clk) begin
        if (write_en_in) begin
            IMEM[addr_in] <= write_data_in;
        end
    end

endmodule