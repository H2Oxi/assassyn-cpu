from assassyn.frontend import *
from assassyn.test import run_test
from impl.ip.ips import RegFile as ExternalRegFile

from assassyn.backend import elaborate
from assassyn import utils


class Driver(Module):

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, forward_rs1: Module, forward_rs2: Module,
              forward_we: Module, forward_rd_addr: Module, forward_rd_wdata: Module):
        cnt = RegArray(UInt(32), 1)
        cnt[0] = cnt[0] + UInt(32)(1)

        # Test sequence covering various scenarios
        rs1_addr = cnt[0].case({
            # Basic read tests
            UInt(32)(0): UInt(5)(0),   # Read x0
            UInt(32)(1): UInt(5)(1),   # Read x1 (after write)
            UInt(32)(2): UInt(5)(2),   # Read x2 (after write)
            UInt(32)(3): UInt(5)(1),   # Read x1 again
            # Bypass test: read while writing
            UInt(32)(10): UInt(5)(5),  # Will be written in same cycle
            UInt(32)(11): UInt(5)(5),  # Read back after bypass
            UInt(32)(12): UInt(5)(0),  # Read x0 during write to x0
            # Read various registers
            UInt(32)(20): UInt(5)(10),
            UInt(32)(21): UInt(5)(15),
            UInt(32)(22): UInt(5)(31), # Last register
            UInt(32)(30): UInt(5)(7),  # Read for bypass test
            UInt(32)(31): UInt(5)(7),  # Read same after bypass
            None: UInt(5)(0),
        })

        rs2_addr = cnt[0].case({
            UInt(32)(0): UInt(5)(0),   # Read x0
            UInt(32)(1): UInt(5)(2),   # Read x2 (after write)
            UInt(32)(2): UInt(5)(1),   # Read x1 (after write)
            UInt(32)(3): UInt(5)(2),   # Read x2 again
            # Bypass test
            UInt(32)(10): UInt(5)(6),  # Different from rs1
            UInt(32)(11): UInt(5)(6),
            UInt(32)(12): UInt(5)(0),
            # Read various registers
            UInt(32)(20): UInt(5)(11),
            UInt(32)(21): UInt(5)(16),
            UInt(32)(22): UInt(5)(30),
            UInt(32)(30): UInt(5)(8),  # Different from rs1
            UInt(32)(31): UInt(5)(7),  # Same as rs1 for testing
            None: UInt(5)(0),
        })

        # Write enable pattern
        rd_we = cnt[0].case({
            # Initial writes to populate registers
            UInt(32)(0): Bits(1)(1),   # Write to x1
            UInt(32)(1): Bits(1)(1),   # Write to x2
            UInt(32)(2): Bits(1)(0),   # No write
            UInt(32)(3): Bits(1)(0),   # No write
            # Bypass test writes
            UInt(32)(10): Bits(1)(1),  # Write to x5 (bypass)
            UInt(32)(11): Bits(1)(0),  # No write
            UInt(32)(12): Bits(1)(1),  # Try write to x0 (should be ignored)
            # Additional writes
            UInt(32)(20): Bits(1)(1),  # Write to x10
            UInt(32)(21): Bits(1)(1),  # Write to x15
            UInt(32)(22): Bits(1)(1),  # Write to x31
            UInt(32)(30): Bits(1)(1),  # Write to x7 (bypass test)
            UInt(32)(31): Bits(1)(0),  # No write
            None: Bits(1)(0),
        })

        # Write address
        rd_addr = cnt[0].case({
            UInt(32)(0): UInt(5)(1),   # x1
            UInt(32)(1): UInt(5)(2),   # x2
            UInt(32)(10): UInt(5)(5),  # x5 (bypass)
            UInt(32)(12): UInt(5)(0),  # x0 (write should be ignored)
            UInt(32)(20): UInt(5)(10), # x10
            UInt(32)(21): UInt(5)(15), # x15
            UInt(32)(22): UInt(5)(31), # x31
            UInt(32)(30): UInt(5)(7),  # x7 (bypass)
            None: UInt(5)(0),
        })

        # Write data
        rd_wdata = cnt[0].case({
            UInt(32)(0): UInt(32)(0xDEADBEEF),  # x1 = 0xDEADBEEF
            UInt(32)(1): UInt(32)(0x12345678),  # x2 = 0x12345678
            UInt(32)(10): UInt(32)(0xAAAAAAAA), # x5 = 0xAAAAAAAA (bypass)
            UInt(32)(12): UInt(32)(0xFFFFFFFF), # x0 = 0xFFFFFFFF (should be ignored)
            UInt(32)(20): UInt(32)(0x11111111), # x10 = 0x11111111
            UInt(32)(21): UInt(32)(0x22222222), # x15 = 0x22222222
            UInt(32)(22): UInt(32)(0x33333333), # x31 = 0x33333333
            UInt(32)(30): UInt(32)(0xBBBBBBBB), # x7 = 0xBBBBBBBB (bypass)
            None: UInt(32)(0),
        })

        forward_rs1.async_called(data=rs1_addr)
        forward_rs2.async_called(data=rs2_addr)
        forward_we.async_called(data=rd_we)
        forward_rd_addr.async_called(data=rd_addr)
        forward_rd_wdata.async_called(data=rd_wdata)


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
    cnt = 0

    for i in raw.split('\n'):
        if '[test]' in i:
            # Parse log line
            line_toks = i.split('|')
            rs1_addr = int(line_toks[0].split(':')[-1])
            rs1_data = int(line_toks[1].split(':')[-1])
            rs2_addr = int(line_toks[2].split(':')[-1])
            rs2_data = int(line_toks[3].split(':')[-1])
            rd_we = int(line_toks[4].split(':')[-1])
            rd_addr = int(line_toks[5].split(':')[-1])
            rd_wdata = int(line_toks[6].split(':')[-1])

            # Get expected values from reference model using current cycle's inputs
            ref_rs1_data, ref_rs2_data = ref.tick(rs1_addr, rs2_addr, rd_we, rd_addr, rd_wdata)

            # Debug output for first few cycles
            if cnt < 10:
                reg_val = ref.regs[rs1_addr] if rs1_addr < 32 else 0
                print(f"Cycle {cnt}: rs1_addr={rs1_addr}, rs1_data={rs1_data:#x}, ref={ref_rs1_data:#x}, " +
                      f"rd_we={rd_we}, rd_addr={rd_addr}, rd_wdata={rd_wdata:#x}")
                print(f"         ref.rs1_addr_reg={ref.rs1_addr_reg}, ref.regs[{rs1_addr}]={reg_val:#x}")

            # Check rs1 data
            assert rs1_data == ref_rs1_data, \
                f'RS1 data incorrect at cycle {cnt}: addr={rs1_addr}, got {rs1_data:#x}, expected {ref_rs1_data:#x}'

            # Check rs2 data
            assert rs2_data == ref_rs2_data, \
                f'RS2 data incorrect at cycle {cnt}: addr={rs2_addr}, got {rs2_data:#x}, expected {ref_rs2_data:#x}'

            cnt += 1

    # We expect around sim_threshold - 2 cycles (accounting for reset and initialization)
    assert cnt >= 95, f'cnt: {cnt} < 95 (too few test cycles)'
    print(f"\n✓ Test passed! Ran {cnt} cycles successfully.")


def build_system():
    driver = Driver()
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
