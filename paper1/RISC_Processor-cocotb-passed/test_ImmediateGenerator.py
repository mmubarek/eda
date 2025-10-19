import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue

def sign_extend(value, num_bits, data_width):
    """
    Sign-extends a given value from num_bits to data_width.
    Assumes value is already truncated to num_bits.
    """
    if value & (1 << (num_bits - 1)):  # Check if the MSB of the num_bits value is set
        # If MSB is 1, it's a negative number, extend with 1s
        # Create a mask of 1s for the higher bits
        mask = ((1 << (data_width - num_bits)) - 1) << num_bits
        return value | mask
    else:
        # If MSB is 0, it's a positive number, extend with 0s
        return value

@cocotb.test()
async def immediate_generator_test(dut):
    """Test the ImmediateGenerator module for various immediate types."""

    # Get parameters from the DUT
    INSTR_WIDTH = int(dut.INSTR_WIDTH.value)
    DATA_WIDTH = int(dut.DATA_WIDTH.value)

    cocotb.log.info(f"Starting ImmediateGenerator test with INSTR_WIDTH={INSTR_WIDTH}, DATA_WIDTH={DATA_WIDTH}")

    # Helper function to calculate expected I-type immediate
    def calculate_expected_i_imm(instr_val):
        # I-type immediate: instr[31:20] (12 bits)
        imm_12_bits = (instr_val >> 20) & 0xFFF
        return sign_extend(imm_12_bits, 12, DATA_WIDTH)

    # Helper function to calculate expected S-type immediate
    def calculate_expected_s_imm(instr_val):
        # S-type immediate: {instr[31:25], instr[11:7]} (12 bits)
        imm_7_bits = (instr_val >> 25) & 0x7F  # instr[31:25]
        imm_5_bits = (instr_val >> 7) & 0x1F   # instr[11:7]
        imm_12_bits = (imm_7_bits << 5) | imm_5_bits
        return sign_extend(imm_12_bits, 12, DATA_WIDTH)

    # Helper function to calculate expected B-type immediate
    def calculate_expected_b_imm(instr_val):
        # B-type immediate: {instr[31], instr[7], instr[30:25], instr[11:8], 1'b0} (13 bits)
        imm_1_bit_31 = (instr_val >> 31) & 0x1      # instr[31]
        imm_1_bit_7 = (instr_val >> 7) & 0x1        # instr[7]
        imm_6_bits_30_25 = (instr_val >> 25) & 0x3F # instr[30:25]
        imm_4_bits_11_8 = (instr_val >> 8) & 0xF    # instr[11:8]
        
        # Concatenate bits to form the 13-bit immediate value
        imm_13_bits = (imm_1_bit_31 << 12) | \
                      (imm_1_bit_7 << 11) | \
                      (imm_6_bits_30_25 << 5) | \
                      (imm_4_bits_11_8 << 1) | \
                      0x0 # The fixed 1'b0 at the LSB
        return sign_extend(imm_13_bits, 13, DATA_WIDTH)

    # --- Test Cases for I-type Immediate (imm_type_sel = 2'b00) ---
    cocotb.log.info("--- Testing I-type Immediate (imm_type_sel = 00) ---")
    dut.imm_type_sel.value = 0b00

    # Test 1.1: Positive I-type immediate (e.g., 0x001)
    # instr[31:20] = 0x001, instr[31]=0
    instr_val = (0x001 << 20)
    dut.instr.value = instr_val
    await Timer(1, units="ns") # Wait for combinational logic to settle
    expected_imm = calculate_expected_i_imm(instr_val)
    cocotb.log.info(f"I-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"I-type positive failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 1.2: Negative I-type immediate (e.g., 0xFFF)
    # instr[31:20] = 0xFFF, instr[31]=1
    instr_val = (0xFFF << 20)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_i_imm(instr_val)
    cocotb.log.info(f"I-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"I-type negative failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 1.3: Zero I-type immediate
    instr_val = 0x00000000
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_i_imm(instr_val)
    cocotb.log.info(f"I-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"I-type zero failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 1.4: Max positive I-type immediate (0x7FF)
    instr_val = (0x7FF << 20)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_i_imm(instr_val)
    cocotb.log.info(f"I-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"I-type max positive failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 1.5: Min negative I-type immediate (0x800)
    instr_val = (0x800 << 20)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_i_imm(instr_val)
    cocotb.log.info(f"I-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"I-type min negative failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # --- Test Cases for S-type Immediate (imm_type_sel = 2'b01) ---
    cocotb.log.info("--- Testing S-type Immediate (imm_type_sel = 01) ---")
    dut.imm_type_sel.value = 0b01

    # Test 2.1: Positive S-type immediate (e.g., {0x01, 0x01} -> 0x041)
    # instr[31:25] = 0x01, instr[11:7] = 0x01
    instr_val = (0x01 << 25) | (0x01 << 7)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_s_imm(instr_val)
    cocotb.log.info(f"S-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"S-type positive failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 2.2: Negative S-type immediate (e.g., {0x3F, 0x1F} -> 0xFFF)
    # instr[31:25] = 0x3F, instr[11:7] = 0x1F
    instr_val = (0x3F << 25) | (0x1F << 7)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_s_imm(instr_val)
    cocotb.log.info(f"S-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"S-type negative failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 2.3: Zero S-type immediate
    instr_val = 0x00000000
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_s_imm(instr_val)
    cocotb.log.info(f"S-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"S-type zero failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 2.4: Max positive S-type immediate (0x7FF)
    # instr[31:25] = 0x1F, instr[11:7] = 0x1F
    instr_val = (0x1F << 25) | (0x1F << 7)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_s_imm(instr_val)
    cocotb.log.info(f"S-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"S-type max positive failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 2.5: Min negative S-type immediate (0x800)
    # instr[31:25] = 0x20, instr[11:7] = 0x00
    instr_val = (0x20 << 25) | (0x00 << 7)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_s_imm(instr_val)
    cocotb.log.info(f"S-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"S-type min negative failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # --- Test Cases for B-type Immediate (imm_type_sel = 2'b10) ---
    cocotb.log.info("--- Testing B-type Immediate (imm_type_sel = 10) ---")
    dut.imm_type_sel.value = 0b10

    # Test 3.1: Positive B-type immediate (e.g., {0,0,0x01,0x01,0} -> 0x002)
    # instr[31]=0, instr[7]=0, instr[30:25]=0x01, instr[11:8]=0x01
    instr_val = (0x00 << 31) | (0x00 << 7) | (0x01 << 25) | (0x01 << 8)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_b_imm(instr_val)
    cocotb.log.info(f"B-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"B-type positive failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 3.2: Negative B-type immediate (e.g., {1,1,0x3F,0x0F,0} -> 0x1FFF)
    # instr[31]=1, instr[7]=1, instr[30:25]=0x3F, instr[11:8]=0x0F
    instr_val = (0x01 << 31) | (0x01 << 7) | (0x3F << 25) | (0x0F << 8)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_b_imm(instr_val)
    cocotb.log.info(f"B-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"B-type negative failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 3.3: Zero B-type immediate
    instr_val = 0x00000000
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_b_imm(instr_val)
    cocotb.log.info(f"B-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"B-type zero failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 3.4: Max positive B-type immediate (0x0FFF)
    # instr[31]=0, instr[7]=1, instr[30:25]=0x3F, instr[11:8]=0x0F
    instr_val = (0x00 << 31) | (0x01 << 7) | (0x3F << 25) | (0x0F << 8)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_b_imm(instr_val)
    cocotb.log.info(f"B-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"B-type max positive failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # Test 3.5: Min negative B-type immediate (0x1000)
    # instr[31]=1, instr[7]=0, instr[30:25]=0x00, instr[11:8]=0x00
    instr_val = (0x01 << 31) | (0x00 << 7) | (0x00 << 25) | (0x00 << 8)
    dut.instr.value = instr_val
    await Timer(1, units="ns")
    expected_imm = calculate_expected_b_imm(instr_val)
    cocotb.log.info(f"B-type: instr=0x{instr_val:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"B-type min negative failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    # --- Test Case for Default/Unsupported Immediate Type (imm_type_sel = 2'b11) ---
    cocotb.log.info("--- Testing Default Case (imm_type_sel = 11) ---")
    dut.imm_type_sel.value = 0b11
    dut.instr.value = 0xFFFFFFFF # Arbitrary instruction, should not matter
    await Timer(1, units="ns")
    expected_imm = 0
    cocotb.log.info(f"Default: instr=0x{dut.instr.value.integer:08X}, expected=0x{expected_imm:08X}, actual=0x{dut.immediate.value.integer:08X}")
    assert dut.immediate.value.integer == expected_imm, \
        f"Default case failed: Expected 0x{expected_imm:08X}, got 0x{dut.immediate.value.integer:08X}"

    cocotb.log.info("All ImmediateGenerator tests passed successfully!")