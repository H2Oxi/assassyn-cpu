from assassyn.frontend import *
from impl.gen_cpu.submodules import InsDecoder
from impl.gen_cpu.decoder_defs import DecoderOutputType

class Decoder(Module):
    
    def __init__(self):
        super().__init__(ports={})
        self.name = 'D'

    @module.combinational
    def build(self, rdata:RegArray):
        # Extract instruction from rdata
        instruction_code = rdata[0].bitcast(Bits(32))

        # Instantiate the instruction decoder
        decoder = InsDecoder(instr_in=instruction_code)

        # Bundle all decoder outputs into a Record using the imported type
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

        return decoder_output

