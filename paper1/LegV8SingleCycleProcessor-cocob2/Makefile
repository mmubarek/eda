# Makefile for Cocotb Simulation
SIM = verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES := $(shell cat filelist.f)
VHDL_SOURCES = 
TOPLEVEL = Lev8SingleCycleProcessor
MODULE = test_Lev8SingleCycleProcessor
include $(shell cocotb-config --makefiles)/Makefile.sim

