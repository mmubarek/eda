module ImmediateGenerator #(
  parameter INST_WIDTH = 32,
  parameter DATA_WIDTH = 32
)
(
  input logic [INST_WIDTH-1:0] instr_in,
  output logic [DATA_WIDTH-1:0] imm_out
);

  // Immediate field widths for LEGv8 formats (typical LEGv8 layout)
  localparam int I_WIDTH  = 12; // I-type imm12 : instr[21:10]
  localparam int D_WIDTH  = 9;  // D-type imm9  : instr[20:12]
  localparam int CB_WIDTH = 19; // CB-type imm19: instr[23:5] (shift left 2)
  localparam int B_WIDTH  = 26; // B-type imm26 : instr[25:0] (shift left 2)

  // Extract raw immediate bitfields from instruction
  logic [I_WIDTH-1:0]  imm_i_raw;
  logic [D_WIDTH-1:0]  imm_d_raw;
  logic [CB_WIDTH-1:0] imm_cb_raw;
  logic [B_WIDTH-1:0]  imm_b_raw;

  assign imm_i_raw  = instr_in[21:10];
  assign imm_d_raw  = instr_in[20:12];
  assign imm_cb_raw = instr_in[23:5];
  assign imm_b_raw  = instr_in[25:0];

  // Simple LEGv8 format detection (common LEGv8 opcode patterns)
  // NOTE: These patterns follow the conventional LEGv8/AArch64 encoding used
  // in many academic exercises:
  //  - B-type (unconditional branch) : instr[31:26] == 6'b000101
  //  - CB-type (conditional branch)  : instr[31:24] == 8'b10110100
  //  - D-type (load/store - LDUR/STUR) : instr[31:21] == 11'b11111000010 or 11111000000
  // If none of the above, fall back to I-type immediate extraction.
  wire is_B  = (instr_in[31:26] == 6'b000101) || (instr_in[31:26] == 6'b100101);
  wire is_CB = (instr_in[31:24] == 8'b10110100) || (instr_in[31:24] == 8'b10110101);
  wire is_D  = (instr_in[31:21] == 11'b11111000010) || (instr_in[31:21] == 11'b11111000000);

  // Create signed, properly shifted immediates of sufficient width, then
  // assign to imm_out with sign-extension/truncation handled by SystemVerilog signed assignment.
  logic signed [DATA_WIDTH-1:0] imm_i_signed;
  logic signed [DATA_WIDTH-1:0] imm_d_signed;
  logic signed [DATA_WIDTH-1:0] imm_cb_signed;
  logic signed [DATA_WIDTH-1:0] imm_b_signed;

  // For I-type and D-type, no shift is applied.
  // For CB-type and B-type, these immediates are branch offsets and are shifted left by 2.
  // Use explicit sign-extension to match 32-bit width - Pitfall 5 fix
  always_comb begin
    // Default zeros
    imm_i_signed  = '0;
    imm_d_signed  = '0;
    imm_cb_signed = '0;
    imm_b_signed  = '0;

    // I-type: sign-extend imm12 to 32 bits
    imm_i_signed = {{20{imm_i_raw[I_WIDTH-1]}}, imm_i_raw};

    // D-type: sign-extend imm9 to 32 bits
    imm_d_signed = {{23{imm_d_raw[D_WIDTH-1]}}, imm_d_raw};

    // CB-type: imm19 << 2 with sign-extension to 32 bits
    imm_cb_signed = {{11{imm_cb_raw[CB_WIDTH-1]}}, imm_cb_raw, 2'b00};

    // B-type: imm26 << 2 with sign-extension to 32 bits
    imm_b_signed = {{4{imm_b_raw[B_WIDTH-1]}}, imm_b_raw, 2'b00};

    // Select which immediate to output based on decoded format
    if (is_B) begin
      imm_out = imm_b_signed;
    end else if (is_CB) begin
      imm_out = imm_cb_signed;
    end else if (is_D) begin
      imm_out = imm_d_signed;
    end else begin
      // Default to I-type immediate for other instruction formats
      imm_out = imm_i_signed;
    end
  end

endmodule