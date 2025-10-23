import pytest

from assassyn.frontend import *
from assassyn.test import run_test

class MergeStage(Module):
    def __init__(self):
        super().__init__(
            ports={'data_branch1': Port(UInt(32)),
                   'data_branch2': Port(UInt(32)),
                   },
        )

    @module.combinational
    def build(self):
        data_branch1,data_branch2 = self.pop_all_ports(True)
        log("[merge_stage] data_branch1: {}, data_branch2: {}", data_branch1, data_branch2)


class Merging(Downstream):
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, valid1: Value, valid2: Value, data_branch1: Value, data_branch2: Value, merge_stage: MergeStage):
        valid1 = valid1.optional(Bits(1)(0))
        valid2 = valid2.optional(Bits(1)(0))

        valid1_reg = RegArray(Bits(1), 1,initializer=[Bits(1)(0)])
        valid2_reg = RegArray(Bits(1), 1,initializer=[Bits(1)(0)])

        merge = (valid1_reg[0] & valid2_reg[0])

        hold_high1 = valid1_reg[0].select(Bits(1)(1), valid1)
        hold_high2 = valid2_reg[0].select(Bits(1)(1), valid2)

        valid1_reg[0] = merge.select(Bits(1)(0), hold_high1)
        valid2_reg[0] = merge.select(Bits(1)(0), hold_high2)


        with Condition(merge):
            merge_stage.async_called(data_branch1=data_branch1, data_branch2=data_branch2)


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
    def build(self, branch1: Branch1, branch2: Branch2):
        cnt = RegArray(UInt(32), 1)
        cnt[0] = cnt[0] + UInt(32)(1)

        valid1_value = (cnt[0][0:1] == UInt(2)(2))
        valid2_value = (cnt[0][0:1] == UInt(2)(3))

        with Condition(valid1_value):
            branch1.async_called(data=cnt[0])

        with Condition(valid2_value):
            branch2.async_called(data=cnt[0])

        return valid1_value, valid2_value


def top():
    
    branch1 = Branch1()
    data_branch1 = branch1.build()

    branch2 = Branch2()
    data_branch2 = branch2.build()

    mergestage = MergeStage()
    mergestage.build()

    driver = Driver()
    valid1, valid2 = driver.build(branch1, branch2)

    merging = Merging()
    merging.build(valid1, valid2, data_branch1, data_branch2, mergestage)




def check(raw):
    pass

def sim_branch():
    run_test('branch', top, check)


if __name__ == '__main__':
    sim_branch()
