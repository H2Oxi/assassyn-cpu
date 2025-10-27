# Done - Generate Decoder Test

Oct 25, 13:00

## Task 1: Create Driver module for instruction fetch
Status: Completed

Implementation details:
- Created `Driver` class in `test/sw/test_decoder.py:21-48`
- Driver controls SRAM to read instructions sequentially
- Uses a counter (RegArray) to generate addresses
- Instantiates SRAM with 32-bit width, 512 entries
- Reads from SRAM and calls decoder asynchronously

## Task 2: Implement decoder test in test_decoder.py
Status: Completed

Implementation details:
- Created `DecoderWithLog` class that wraps InsDecoder with logging (test/sw/test_decoder.py:204-256)
- Instantiates InsDecoder and bundles all outputs into DecoderOutputType Record
- Logs instruction code and key decoder outputs (rd, rs1, rs2, fmt, alu_en)
- Uses SRAM initialized from `resources/riscv/benchmarks/0to100.exe`
- Test function `test_decoder()` at test/sw/test_decoder.py:212-271

## Task 3: Create check function with reference decoder
Status: Completed

Implementation details:
- Created Python reference decoder `decode_instruction_ref()` at test/sw/test_decoder.py:51-146
- Decodes based on opcode to identify instruction format (R/I/S/B/U/J/SYS)
- Extracts register addresses (rd, rs1, rs2) from instruction encoding
- Determines control signals (rs1_used, rs2_used, rd_write_en, etc.)
- Created `check_decoder()` function at test/sw/test_decoder.py:150-209
- Parses simulator log output and compares with reference decoder
- Validates register address extraction (rd, rs1, rs2)

## Task 4: Test and debug
Status: Completed

Issues fixed:
1. Fixed Decoder ports issue in `impl/gen_cpu/dut/decoding.py:13` - removed unnecessary `pop_all_ports` call
2. Added missing import of `InsDecoder` to test file
3. Moved log statement inside module build function to avoid context issues
4. Fixed resource_base path to point to correct location
5. Fixed log parsing to handle simulator output format with Cycle information

Test Results:
- Successfully tested 13 instructions from 0to100.exe
- All register address extractions validated correctly
- 0 errors reported
- Test passes successfully!

Command to run test:
```bash
python test/sw/test_decoder.py
```
