"""Simple single-issue RISC-V CPU implementation

This module implements a basic 5-stage pipeline CPU with the following stages:
- Fetchor (F): Instruction fetch from icache
- Decoder (D): Instruction decode
- Executor (E): ALU/Adder execution and memory access
- MemoryAccessor (M): Writeback data selection
- WriteBack (W): Register file writeback

The top() function connects all pipeline stages in the correct order.
"""

from assassyn.frontend import *

from impl.gen_cpu.pipestage import Fetchor, Decoder, Executor, MemoryAccessor, WriteBack
from impl.gen_cpu.downstreams import regfile_wrapper


def top(icache_init_file: str, dcache_init_file: str, depth_log: int = 9):
    """Build and connect all CPU pipeline stages

    This is NOT a Module.build() method - it's a plain function that
    instantiates modules and calls their build methods to connect them.

    Args:
        icache_init_file: Instruction memory initialization file
        dcache_init_file: Data memory initialization file
        depth_log: Log2 of cache depth (default 9 = 512 entries)

    Pipeline connection order:
        1. Instantiate all modules
        2. Build WriteBack (no dependencies)
        3. Build MemoryAccessor (depends on WriteBack)
        4. Build Executor (depends on MemoryAccessor)
        5. Build Decoder (depends on Executor)
        6. Build Fetchor (depends on Decoder)
        7. Build regfile_wrapper (connects Decoder and WriteBack)
    """

    # ========== Instantiate all pipeline stages ==========
    write_back = WriteBack()
    memory_accessor = MemoryAccessor()
    executor = Executor()
    decoder = Decoder()
    fetchor = Fetchor()

    # ========== Build in reverse dependency order ==========

    # Stage 5: WriteBack (no dependencies)
    rd, rd_data, wb_en = write_back.build()

    # Stage 1: Fetchor (depends on Decoder for async_called)
    icache_dout = fetchor.build(
        decoder=decoder,
        init_file=icache_init_file,
        depth_log=depth_log
    )

    # Stage 2: Decoder (depends on Executor for async_called)
    # Returns register addresses for regfile read and immediate value
    rs1_addr, rs2_addr, imm = decoder.build(
        executor=executor,
        rdata=icache_dout
    )

    # ========== Connect regfile_wrapper ==========
    # regfile receives:
    # - Read addresses from Decoder (rs1_addr, rs2_addr)
    # - Write control and data from WriteBack (rd, rd_data, wb_en)
    regfile = regfile_wrapper()
    rs1_data, rs2_data = regfile.build(
        rs1_addr=rs1_addr,
        rs2_addr=rs2_addr,
        rd_write_en=wb_en,  # From WriteBack (passed through pipeline)
        rd_addr=rd,         # From WriteBack
        rd_wdata=rd_data    # From WriteBack
    )

    # Connect Executor with regfile data
    # Note: rs1_data and rs2_data are RegOut from ExternalSV (RegFile)
    # and can be used directly as Array. imm is passed via Port through
    # Decoder's async_called, so we don't need to pass it here.
    dcache = executor.build(
        memory_accessor=memory_accessor,
        RS1_data=rs1_data,  # RegOut can be used as Array directly
        RS2_data=rs2_data,  # RegOut can be used as Array directly
        init_file=dcache_init_file,
        depth_log=depth_log
    )

    # Stage 4: MemoryAccessor (depends on WriteBack for async_called)
    # Connects dcache data and sends selected writeback data to WriteBack
    wb_data = memory_accessor.build(
        write_back=write_back,
        mem_rdata=dcache.dout
    )


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python main.py <icache_init_file> <dcache_init_file> [depth_log]")
        print("Example: python main.py workload.exe workload.data 9")
        sys.exit(1)

    icache_file = sys.argv[1]
    dcache_file = sys.argv[2]
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 9

    print(f"Building SimpleCPU with cache depth 2^{depth} = {1<<depth}")
    top(icache_file, dcache_file, depth)
    print("SimpleCPU built successfully")
