# Done - Using Record syntax for InsDecoder

Oct 24, 23:00

## Task 1: Instantiate InsDecoder in Decoder.build()
Status: Completed

Implementation details:
- Added import for `InsDecoder` from `impl.gen_cpu.submodules`
- Instantiated `InsDecoder` with `instruction_code` as input to `instr_in` port
- Used external SV instantiation pattern similar to `test_adder.py`

## Task 2: Use Record syntax to organize decoder outputs
Status: Completed

Implementation details:
- Created a `Record` type with all decoder output fields:
  - Control signals: decoded_valid, illegal, rs1_used, rs2_used, rd_write_en, etc.
  - Register addresses: rs1_addr, rs2_addr, rd_addr
  - ALU control: alu_en, alu_op, alu_in1_sel, alu_in2_sel
  - Comparator control: cmp_op, cmp_out_used
  - Adder control: adder_use, add_in1_sel, add_in2_sel, add_postproc, addr_purpose
  - Writeback control: wb_data_sel, wb_en
  - Memory control: mem_read, mem_write, mem_wdata_sel, mem_wstrb
  - Immediate value: imm
- Used `Record.bundle()` method to create a structured `RecordValue` containing all decoder outputs
- Returned the `decoder_output` Record from `Decoder.build()`

All tasks completed successfully!

## Refactoring: Move DecoderOutputType to decoder_defs.py

Implementation details:
- Added `DecoderOutputType` as a module-level Record definition in `decoder_defs.py:106-134`
- Imported necessary types: `Record`, `UInt`, `Bits` from `assassyn.frontend`
- Updated `pipestage.py` to import `DecoderOutputType` from `decoder_defs`
- Removed inline Record type definition from `Decoder.build()` method
- Now using the imported `DecoderOutputType.bundle()` directly

This refactoring improves code organization and makes the decoder output type reusable across the codebase.
