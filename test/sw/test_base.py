"""Base test for gen_cpu using 0to100.exe workload

This test module validates the gen_cpu implementation by running the 0to100
benchmark and verifying correct execution.
"""

import os
import re
import shutil
import ast

from assassyn.frontend import *
from assassyn.backend import config, elaborate
from assassyn import utils
from assassyn.test import LogChecker, RegexExtractor, LogRecord

from impl.gen_cpu.pipestage import Fetchor, Decoder, Executor, MemoryAccessor, WriteBack
from impl.gen_cpu.downstreams import regfile_wrapper, jump_predictor_wrapper

# Define workspace path relative to current file
current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f'{current_path}/.workspace/'

WRITEBACK_PATTERN = re.compile(
    r"Cycle @(?P<cycle>\d+(?:\.\d+)?):.*?\[writeback\]\s+x(?P<reg>\d+):\s+(?P<value>0x[0-9a-fA-F]+|\d+)"
)


class Driver(Module):
    """Driver module to control CPU startup timing"""

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, fetchor):
        """Control when to start the CPU

        Args:
            fetchor: Fetchor module to start async calling

        The driver waits until counter > 10 before starting the CPU,
        giving time for initialization.
        """
        # Counter for controlling startup
        cnt = RegArray(UInt(32), 1)

        # Increment counter
        (cnt & self)[0] <= cnt[0] + UInt(32)(1)

        start = cnt[0] > UInt(32)(10)

        # Only start calling fetchor after cnt[0] > 10
        with Condition(start):
            fetchor.async_called(start=start)


def cp_if_exists(src, dst, placeholder=False):
    """Copy file from src to dst if it exists

    Args:
        src: Source file path
        dst: Destination file path
        placeholder: If True and src doesn't exist, create empty file at dst
    """
    if os.path.exists(src):
        shutil.copy(src, dst)
    elif placeholder:
        open(dst, 'w').write('')


def init_workspace(base_path, case):
    """Initialize workspace with workload files

    Args:
        base_path: Base directory containing workload files
        case: Workload name (e.g., '0to100')
    """
    # Clean and recreate workspace
    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    os.mkdir(workspace)

    # Copy workload files
    # .exe: instruction memory (required)
    cp_if_exists(f'{base_path}/{case}.exe', f'{workspace}/workload.exe', False)
    # .data: data memory (optional, create empty if missing)
    cp_if_exists(f'{base_path}/{case}.data', f'{workspace}/workload.data', True)
    # .sh: verification script (optional)
    cp_if_exists(f'{base_path}/{case}.sh', f'{workspace}/workload.sh', False)
    # .config: workload configuration (optional, used for data offset)
    cp_if_exists(f'{base_path}/{case}.config', f'{workspace}/workload.config', False)


def _load_workload_config(path: str) -> dict:
    """Load workload configuration file if present."""
    if not os.path.exists(path):
        return {}

    with open(path, 'r') as cfg_file:
        raw = cfg_file.read()

    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError) as exc:
        raise ValueError(f"Failed to parse workload config at {path}") from exc


def build_cpu(depth_log=9):
    """Build the CPU once and return simulator components

    Args:
        depth_log: Log2 of cache depth (default 9 = 512 entries)

    Returns:
        tuple: (sys, simulator_binary, verilog_path)
    """
    sys = SysBuilder('gen_cpu')

    # Use absolute paths for SRAM init files
    icache_file = os.path.abspath(f'{workspace}/workload.exe')
    dcache_file = os.path.abspath(f'{workspace}/workload.data')
    config_file = os.path.abspath(f'{workspace}/workload.config')
    workload_cfg = _load_workload_config(config_file)
    data_offset = int(workload_cfg.get('data_offset', 0))

    with sys:
        # ========== Instantiate all pipeline stages ==========
        write_back = WriteBack()
        memory_accessor = MemoryAccessor()
        executor = Executor()
        decoder = Decoder()
        fetchor = Fetchor()
        driver = Driver()
        jump_predictor = jump_predictor_wrapper()

        # ========== Define PC register as the single source of truth ==========
        # PC assignment should only happen in ONE place
        pc = RegArray(UInt(32), 1, initializer=[0])
        jump_update_done = RegArray(Bits(1), 1, initializer=[0])

        # ========== Build stages in correct order ==========

        # Stage 5: WriteBack (no dependencies)
        rd, rd_data, wb_en = write_back.build()

        wb_stage_rd = write_back.forward_rd
        wb_stage_rd_data = write_back.forward_rd_data
        wb_stage_wb_en = write_back.forward_wb_en


        # Build the Driver to control fetchor startup
        driver.build(fetchor)

        # Build Fetchor with PC as input
        icache_dout = fetchor.build(decoder=decoder, pc=pc, init_file=icache_file, depth_log=depth_log, jump_update_done=jump_update_done)

        # Build Decoder with instruction data
        rs1_addr, rs2_addr, imm = decoder.build(executor=executor, rdata=icache_dout)

        # Build regfile_wrapper
        rs1_data, rs2_data = regfile_wrapper().build(
            rs1_addr=rs1_addr,
            rs2_addr=rs2_addr,
            rd_write_en=wb_en,
            rd_addr=rd,
            rd_wdata=rd_data
        )

        ma_stage_rd = RegArray(UInt(5), 1, initializer=[0])
        ma_stage_rd_data = RegArray(UInt(32), 1, initializer=[0])
        ma_stage_wb_en = RegArray(Bits(1), 1, initializer=[0])
        ma_stage_is_load = RegArray(Bits(1), 1, initializer=[0])
        ma_stage_load_data = RegArray(UInt(32), 1, initializer=[0])
        ma_stage_load_rd = RegArray(UInt(5), 1, initializer=[0])
        ma_stage_load_valid = RegArray(Bits(1), 1, initializer=[0])

        # Build Executor - returns jump control values
        dcache, addr_purpose, adder_result, cmp_out, cmp_out_used = executor.build(
            memory_accessor=memory_accessor,
            RS1_data=rs1_data,
            RS2_data=rs2_data,
            init_file=dcache_file,
            depth_log=depth_log,
            addr_offset=data_offset,
            ma_stage_rd=ma_stage_rd,
            ma_stage_rd_data=ma_stage_rd_data,
            ma_stage_wb_en=ma_stage_wb_en,
            ma_stage_is_load=ma_stage_is_load,
            ma_stage_load_data=ma_stage_load_data,
            ma_stage_load_rd=ma_stage_load_rd,
            ma_stage_load_valid=ma_stage_load_valid,
            wb_stage_rd=wb_stage_rd,
            wb_stage_rd_data=wb_stage_rd_data,
            wb_stage_wb_en=wb_stage_wb_en,
        )

        # Build MemoryAccessor
        wb_data = memory_accessor.build(
            write_back=write_back,
            mem_rdata=dcache.dout,
            ma_stage_rd=ma_stage_rd,
            ma_stage_rd_data=ma_stage_rd_data,
            ma_stage_wb_en=ma_stage_wb_en,
            ma_stage_is_load=ma_stage_is_load,
            ma_stage_load_data=ma_stage_load_data,
            ma_stage_load_rd=ma_stage_load_rd,
            ma_stage_load_valid=ma_stage_load_valid,
        )

        # Build jump_predictor - pass PC to it so it can update PC
        # It returns jump_update_done signal for Decoder
        jump_predictor.build(
            pc=pc,
            addr_purpose=addr_purpose,
            adder_result=adder_result,
            cmp_out=cmp_out,
            cmp_out_used=cmp_out_used,
            jump_processed=jump_update_done
        )

    print(sys)

    # Configure elaboration
    conf = config(
        verilog=utils.has_verilator(),
        sim_threshold=10000,
        idle_threshold=10000,
        resource_base='',
        fifo_depth=1,
    )

    # Elaborate to generate simulator and verilog
    simulator_path, verilog_path = elaborate(sys, **conf)

    # Build the simulator binary once
    print("Building simulator binary...")
    simulator_binary = utils.build_simulator(simulator_path)
    print(f"Simulator binary built: {simulator_binary}")

    return sys, simulator_binary, verilog_path


def check():
    """Verify test results from raw.log using internal LogChecker."""

    raw_log_path = os.path.join(os.getcwd(), 'raw.log')
    if not os.path.exists(raw_log_path):
        raise FileNotFoundError(f"raw.log not found at {raw_log_path}")

    with open(raw_log_path, 'r') as raw_file:
        raw_content = raw_file.read()

    data_path = os.path.join(workspace, 'workload.data')
    expected_sum = _load_reference_sum(data_path)

    checker = LogChecker(
        RegexExtractor(r'\[writeback\]'),
        _parse_writeback_record,
    )

    stats = {
        'x14_sum': 0,
        'x14_last_cycle': None,
        'x10_last': None,
        'x10_cycle': None,
    }

    def _aggregate(record: LogRecord):
        reg = record.data.get('reg')
        value = record.data.get('value')
        cycle = record.data.get('cycle')

        if reg == 14:
            stats['x14_sum'] += value
            stats['x14_last_cycle'] = cycle
        elif reg == 10:
            stats['x10_last'] = value
            stats['x10_cycle'] = cycle

    checker.add_hook(_aggregate)
    checker.collect(raw_content)

    if stats['x14_sum'] != expected_sum:
        timestamp = stats['x14_last_cycle']
        raise AssertionError(
            f"x14 accumulation mismatch at cycle {timestamp if timestamp is not None else 'unknown'}: "
            f"got {stats['x14_sum']:#x}, expected {expected_sum:#x}"
        )

    if stats['x10_last'] is None:
        raise AssertionError("Did not observe any writeback to x10; cannot validate accumulator result.")

    if stats['x10_last'] != expected_sum:
        timestamp = stats['x10_cycle']
        raise AssertionError(
            f"x10 final value mismatch at cycle {timestamp if timestamp is not None else 'unknown'}: "
            f"got {stats['x10_last']:#x}, expected {expected_sum:#x}"
        )

    print(
        f"Validation passed: writeback entries={len(checker.records)}, "
        f"x14_sum={stats['x14_sum']:#x}, x10_final={stats['x10_last']:#x}, reference={expected_sum:#x}"
    )


def _parse_writeback_record(line: str, index: int) -> LogRecord:
    """Parse a single writeback log line into LogRecord with cycle information."""
    match = WRITEBACK_PATTERN.search(line)
    if not match:
        raise AssertionError(f"Line #{index} does not contain writeback info: {line}")

    cycle_raw = match.group('cycle')
    try:
        cycle_value = float(cycle_raw)
    except ValueError:
        cycle_value = None

    reg = int(match.group('reg'), 10)
    value = int(match.group('value'), 0)

    data = {
        'cycle': cycle_value,
        'reg': reg,
        'value': value,
    }

    return LogRecord(index=index, line=line, data=data, meta={'timestamp': cycle_value})


def _load_reference_sum(path: str) -> int:
    """Sum the expected values from workload.data."""
    if not os.path.exists(path):
        return 0

    total = 0
    with open(path, 'r') as data_file:
        for raw_line in data_file:
            line = raw_line.split('//', 1)[0].split('#', 1)[0].strip()
            if not line:
                continue
            tokens = line.split()
            for token in tokens:
                try:
                    total += int(token, 16)
                except ValueError:
                    total += int(token, 0)
    return total


def run_cpu(sys, simulator_binary, verilog_path):
    """Run the CPU with loaded workload

    Args:
        sys: SysBuilder system
        simulator_binary: Path to compiled simulator
        verilog_path: Path to verilog output directory
    """
    # Run simulator
    raw = utils.run_simulator(binary_path=simulator_binary)
    open('raw.log', 'w').write(raw)
    check()

    # Run verilator if available
    #if utils.has_verilator():
    #    raw = utils.run_verilator(verilog_path)
    #    open('raw.log', 'w').write(raw)
    #    check()

    # Clean up log file
    os.remove('raw.log')


if __name__ == '__main__':
    # Define workload path
    # Note: utils.repo_path() returns the assassyn subdir, we need parent dir
    wl_path = f'{os.path.dirname(utils.repo_path())}/resources/riscv/benchmarks'

    # Initialize workspace with 0to100 workload
    print("Initializing workspace with 0to100.exe...")
    init_workspace(wl_path, '0to100')

    # Build CPU once
    print("Building gen_cpu...")
    sys, simulator_binary, verilog_path = build_cpu(depth_log=9)
    print("gen_cpu built successfully!")

    # Run test
    print("Running 0to100 test...")
    run_cpu(sys, simulator_binary, verilog_path)

    print("All tests passed!")
