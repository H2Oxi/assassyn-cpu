"""Base test for gen_cpu using 0to100.exe workload

This test module validates the gen_cpu implementation by running the 0to100
benchmark and verifying correct execution.
"""

import os
import shutil
import subprocess

from assassyn.frontend import SysBuilder
from assassyn.backend import config, elaborate
from assassyn import utils

from impl.gen_cpu.main import top

# Define workspace path relative to current file
current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f'{current_path}/.workspace/'


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
        # Call top() to build the CPU pipeline
        top(
            icache_init_file=icache_file,
            dcache_init_file=dcache_file,
            depth_log=depth_log
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
    wl_path = f'{utils.repo_path()}/resources/riscv/benchmarks'

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
