''' A simplest single issue RISCV CPU, which has no operand buffer.'''
import os
import shutil
import subprocess

from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils

from impl.ip.ips import ALU, Adder
from impl.gen_cpu.submodules import InsDecoder
from impl.gen_cpu.decoder_defs import (
    AluIn1Sel, AluIn2Sel, AddIn1Sel, AddIn2Sel, MemWDataSel, WbDataSel, AddrPurpose
)

''' Define the pipeline stages'''

class Fetchor(Module):

    def __init__(self):
        super().__init__(ports={}, no_arbiter=True)
        self.name = 'F'

    @module.combinational
    def build(self, decoder: Module, pc: RegArray, jump_update_done: RegArray, init_file:str, depth_log:int=9):
        """Fetch instructions from icache and pass to decoder

        Args:
            decoder: Decoder module to receive fetched instructions
            pc: Program Counter RegArray from jump_predictor_wrapper
            jump_update_done: Signal from jump_predictor indicating jump completion
            init_file: Path to instruction memory initialization file
            depth_log: Log2 of instruction cache depth (default 9 = 512 entries)
        """
        # Instantiate instruction cache
        icache = SRAM(width=32, depth=1<<depth_log, init_file=init_file)
        icache.name = 'icache'

        # Read from icache: we=0 (no write), re=1 (read enable)
        # Address is PC >> 2 (word-aligned, so divide by 4)
        fetch_addr = pc[0][2:2+depth_log-1].bitcast(UInt(depth_log))
        icache.build(
            we=Bits(1)(0),     # Write enable = 0 (read-only)
            re=Bits(1)(1),     # Read enable = 1
            addr=fetch_addr,   # Fetch address (word-aligned)
            wdata=Bits(32)(0)  # Write data (unused)
        )

        # Log fetch address for debugging
        log('[fetchor] fetch_addr: 0x{:08x}', pc[0])

        # Pass fetched instruction, PC, and jump_update_done to decoder
        decoder.async_called(fetch_addr=pc[0], jump_update_done=jump_update_done[0])

        # Return icache output for decoder to use
        return icache.dout

class Decoder(Module):

    def __init__(self):
        super().__init__(ports={
            'fetch_addr': Port(Bits(32)),
            'jump_update_done': Port(Bits(1)),  # Signal from jump_predictor_wrapper
        })
        self.name = 'D'

    @module.combinational
    def build(self, executor: Module, rdata: RegArray):
        """Decode instruction and pass control signals to executor

        Args:
            executor: Executor module to receive decoded control signals
            rdata: Instruction data from icache (RegArray from Fetchor)

        Returns:
            Tuple of (rs1_addr, rs2_addr, imm) for regfile_wrapper
        """
        # Pop ports
        # fetch_addr comes from Fetchor
        # jump_update_done comes from jump_predictor_wrapper when PC update is complete
        fetch_addr, jump_update_done = self.pop_all_ports(False)
        instruction_code = rdata[0].bitcast(Bits(32))

        # Log instruction data for debugging
        log('[decoder] fetch_addr: 0x{:08x} ins: 0x{:08x}', fetch_addr, instruction_code)

        # Instantiate the instruction decoder and use outputs directly
        decoder = InsDecoder(instr_in=instruction_code)

        # Check if instruction is valid (decoded correctly and not illegal)
        base_valid = decoder.decoded_valid & (~decoder.illegal)

        # Detect if this is a jump instruction based on addr_purpose
        from impl.gen_cpu.decoder_defs import AddrPurpose
        is_jump = (decoder.addr_purpose == UInt(3)(AddrPurpose.BR_TARGET.value)) | \
                  (decoder.addr_purpose == UInt(3)(AddrPurpose.IND_TARGET.value))

        # Valid control logic:
        # - We use a register to track if we're waiting for a jump to complete
        # - When a jump instruction is detected, we set waiting_for_jump=1
        # - We keep valid disabled until jump_update_done signal arrives
        # - After jump_update_done, we resume normal operation
        jump_inflight = RegArray(Bits(1), 1, initializer=[0])

        jump_request = (base_valid & is_jump).bitcast(Bits(1))
        next_jump_inflight = jump_request | (jump_inflight[0] & ~jump_update_done)
        (jump_inflight & self)[0] <= next_jump_inflight

        # Final valid signal: only valid if no jump in flight
        valid = base_valid & ~jump_inflight[0]

        # Pass all necessary control signals to executor
        with Condition(valid == Bits(1)(1)):
            executor.async_called(
                fetch_addr=fetch_addr,
                # ALU control signals
                alu_en=decoder.alu_en,
                alu_in1_sel=decoder.alu_in1_sel,
                alu_in2_sel=decoder.alu_in2_sel,
                alu_op=decoder.alu_op,
                cmp_op=decoder.cmp_op,
                cmp_out_used=decoder.cmp_out_used,  # For jump_predictor
                # Adder control signals
                adder_use=decoder.adder_use,
                add_in1_sel=decoder.add_in1_sel,
                add_in2_sel=decoder.add_in2_sel,
                add_postproc=decoder.add_postproc,
                addr_purpose=decoder.addr_purpose,  # For jump_predictor
                # Memory control signals
                mem_read=decoder.mem_read,
                mem_write=decoder.mem_write,
                mem_wdata_sel=decoder.mem_wdata_sel,
                mem_wstrb=decoder.mem_wstrb,
                # Writeback control signals
                wb_data_sel=decoder.wb_data_sel,
                wb_en=decoder.wb_en,
                rd_addr=decoder.rd_addr,
                # Immediate value
                imm=decoder.imm,
            )

        # Handle illegal instructions
        with Condition(decoder.illegal == Bits(1)(1)):
            log("Illegal instruction at address: 0x{:08x}, instruction: 0x{:08x}",
                fetch_addr, instruction_code)
            finish()

        # Return signals needed for regfile read:
        # - rs1_addr, rs2_addr: for reading source registers
        # - imm: immediate value (may be used in downstream modules)
        # Note: rd_addr and rd_write_en are passed through the pipeline
        # via Executor → MemoryAccessor → WriteBack, not returned here
        return (decoder.rs1_addr, decoder.rs2_addr, decoder.imm)




class Executor(Module):

    def __init__(self):
        super().__init__(ports={
            'fetch_addr': Port(Bits(32)),
            # ALU control signals
            'alu_en': Port(Bits(1)),
            'alu_in1_sel': Port(UInt(2)),
            'alu_in2_sel': Port(UInt(2)),
            'alu_op': Port(UInt(4)),
            'cmp_op': Port(UInt(3)),
            'cmp_out_used': Port(Bits(1)),  # For jump control
            # Adder control signals
            'adder_use': Port(UInt(3)),
            'add_in1_sel': Port(UInt(2)),
            'add_in2_sel': Port(Bits(1)),
            'add_postproc': Port(Bits(1)),
            'addr_purpose': Port(UInt(3)),  # For jump control
            # Memory control signals
            'mem_read': Port(Bits(1)),
            'mem_write': Port(Bits(1)),
            'mem_wdata_sel': Port(Bits(1)),
            'mem_wstrb': Port(Bits(4)),
            # Writeback control signals
            'wb_data_sel': Port(UInt(3)),
            'wb_en': Port(Bits(1)),
            'rd_addr': Port(UInt(5)),
            # Immediate value
            'imm': Port(UInt(32)),
        })
        self.name = 'E'

    @module.combinational
    def build(self, memory_accessor: Module, RS1_data: Array, RS2_data: Array,
              init_file: str, depth_log: int = 9):
        """Execute ALU operations, address calculation, and memory access

        Args:
            memory_accessor: MemoryAccessor module for next pipeline stage
            RS1_data: Register file rs1 read data
            RS2_data: Register file rs2 read data
            init_file: Data cache initialization file
            depth_log: Log2 of data cache depth (default 9 = 512 entries)
        """
        # Pop all control signals from ports
        (fetch_addr, alu_en, alu_in1_sel, alu_in2_sel, alu_op, cmp_op, cmp_out_used,
         adder_use, add_in1_sel, add_in2_sel, add_postproc, addr_purpose,
         mem_read, mem_write, mem_wdata_sel, mem_wstrb,
         wb_data_sel, wb_en, rd_addr, imm) = self.pop_all_ports(False)
        # Pass-through control signals for downstream modules

        # ========== ALU Input Selection ==========
        # Select ALU input 1: ZERO or RS1
        alu_in1 = (alu_in1_sel == UInt(2)(AluIn1Sel.RS1.value)).select(
            RS1_data[0],
            UInt(32)(0)  # ZERO
        )

        # Select ALU input 2: ZERO, RS2, or IMM
        alu_in2 = UInt(32)(0)  # default ZERO
        alu_in2 = (alu_in2_sel == UInt(2)(AluIn2Sel.RS2.value)).select(RS2_data[0], alu_in2)
        alu_in2 = (alu_in2_sel == UInt(2)(AluIn2Sel.IMM.value)).select(imm, alu_in2)

        # Override ALU inputs for branch compare when cmp_out is used
        cmp_override = (cmp_out_used == Bits(1)(1))
        alu_in1_final = cmp_override.select(RS1_data[0], alu_in1)
        alu_in2_final = cmp_override.select(RS2_data[0], alu_in2)

        # Instantiate ALU
        alu = ALU(
            alu_in1=alu_in1_final,
            alu_in2=alu_in2_final,
            alu_op=alu_op,
            cmp_op=cmp_op,
        )

        # ========== Adder Input Selection ==========
        # Select adder input 1: ZERO, RS1, or PC
        add_in1 = UInt(32)(0)  # default ZERO
        add_in1 = (add_in1_sel == UInt(2)(AddIn1Sel.RS1.value)).select(RS1_data[0], add_in1)
        add_in1 = (add_in1_sel == UInt(2)(AddIn1Sel.PC.value)).select(
            fetch_addr.bitcast(UInt(32)), add_in1)

        # Select adder input 2: ZERO or IMM
        add_in2 = (add_in2_sel == Bits(1)(AddIn2Sel.IMM.value)).select(
            imm,
            UInt(32)(0)  # ZERO
        )

        # Instantiate Adder
        adder = Adder(
            add_in1=add_in1,
            add_in2=add_in2,
        )

        # Apply post-processing: clear LSB if needed (for JALR)
        # Ensure both branches have the same type (UInt(32))
        add_out_uint = adder.add_out.bitcast(UInt(32))  # Ensure UInt(32)
        masked_out = (add_out_uint & UInt(32)(0xFFFFFFFE)).bitcast(UInt(32))  # Clear LSB
        adder_result = (add_postproc == Bits(1)(1)).select(
            masked_out,  # UInt(32)
            add_out_uint  # UInt(32)
        )

        # ========== Data Memory (dcache) ==========
        dcache = SRAM(width=32, depth=1<<depth_log, init_file=init_file)
        dcache.name = 'dcache'

        # Memory address: use adder result for effective address calculation
        mem_addr = adder_result[2:2+depth_log-1].bitcast(UInt(depth_log))

        # Memory write data selection: RS2
        mem_wdata = (mem_wdata_sel == Bits(1)(MemWDataSel.RS2.value)).select(
            RS2_data[0].bitcast(Bits(32)),
            Bits(32)(0)
        )

        # Build dcache with control signals
        dcache.build(
            we=mem_write,
            re=mem_read,
            addr=mem_addr,
            wdata=mem_wdata
        )

        # ========== Pass to Memory Accessor ==========
        memory_accessor.async_called(
            alu_out=alu.alu_out,
            cmp_out=alu.cmp_out,
            adder_out=adder_result,
            imm=imm,
            fetch_addr=fetch_addr,
            wb_data_sel=wb_data_sel,
            wb_en=wb_en,
            rd_addr=rd_addr,
        )

        with Condition(addr_purpose == UInt(3)(AddrPurpose.BR_TARGET.value)):
            log('[executor] branch fetch_addr:0x{:08x} rs1:0x{:08x} rs2:0x{:08x} cmp_op:{} cmp_out:{} cmp_used:{} target:0x{:08x}',
                fetch_addr, RS1_data[0], RS2_data[0], cmp_op, alu.cmp_out, cmp_out_used, adder_result)

        # Return dcache and jump control signals for external connections
        # dcache: for memory_accessor
        # Jump control signals: for jump_predictor_wrapper
        return dcache, addr_purpose, adder_result, alu.cmp_out, cmp_out_used
        



class MemoryAccessor(Module):

    def __init__(self):
        super().__init__(ports={
            'alu_out': Port(UInt(32)),
            'cmp_out': Port(Bits(1)),
            'adder_out': Port(UInt(32)),
            'imm': Port(UInt(32)),
            'fetch_addr': Port(Bits(32)),
            'wb_data_sel': Port(UInt(3)),
            'wb_en': Port(Bits(1)),
            'rd_addr': Port(UInt(5)),
        }, no_arbiter=True)
        self.name = 'M'

    @module.combinational
    def build(self, write_back: Module, mem_rdata: RegArray):
        """Select writeback data and pass to WriteBack stage

        Args:
            write_back: WriteBack module for final register write
            mem_rdata: Memory read data from dcache.dout (RegArray)

        Returns:
            Selected writeback data based on wb_data_sel
        """
        # Pop all signals from ports
        (alu_out, cmp_out, adder_out, imm, fetch_addr,
         wb_data_sel, wb_en, rd_addr) = self.pop_all_ports(False)

        # ========== Writeback Data Selection ==========
        # Default to NONE (zero)
        wb_data = UInt(32)(0)

        # Select based on wb_data_sel
        wb_data = (wb_data_sel == UInt(3)(WbDataSel.ALU.value)).select(
            alu_out, wb_data)

        wb_data = (wb_data_sel == UInt(3)(WbDataSel.IMM.value)).select(
            imm, wb_data)

        wb_data = (wb_data_sel == UInt(3)(WbDataSel.ADDER.value)).select(
            adder_out, wb_data)

        wb_data = (wb_data_sel == UInt(3)(WbDataSel.LOAD.value)).select(
            mem_rdata[0].bitcast(UInt(32)), wb_data)

        wb_data = (wb_data_sel == UInt(3)(WbDataSel.LOAD_ZEXT8.value)).select(
            (mem_rdata[0].bitcast(UInt(32)) & UInt(32)(0xFF)).bitcast(UInt(32)),  # Zero-extend byte
            wb_data)

        with Condition(wb_data_sel == UInt(3)(WbDataSel.LOAD.value)):
            log('[memory_accessor] load addr:0x{:08x} data:0x{:08x}',
                adder_out, mem_rdata[0].bitcast(UInt(32)))

        # PC+4 for JAL/JALR return address
        pc_plus4 = fetch_addr.bitcast(UInt(32)) + UInt(32)(4)
        wb_data = (wb_data_sel == UInt(3)(WbDataSel.PC_PLUS4.value)).select(
            pc_plus4, wb_data)

        # ========== Pass to WriteBack ==========
        write_back.async_called(
            rd=rd_addr.bitcast(Bits(5)),
            rd_data=wb_data.bitcast(Bits(32)),
            wb_en=wb_en
        )

        return wb_data


class WriteBack(Module):
    """WriteBack stage - final pipeline stage that returns writeback data

    This is the simplest pipeline stage that just receives the writeback
    data from MemoryAccessor and returns it for regfile_wrapper to use.
    """

    def __init__(self):
        super().__init__(
            ports={
                'rd': Port(Bits(5)),        # Destination register address
                'rd_data': Port(Bits(32)),  # Writeback data
                'wb_en': Port(Bits(1)),     # Writeback enable
            }, no_arbiter=True)

        self.name = 'W'

    @module.combinational
    def build(self):
        """Pop writeback signals and return for regfile connection

        Returns:
            Tuple of (rd, rd_data, wb_en) to be connected to regfile_wrapper
        """
        # Pop writeback data from ports (sent by MemoryAccessor)
        rd, rd_data, wb_en = self.pop_all_ports(False)
        prev_wb_en = RegArray(Bits(1), 1, initializer=[0])
        prev_rd = RegArray(Bits(5), 1, initializer=[0])
        prev_data = RegArray(Bits(32), 1, initializer=[0])

        same_en = (prev_wb_en[0] == wb_en)
        same_rd = (prev_rd[0] == rd)
        same_data = (prev_data[0] == rd_data)

        new_write = (wb_en == Bits(1)(1)) & (~same_en | ~same_rd | ~same_data)

        (prev_wb_en & self)[0] <= wb_en
        (prev_rd & self)[0] <= rd
        (prev_data & self)[0] <= rd_data

        # Log writeback data for verification
        # Format: [writeback] x<rd>: 0x<rd_data> (matches 0to100.sh requirements)
        with Condition(new_write):
            log('[writeback] x{}: 0x{:08x}', rd.bitcast(UInt(5)), rd_data)

        # Return for external connection to regfile_wrapper
        return rd, rd_data, wb_en
