# Define the 50 MHz clock (20ns period)
create_clock -name clk_50MHz -period 20.000 [get_ports clk_50MHz]

# Optional: tell Quartus to ignore timing between async domains, or cut false paths if you have them
# set_false_path -from [get_clocks clk_50MHz] -to [get_clocks other_clk] 
