"""Base test for gen_cpu using 0to100.exe workload

This test module validates the gen_cpu implementation by running the 0to100
benchmark and verifying correct execution.
"""

import os
import shutil
import subprocess

from assassyn.frontend import *
from assassyn.backend import config, elaborate
from assassyn import utils

from impl.gen_cpu.pipestage import Fetchor, Decoder, Executor, MemoryAccessor, WriteBack
from impl.gen_cpu.downstreams import regfile_wrapper, jump_predictor_wrapper

# Define workspace path relative to current file
current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f'{current_path}/.workspace/'


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

        # Only start calling fetchor after cnt[0] > 10
        with Condition(cnt[0] > UInt(32)(10)):
            fetchor.async_called()


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
        pc = RegArray(UInt(32), 1)
        jump_update_done = RegArray(Bits(1), 1,initializer=[0])

        # ========== Build stages in correct order ==========

        # Stage 5: WriteBack (no dependencies)
        rd, rd_data, wb_en = write_back.build()

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

        # Build Executor - returns jump control values
        dcache, addr_purpose, adder_result, cmp_out, cmp_out_used = executor.build(
            memory_accessor=memory_accessor,
            RS1_data=rs1_data,
            RS2_data=rs2_data,
            init_file=dcache_file,
            depth_log=depth_log
        )

        # Build MemoryAccessor
        wb_data = memory_accessor.build(write_back=write_back, mem_rdata=dcache.dout)

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
    """Verify test results from raw.log

    Raises:
        AssertionError: If test fails
    """
    script = f'{workspace}/workload.sh'
    if os.path.exists(script):
        # Use workload-specific verification script
        res = subprocess.run([script, 'raw.log', f'{workspace}/workload.data'])
    else:
        # Use generic find_pass.sh script
        script = f'{utils.repo_path()}/examples/minor-cpu/utils/find_pass.sh'
        res = subprocess.run([script, 'raw.log'])

    assert res.returncode == 0, f'Failed test: {res.returncode}'
    print('Test passed!')


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
    if utils.has_verilator():
        raw = utils.run_verilator(verilog_path)
        open('raw.log', 'w').write(raw)
        check()

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
