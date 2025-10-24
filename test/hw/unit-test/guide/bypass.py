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
        log("[real] fifo_data: {}", data) 


class Stage1(Module):
    def __init__(self):
        super().__init__(
            ports={
                'data': Port(UInt(32)),
                'regdata': Port(UInt(32)),
                   },
        )

    @module.combinational
    def build(self, stage2: Stage2 , reg: Array):
        data,regdata = self.pop_all_ports(True)
        log("[stage1] data: {}", data)
        stage2.async_called(data=data)
        reg[0] = regdata
        return data , regdata


class Bypass(Downstream):
    
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, fifo_bypass: Value, reg_wr_bypass: Value, reg: Array):
        fifo_bypass = fifo_bypass.optional(UInt(32)(0))
        reg_wr_bypass = reg_wr_bypass.optional(UInt(32)(0))


        log("[bypass] fifo_bypass: {}", fifo_bypass)
        log("[bypass] reg_wr_bypass: {}", reg_wr_bypass)
        log("[real] reg: {}", reg[0])


class Driver(Module):

        def __init__(self):
            super().__init__(ports={})

        @module.combinational
        def build(self, stage1: Stage1):
            cnt = RegArray(UInt(32), 1)
            cnt[0] = cnt[0] + UInt(32)(1)
            stage1.async_called(data=cnt[0], regdata=(cnt[0]+ cnt[0]))


def top():
    reg = RegArray(UInt(32), 1)
    stage2 = Stage2()
    stage2.build()

    stage1 = Stage1()
    fifodata, regdata = stage1.build(stage2, reg)

    driver = Driver()
    driver.build(stage1)

    bypass = Bypass()
    bypass.build(fifodata, regdata, reg)


def check(raw):
    """
    Check bypass functionality:
    1. reg_wr_bypass should be 1 cycle ahead of reg
    2. fifo_bypass should be 1 cycle ahead of fifo_data (popped data)
    """
    lines = raw.strip().split('\n')

    # Parse logs into structured data
    cycles = {}
    for line in lines:
        if 'Cycle @' not in line:
            continue

        parts = line.split('Cycle @')
        if len(parts) < 2:
            continue

        cycle_str = parts[1].split(':')[0]
        cycle_num = float(cycle_str)

        if cycle_num not in cycles:
            cycles[cycle_num] = {}

        # Extract signal values
        if '[bypass] fifo_bypass:' in line:
            value = int(line.split(': ')[-1])
            cycles[cycle_num]['fifo_bypass'] = value
        elif '[bypass] reg_wr_bypass:' in line:
            value = int(line.split(': ')[-1])
            cycles[cycle_num]['reg_wr_bypass'] = value
        elif '[real] reg:' in line:
            value = int(line.split(': ')[-1])
            cycles[cycle_num]['reg'] = value
        elif '[real] fifo_data:' in line:
            value = int(line.split(': ')[-1])
            cycles[cycle_num]['fifo_data'] = value

    # Verify bypass correctness
    sorted_cycles = sorted(cycles.keys())
    errors = []

    for i in range(len(sorted_cycles) - 1):
        curr_cycle = sorted_cycles[i]
        next_cycle = sorted_cycles[i + 1]

        curr_data = cycles[curr_cycle]
        next_data = cycles[next_cycle]

        # Check 1: reg_wr_bypass at cycle N should equal reg at cycle N+1
        if 'reg_wr_bypass' in curr_data and 'reg' in next_data:
            if curr_data['reg_wr_bypass'] != next_data['reg']:
                errors.append(
                    f"Cycle {curr_cycle}: reg_wr_bypass={curr_data['reg_wr_bypass']} "
                    f"does not match reg={next_data['reg']} at cycle {next_cycle}"
                )

        # Check 2: fifo_bypass at cycle N should equal fifo_data at cycle N+1
        if 'fifo_bypass' in curr_data and 'fifo_data' in next_data:
            if curr_data['fifo_bypass'] != next_data['fifo_data']:
                errors.append(
                    f"Cycle {curr_cycle}: fifo_bypass={curr_data['fifo_bypass']} "
                    f"does not match fifo_data={next_data['fifo_data']} at cycle {next_cycle}"
                )

    if errors:
        print("\n=== BYPASS CHECK FAILED ===")
        for error in errors:
            print(f"ERROR: {error}")
        raise AssertionError(f"Found {len(errors)} bypass timing errors")
    else:
        print("\n=== BYPASS CHECK PASSED ===")
        print(f"Verified {len(sorted_cycles)} cycles")
        print("✓ reg_wr_bypass is correctly 1 cycle ahead of reg")
        print("✓ fifo_bypass is correctly 1 cycle ahead of fifo_data")


def sim_bypass():
    run_test('bypass', top, check)


if __name__ == '__main__':
    sim_bypass()
