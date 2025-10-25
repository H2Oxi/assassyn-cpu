from assassyn.frontend import *
from assassyn.test import run_test
from impl.gen_cpu.dut.decoding import Decoder
from impl.gen_cpu.submodules import InsDecoder
from impl.gen_cpu.decoder_defs import (
    DecoderOutputType,
    InstrFormat,
    AluOp,
    CmpOp,
    AluIn1Sel,
    AluIn2Sel,
    AdderUse,
    AddIn1Sel,
    AddIn2Sel,
    WbDataSel,
)
from assassyn.backend import elaborate
from assassyn import utils


class Driver(Module):
    """Driver module to fetch instructions from SRAM sequentially"""

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, width, init_file, decoder):
        # Counter for address generation
        cnt = RegArray(UInt(32), 1)
        addr = cnt[0][0:8].bitcast(UInt(9))  # Use lower 9 bits as address

        # Increment counter
        (cnt & self)[0] <= cnt[0] + UInt(32)(1)

        # Instantiate SRAM with instruction memory
        # width=32 for 32-bit instructions, 512 entries
        sram = SRAM(width, 512, init_file)

        # Read from SRAM (we=0, re=1 for read-only)
        we = Bits(1)(0)
        re = Bits(1)(1)
        wdata = Bits(width)(0)
        sram.build(we, re, addr, wdata)

        # Call decoder asynchronously with SRAM output
        decoder.async_called()

        return sram


def decode_instruction_ref(inst_code):
    """Python reference decoder for verification

    Returns a dict with expected decoder outputs
    """
    opcode = inst_code & 0x7F
    funct3 = (inst_code >> 12) & 0x7
    funct7 = (inst_code >> 25) & 0x7F

    rd = (inst_code >> 7) & 0x1F
    rs1 = (inst_code >> 15) & 0x1F
    rs2 = (inst_code >> 20) & 0x1F

    result = {
        'inst_code': inst_code,
        'opcode': opcode,
        'rd': rd,
        'rs1': rs1,
        'rs2': rs2,
        'funct3': funct3,
        'funct7': funct7,
        'decoded_valid': 1,
        'illegal': 0,
    }

    # Decode based on opcode
    if opcode == 0b0110011:  # R-type (add, sub, and, or, xor, sll, srl, sra, sltu)
        result['instr_format'] = InstrFormat.R
        result['rs1_used'] = 1
        result['rs2_used'] = 1
        result['rd_write_en'] = 1 if rd != 0 else 0
        result['alu_en'] = 1

    elif opcode == 0b0010011:  # I-type ALU (addi, andi, ori, xori, slli, srli, srai)
        result['instr_format'] = InstrFormat.I
        result['rs1_used'] = 1
        result['rs2_used'] = 0
        result['rd_write_en'] = 1 if rd != 0 else 0
        result['alu_en'] = 1

    elif opcode == 0b0000011:  # I-type Load (lw, lbu)
        result['instr_format'] = InstrFormat.I
        result['rs1_used'] = 1
        result['rs2_used'] = 0
        result['rd_write_en'] = 1 if rd != 0 else 0
        result['mem_read'] = 1

    elif opcode == 0b0100011:  # S-type (sw)
        result['instr_format'] = InstrFormat.S
        result['rs1_used'] = 1
        result['rs2_used'] = 1
        result['rd_write_en'] = 0
        result['mem_write'] = 1

    elif opcode == 0b1100011:  # B-type (beq, bne, blt, bge, bltu, bgeu)
        result['instr_format'] = InstrFormat.B
        result['rs1_used'] = 1
        result['rs2_used'] = 1
        result['rd_write_en'] = 0
        result['cmp_out_used'] = 1

    elif opcode == 0b0110111:  # U-type (lui)
        result['instr_format'] = InstrFormat.U
        result['rs1_used'] = 0
        result['rs2_used'] = 0
        result['rd_write_en'] = 1 if rd != 0 else 0

    elif opcode == 0b0010111:  # U-type (auipc)
        result['instr_format'] = InstrFormat.U
        result['rs1_used'] = 0
        result['rs2_used'] = 0
        result['rd_write_en'] = 1 if rd != 0 else 0

    elif opcode == 0b1101111:  # J-type (jal)
        result['instr_format'] = InstrFormat.J
        result['rs1_used'] = 0
        result['rs2_used'] = 0
        result['rd_write_en'] = 1 if rd != 0 else 0

    elif opcode == 0b1100111:  # I-type (jalr)
        result['instr_format'] = InstrFormat.I
        result['rs1_used'] = 1
        result['rs2_used'] = 0
        result['rd_write_en'] = 1 if rd != 0 else 0

    elif opcode == 0b1110011:  # System (ebreak, ecall, fence)
        result['instr_format'] = InstrFormat.SYS
        result['rs1_used'] = 0
        result['rs2_used'] = 0
        result['rd_write_en'] = 0

    else:
        result['decoded_valid'] = 0
        result['illegal'] = 1

    return result


def check_decoder(raw):
    """Check decoder outputs against reference decoder"""
    lines = raw.splitlines()
    test_count = 0
    error_count = 0

    for line in lines:
        if '[decoder_test]' not in line:
            continue

        # Parse the log line
        # Expected format: Cycle @N.NN: [Module] [decoder_test] inst:0x12345678 rd:5 rs1:10 rs2:15 ...
        # Extract the part after [decoder_test]
        decoder_part = line.split('[decoder_test]')[1].strip()
        tokens = decoder_part.split()

        inst_code = None
        hw_outputs = {}

        for token in tokens:
            if ':' not in token:
                continue
            parts = token.split(':')
            if len(parts) != 2:
                continue
            key, value = parts
            if not value:  # Skip empty values
                continue
            if key == 'inst':
                inst_code = int(value, 16)
            else:
                try:
                    hw_outputs[key] = int(value)
                except ValueError:
                    continue

        if inst_code is None or inst_code == 0:
            continue

        # Get reference outputs
        ref_outputs = decode_instruction_ref(inst_code)

        # Compare key fields
        test_count += 1
        errors = []

        # Check register addresses
        if 'rd' in hw_outputs and hw_outputs['rd'] != ref_outputs['rd']:
            errors.append(f"rd mismatch: hw={hw_outputs['rd']} ref={ref_outputs['rd']}")
        if 'rs1' in hw_outputs and hw_outputs['rs1'] != ref_outputs['rs1']:
            errors.append(f"rs1 mismatch: hw={hw_outputs['rs1']} ref={ref_outputs['rs1']}")
        if 'rs2' in hw_outputs and hw_outputs['rs2'] != ref_outputs['rs2']:
            errors.append(f"rs2 mismatch: hw={hw_outputs['rs2']} ref={ref_outputs['rs2']}")

        if errors:
            error_count += 1
            print(f"Instruction 0x{inst_code:08x}: {', '.join(errors)}")

    print(f"Tested {test_count} instructions, {error_count} errors")
    assert error_count == 0, f"Decoder test failed with {error_count} errors"


def test_decoder():
    """Test the instruction decoder with 0to100.exe benchmark"""

    # Create a custom decoder module that includes logging
    class DecoderWithLog(Module):
        def __init__(self):
            super().__init__(ports={})

        @module.combinational
        def build(self, rdata: RegArray):
            # Extract instruction from rdata
            instruction_code = rdata[0].bitcast(Bits(32))

            # Instantiate the instruction decoder
            decoder = InsDecoder(instr_in=instruction_code)

            # Bundle all decoder outputs into a Record
            decoder_output = DecoderOutputType.bundle(
                decoded_valid=decoder.decoded_valid,
                illegal=decoder.illegal,
                instr_format=decoder.instr_format,
                rs1_addr=decoder.rs1_addr,
                rs2_addr=decoder.rs2_addr,
                rd_addr=decoder.rd_addr,
                rs1_used=decoder.rs1_used,
                rs2_used=decoder.rs2_used,
                rd_write_en=decoder.rd_write_en,
                alu_en=decoder.alu_en,
                alu_op=decoder.alu_op,
                alu_in1_sel=decoder.alu_in1_sel,
                alu_in2_sel=decoder.alu_in2_sel,
                cmp_op=decoder.cmp_op,
                cmp_out_used=decoder.cmp_out_used,
                adder_use=decoder.adder_use,
                add_in1_sel=decoder.add_in1_sel,
                add_in2_sel=decoder.add_in2_sel,
                add_postproc=decoder.add_postproc,
                addr_purpose=decoder.addr_purpose,
                wb_data_sel=decoder.wb_data_sel,
                wb_en=decoder.wb_en,
                mem_read=decoder.mem_read,
                mem_write=decoder.mem_write,
                mem_wdata_sel=decoder.mem_wdata_sel,
                mem_wstrb=decoder.mem_wstrb,
                imm=decoder.imm,
            )

            # Log decoder outputs for verification
            log('[decoder_test] inst:{:x} rd:{} rs1:{} rs2:{} fmt:{} alu_en:{}',
                instruction_code,
                decoder_output.rd_addr,
                decoder_output.rs1_addr,
                decoder_output.rs2_addr,
                decoder_output.instr_format,
                decoder_output.alu_en)

            return decoder_output

    def top():
        decoder = DecoderWithLog()
        driver = Driver()

        # Build driver with SRAM initialized from 0to100.exe
        sram = driver.build(32, '0to100.exe', decoder)

        # Build decoder with SRAM output
        decoder.build(sram.dout)

    run_test('test_decoder', top, check_decoder,
             sim_threshold=50, idle_threshold=50,
             resource_base='/Users/gaod/work/assassyn-cpu/resources/riscv/benchmarks')


if __name__ == "__main__":
    test_decoder()




