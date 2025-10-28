from assassyn.frontend import *
from assassyn.test import (
    run_test,
    StimulusTimeline,
    StimulusDriver,
    LogChecker,
    PrefixExtractor,
    KeyValueParser,
)
from impl.ip.ips import RegFile as ExternalRegFile

from assassyn.backend import elaborate
from assassyn import utils


def _build_regfile_stimulus():
    timeline = StimulusTimeline()
    timeline.signal('rs1_addr', UInt(5)).case_map({
        0: 0,
        1: 1,
        2: 2,
        3: 1,
        10: 5,
        11: 5,
        12: 0,
        20: 10,
        21: 15,
        22: 31,
        30: 7,
        31: 7,
    }, default=0)

    timeline.signal('rs2_addr', UInt(5)).case_map({
        0: 0,
        1: 2,
        2: 1,
        3: 2,
        10: 6,
        11: 6,
        12: 0,
        20: 11,
        21: 16,
        22: 30,
        30: 8,
        31: 7,
    }, default=0)

    timeline.signal('rd_we', Bits(1)).case_map({
        0: 1,
        1: 1,
        2: 0,
        3: 0,
        10: 1,
        11: 0,
        12: 1,
        20: 1,
        21: 1,
        22: 1,
        30: 1,
        31: 0,
    }, default=0)

    timeline.signal('rd_addr', UInt(5)).case_map({
        0: 1,
        1: 2,
        10: 5,
        12: 0,
        20: 10,
        21: 15,
        22: 31,
        30: 7,
    }, default=0)

    timeline.signal('rd_wdata', UInt(32)).case_map({
        0: 0xDEADBEEF,
        1: 0x12345678,
        10: 0xAAAAAAAA,
        12: 0xFFFFFFFF,
        20: 0x11111111,
        21: 0x22222222,
        22: 0x33333333,
        30: 0xBBBBBBBB,
    }, default=0)

    return timeline


class Driver(Module):

    def __init__(self, timeline: StimulusTimeline):
        super().__init__(ports={})
        self.timeline = timeline

    @module.combinational
    def build(self, forward_rs1: Module, forward_rs2: Module,
              forward_we: Module, forward_rd_addr: Module, forward_rd_wdata: Module):
        cnt = self.timeline.build_counter()
        cnt[0] = cnt[0] + self.timeline.counter_dtype(self.timeline.step)

        stimulus = StimulusDriver(self.timeline)
        stimulus.bind(forward_rs1.async_called, data='rs1_addr')
        stimulus.bind(forward_rs2.async_called, data='rs2_addr')
        stimulus.bind(forward_we.async_called, data='rd_we')
        stimulus.bind(forward_rd_addr.async_called, data='rd_addr')
        stimulus.bind(forward_rd_wdata.async_called, data='rd_wdata')
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


class ForwardBit(Module):
    def __init__(self):
        super().__init__(
            ports={'data': Port(Bits(1))},
        )

    @module.combinational
    def build(self):
        data = self.pop_all_ports(True)
        return data


class Logger(Module):
    def __init__(self):
        super().__init__(
            ports={
                'rs1_addr': Port(UInt(5)),
                'rs2_addr': Port(UInt(5)),
                'rd_we': Port(Bits(1)),
                'rd_addr': Port(UInt(5)),
                'rd_wdata': Port(UInt(32))
            }
        )

    @module.combinational
    def build(self, rs1_data_arr: Array, rs2_data_arr: Array):
        rs1_addr, rs2_addr, rd_we, rd_addr, rd_wdata = self.pop_all_ports(True)
        log("[test] rs1_addr:{}|rs1_data:{}|rs2_addr:{}|rs2_data:{}|rd_we:{}|rd_addr:{}|rd_wdata:{}",
            rs1_addr, rs1_data_arr[0], rs2_addr, rs2_data_arr[0], rd_we, rd_addr, rd_wdata)


class RegFile(Downstream):

    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, rs1_addr: Value, rs2_addr: Value, rd_we: Value,
              rd_addr: Value, rd_wdata: Value, logger: Module):
        rs1_addr = rs1_addr.optional(UInt(5)(0))
        rs2_addr = rs2_addr.optional(UInt(5)(0))
        rd_we = rd_we.optional(Bits(1)(0))
        rd_addr = rd_addr.optional(UInt(5)(0))
        rd_wdata = rd_wdata.optional(UInt(32)(0))

        # Clock and reset are automatically handled by the framework
        # when __has_clock__ and __has_reset__ are set to True
        regfile = ExternalRegFile(
            rs1_addr=rs1_addr,
            rs2_addr=rs2_addr,
            rd_we=rd_we,
            rd_addr=rd_addr,
            rd_wdata=rd_wdata
        )

        # Call logger with input signals from within this module context
        logger.async_called(
            rs1_addr=rs1_addr,
            rs2_addr=rs2_addr,
            rd_we=rd_we,
            rd_addr=rd_addr,
            rd_wdata=rd_wdata
        )

        # Return the registered outputs
        return regfile.rs1_data, regfile.rs2_data


# Reference model: simulates the register file behavior
class RefRegFile:
    def __init__(self):
        # 32 registers, all initialized to 0
        self.regs = [0] * 32
        # Store registered read addresses (1-cycle delayed)
        self.rs1_addr_reg = 0
        self.rs2_addr_reg = 0

    def tick(self, rs1_addr, rs2_addr, rd_we, rd_addr, rd_wdata):
        """Simulate one clock cycle

        The timing model (corrected based on actual behavior):
        1. At clock edge: write happens AND read addresses are registered simultaneously
        2. Read data output: combinational logic based on NEW registered addresses (just updated)
        3. Bypass: current cycle write vs current registered read address
        """
        # First: Write operation (happens at clock edge)
        if rd_we and rd_addr != 0:
            self.regs[rd_addr] = rd_wdata & 0xFFFFFFFF

        # Second: Update read address registers (happens at clock edge, simultaneously with write)
        self.rs1_addr_reg = rs1_addr
        self.rs2_addr_reg = rs2_addr

        # Third: Generate read data output (combinational, based on CURRENT registered addresses)
        # The output is based on the addresses that were JUST registered in this cycle

        # RS1 read output
        if self.rs1_addr_reg == 0:
            rs1_data = 0
        elif (rd_we and rd_addr == self.rs1_addr_reg and rd_addr != 0):
            # Bypass: forward current write data
            rs1_data = rd_wdata & 0xFFFFFFFF
        else:
            # Normal read from register array (which was just updated by write)
            rs1_data = self.regs[self.rs1_addr_reg]

        # RS2 read output
        if self.rs2_addr_reg == 0:
            rs2_data = 0
        elif (rd_we and rd_addr == self.rs2_addr_reg and rd_addr != 0):
            # Bypass: forward current write data
            rs2_data = rd_wdata & 0xFFFFFFFF
        else:
            rs2_data = self.regs[self.rs2_addr_reg]

        return rs1_data, rs2_data


def check_raw(raw):
    """Check register file output against reference model"""
    ref = RefRegFile()
    checker = LogChecker(
        PrefixExtractor('[test]', mode='contains'),
        KeyValueParser(pair_sep='|', kv_sep=':'),
    )
    checker.expect_at_least(95)

    state = {'cnt': 0}

    def _validate(record):
        record.require('rs1_addr', 'rs2_addr', 'rd_we', 'rd_addr', 'rd_wdata', 'rs1_data', 'rs2_data')

        rs1_addr = record.data['rs1_addr']
        rs2_addr = record.data['rs2_addr']
        rd_we = record.data['rd_we']
        rd_addr = record.data['rd_addr']
        rd_wdata = record.data['rd_wdata']
        rs1_data = record.data['rs1_data']
        rs2_data = record.data['rs2_data']

        ref_rs1_data, ref_rs2_data = ref.tick(rs1_addr, rs2_addr, rd_we, rd_addr, rd_wdata)

        if state['cnt'] < 10:
            reg_val = ref.regs[rs1_addr] if rs1_addr < 32 else 0
            print(f"Cycle {state['cnt']}: rs1_addr={rs1_addr}, rs1_data={rs1_data:#x}, ref={ref_rs1_data:#x}, "
                  f"rd_we={rd_we}, rd_addr={rd_addr}, rd_wdata={rd_wdata:#x}")
            print(f"         ref.rs1_addr_reg={ref.rs1_addr_reg}, ref.regs[{rs1_addr}]={reg_val:#x}")

        assert rs1_data == ref_rs1_data, \
            f'RS1 data incorrect at cycle {state["cnt"]}: addr={rs1_addr}, got {rs1_data:#x}, expected {ref_rs1_data:#x}'

        assert rs2_data == ref_rs2_data, \
            f'RS2 data incorrect at cycle {state["cnt"]}: addr={rs2_addr}, got {rs2_data:#x}, expected {ref_rs2_data:#x}'

        state['cnt'] += 1

    checker.add_hook(_validate)
    checker.collect(raw)

    cnt = checker.summary['count']
    print(f"\n✓ Test passed! Ran {cnt} cycles successfully.")


def build_system():
    timeline = _build_regfile_stimulus()
    driver = Driver(timeline)
    forward_rs1 = ForwardData(5)     # rs1_addr (5 bits)
    forward_rs2 = ForwardData(5)     # rs2_addr (5 bits)
    forward_we = ForwardBit()        # rd_we (1 bit)
    forward_rd_addr = ForwardData(5) # rd_addr (5 bits)
    forward_rd_wdata = ForwardData(32) # rd_wdata (32 bits)

    rs1_addr_val = forward_rs1.build()
    rs2_addr_val = forward_rs2.build()
    rd_we_val = forward_we.build()
    rd_addr_val = forward_rd_addr.build()
    rd_wdata_val = forward_rd_wdata.build()

    logger = Logger()

    regfile = RegFile()
    rs1_data, rs2_data = regfile.build(
        rs1_addr_val, rs2_addr_val, rd_we_val, rd_addr_val, rd_wdata_val, logger
    )

    logger.build(rs1_data, rs2_data)

    driver.build(forward_rs1, forward_rs2, forward_we, forward_rd_addr, forward_rd_wdata)


def test_regfile():
    run_test('test_regfile', build_system, check_raw, sim_threshold=100, idle_threshold=100)


if __name__ == '__main__':
    test_regfile()
