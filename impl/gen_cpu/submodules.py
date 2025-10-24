from assassyn.frontend import *

from .decoder_defs import (
    AddrPurpose,
    AddIn1Sel,
    AddIn2Sel,
    AddPostproc,
    AdderUse,
    AluIn1Sel,
    AluIn2Sel,
    AluOp,
    CmpOp,
    InstrFormat,
    MemWDataSel,
    WbDataSel,
)


@external
class InsDecoder(ExternalSV):
    """External SystemVerilog instruction decoder for the RV32I subset.

    The decoder consumes the 32-bit instruction word and produces immediate
    values plus control signals that mirror the planning spreadsheet
    (docs/rv32i.csv). Enumerated outputs follow the numeric encodings defined
    in impl/gen_cpu/decoder_defs.py so the downstream Python can map them
    directly to mux selections or control bundles.
    """

    instr_in: WireIn[Bits(32)]  # Raw RV32I instruction word from fetch
    decoded_valid: WireOut[Bits(1)]  # High if opcode/funct tuple is supported
    illegal: WireOut[Bits(1)]  # Signals unimplemented/illegal instruction form

    instr_format: WireOut[UInt(3)]  # See InstrFormat

    rs1_addr: WireOut[UInt(5)]  # Source register 1 index
    rs2_addr: WireOut[UInt(5)]  # Source register 2 index
    rd_addr: WireOut[UInt(5)]   # Destination register index

    rs1_used: WireOut[Bits(1)]  # 1 when rs1 is consumed by the instruction
    rs2_used: WireOut[Bits(1)]  # 1 when rs2 is consumed by the instruction
    rd_write_en: WireOut[Bits(1)]  # 1 when rd writeback is architecturally required

    alu_en: WireOut[Bits(1)]  # 1 when ALU should execute (alu_op meaningful)
    alu_op: WireOut[UInt(4)]  # AluOp encoding
    alu_in1_sel: WireOut[UInt(2)]  # AluIn1Sel encoding
    alu_in2_sel: WireOut[UInt(2)]  # AluIn2Sel encoding
    cmp_op: WireOut[UInt(3)]  # CmpOp encoding
    cmp_out_used: WireOut[Bits(1)]  # 1 when comparator result gates control flow

    adder_use: WireOut[UInt(3)]  # AdderUse encoding
    add_in1_sel: WireOut[UInt(2)]  # AddIn1Sel encoding
    add_in2_sel: WireOut[UInt(3)]  # AddIn2Sel encoding
    add_postproc: WireOut[Bits(1)]  # 1 => clear LSB, see AddPostproc
    addr_purpose: WireOut[UInt(3)]  # AddrPurpose encoding

    wb_data_sel: WireOut[UInt(3)]  # WbDataSel encoding
    wb_en: WireOut[Bits(1)]  # Final writeback enable (includes rd!=x0 guard)

    mem_read: WireOut[Bits(1)]  # Data memory read enable
    mem_write: WireOut[Bits(1)]  # Data memory write enable
    mem_wdata_sel: WireOut[Bits(1)]  # MemWDataSel encoding
    mem_wstrb: WireOut[Bits(4)]  # Byte enables for stores

    imm: WireOut[UInt(32)]  # Unified immediate output (type determined by instruction format and sel signals)

    __source__: str = "../impl/external_src/ins_decoder.sv"
    __module_name__: str = "ins_decoder"
