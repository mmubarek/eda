import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import random

# Constants derived from the Verilog module
NUM_REGISTERS = 32
REG_ADDR_WIDTH = 5  # $clog2(32)
DATA_WIDTH = 32

class RegisterFileTB:
    def __init__(self, dut):
        self.dut = dut
        # Python model of the register file, initialized to 0
        self.model_registers = [0] * NUM_REGISTERS

    async def reset(self):
        """Resets the DUT and initializes the model."""
        cocotb.log.info("Resetting DUT")
        self.dut.rst_n.value = 0
        self.dut.reg_write_en.value = 0
        self.dut.rd_addr.value = 0
        self.dut.rd_data.value = 0
        self.dut.rs1_addr.value = 0
        self.dut.rs2_addr.value = 0

        # Initialize model registers to 0 on reset
        for i in range(NUM_REGISTERS):
            self.model_registers[i] = 0

        await Timer(10, units="ns")  # Hold reset for a bit
        await RisingEdge(self.dut.clk)  # Ensure reset is active for at least one clock cycle
        self.dut.rst_n.value = 1
        cocotb.log.info("Reset complete")
        await RisingEdge(self.dut.clk)  # Wait one more cycle after reset de-assertion

    async def write_register(self, addr, data):
        """
        Performs a write operation to the register file.
        Updates the internal model *before* the clock edge, as the write is synchronous.
        """
        cocotb.log.info(f"Attempting write: rd_addr=x{addr}, rd_data=0x{data:08x}")

        # Update model first, considering x0 behavior
        if addr == 0:
            cocotb.log.warning(f"Attempting to write to x0 (addr={addr}). This should have no effect on the model.")
            # Model for x0 remains 0
        else:
            self.model_registers[addr] = data
            cocotb.log.info(f"Model updated: x{addr} = 0x{self.model_registers[addr]:08x}")

        self.dut.rd_addr.value = addr
        self.dut.rd_data.value = data
        self.dut.reg_write_en.value = 1
        await RisingEdge(self.dut.clk)  # Write happens on the rising edge
        self.dut.reg_write_en.value = 0  # De-assert write enable after the edge

    async def read_registers(self, rs1_addr, rs2_addr):
        """
        Performs read operations from the register file and asserts against the model.
        Reads are asynchronous, so only a small delay is needed for propagation.
        """
        self.dut.rs1_addr.value = rs1_addr
        self.dut.rs2_addr.value = rs2_addr
        await Timer(1, units="ns")  # Small delay for combinational logic to settle

        rs1_data_dut = self.dut.rs1_data.value.integer
        rs2_data_dut = self.dut.rs2_data.value.integer

        # Expected values from model, considering x0 behavior
        rs1_data_expected = 0 if rs1_addr == 0 else self.model_registers[rs1_addr]
        rs2_data_expected = 0 if rs2_addr == 0 else self.model_registers[rs2_addr]

        cocotb.log.info(f"Reading x{rs1_addr}: DUT=0x{rs1_data_dut:08x}, Expected=0x{rs1_data_expected:08x}")
        cocotb.log.info(f"Reading x{rs2_addr}: DUT=0x{rs2_data_dut:08x}, Expected=0x{rs2_data_expected:08x}")

        assert rs1_data_dut == rs1_data_expected, \
            f"Read from x{rs1_addr} mismatch: DUT=0x{rs1_data_dut:08x}, Expected=0x{rs1_data_expected:08x}"
        assert rs2_data_dut == rs2_data_expected, \
            f"Read from x{rs2_addr} mismatch: DUT=0x{rs2_data_dut:08x}, Expected=0x{rs2_data_expected:08x}"

        return rs1_data_dut, rs2_data_dut

@cocotb.test()
async def test_register_file(dut):
    cocotb.log.info("Starting RegisterFile testbench")

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")  # 100 MHz clock
    cocotb.start_soon(clock.start())

    tb = RegisterFileTB(dut)

    # 1. Reset Test
    cocotb.log.info("\n--- Test 1: Reset Behavior ---")
    await tb.reset()
    # After reset, all registers (except x0) should be 0
    for i in range(1, NUM_REGISTERS):
        # Read two registers, one of them is i, the other is a random one
        await tb.read_registers(i, random.randint(0, NUM_REGISTERS - 1))
        assert tb.model_registers[i] == 0, f"Model for x{i} not 0 after reset"

    # 2. Test x0 (Register 0) Behavior
    cocotb.log.info("\n--- Test 2: x0 (Register 0) Behavior ---")
    # Try writing to x0 - should have no effect
    initial_x1_val = tb.model_registers[1]  # Should be 0 from reset
    await tb.write_register(0, 0xDEADBEEF)  # Attempt to write to x0
    # Read x0 and x1 to verify no change
    await tb.read_registers(0, 1)
    assert dut.rs1_data.value.integer == 0, "x0 should always read 0, even after attempted write"
    assert dut.rs2_data.value.integer == initial_x1_val, "Writing to x0 should not affect other registers (e.g., x1)"
    assert tb.model_registers[0] == 0, "Model x0 should remain 0"

    # 3. Basic Single Write/Read Test
    cocotb.log.info("\n--- Test 3: Basic Single Write/Read ---")
    test_addr = 5
    test_data = 0x12345678
    await tb.write_register(test_addr, test_data)
    await tb.read_registers(test_addr, 0)  # Read the written register and x0
    assert dut.rs1_data.value.integer == test_data, f"Basic write/read failed for x{test_addr}"

    # 4. Multiple Writes/Reads
    cocotb.log.info("\n--- Test 4: Multiple Writes/Reads ---")
    # Write unique values to several registers (skip x0)
    for i in range(1, NUM_REGISTERS):
        data = random.randint(0, 2**DATA_WIDTH - 1)
        await tb.write_register(i, data)

    # Verify all written values
    for i in range(1, NUM_REGISTERS):
        # Read i and a random other register
        await tb.read_registers(i, random.randint(0, NUM_REGISTERS - 1))
        assert dut.rs1_data.value.integer == tb.model_registers[i], f"Multiple write/read failed for x{i}"

    # 5. Read-After-Write (Same Cycle vs. Next Cycle)
    cocotb.log.info("\n--- Test 5: Read-After-Write Behavior ---")
    addr_to_test = 10
    old_data = tb.model_registers[addr_to_test]  # Current value in model (and DUT)
    new_data = 0xAABBCCDD

    # Set up read addresses *before* the write operation's clock edge
    dut.rs1_addr.value = addr_to_test
    dut.rs2_addr.value = (addr_to_test + 1) % NUM_REGISTERS
    await Timer(1, units="ns")  # Allow read outputs to settle combinatorially

    # Assert old value is read in the same cycle as write setup (before the clock edge)
    cocotb.log.info(f"Checking read in same cycle as write setup for x{addr_to_test}")
    assert dut.rs1_data.value.integer == old_data, \
        f"Read-after-write (same cycle) failed: DUT=0x{dut.rs1_data.value.integer:08x}, Expected=0x{old_data:08x}"

    # Perform the write. This advances clock by one edge, committing the write.
    await tb.write_register(addr_to_test, new_data)

    # Now, in the next cycle (after the write has committed), the new data should be available
    cocotb.log.info(f"Checking read in next cycle after write for x{addr_to_test}")
    await tb.read_registers(addr_to_test, (addr_to_test + 1) % NUM_REGISTERS)
    assert dut.rs1_data.value.integer == new_data, \
        f"Read-after-write (next cycle) failed: DUT=0x{dut.rs1_data.value.integer:08x}, Expected=0x{new_data:08x}"

    # 6. No Write Enable Test
    cocotb.log.info("\n--- Test 6: No Write Enable ---")
    addr_no_write = 15
    original_data = tb.model_registers[addr_no_write]
    attempted_data = 0xFFEEDDCC

    dut.reg_write_en.value = 0  # Ensure write enable is low
    dut.rd_addr.value = addr_no_write
    dut.rd_data.value = attempted_data
    await RisingEdge(dut.clk)  # Clock cycle passes with write_en low

    await tb.read_registers(addr_no_write, 0)
    assert dut.rs1_data.value.integer == original_data, \
        f"Register x{addr_no_write} changed when reg_write_en was low. Expected 0x{original_data:08x}, got 0x{dut.rs1_data.value.integer:08x}"
    assert tb.model_registers[addr_no_write] == original_data, \
        f"Model for x{addr_no_write} changed unexpectedly when reg_write_en was low."

    # 7. Extensive Randomized Test
    cocotb.log.info("\n--- Test 7: Extensive Randomized Operations ---")
    num_random_cycles = 500
    for i in range(num_random_cycles):
        cocotb.log.info(f"Random test cycle {i+1}/{num_random_cycles}")

        # Randomly decide to write or not
        do_write = random.random() < 0.7  # 70% chance to write
        
        if do_write:
            write_addr = random.randint(1, NUM_REGISTERS - 1)  # Don't write to x0
            write_data = random.randint(0, 2**DATA_WIDTH - 1)
            await tb.write_register(write_addr, write_data)
        else:
            # If not writing, just advance clock to simulate time passing
            dut.reg_write_en.value = 0
            await RisingEdge(dut.clk)

        # Randomly choose two read addresses
        read_addr1 = random.randint(0, NUM_REGISTERS - 1)
        read_addr2 = random.randint(0, NUM_REGISTERS - 1)

        # Perform read and verify against model
        await tb.read_registers(read_addr1, read_addr2)

    cocotb.log.info("RegisterFile testbench finished successfully!")