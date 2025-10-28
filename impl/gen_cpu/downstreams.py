from assassyn.frontend import *
from impl.ip.ips import RegFile
from impl.gen_cpu.decoder_defs import AddrPurpose

class regfile_wrapper(Downstream):
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, rs1_addr:Value, rs2_addr:Value, rd_write_en:Value, rd_addr:Value, rd_wdata:Value):
        # Add optional protection to handle X values in early cycles
        rs1_addr = rs1_addr.optional(UInt(5)(0))
        rs2_addr = rs2_addr.optional(UInt(5)(0))
        rd_write_en = rd_write_en.optional(Bits(1)(0))
        rd_addr = rd_addr.optional(Bits(5)(0))
        rd_wdata = rd_wdata.optional(Bits(32)(0))

        regfile = RegFile(
            rs1_addr=rs1_addr,
            rs2_addr=rs2_addr,
            rd_we   =rd_write_en,
            rd_addr =rd_addr,
            rd_wdata=rd_wdata
        )

        return regfile.rs1_data, regfile.rs2_data


class jump_predictor_wrapper(Downstream):
    """Downstream module for managing PC updates and jump control

    This module:
    1. Receives jump information from Executor (addr_purpose, adder_result, cmp_out)
    2. Determines if a jump should be taken
    3. Manages PC update logic (PC+4 vs jump target)
    4. Provides next PC value to Fetchor
    5. Provides address update completion signal to Decoder
    """

    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, pc, addr_purpose, adder_result, cmp_out, cmp_out_used, jump_processed):
        """Build jump predictor logic

        This module updates the PC register based on jump/branch instructions.

        Args:
            pc: PC RegArray (created externally, passed in as input)
            addr_purpose: Address purpose from Executor (UInt(3), indicates jump type)
            adder_result: Calculated jump target address from Executor (UInt(32))
            cmp_out: Comparator output from Executor (Bits(1), for conditional branches)
            cmp_out_used: Flag from Executor (Bits(1), 1 for branch, 0 for JAL/JALR)

        Returns:
            jump_update_done: Signal indicating when jump processing is complete (Bits(1))
        """
        # Add optional protection for inputs that may be X in early cycles
        addr_purpose = addr_purpose.optional(UInt(3)(AddrPurpose.NONE.value))
        jump_target = adder_result.optional(UInt(32)(0))
        cmp_out = cmp_out.optional(Bits(1)(0))
        cmp_out_used = cmp_out_used.optional(Bits(1)(0))

        # Detect if this is a jump instruction
        # Note: ADDR_BR is used for both Branch and JAL instructions
        # ADDR_IND is used for JALR (indirect jump)
        is_br_or_jal = (addr_purpose == UInt(3)(AddrPurpose.BR_TARGET.value))
        is_jalr = (addr_purpose == UInt(3)(AddrPurpose.IND_TARGET.value))
        is_jump_instr = is_br_or_jal | is_jalr

        # Determine if jump should be taken
        # - For branches (cmp_out_used=1): take jump only if cmp_out is true (conditional)
        # - For JAL (cmp_out_used=0): always take jump (unconditional)
        # - For JALR (cmp_out_used=0): always take jump (unconditional)

        # Conditional branch: cmp_out_used=1 and cmp_out=1
        conditional_branch_taken = (cmp_out_used == Bits(1)(1)) & (cmp_out == Bits(1)(1))

        # Unconditional jump: JAL or JALR (cmp_out_used=0)
        unconditional_jump = (cmp_out_used == Bits(1)(0)) & is_jump_instr

        take_jump = conditional_branch_taken | unconditional_jump

        # Calculate next PC
        # If take_jump: use jump_target
        # Otherwise: use PC + 4
        pc_plus_4 = pc[0] + UInt(32)(4)
        next_pc = take_jump.select(jump_target, pc_plus_4)

        # Update PC register (this is the ONLY place where PC is assigned)
        (pc & self)[0] <= next_pc

        # Generate signal to decoder when address update is complete
        # We track whether a jump was processed in the previous cycle
        (jump_processed & self)[0] <= is_jump_instr.bitcast(Bits(1))

        # Log jump events for debugging
        with Condition(take_jump):
            log('[jump_predictor] PC: 0x{:08x} -> 0x{:08x} (addr_purpose:{} cmp_used:{} cmp:{})',
                pc[0], jump_target, addr_purpose, cmp_out_used, cmp_out)

        # Return the jump_update_done signal for Decoder to use
        return jump_processed[0]