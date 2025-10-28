import pytest

from assassyn.frontend import *
from assassyn.test import (
    run_test,
    StimulusTimeline,
    StimulusDriver,
    LogChecker,
    RegexExtractor,
    RegexParser,
)

class Stage2(Module):
    def __init__(self):
        super().__init__(
            ports={'data': Port(UInt(32))},
        )

    @module.combinational
    def build(self):
        data = self.pop_all_ports(True)
        log("[stage2] data: {}", data)  


class Stage1(Module):
    def __init__(self):
        super().__init__(
            ports={'data': Port(UInt(32))},
        )

    @module.combinational
    def build(self, stage2: Stage2):
        data = self.pop_all_ports(True)
        stall_cond = data % UInt(32)(3) == UInt(32)(0)
        wait_until(stall_cond)
        stage2.async_called(data=data)


def _build_stall_stimulus():
    timeline = StimulusTimeline()
    timeline.signal('data', UInt(32)).default(lambda cnt: cnt)
    return timeline


class Driver(Module):

    def __init__(self, timeline: StimulusTimeline):
        super().__init__(ports={})
        self.timeline = timeline

    @module.combinational
    def build(self, stage1: Stage1):
        cnt = self.timeline.build_counter()
        cnt[0] = cnt[0] + self.timeline.counter_dtype(self.timeline.step)

        stimulus = StimulusDriver(self.timeline)
        stimulus.bind(stage1.async_called, data='data')
        stimulus.drive(cnt[0])



def top():
    timeline = _build_stall_stimulus()
    stage2 = Stage2()
    stage2.build()

    stage1 = Stage1()
    stage1.build(stage2)

    driver = Driver(timeline)
    driver.build(stage1)


def check(raw):
    pattern = r'Cycle @(?P<cycle>\d+\.\d+):.*\[stage2\]\s+data:\s*(?P<value>-?\d+)'
    checker = LogChecker(
        RegexExtractor(pattern),
        RegexParser(pattern),
    )

    def _validate(record):
        value = int(record.data['value'])
        assert value % 3 == 0

    checker.add_hook(_validate)
    checker.collect(raw)



def sim_stall():
    run_test('stall', top, check)


if __name__ == '__main__':
    sim_stall()
