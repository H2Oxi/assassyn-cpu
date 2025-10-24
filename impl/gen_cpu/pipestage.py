''' A simplest single issue RISCV CPU, which has no operand buffer.
'''
import os
import shutil
import subprocess

from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils

from impl.ip.ips import *

''' Define the pipeline stages'''

class Fetchor(Module):
    
    def __init__(self):
        super().__init__(ports={}, no_arbiter=True)
        self.name = 'F'

    @module.combinational
    def build(self):
        pc_reg = RegArray(Bits(32), 1)
        addr = pc_reg[0]

        return pc_reg, addr
    
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

        # we should generate the input given to executor here(ALU signals, immediate values.)
        #alu_a, alu_b, alu_op = decoding_logic(instruction_code)

        #valid checker
        #valid = valid_checker(signals)

        # downstream: oprand_bypass
        #executor.async_called(valid=valid, alu_a=alu_a, alu_b=alu_b, alu_op=alu_op, fetch_addr=fetch_addr)

        


class Executor(Module):
    
    def __init__(self):
        super().__init__(ports={
            'valid': Port(),
            'alu_a': Port(),
            'alu_b': Port(),
            'alu_op': Port(Bits(4)),
            'fetch_addr': Port(Bits(32)),
        })
        self.name = 'E'

    @module.combinational
    def build(self):
        
        valid = self.pop_port('valid')
        wait_until(valid)

        # instantiation of ALU, and other arithmetic units should be done here.
        pass


class MemoryAccessor(Module):
    
    def __init__(self):
        super().__init__(ports={}, no_arbiter=True)
        self.name = 'M'
    
    @module.combinational
    def build(self):


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
