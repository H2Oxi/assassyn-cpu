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
    """Downstream module that manages program counter updates.

    Inputs:
        pc (RegArray[UInt(32)]): shared PC register updated in this module only.
        addr_purpose (UInt(3)): executor output indicating the purpose of adder_result.
        adder_result (UInt(32)): jump target calculated by the executor.
        cmp_out (Bits(1)): branch comparator output.
        cmp_out_used (Bits(1)): flag showing whether cmp_out is meaningful (branches).
        jump_processed (RegArray[Bits(1)]): handshake flag for decoder valid control.

    Output:
        jump_processed[0]: combinational view of the handshake flag for downstream modules.

    Internal state is modelled with an FSM to ensure every jump is handled exactly once while
    keeping sequential PC updates explicit.
    """

    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, pc, addr_purpose, adder_result, cmp_out, cmp_out_used, jump_processed):
        """Select between sequential and jump target PC values and drive the handshake."""
        # Optional protects propagating X during reset
        addr_purpose = addr_purpose.optional(UInt(3)(AddrPurpose.NONE.value))
        jump_target = adder_result.optional(UInt(32)(0))
        cmp_out = cmp_out.optional(Bits(1)(0))
        cmp_out_used = cmp_out_used.optional(Bits(1)(0))

        # Determine jump categories
        is_branch_or_jal = (addr_purpose == UInt(3)(AddrPurpose.BR_TARGET.value))
        is_indirect_jump = (addr_purpose == UInt(3)(AddrPurpose.IND_TARGET.value))
        is_j_target = (addr_purpose == UInt(3)(AddrPurpose.J_TARGET.value))
        is_jump_instr = (is_branch_or_jal | is_indirect_jump | is_j_target).bitcast(Bits(1))

        # Default sequential next PC
        pc_plus_4 = pc[0] + UInt(32)(4)

        # FSM state: idle -> cooldown once a jump is observed, back to idle after pipeline flush
        fsm_state = RegArray(Bits(1), 1, initializer=[0])

        cond_jump = (is_jump_instr == Bits(1)(1))
        cond_no_jump = (is_jump_instr == Bits(1)(0))

        transfer_table = {
            "idle": {
                cond_jump: "cooldown",
                cond_no_jump: "idle",
            },
            "cooldown": {
                cond_no_jump: "idle",
                cond_jump: "cooldown",
            },
        }

        def idle_body():
            jump_candidate = (is_jump_instr == Bits(1)(1))
            branch_enabled = (cmp_out_used == Bits(1)(1))
            branch_condition = branch_enabled.select(cmp_out, Bits(1)(1))
            jump_taken = jump_candidate & branch_condition

            next_pc_value = jump_taken.select(jump_target, pc_plus_4)
            jump_processed_value = jump_candidate

            (pc & self)[0] <= next_pc_value
            (jump_processed & self)[0] <= jump_processed_value

            with Condition(jump_candidate == Bits(1)(1)):
                log('[jump_predictor] inspect addr_purpose:{} cmp_used:{} cmp:{} taken:{} target:0x{:08x}',
                    addr_purpose, cmp_out_used, cmp_out, jump_taken, jump_target)

            with Condition(jump_taken == Bits(1)(1)):
                log('[jump_predictor] PC: 0x{:08x} -> 0x{:08x} (addr_purpose:{} cmp_used:{} cmp:{} taken:{})',
                    pc[0], next_pc_value, addr_purpose, cmp_out_used, cmp_out, jump_taken)

        def cooldown_body():
            # Continue sequential fetch while Decoder drains the previous jump
            (pc & self)[0] <= pc_plus_4
            (jump_processed & self)[0] <= Bits(1)(0)

        body_table = {
            "idle": idle_body,
            "cooldown": cooldown_body,
        }

        jump_fsm = fsm.FSM(fsm_state, transfer_table)
        jump_fsm.generate(body_table)

        return jump_processed[0]
