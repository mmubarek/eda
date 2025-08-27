module clockDivider (clk, outputClocks);
	input logic clk;
	output logic [15:0] outputClocks = 0;
	
	always_ff @(posedge clk)begin
		outputClocks <= outputClocks+1;
	end
	
endmodule