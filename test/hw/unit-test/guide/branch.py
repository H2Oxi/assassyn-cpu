import pytest

from assassyn.frontend import *
from assassyn.test import run_test

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


class Driver(Module):
    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, branch1: Branch1, branch2: Branch2, valid1: Array, valid2: Array):
        cnt = RegArray(UInt(32), 1)
        cnt[0] = cnt[0] + UInt(32)(1)

        valid1_value = (cnt[0][0:1] == UInt(2)(2))
        valid2_value = (cnt[0][0:1] == UInt(2)(3))

        with Condition(valid1_value):
            branch1.async_called(data=cnt[0])

        with Condition(valid2_value):
            branch2.async_called(data=cnt[0])
        
        valid1[0] = valid1_value
        valid2[0] = valid2_value

        


def top():
    
    branch1 = Branch1()
    data_branch1 = branch1.build()

    branch2 = Branch2()
    data_branch2 = branch2.build()
    
    valid1 = RegArray(Bits(1),1)
    valid2 = RegArray(Bits(1),1)

    driver = Driver()
    driver.build(branch1, branch2, valid1, valid2)

    merging = Merging()
    merging.build(valid1, valid2, data_branch1, data_branch2)



def check(raw):
    pass

def sim_branch():
    run_test('branch', top, check)


if __name__ == '__main__':
    sim_branch()
