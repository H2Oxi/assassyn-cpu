from assassyn.frontend import *
from assassyn.test import (
    run_test,
    StimulusDriver,
    StimulusTimeline,
    LogChecker,
    PrefixExtractor,
    KeyValueParser,
    ReferenceHook,
)
from impl.ip.ips import Adder as ExternalAdder


from assassyn.backend import elaborate
from assassyn import utils


def _build_adder_stimulus():
    timeline = StimulusTimeline()

    def _signed(value: int):
        return lambda _: Int(32)(value).bitcast(UInt(32))

    timeline.signal('add_in1', UInt(32)).sequence([
        _signed(-100),
        _signed(0),
        _signed(100),
    ], start=0).default(lambda cnt: cnt)

    timeline.signal('add_in2', UInt(32)).sequence([
        _signed(100),
        _signed(-100),
        _signed(-1),
    ], start=0).default(lambda cnt: cnt)

    return timeline


class Driver(Module):

    def __init__(self, timeline: StimulusTimeline):
        super().__init__(ports={})
        self.timeline = timeline

    @module.combinational
    def build(self, forward1: Module, forward2: Module):
        cnt = self.timeline.build_counter()
        cnt[0] = cnt[0] + self.timeline.counter_dtype(self.timeline.step)

        stimulus = StimulusDriver(self.timeline)
        stimulus.bind(forward1.async_called, data='add_in1')
        stimulus.bind(forward2.async_called, data='add_in2')
        stimulus.drive(cnt[0])


class ForwardData(Module):
    def __init__(self):
        super().__init__(
            ports={'data': Port(UInt(32))},
        )

    @module.combinational
    def build(self):
        data = self.pop_all_ports(True)
        return data


class Adder(Downstream):

    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, add_in1: Value, add_in2: Value):
        #here we assumed user explicitly know the direction of the external module ports
        add_in1 = add_in1.optional(UInt(32)(1))
        add_in2 = add_in2.optional(UInt(32)(1))

        adder = ExternalAdder(add_in1=add_in1, add_in2=add_in2)
        log("[test] add_in1:{}|add_in2:{}|add_out:{}", add_in1, add_in2, adder.add_out)

def ref_model(add_in1, add_in2):
    return (add_in1 + add_in2) & 0xFFFFFFFF

def check_raw(raw):
    checker = LogChecker(
        PrefixExtractor('[test]', mode='contains'),
        KeyValueParser(pair_sep='|', kv_sep=':'),
    )
    checker.expect_count(99)
    checker.add_hook(
        ReferenceHook(
            ref_model,
            inputs=['add_in1', 'add_in2'],
            outputs=['add_out'],
            name='adder_ref',
        )
    )
    checker.collect(raw)

def build_system():
    timeline = _build_adder_stimulus()
    driver = Driver(timeline)
    forward1 = ForwardData()
    forward2 = ForwardData()
    add_in1 = forward1.build()
    add_in2 = forward2.build()
    adder = Adder()
    driver.build(forward1, forward2)
    adder.build(add_in1, add_in2)

def test_easy_external():
    run_test('test_adder', build_system, check_raw, sim_threshold=100, idle_threshold=100)

if __name__ == '__main__':
    test_easy_external()
