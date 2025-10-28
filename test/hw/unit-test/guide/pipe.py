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
        log("[stage1] data: {}", data)
        stage2.async_called(data=data)



def _build_pipe_stimulus():
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
    timeline = _build_pipe_stimulus()
    stage2 = Stage2()
    stage2.build()

    stage1 = Stage1()
    stage1.build(stage2)

    driver = Driver(timeline)
    driver.build(stage1)


def check(raw):
    pattern = r'Cycle @(?P<cycle>\d+\.\d+):.*\[(?P<tag>stage1|stage2)\]\s+data:\s*(?P<value>-?\d+)'
    checker = LogChecker(
        RegexExtractor(pattern),
        RegexParser(pattern),
    )

    cycles = {}

    def _collect(record):
        cycle = float(record.data['cycle'])
        tag = record.data['tag']
        value = int(record.data['value'])
        cycles.setdefault(cycle, {})[tag] = value

    checker.add_hook(_collect)
    checker.collect(raw)

    cnt = 0
    for cycle, stages in cycles.items():
        if 'stage1' in stages and 'stage2' in stages:
            diff = abs(stages['stage1'] - stages['stage2'])
            assert diff == 1, f"Cycle {cycle}: stage1={stages['stage1']}, stage2={stages['stage2']}, diff={diff} != 1"
            cnt += 1

    assert cnt > 0, "No valid cycle data found to check"


def sim_pipe():
    run_test('pipe', top, check)


if __name__ == '__main__':
    sim_pipe()
