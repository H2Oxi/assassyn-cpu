from assassyn.frontend import *


@external
class Adder(ExternalSV):
    '''External SystemVerilog adder module.'''

    add_in1: WireIn[UInt(32)]# the input for adder
    add_in2: WireIn[UInt(32)]# the second input for adder
    add_out: WireOut[UInt(32)]# the output for adder, ignore overflow

    __source__: str = "../impl/ip/ip_repo/adder.sv"
    __module_name__: str = "adder"

@external
class ALU(ExternalSV):
    '''External SystemVerilog ALU module for RV32I instruction set.

    Supports arithmetic, logical, and comparison operations based on rv32i.csv specification.
    '''

    alu_in1: WireIn[UInt(32)]  # First operand for ALU operations
    alu_in2: WireIn[UInt(32)]  # Second operand for ALU operations
    alu_op: WireIn[UInt(4)]    # ALU operation code: 0=ADD, 1=SUB, 2=AND, 3=OR, 4=XOR, 5=SLL, 6=SRL, 7=SRA, 8=SLTU
    cmp_op: WireIn[UInt(3)]    # Comparator operation code: 0=EQ, 1=NE, 2=LT, 3=GE, 4=LTU, 5=GEU, 6=NONE
    alu_out: WireOut[UInt(32)] # ALU operation result (32-bit output)
    cmp_out: WireOut[Bits(1)]  # Comparator result (1-bit: 1=true, 0=false)

    __source__: str = "../impl/ip/ip_repo/alu.sv"
    __module_name__: str = "alu"

@external
class RegFile(ExternalSV):
    '''External SystemVerilog Register File module for RV32I.

    32 general-purpose registers with 2 read ports and 1 write port.
    Synchronous read/write (BRAM-friendly) with 1-cycle read latency.
    x0 always reads 0, writes to x0 are ignored.
    Includes internal bypass for same-cycle read-write conflicts.
    '''

    # Read port 1 (rs1)
    rs1_addr: WireIn[UInt(5)]    # Read address for rs1 (0-31)
    rs1_data: RegOut[UInt(32)]   # Read data from rs1 (1-cycle delayed)
    # Read port 2 (rs2)
    rs2_addr: WireIn[UInt(5)]    # Read address for rs2 (0-31)
    rs2_data: RegOut[UInt(32)]   # Read data from rs2 (1-cycle delayed)
    # Write port (rd)
    rd_we: WireIn[Bits(1)]       # Write enable for rd (ignored if rd_addr==0)
    rd_addr: WireIn[UInt(5)]     # Write address for rd (0-31)
    rd_wdata: WireIn[UInt(32)]   # Write data for rd

    __source__: str = "../impl/ip/ip_repo/regfile.sv"
    __module_name__: str = "regfile"
    __has_clock__: bool = True   # Requires clock signal
    __has_reset__: bool = True   # Requires reset signal (active-high)


