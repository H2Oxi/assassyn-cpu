// RV32I ALU Module
// Implements arithmetic, logical, and comparison operations
// Based on rv32i.csv specification

module alu(
    input  logic [31:0] alu_in1,    // First operand
    input  logic [31:0] alu_in2,    // Second operand
    input  logic [3:0]  alu_op,     // ALU operation code
    input  logic [2:0]  cmp_op,     // Comparator operation code
    output logic [31:0] alu_out,    // ALU result
    output logic        cmp_out     // Comparator result
);

    // ALU operation codes
    localparam ALU_ADD  = 4'd0;
    localparam ALU_SUB  = 4'd1;
    localparam ALU_AND  = 4'd2;
    localparam ALU_OR   = 4'd3;
    localparam ALU_XOR  = 4'd4;
    localparam ALU_SLL  = 4'd5;
    localparam ALU_SRL  = 4'd6;
    localparam ALU_SRA  = 4'd7;
    localparam ALU_SLTU = 4'd8;

    // Comparator operation codes
    localparam CMP_EQ   = 3'd0;
    localparam CMP_NE   = 3'd1;
    localparam CMP_LT   = 3'd2;
    localparam CMP_GE   = 3'd3;
    localparam CMP_LTU  = 3'd4;
    localparam CMP_GEU  = 3'd5;
    localparam CMP_NONE = 3'd6;

    // Shift amount (lower 5 bits of alu_in2)
    logic [4:0] shamt;
    assign shamt = alu_in2[4:0];

    // ALU operations
    always_comb begin
        case (alu_op)
            ALU_ADD:  alu_out = alu_in1 + alu_in2;
            ALU_SUB:  alu_out = alu_in1 - alu_in2;
            ALU_AND:  alu_out = alu_in1 & alu_in2;
            ALU_OR:   alu_out = alu_in1 | alu_in2;
            ALU_XOR:  alu_out = alu_in1 ^ alu_in2;
            ALU_SLL:  alu_out = alu_in1 << shamt;
            ALU_SRL:  alu_out = alu_in1 >> shamt;
            ALU_SRA:  alu_out = $signed(alu_in1) >>> shamt;
            ALU_SLTU: alu_out = (alu_in1 < alu_in2) ? 32'd1 : 32'd0;
            default:  alu_out = 32'd0;
        endcase
    end

    // Comparator operations
    always_comb begin
        case (cmp_op)
            CMP_EQ:   cmp_out = (alu_in1 == alu_in2);
            CMP_NE:   cmp_out = (alu_in1 != alu_in2);
            CMP_LT:   cmp_out = ($signed(alu_in1) < $signed(alu_in2));
            CMP_GE:   cmp_out = ($signed(alu_in1) >= $signed(alu_in2));
            CMP_LTU:  cmp_out = (alu_in1 < alu_in2);
            CMP_GEU:  cmp_out = (alu_in1 >= alu_in2);
            default:  cmp_out = 1'b0;
        endcase
    end

endmodule
