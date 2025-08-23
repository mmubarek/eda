import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

@cocotb.test()
async def test_sign_extender(dut):
    """Test the SignExtender module for all possible 6-bit inputs."""

    cocotb.log.info("Starting SignExtender test")

    # Iterate through all possible 6-bit input values (0 to 2^6 - 1, i.e., 0 to 63)
    for i in range(2**6):
        # Set the input value to the DUT
        dut.in_val.value = i

        # Allow a small delay for combinational logic to propagate.
        # While cocotb's value propagation is immediate, a small delay
        # can sometimes be useful for simulator updates or consistency.
        await Timer(1, units="ns")

        # Read the actual output value from the DUT
        actual_out_val = dut.out_val.value

        # --- Calculate the expected output value based on the Verilog logic ---
        # The Verilog module uses: assign out_val = {{2{in_val[5]}}, in_val};
        # This means the MSB of in_val (bit 5) is replicated to fill the higher bits (bits 6 and 7)
        # of the 8-bit out_val.

        # Extract the MSB of the 6-bit input
        msb_in_val = (i >> 5) & 1

        expected_out_val_int = 0
        if msb_in_val == 1:
            # If MSB is 1 (negative number in two's complement), replicate '1'
            # This means the top 2 bits of out_val should be '11'
            expected_out_val_int = (0b11 << 6) | i
        else:
            # If MSB is 0 (positive number), replicate '0'
            # This means the top 2 bits of out_val should be '00'
            expected_out_val_int = (0b00 << 6) | i

        # Create a cocotb BinaryValue for the expected output for direct comparison
        expected_out_val_bin = BinaryValue(expected_out_val_int, n_bits=8, bigEndian=False)

        # Assertion 1: Check bit-level correctness
        # Compare the actual output bits with the calculated expected bits
        assert actual_out_val == expected_out_val_bin, \
            f"Bit-level mismatch for in_val={i:#08b} (dec: {i})\n" \
            f"  Expected bits: 0b{expected_out_val_bin.binstr}\n" \
            f"  Actual bits:   0b{actual_out_val.binstr}"

        # Assertion 2: Check signed integer equivalence
        # The purpose of a sign extender is to preserve the signed value.
        # Convert the 6-bit input value to its signed integer representation
        signed_in_val = dut.in_val.value.signed_integer
        # Convert the 8-bit actual output value to its signed integer representation
        signed_out_val = actual_out_val.signed_integer

        # Assert that the signed integer values are equal
        assert signed_in_val == signed_out_val, \
            f"Signed value mismatch for in_val={i:#08b} (dec: {i})\n" \
            f"  Expected signed: {signed_in_val}\n" \
            f"  Actual signed:   {signed_out_val}"

        cocotb.log.info(f"Test passed for in_val={i:#08b} (dec: {i}), "
                         f"out_val=0b{actual_out_val.binstr} (dec: {actual_out_val.signed_integer})")

    cocotb.log.info("All SignExtender tests completed successfully!")