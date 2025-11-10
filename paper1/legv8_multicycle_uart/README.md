# LEGv8 Processor for FPGAs

## 1. Project Overview

This project is a SystemVerilog implementation of a multi-cycle LEGv8-like processor core designed for FPGA synthesis. The processor supports dynamic program loading from a host PC via a UART interface, allowing for rapid software testing without re-synthesizing the hardware.

The architecture is modular, with a clear separation between the top-level FPGA wrapper (`fpga_top.sv`), the processor core (`LEGv8_Core.sv`), and the core's main components: the Controller (`LEGv8_Controller.sv`) and the Datapath (`LEGv8_Datapath.sv`).

## 2. How to Operate

Operating the processor involves three main steps: generating a binary program file, loading it onto the FPGA, and running it.

### Step 1: Generate a Program Binary

A Python script, `generate_test_program.py`, is provided to easily convert LEGv8 machine code into the required `.bin` format.
Note that there is a sample program.bin already written in program.bin. You can skip to step 2 for quick test.

1.  **Write LEGv8 Assembly:** Write your desired program in LEGv8 assembly. You are given an example in test_prog.txt.
2.  **Assemble to Machine Code:** Convert your assembly instructions into their 32-bit hexadecimal machine code equivalents. (This can be done using an external LEGv8 assembler or by manual encoding).
3.  **Edit the Script:** Open `generate_test_program.py` and replace the hexadecimal strings in the `instructions` list with your own machine code.

    ```python
    # In generate_test_program.py
    instructions = [
        "9100154A", # Your first instruction
        "9100016B", # Your second instruction
        # ... etc.
    ]
    ```

4.  **Run the Script:** Execute the script from your terminal. This will create a `program.bin` file in the project directory.

    ```sh
    python generate_test_program.py
    ```

### Step 2: Load the Program

The `fpga_program_loader.py` script handles communication with the FPGA.

1.  **Run the Loader:** Start the script from your terminal.

    ```sh
    python fpga_program_loader.py
    ```

2.  **Select COM Port:** The script will list available serial ports. Enter the number corresponding to your FPGA's UART device.
3.  **Provide Binary File:** When prompted, enter the name of the binary file you generated (e.g., `program.bin`).

### Step 3: Run the Program on the FPGA

The loader script will now guide you through the hardware interaction:

1.  **Reset:** Press the physical **RESET** button on the FPGA, then press Enter in the terminal. The FPGA will send back a handshake signal (`0x00000001`).
2.  **Load Mode:** Press the physical **START** button on the FPGA once, then press Enter. This puts the processor into "load mode". The FPGA will send a second handshake (`0x00000002`), and the script will automatically transmit the binary file.
3.  **Run Mode:** After the program is loaded, press the **START** button a second time, then press Enter. The FPGA will send a final handshake (`0x00000003`), and the processor will immediately begin executing your program from address `0`.

### Step 4: Monitor the Output

The script will automatically print any 32-bit values sent back from the processor over UART. In this project, the processor is configured to send the result of every instruction that writes to a register.

For default program.bin (test_prog.txt), you will get the following output:

--- Waiting for ALU results ---
ALU Result = 0x00000064
ALU Result = 0x00000032
ALU Result = 0x00000003
ALU Result = 0x00000096
ALU Result = 0x00000032
ALU Result = 0x00000020
ALU Result = 0x00000076
ALU Result = 0x00000056
ALU Result = 0x00000014
ALU Result = 0x00000018
ALU Result = 0x0000005A
ALU Result = 0x00000002
ALU Result = 0x00000002
ALU Result = 0x00000050
ALU Result = 0x00000001
ALU Result = 0x00000001
ALU Result = 0x00000046
ALU Result = 0x00000000
ALU Result = 0x00000000
ALU Result = 0x00000096
ALU Result = 0x00000000
ALU Result = 0x000003E7
ALU Result = 0x00000000
ALU Result = 0x0000047D


## 3 Devices and Tools Used 
* DE-10 lite FPGA board
* Quartus for Syntheis and FPGA programming 
* USB to serial adapter
