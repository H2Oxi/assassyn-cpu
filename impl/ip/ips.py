from assassyn.frontend import *


@external
class Adder(ExternalSV):
    '''External SystemVerilog adder module.'''

    add_in1: WireIn[UInt(32)]# the input for adder
    add_in2: WireIn[UInt(32)]# the second input for adder
    add_out: WireOut[UInt(32)]# the output for adder, ignore overflow

    __source__: str = "impl/ip/adder.sv"
    __module_name__: str = "adder"

@external
class ALU(ExternalSV):
    '''External SystemVerilog ALU module.'''

    alu_in1: WireIn[UInt(32)]
    alu_in2: WireIn[UInt(32)]
    alu_op: WireOut[UInt(32)]
    cmp_op: WireOut[UInt(32)]
    alu_out: WireOut[UInt(32)]
    cmp_out: WireOut[Bits(1)]

    __source__: str = "impl/gen_cpu/external_src/alu.sv"
    __module_name__: str = "alu"


