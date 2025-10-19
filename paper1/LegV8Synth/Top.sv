//takes variables connected to output and input functions on the de1 board
//and connects them to inputs and outputs in 2 modules - 
//word display and the upc module 
//input :switches, keys , and upc
//output 7 segment displays, ledrs 
module Top (CLOCK_50, START, LEDR); 
	input logic CLOCK_50;
	input logic START; 
	output logic LEDR;
	
	 logic [7:0] pc_debug, alu_debug, reg_debug;
    logic [15:0] instr_debug;
	 
	 logic [25:0] dividedClocks;
	 ClockDivider clockDiv(.clk_in(CLOCK_50), .div_value(4) .rst_n(START),  .clk_out(dividedClocks));
	 LegV8SingleCycleProcessor m(.clk(dividedClocks[8]), .rst(~START), .debug_pc_out(pc_debug), .debug_instruction_out(instr_debug), 
		.debug_alu_result(alu_debug), .debug_reg_write_data(reg_debug));
	
	assign LEDR = (alu_debug == 4'b1111);

endmodule 
