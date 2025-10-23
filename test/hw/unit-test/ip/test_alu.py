from assassyn.frontend import *
from assassyn.test import run_test
from impl.ip.ips import ALU as ExternalALU

from assassyn.backend import elaborate
from assassyn import utils


class Driver(Module):

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, forward1: Module, forward2: Module, forward3: Module, forward4: Module):
        cnt = RegArray(UInt(32), 1)
        cnt[0] = cnt[0] + UInt(32)(1)

        # Test cases covering edge cases and all operations
        alu_in1 = cnt[0].case({
            # Edge cases for basic arithmetic
            UInt(32)(0): UInt(32)(0),
            UInt(32)(1): UInt(32)(0xFFFFFFFF),  # -1 in two's complement
            UInt(32)(2): UInt(32)(0x7FFFFFFF),  # max positive
            UInt(32)(3): UInt(32)(0x80000000),  # min negative
            UInt(32)(4): UInt(32)(100),
            UInt(32)(5): UInt(32)(50),
            # Shift operations
            UInt(32)(10): UInt(32)(0x12345678),
            UInt(32)(11): UInt(32)(0x80000001),
            UInt(32)(12): UInt(32)(0xFFFFFFFF),
            # Logical operations
            UInt(32)(20): UInt(32)(0xAAAAAAAA),
            UInt(32)(21): UInt(32)(0xF0F0F0F0),
            # Comparison edge cases
            UInt(32)(30): UInt(32)(10),
            UInt(32)(31): UInt(32)(0xFFFFFFFF),
            UInt(32)(32): UInt(32)(0x80000000),
            None: cnt[0],
        })

        alu_in2 = cnt[0].case({
            UInt(32)(0): UInt(32)(0),
            UInt(32)(1): UInt(32)(1),
            UInt(32)(2): UInt(32)(1),
            UInt(32)(3): UInt(32)(1),
            UInt(32)(4): UInt(32)(50),
            UInt(32)(5): UInt(32)(100),
            # Shift amounts
            UInt(32)(10): UInt(32)(4),
            UInt(32)(11): UInt(32)(8),
            UInt(32)(12): UInt(32)(16),
            # Logical operations
            UInt(32)(20): UInt(32)(0x55555555),
            UInt(32)(21): UInt(32)(0x0F0F0F0F),
            # Comparison
            UInt(32)(30): UInt(32)(20),
            UInt(32)(31): UInt(32)(0),
            UInt(32)(32): UInt(32)(0x7FFFFFFF),
            None: cnt[0],
        })

        # ALU operation: cycle through all operations
        # 0=ADD, 1=SUB, 2=AND, 3=OR, 4=XOR, 5=SLL, 6=SRL, 7=SRA, 8=SLTU
        alu_op = cnt[0].case({
            UInt(32)(0): UInt(4)(0),  # ADD
            UInt(32)(1): UInt(4)(0),  # ADD
            UInt(32)(2): UInt(4)(0),  # ADD
            UInt(32)(3): UInt(4)(0),  # ADD
            UInt(32)(4): UInt(4)(1),  # SUB
            UInt(32)(5): UInt(4)(1),  # SUB
            UInt(32)(10): UInt(4)(5), # SLL
            UInt(32)(11): UInt(4)(6), # SRL
            UInt(32)(12): UInt(4)(7), # SRA
            UInt(32)(20): UInt(4)(2), # AND
            UInt(32)(21): UInt(4)(3), # OR
            UInt(32)(30): UInt(4)(8), # SLTU
            UInt(32)(31): UInt(4)(8), # SLTU
            UInt(32)(32): UInt(4)(8), # SLTU
            None: UInt(4)(4),  # XOR for other cases
        })

        # Comparator operation: cycle through all comparisons
        # 0=EQ, 1=NE, 2=LT, 3=GE, 4=LTU, 5=GEU, 6=NONE
        cmp_op = cnt[0].case({
            UInt(32)(0): UInt(3)(0),  # EQ
            UInt(32)(1): UInt(3)(0),  # EQ
            UInt(32)(2): UInt(3)(1),  # NE
            UInt(32)(3): UInt(3)(2),  # LT (signed)
            UInt(32)(4): UInt(3)(3),  # GE (signed)
            UInt(32)(30): UInt(3)(4), # LTU (unsigned)
            UInt(32)(31): UInt(3)(4), # LTU (unsigned)
            UInt(32)(32): UInt(3)(5), # GEU (unsigned)
            None: UInt(3)(6),  # NONE for other cases
        })

        forward1.async_called(data=alu_in1)
        forward2.async_called(data=alu_in2)
        forward3.async_called(data=alu_op)
        forward4.async_called(data=cmp_op)


class ForwardData(Module):
    def __init__(self, width=32):
        super().__init__(
            ports={'data': Port(UInt(width))},
        )

    @module.combinational
    def build(self):
        data = self.pop_all_ports(True)
        return data


class ALU(Downstream):

    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, alu_in1: Value, alu_in2: Value, alu_op: Value, cmp_op: Value):
        alu_in1 = alu_in1.optional(UInt(32)(0))
        alu_in2 = alu_in2.optional(UInt(32)(0))
        alu_op = alu_op.optional(UInt(4)(0))
        cmp_op = cmp_op.optional(UInt(3)(6))

        alu = ExternalALU(alu_in1=alu_in1, alu_in2=alu_in2, alu_op=alu_op, cmp_op=cmp_op)
        log("[test] alu_in1:{}|alu_in2:{}|alu_op:{}|cmp_op:{}|alu_out:{}|cmp_out:{}",
            alu_in1, alu_in2, alu_op, cmp_op, alu.alu_out, alu.cmp_out)


def ref_alu(alu_in1, alu_in2, alu_op):
    """Reference model for ALU operations"""
    # Convert to signed integers for signed operations
    def to_signed32(val):
        if val & 0x80000000:
            return val - 0x100000000
        return val

    def to_unsigned32(val):
        return val & 0xFFFFFFFF

    shamt = alu_in2 & 0x1F  # lower 5 bits

    if alu_op == 0:  # ADD
        result = to_unsigned32(alu_in1 + alu_in2)
    elif alu_op == 1:  # SUB
        result = to_unsigned32(alu_in1 - alu_in2)
    elif alu_op == 2:  # AND
        result = alu_in1 & alu_in2
    elif alu_op == 3:  # OR
        result = alu_in1 | alu_in2
    elif alu_op == 4:  # XOR
        result = alu_in1 ^ alu_in2
    elif alu_op == 5:  # SLL
        result = to_unsigned32(alu_in1 << shamt)
    elif alu_op == 6:  # SRL (logical shift right)
        result = alu_in1 >> shamt
    elif alu_op == 7:  # SRA (arithmetic shift right)
        signed_val = to_signed32(alu_in1)
        result = to_unsigned32(signed_val >> shamt)
    elif alu_op == 8:  # SLTU (unsigned comparison)
        result = 1 if alu_in1 < alu_in2 else 0
    else:
        result = 0

    return result


def ref_cmp(alu_in1, alu_in2, cmp_op):
    """Reference model for comparator operations"""
    def to_signed32(val):
        if val & 0x80000000:
            return val - 0x100000000
        return val

    if cmp_op == 0:  # EQ
        return 1 if alu_in1 == alu_in2 else 0
    elif cmp_op == 1:  # NE
        return 1 if alu_in1 != alu_in2 else 0
    elif cmp_op == 2:  # LT (signed)
        return 1 if to_signed32(alu_in1) < to_signed32(alu_in2) else 0
    elif cmp_op == 3:  # GE (signed)
        return 1 if to_signed32(alu_in1) >= to_signed32(alu_in2) else 0
    elif cmp_op == 4:  # LTU (unsigned)
        return 1 if alu_in1 < alu_in2 else 0
    elif cmp_op == 5:  # GEU (unsigned)
        return 1 if alu_in1 >= alu_in2 else 0
    else:  # NONE
        return 0


def check_raw(raw):
    """Check ALU output against reference model"""
    cnt = 0
    for i in raw.split('\n'):
        if '[test]' in i:
            # Parse log line: alu_in1:X|alu_in2:Y|alu_op:Z|cmp_op:W|alu_out:A|cmp_out:B
            line_toks = i.split('|')
            alu_in1 = int(line_toks[0].split(':')[-1])
            alu_in2 = int(line_toks[1].split(':')[-1])
            alu_op = int(line_toks[2].split(':')[-1])
            cmp_op = int(line_toks[3].split(':')[-1])
            alu_out = int(line_toks[4].split(':')[-1])
            cmp_out = int(line_toks[5].split(':')[-1])

            # Check ALU output
            ref_alu_out = ref_alu(alu_in1, alu_in2, alu_op)
            assert alu_out == ref_alu_out, \
                f'ALU output incorrect: op={alu_op}, {alu_in1} op {alu_in2} = {alu_out}, expected {ref_alu_out}'

            # Check comparator output
            ref_cmp_out = ref_cmp(alu_in1, alu_in2, cmp_op)
            assert cmp_out == ref_cmp_out, \
                f'CMP output incorrect: op={cmp_op}, {alu_in1} cmp {alu_in2} = {cmp_out}, expected {ref_cmp_out}'

            cnt += 1

    assert cnt == 99, f'cnt: {cnt} != 99'


def build_system():
    driver = Driver()
    forward1 = ForwardData(32)  # alu_in1
    forward2 = ForwardData(32)  # alu_in2
    forward3 = ForwardData(4)   # alu_op
    forward4 = ForwardData(3)   # cmp_op
    alu_in1 = forward1.build()
    alu_in2 = forward2.build()
    alu_op = forward3.build()
    cmp_op = forward4.build()
    alu = ALU()
    driver.build(forward1, forward2, forward3, forward4)
    alu.build(alu_in1, alu_in2, alu_op, cmp_op)


def test_alu():
    run_test('test_alu', build_system, check_raw, sim_threshold=100, idle_threshold=100)


if __name__ == '__main__':
    test_alu()
