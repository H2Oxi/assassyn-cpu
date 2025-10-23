# done4 - 指令解码器端到端打通

oct,23,完成时间

## 完成内容

### 1. ✅ 规划并声明 `ins_decoder` 模块接口

**文件位置**: `impl/gen_cpu/submodules.py:3-66`

- 新增 `InsDecoder(ExternalSV)` 描述类，梳理输入输出端口（原始指令、各类 immediates、控制信号、写回/访存标志）。
- 引入 `impl/gen_cpu/decoder_defs.py` 中的枚举，确保 Python 端与 SystemVerilog 共用一致的编码。
- 在注释中标明每个信号用途，方便后续流水级模块直接消费。

### 2. ✅ 统一控制信号编码

**文件位置**: `impl/gen_cpu/decoder_defs.py`

- 定义 `InstrFormat / AluOp / CmpOp / AdderUse / AddIn{1,2}Sel / WbDataSel / MemWDataSel` 等枚举。
- 明确每个控制字段数值，对齐 `docs/rv32i.csv` 表头的语义，避免魔数散落。

### 3. ✅ 实现 SystemVerilog 解码器

**文件位置**: `impl/gen_cpu/external_src/ins_decoder.sv`

- 组合逻辑版 RV32I 解码器：按 opcode/funct3/funct7 分类处理 R/I/S/B/U/J/SYS 指令。
- 生成所有立即数（I/S/B/U/J/shamt），下发 ALU / Adder / Branch / LoadStore 所需控制信号。
- 对非法或未支持指令拉高 `illegal` 并保持默认安全配置。

### 4. ✅ 最小化验证回路

**CI Smoke**: `test/hw/ci-test/test_decoder_stage[1-5].py`

- 按指令族（算术/立即数/访存/分支跳转/系统）检查 SV 源码中是否存在对应处理入口，保证迭代路径清晰。

**单元一致性**: `test/hw/unit-test/submodules/test_ins_decoder.py`

- 解析 `docs/rv32i.csv` 校验：CSV 配置项与 Python 枚举值保持一致。
- 同时检查 SV 文件中的关键控制项关键字，防止回归时误删。

### 5. ✅ 测试执行

```bash
pytest test/hw/ci-test
pytest test/hw/unit-test/submodules/test_ins_decoder.py
```

全部用例通过。

## 相关文件

- 新建: `impl/gen_cpu/decoder_defs.py`
- 新建: `impl/gen_cpu/external_src/ins_decoder.sv`
- 修改: `impl/gen_cpu/submodules.py`
- 新建: `test/hw/ci-test/test_decoder_stage{1..5}.py`
- 新建: `test/hw/unit-test/submodules/test_ins_decoder.py`
