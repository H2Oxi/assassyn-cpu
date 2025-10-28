from assassyn.frontend import *
from assassyn.test import (
    run_test,
    StimulusTimeline,
    StimulusDriver,
    LogChecker,
    PrefixExtractor,
    KeyValueParser,
    ReferenceHook,
)
from impl.ip.ips import ALU as ExternalALU

from assassyn.backend import elaborate
from assassyn import utils


def _build_alu_stimulus():
    timeline = StimulusTimeline()

    timeline.signal('alu_in1', UInt(32)).case_map({
        0: 0,
        1: 0xFFFFFFFF,
        2: 0x7FFFFFFF,
        3: 0x80000000,
        4: 100,
        5: 50,
        10: 0x12345678,
        11: 0x80000001,
        12: 0xFFFFFFFF,
        20: 0xAAAAAAAA,
        21: 0xF0F0F0F0,
        30: 10,
        31: 0xFFFFFFFF,
        32: 0x80000000,
    }, default=lambda cnt: cnt)

    timeline.signal('alu_in2', UInt(32)).case_map({
        0: 0,
        1: 1,
        2: 1,
        3: 1,
        4: 50,
        5: 100,
        10: 4,
        11: 8,
        12: 16,
        20: 0x55555555,
        21: 0x0F0F0F0F,
        30: 20,
        31: 0,
        32: 0x7FFFFFFF,
    }, default=lambda cnt: cnt)

    timeline.signal('alu_op', UInt(4)).case_map({
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 1,
        5: 1,
        10: 5,
        11: 6,
        12: 7,
        20: 2,
        21: 3,
        30: 8,
        31: 8,
        32: 8,
    }, default=4)

    timeline.signal('cmp_op', UInt(3)).case_map({
        0: 0,
        1: 0,
        2: 1,
        3: 2,
        4: 3,
        30: 4,
        31: 4,
        32: 5,
    }, default=6)

    return timeline


class Driver(Module):

    def __init__(self, timeline: StimulusTimeline):
        super().__init__(ports={})
        self.timeline = timeline

    @module.combinational
    def build(self, forward1: Module, forward2: Module, forward3: Module, forward4: Module):
        cnt = self.timeline.build_counter()
        cnt[0] = cnt[0] + self.timeline.counter_dtype(self.timeline.step)

        stimulus = StimulusDriver(self.timeline)
        stimulus.bind(forward1.async_called, data='alu_in1')
        stimulus.bind(forward2.async_called, data='alu_in2')
        stimulus.bind(forward3.async_called, data='alu_op')
        stimulus.bind(forward4.async_called, data='cmp_op')
        stimulus.drive(cnt[0])


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


def ref_alu_combined(alu_in1, alu_in2, alu_op, cmp_op):
    return {
        'alu_out': ref_alu(alu_in1, alu_in2, alu_op),
        'cmp_out': ref_cmp(alu_in1, alu_in2, cmp_op),
    }


def check_raw(raw):
    """Check ALU output against reference model"""
    checker = LogChecker(
        PrefixExtractor('[test]', mode='contains'),
        KeyValueParser(pair_sep='|', kv_sep=':'),
    )
    checker.expect_count(99)
    checker.add_hook(
        ReferenceHook(
            ref_alu_combined,
            inputs=['alu_in1', 'alu_in2', 'alu_op', 'cmp_op'],
            outputs=['alu_out', 'cmp_out'],
            name='alu_ref',
        )
    )
    checker.collect(raw)


def build_system():
    timeline = _build_alu_stimulus()
    driver = Driver(timeline)
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
