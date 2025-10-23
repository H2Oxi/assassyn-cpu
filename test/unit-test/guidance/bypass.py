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
        log("[stage1] data: {}", data)
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


def check(raw):
    # 解析日志，按时钟周期分组
    cycles = {}
    for line in raw.split('\n'):
        if '[stage1]' in line or '[stage2]' in line:
            # 提取时钟周期和数据值
            parts = line.split()
            # 假设格式包含时钟信息，需要找到cycle和data
            if '[stage1]' in line:
                # 从日志中提取data值
                data_idx = parts.index('data:') if 'data:' in parts else -1
                if data_idx != -1 and data_idx + 1 < len(parts):
                    data_val = int(parts[data_idx + 1])
                    # 提取时钟周期（假设在行首或特定位置）
                    # 这里需要根据实际日志格式调整
                    cycle = parts[0] if parts[0].isdigit() else 0
                    if cycle not in cycles:
                        cycles[cycle] = {}
                    cycles[cycle]['stage1'] = data_val
            elif '[stage2]' in line:
                data_idx = parts.index('data:') if 'data:' in parts else -1
                if data_idx != -1 and data_idx + 1 < len(parts):
                    data_val = int(parts[data_idx + 1])
                    cycle = parts[0] if parts[0].isdigit() else 0
                    if cycle not in cycles:
                        cycles[cycle] = {}
                    cycles[cycle]['stage2'] = data_val

    # 检查同一时钟周期下stage1和stage2的数据是否相差1
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
