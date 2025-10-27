# Todo: 修复 decoder 的 imm 接口设计

**任务类型**: fix
**创建时间**: 2025-10-27
**预计完成**: tbd

## 背景

需要分析和验证 `impl/gen_cpu/submodules.py` 中 InsDecoder 模块的 imm 接口设计，确认其与后续模块（`impl/ip/ips.py` 中定义的所有模块）的连接方式是否合理。之前应该已经优化了 imm 逻辑，使所有种类的 imm 都在 sv 源文件内被预处理，以确保不同情况下直接使用 imm 都是可以支持的。

## 任务步骤

### Step 1: 分析当前 InsDecoder 的 imm 接口设计

**目标**: 理解当前 InsDecoder 如何输出 imm，以及与各种 sel 信号的关系

**详细任务**:
1. 检查 `impl/gen_cpu/submodules.py` 中 InsDecoder 的所有输出端口
2. 确认 imm 输出端口的定义（已知是 `imm: WireOut[UInt(32)]`）
3. 分析所有与 imm 使用相关的 sel 信号：
   - `alu_in2_sel`: 选择 ALU 第二个输入（可能包含 IMM_I, IMM_SHAMT5）
   - `add_in2_sel`: 选择 Adder 第二个输入（可能包含 IMM_I, IMM_S, IMM_B_SHL1, IMM_J_SHL1, UIMM_SHL12）
   - `wb_data_sel`: 选择 writeback 数据源（可能包含 IMM_LUI）

**输出**: 列出所有 sel 信号及其与 imm 相关的选项

---

### Step 2: 检查 SV 源文件中的 imm 预处理逻辑

**目标**: 验证 `impl/external_src/ins_decoder.sv` 是否正确预处理了所有类型的 imm

**详细任务**:
1. 检查 ins_decoder.sv 中 imm 的内部计算：
   - imm_i_internal
   - imm_s_internal
   - imm_b_internal
   - imm_u_internal
   - imm_j_internal
   - imm_shamt_internal
2. 确认每种指令格式输出的 imm 值是否正确
3. 验证 imm 输出是否已经包含了所有必要的预处理（如移位、符号扩展等）

**ckpt-1**: 记录所有 imm 类型的预处理方式及其是否满足后续模块的直接使用需求

---

### Step 3: 分析后续模块对 imm 的使用方式

**目标**: 检查 `impl/ip/ips.py` 中所有模块如何使用来自 decoder 的数据

**详细任务**:
1. 列出 `impl/ip/ips.py` 中的所有模块：
   - Adder
   - ALU
   - RegFile
2. 分析每个模块的输入端口，确认哪些需要 imm 数据
3. 检查这些模块是否直接接收 imm，还是通过 sel 信号选择后接收

**输出**: 创建一个映射表，显示每个模块如何使用 decoder 的输出

---

### Step 4: 设计 sel 和 imm 的结合方式

**目标**: 确定如何将 sel 信号和 imm 值结合，为后续模块提供正确的 imm 数据

**详细任务**:
1. 分析当前设计中的数据流：
   - decoder 输出单一的 imm 值
   - decoder 输出多个 sel 信号
   - 后续模块（ALU, Adder）需要根据 sel 选择正确的 imm
2. 确认是否需要在 decoder 和后续模块之间添加 mux 逻辑
3. 评估两种设计方案：
   - 方案A: decoder 根据指令类型输出对应的 imm，后续模块直接使用
   - 方案B: decoder 输出所有类型的 imm，后续模块通过 sel 选择

**ckpt-2**: 记录当前设计方案的选择及其理由，等待用户确认

---

### Step 5: 检查接口设计的合理性

**目标**: 识别 InsDecoder 当前接口设计中的不合理之处

**详细任务**:
1. 检查 imm 输出是否足够（单一 imm 输出 vs 多个 imm 输出）
2. 检查 sel 信号的编码是否与 SV 源文件一致
3. 检查是否有冗余或缺失的接口
4. 验证端口宽度是否合理
5. 确认命名是否清晰一致

**输出**: 列出所有发现的设计问题及改进建议

---

### Step 6: 提出修复方案（如需要）

**目标**: 如果发现设计问题，提出具体的修复方案

**详细任务**:
1. 基于 Step 5 的发现，设计修复方案
2. 评估修复对现有代码的影响范围
3. 列出需要修改的文件

**ckpt-3**: 记录修复方案，等待用户确认是否执行修复

---

### Step 7: 实施修复（如获得确认）

**目标**: 根据确认的方案修改代码

**详细任务**:
1. 修改 `impl/gen_cpu/submodules.py`（如需要）
2. 修改 `impl/external_src/ins_decoder.sv`（如需要）
3. 更新相关测试文件（如需要）

**ckpt-4**: 记录所有代码修改，等待用户验证

---

### Step 8: 验证修复结果

**目标**: 确保修复后的设计正确工作

**详细任务**:
1. 运行现有的 decoder 测试
2. 检查测试结果
3. 如有测试失败，分析原因并修复

**输出**: 测试结果总结

---

## 检查点说明

- **ckpt-1**: 验证 SV 文件中的 imm 预处理逻辑
- **ckpt-2**: 确认 sel 和 imm 结合的设计方案
- **ckpt-3**: 确认修复方案（如有设计问题）
- **ckpt-4**: 验证代码修改结果

## 预期产出

1. InsDecoder 接口设计的分析报告
2. sel 和 imm 结合方式的设计文档
3. 修复后的代码（如需要）
4. 测试验证结果
