import pytest

from assassyn.frontend import *
from assassyn.test import (
    run_test,
    StimulusTimeline,
    LogChecker,
    RegexExtractor,
    RegexParser,
)

class Merging(Downstream):
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, valid1: Array, valid2: Array, data_branch1: Value, data_branch2: Value):
        valid1_v = valid1[0]
        valid2_v = valid2[0]

        with Condition(valid1_v):
            log("[merge] data_branch1: {}", data_branch1)

        with Condition(valid2_v):
            log("[merge] data_branch2: {}", data_branch2)
            


class Branch2(Module):
    def __init__(self):
        super().__init__(
            ports={'data': Port(UInt(32))},
        )

    @module.combinational
    def build(self):
        data = self.pop_all_ports(True)
        log("[branch2] data: {}", data)  
        return data


class Branch1(Module):
    def __init__(self):
        super().__init__(
            ports={'data': Port(UInt(32))},
        )

    @module.combinational
    def build(self):
        data = self.pop_all_ports(True)
        log("[branch1] data: {}", data)
        return data


def _build_branch_stimulus():
    timeline = StimulusTimeline()
    timeline.signal('data', UInt(32)).default(lambda cnt: cnt)
    timeline.signal('valid1', Bits(1)).default(lambda cnt: (cnt[0:1] == UInt(2)(2)))
    timeline.signal('valid2', Bits(1)).default(lambda cnt: (cnt[0:1] == UInt(2)(3)))
    return timeline


class Driver(Module):
    def __init__(self, timeline: StimulusTimeline):
        super().__init__(ports={})
        self.timeline = timeline

    @module.combinational
    def build(self, branch1: Branch1, branch2: Branch2, valid1: Array, valid2: Array):
        cnt = self.timeline.build_counter()
        cnt[0] = cnt[0] + self.timeline.counter_dtype(self.timeline.step)

        values = self.timeline.values(cnt[0])

        with Condition(values['valid1']):
            branch1.async_called(data=values['data'])

        with Condition(values['valid2']):
            branch2.async_called(data=values['data'])

        valid1[0] = values['valid1']
        valid2[0] = values['valid2']

        


def top():
    timeline = _build_branch_stimulus()
    
    branch1 = Branch1()
    data_branch1 = branch1.build()

    branch2 = Branch2()
    data_branch2 = branch2.build()
    
    valid1 = RegArray(Bits(1),1)
    valid2 = RegArray(Bits(1),1)

    driver = Driver(timeline)
    driver.build(branch1, branch2, valid1, valid2)

    merging = Merging()
    merging.build(valid1, valid2, data_branch1, data_branch2)



def check(raw):
    pattern = r'Cycle @(?P<cycle>\d+\.\d+):.*\[merge\]\s+(?P<label>data_branch[12]):\s*(?P<value>-?\d+)'
    checker = LogChecker(
        RegexExtractor(pattern),
        RegexParser(pattern),
    )

    counts = {'data_branch1': 0, 'data_branch2': 0}

    def _collect(record):
        label = record.data['label']
        counts[label] += 1

    checker.add_hook(_collect)
    checker.collect(raw)

    assert counts['data_branch1'] > 0, "Expected merge log for branch1"
    assert counts['data_branch2'] > 0, "Expected merge log for branch2"

def sim_branch():
    run_test('branch', top, check)


if __name__ == '__main__':
    sim_branch()
