''' A simplest single issue RISCV CPU, which has no operand buffer.'''
import os
import shutil
import subprocess

from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils

from impl.ip.ips import *
from impl.gen_cpu.submodules import InsDecoder
from impl.gen_cpu.decoder_defs import DecoderOutputType

''' Define the pipeline stages'''

class Fetchor(Module):
    
    def __init__(self):
        super().__init__(ports={}, no_arbiter=True)
        self.name = 'F'

    @module.combinational
    def build(self,fetch_valid:Array, decoder: Module, pc_reg: Array):

        with Condition(fetch_valid[0]):
            decoder.async_called(fetch_addr=pc_reg[0])

class Decoder(Module):
    
    def __init__(self):
        super().__init__(ports={
            'fetch_addr': Port(Bits(32)),
        })
        self.name = 'D'

    @module.combinational
    def build(self, executor: Module,rdata:RegArray):
        fetch_addr = self.pop_all_ports(False)# pop under fetchor's FSM control
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

        valid=decoder_output.decoded_valid & (~decoder_output.illegal)
        with Condition(valid):
            executor.async_called(
                fetch_addr=fetch_addr,

                )
        
        with Condition(~valid):
            log("Illegal instruction at address: 0x{:08X}, instruction: 0x{:08X}".format(fetch_addr.as_int(), instruction_code.as_int()))
            finish()
        
        return decoder_output




class Executor(Module):
    
    def __init__(self):
        super().__init__(ports={
            'fetch_addr': Port(Bits(32)),
            'alu_en': Port(Bits(1)),
            'alu_in1_sel': Port(Bits(2)),
            'alu_in2_sel': Port(Bits(2)),
            'alu_op': Port(Bits(4)),
            'cmp_op': Port(Bits(3)),

        })
        self.name = 'E'

    @module.combinational
    def build(self, memory_accessor: Module):
        fetch_addr = self.pop_port('fetch_addr')

        # instantiation of ALU, and other arithmetic units should be done here.
        
        pass
        



class MemoryAccessor(Module):
    
    def __init__(self):
        super().__init__(ports={}, no_arbiter=True)
        self.name = 'M'
    
    @module.combinational
    def build(self, write_back: Module):


        pass


class WriteBack(Module):
    
    def __init__(self):
        super().__init__(
            ports={
                'rd': Port(Bits(5)),
                'rd_data': Port(Bits(32)),
            }, no_arbiter=True)

        self.name = 'W'

    @module.combinational
    def build(self):

        rd, rd_data = self.pop_all_ports(False)
        return rd, rd_data
