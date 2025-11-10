# A simple utility to convert a list of LEGv8 machine code instructions (as hex strings)
# into a .bin file that can be loaded onto the FPGA.

import struct

# --- Sample Program: Sum of numbers from 1 to N ---
# Assembly:
#   ADDI X10, XZR, #5      // N = 5
#   ADDI X11, XZR, #0      // sum = 0
#   ADDI X12, XZR, #1      // incrementer = 1
# LOOP:
#   ADD  X11, X11, X10    // sum = sum + N
#   SUBI X10, X10, #1      // N = N - 1
#   CBNZ X10, LOOP       // if N != 0, go to LOOP
#   STUR X11, [XZR, #100]  // Store final sum to memory address 100
#   HALT

instructions = [
    "9100154A", # ADDI X10, XZR, #5
    "9100016B", # ADDI X11, XZR, #0
    "9100058C", # ADDI X12, XZR, #1
    "8B0A016B", # ADD  X11, X11, X10
    "D100054A", # SUBI X10, X10, #1
    "B5FFFFEA", # CBNZ X10, #-3 (branch to LOOP)
    "F80067E8", # STUR X11, [XZR, #100]
    "FFE00000", # HALT
]

output_filename = "program.bin"

with open(output_filename, "wb") as f:
    for inst_hex in instructions:
        inst_int = int(inst_hex, 16)
        # Pack as little-endian unsigned integer
        f.write(struct.pack('<I', inst_int))

print(f"Successfully generated '{output_filename}' with {len(instructions)} instructions.")