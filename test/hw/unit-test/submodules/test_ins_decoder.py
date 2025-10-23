import csv
from pathlib import Path

from impl.gen_cpu.decoder_defs import (
    AddrPurpose,
    AddIn1Sel,
    AddIn2Sel,
    AddPostproc,
    AdderUse,
    AluOp,
    InstrFormat,
    MemWDataSel,
    WbDataSel,
)


def load_csv() -> dict[str, dict[str, str]]:
    rows = {}
    with open('docs/rv32i.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows[row['mnemonic']] = row
    return rows


def test_enum_alignment_basic():
    rows = load_csv()

    add_row = rows['add']
    assert add_row['inst_type'] == 'R'
    assert AluOp[add_row['alu_op']].value == AluOp.ADD.value
    assert add_row['wb_source'] == 'ALU'
    assert WbDataSel[add_row['wb_source']].value == WbDataSel.ALU.value

    addi_row = rows['addi']
    assert InstrFormat[addi_row['inst_type']].value == InstrFormat.I.value
    assert AluOp[addi_row['alu_op']].value == AluOp.ADD.value

    lw_row = rows['lw']
    assert AdderUse[lw_row['adder_use']].value == AdderUse.EA.value
    assert AddIn1Sel[lw_row['add_in1_sel']].value == AddIn1Sel.RS1.value
    assert AddIn2Sel[lw_row['add_in2_sel']].value == AddIn2Sel.IMM_I.value
    assert AddrPurpose[lw_row['addr_purpose']].value == AddrPurpose.EA.value
    assert WbDataSel[lw_row['wb_source']].value == WbDataSel.LOAD.value

    sw_row = rows['sw']
    assert InstrFormat[sw_row['inst_type']].value == InstrFormat.S.value
    assert MemWDataSel[sw_row['mem_wdata_sel']].value == MemWDataSel.RS2.value
    assert sw_row['mem_write'] == '1'

    jal_row = rows['jal']
    assert InstrFormat[jal_row['inst_type']].value == InstrFormat.J.value
    assert AdderUse[jal_row['adder_use']].value == AdderUse.J_TARGET.value
    assert WbDataSel[jal_row['wb_source']].value == WbDataSel.PC_PLUS4.value

    ecall_row = rows['ecall']
    assert InstrFormat[ecall_row['inst_type']].value == InstrFormat.SYS.value
    assert AdderUse[ecall_row['adder_use']].value == AdderUse.NONE.value
    assert AddPostproc[ecall_row['add_postproc']].value == AddPostproc.NONE.value


def test_system_verilog_presence():
    content = Path('impl/gen_cpu/external_src/ins_decoder.sv').read_text()
    for keyword in ['ALU_ADD', 'ALU_SUB', 'ADDER_EA', 'ADDER_J_TARGET']:
        assert keyword in content, f"Expected assignment '{keyword}' not found"
