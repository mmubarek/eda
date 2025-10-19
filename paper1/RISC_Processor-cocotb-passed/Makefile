# Makefile for Cocotb Simulation
SIM = verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES := $(shell cat filelist.f)
VHDL_SOURCES = 
TOPLEVEL = RISC_Processor
MODULE = test_RISC_Processor
include $(shell cocotb-config --makefiles)/Makefile.sim
