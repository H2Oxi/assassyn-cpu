// Simple 32-bit adder module
module adder(
    input  logic [31:0] add_in1,
    input  logic [31:0] add_in2,
    output logic [31:0] add_out
);
    assign add_out = add_in1 + add_in2;
endmodule