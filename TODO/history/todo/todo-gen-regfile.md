# todo2 - Register File Implementation

oct,23,15:00,tbd → **COMPLETED** oct,23,2025

## What was done

### 1. ✓ RegFile Declaration in `impl/ip/ips.py`

Created the RegFile class declaration with:
- 2 read ports (rs1, rs2) with 5-bit addresses
- 1 write port (rd) with 5-bit address, 1-bit write enable, and 32-bit data
- Synchronous read/write (FPGA BRAM-friendly) with 1-cycle read latency
- Clock and reset signals marked as required

### 2. ✓ SystemVerilog Implementation in `impl/ip/ip_repo/regfile.sv`

Implemented the register file module with:
- 32 x 32-bit register array
- Synchronous read: read addresses registered on clock edge with 1-cycle output delay
- Synchronous write: write happens at clock edge
- **x0 handling**: Writes to x0 are blocked; reads from x0 always return 0
- **Bypass logic**: When reading and writing the same non-zero register in the same cycle, the write data is forwarded to the output
- **Reset signal**: Uses active-high `rst` signal (as required by the framework), internally converted to `rst_n`

### 3. ✓ Unit Test in `test/unit-test/ip/test_regfile.py`

Created comprehensive unit test with:
- **Driver module**: Generates test sequences covering:
  - Basic read tests
  - Write followed by read tests
  - x0 special handling tests
  - Bypass/forwarding tests
  - Edge cases (last register x31, multiple reads of same register)
- **Reference model**: Python model matching the exact timing behavior of the hardware
- **Test validation**: Verified against both simulator and Verilator backends
- **Test result**: ✓ All 98 test cycles passed successfully

## Key Implementation Details

### Timing Model
The register file uses the following timing model:
1. At posedge clk: Write to register array AND register read addresses simultaneously
2. Read output: Combinational logic based on registered read addresses (from current cycle)
3. Bypass: If `rd_we && rd_addr==rs*_addr_reg && rd_addr!=0`, forward `rd_wdata` to output

### Reset Polarity
Following the framework's convention (as seen in `assassyn/python/ci-tests/resources/reg.sv`):
- External interface uses active-high `rst`
- Internal logic converts to `rst_n = ~rst` for compatibility with asynchronous reset sensitivity

## Test Results
```
✓ Test passed! Ran 98 cycles successfully.
```
Both simulator and Verilator backends validated successfully.