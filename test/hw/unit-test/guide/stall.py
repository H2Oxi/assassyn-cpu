import pytest

from assassyn.frontend import *
from assassyn.test import run_test

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


class Driver(Module):

        def __init__(self):
            super().__init__(ports={})

        @module.combinational
        def build(self, stage1: Stage1):
            cnt = RegArray(UInt(32), 1)
            cnt[0] = cnt[0] + UInt(32)(1)

            stage1.async_called(data=cnt[0])



def top():
    stage2 = Stage2()
    stage2.build()

    stage1 = Stage1()
    stage1.build(stage2)

    driver = Driver()
    driver.build(stage1)


import re


def check(raw):
    for line in raw.split('\n'):
        if '[stage2]' in line:
            match = re.search(r'data: (\d+)', line)
            if match:
                data = int(match.group(1))
                assert data % 3 == 0



def sim_stall():
    run_test('stall', top, check)


if __name__ == '__main__':
    sim_stall()
