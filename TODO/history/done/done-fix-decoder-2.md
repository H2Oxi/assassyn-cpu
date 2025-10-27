# Done: 修复 decoder 的 imm 接口设计

**开始时间**: 2025-10-27
**任务文件**: todo-fix-decoder-2-decorated.md

---

## Step 1: 分析当前 InsDecoder 的 imm 接口设计

**开始时间**: 2025-10-27
**完成时间**: 2025-10-27
**状态**: 完成

### 分析结果

#### 1. InsDecoder 输出端口列表

从 `impl/gen_cpu/submodules.py:20-68` 可见，InsDecoder 有以下关键输出：

- **指令解码基础信息**:
  - `decoded_valid`, `illegal`, `instr_format`
  - `rs1_addr`, `rs2_addr`, `rd_addr`
  - `rs1_used`, `rs2_used`, `rd_write_en`

- **ALU 控制信号**:
  - `alu_en`, `alu_op`
  - `alu_in1_sel`: 选择 ALU 输入1 (ZERO=0, RS1=1)
  - `alu_in2_sel`: 选择 ALU 输入2 (ZERO=0, RS2=1, IMM_I=2, IMM_SHAMT5=3)
  - `cmp_op`, `cmp_out_used`

- **Adder 控制信号**:
  - `adder_use`, `addr_purpose`
  - `add_in1_sel`: 选择 Adder 输入1 (ZERO=0, RS1=1, PC=2)
  - `add_in2_sel`: 选择 Adder 输入2 (ZERO=0, IMM_I=1, IMM_S=2, IMM_B_SHL1=3, IMM_J_SHL1=4, UIMM_SHL12=5)
  - `add_postproc`: 后处理控制 (NONE=0, CLR_LSB=1)

- **写回控制信号**:
  - `wb_data_sel`: 选择写回数据源 (NONE=0, ALU=1, IMM_LUI=2, ADDER=3, LOAD=4, LOAD_ZEXT8=5, PC_PLUS4=6)
  - `wb_en`

- **内存控制信号**:
  - `mem_read`, `mem_write`, `mem_wdata_sel`, `mem_wstrb`

- **立即数输出**:
  - `imm: WireOut[UInt(32)]`: 统一的立即数输出

#### 2. 与 imm 相关的 sel 信号分析

通过分析 decoder_defs.py 和 submodules.py，发现以下 sel 信号与 imm 使用相关：

**a) alu_in2_sel (AluIn2Sel enum)**:
- `ZERO = 0`: 不使用 imm
- `RS2 = 1`: 不使用 imm
- `IMM_I = 2`: 使用 I 型立即数
- `IMM_SHAMT5 = 3`: 使用 5 位移位量立即数

**b) add_in2_sel (AddIn2Sel enum)**:
- `ZERO = 0`: 不使用 imm
- `IMM_I = 1`: 使用 I 型立即数
- `IMM_S = 2`: 使用 S 型立即数
- `IMM_B_SHL1 = 3`: 使用 B 型立即数（已左移1位）
- `IMM_J_SHL1 = 4`: 使用 J 型立即数（已左移1位）
- `UIMM_SHL12 = 5`: 使用 U 型立即数（已左移12位）

**c) wb_data_sel (WbDataSel enum)**:
- `IMM_LUI = 2`: 使用 U 型立即数进行写回

#### 3. 关键发现

**设计问题**: InsDecoder 只有一个 `imm` 输出端口，但在不同指令中需要输出不同类型的立即数：

1. **ALU 使用场景**: 需要 IMM_I 或 IMM_SHAMT5
2. **Adder 使用场景**: 需要 IMM_I, IMM_S, IMM_B (预左移), IMM_J (预左移), 或 UIMM (预左移)
3. **Writeback 使用场景**: 需要 IMM_U (用于 LUI)

**sel 信号的语义**: sel 信号不仅仅是选择器，它们实际上编码了"应该使用哪种类型的立即数"，这意味着：
- sel 信号告诉下游模块应该如何解释 decoder 输出的 `imm` 值
- decoder 的 `imm` 输出必须根据当前指令类型输出正确预处理后的立即数

---

## Step 2: 检查 SV 源文件中的 imm 预处理逻辑

**开始时间**: 2025-10-27
**完成时间**: 2025-10-27
**状态**: 完成

### 分析结果

#### 1. SV 文件中的内部立即数计算

从 `impl/external_src/ins_decoder.sv:126-140` 可见，decoder 内部计算了所有类型的立即数：

```systemverilog
// 内部立即数变量定义 (line 126-131)
logic [31:0] imm_i_internal;
logic [31:0] imm_s_internal;
logic [31:0] imm_b_internal;
logic [31:0] imm_u_internal;
logic [31:0] imm_j_internal;
logic [31:0] imm_shamt_internal;

// 立即数提取逻辑 (line 133-140)
imm_i_internal     = {{20{instr_in[31]}}, instr_in[31:20]};
imm_s_internal     = {{20{instr_in[31]}}, instr_in[31:25], instr_in[11:7]};
imm_b_internal     = {{19{instr_in[31]}}, instr_in[31], instr_in[7], instr_in[30:25], instr_in[11:8], 1'b0};
imm_u_internal     = {instr_in[31:12], 12'b0};
imm_j_internal     = {{11{instr_in[31]}}, instr_in[31], instr_in[19:12], instr_in[20], instr_in[30:21], 1'b0};
imm_shamt_internal = {27'b0, instr_in[24:20]};
```

#### 2. 每种立即数类型的预处理验证

| 立即数类型 | 预处理内容 | 是否满足直接使用 | 说明 |
|-----------|----------|----------------|------|
| imm_i | 符号扩展至32位 | ✓ | 用于 I 型指令 (ADDI, LOAD, JALR 等) |
| imm_s | 符号扩展至32位 | ✓ | 用于 S 型指令 (STORE) |
| imm_b | 符号扩展至32位，LSB=0 | ✓ | 用于 B 型指令 (分支)，已预左移 |
| imm_u | 高20位填充，低12位=0 | ✓ | 用于 U 型指令 (LUI, AUIPC)，已预左移12位 |
| imm_j | 符号扩展至32位，LSB=0 | ✓ | 用于 J 型指令 (JAL)，已预左移 |
| imm_shamt | 零扩展至32位 | ✓ | 用于移位指令的5位立即数 |

#### 3. 各指令类型的 imm 输出检查

通过检查 `ins_decoder.sv` 的 case 语句 (line 177-419)，验证每种指令格式输出的 imm 值：

**R 型指令 (line 178-210)**:
- `imm = 32'b0` (line 208) - R 型不使用立即数 ✓

**I 型算术指令 (line 212-258)**:
- 使用 `imm_i_internal` 或 `imm_shamt_internal`
- line 256: `imm = (sel_in2 == ALU_IN2_IMM_SHAMT) ? imm_shamt_internal : imm_i_internal;` ✓

**LUI (line 260-268)**:
- `imm = imm_u_internal` (line 267) ✓

**AUIPC (line 270-282)**:
- `imm = imm_u_internal` (line 281) ✓
- 与 `add_in2_sel = ADD_IN2_UIMM` 配合使用

**LOAD 指令 (line 284-307)**:
- `imm = imm_i_internal` (line 305) ✓
- 用于地址计算

**STORE 指令 (line 309-325)**:
- `imm = imm_s_internal` (line 323) ✓
- 用于地址计算

**分支指令 (line 327-353)**:
- `imm = imm_b_internal` (line 351) ✓
- 用于分支目标计算

**JAL (line 355-367)**:
- `imm = imm_j_internal` (line 366) ✓

**JALR (line 369-385)**:
- `imm = imm_i_internal` (line 383) ✓

#### 4. 关键结论

**预处理验证**: ✅ 所有立即数都已在 SV 源文件内正确预处理

1. **符号扩展**: I/S/B/J 型立即数都已符号扩展至32位
2. **预左移**: B/J 型立即数的 LSB 已置0（等效于左移1位），U 型立即数低12位已置0（等效于左移12位）
3. **零扩展**: shamt 立即数已零扩展至32位
4. **类型匹配**: 每种指令类型都输出了正确类型的立即数到 `imm` 端口

**设计验证**: decoder 输出的 `imm` 值已经根据指令类型进行了预处理，下游模块可以直接使用，无需额外处理。

**ckpt-1 确认**: 用户确认 imm 预处理逻辑符合预期，继续执行。

---

## Step 3: 分析后续模块对 imm 的使用方式

**开始时间**: 2025-10-27
**完成时间**: 2025-10-27
**状态**: 完成

### 分析结果

#### 1. impl/ip/ips.py 中的模块列表

从 `impl/ip/ips.py:1-59` 可见，项目定义了三个外部模块：

**a) Adder (line 5-13)**:
- 输入: `add_in1: WireIn[UInt(32)]`, `add_in2: WireIn[UInt(32)]`
- 输出: `add_out: WireOut[UInt(32)]`
- 功能: 简单的32位加法器
- **关键发现**: Adder 接收两个 32 位输入，不需要知道它们的来源

**b) ALU (line 16-30)**:
- 输入:
  - `alu_in1: WireIn[UInt(32)]`
  - `alu_in2: WireIn[UInt(32)]`
  - `alu_op: WireIn[UInt(4)]`
  - `cmp_op: WireIn[UInt(3)]`
- 输出: `alu_out: WireOut[UInt(32)]`, `cmp_out: WireOut[Bits(1)]`
- 功能: 支持算术、逻辑和比较操作
- **关键发现**: ALU 接收两个 32 位操作数，不关心它们是寄存器值还是立即数

**c) RegFile (line 33-56)**:
- 功能: 寄存器文件，2读1写端口
- **关键发现**: RegFile 不直接使用 imm

#### 2. 模块使用方式分析

通过查看测试文件，了解了模块的实际使用方式：

**从 test/hw/unit-test/ip/test_alu.py:127** 可见：
```python
alu = ExternalALU(alu_in1=alu_in1, alu_in2=alu_in2, alu_op=alu_op, cmp_op=cmp_op)
```
- ALU 模块直接接收准备好的 32 位操作数
- alu_in1 和 alu_in2 可以是任何 32 位值（寄存器值或立即数）

**从 test/hw/unit-test/ip/test_adder.py:59** 可见：
```python
adder = ExternalAdder(add_in1=add_in1, add_in2=add_in2)
```
- Adder 模块同样直接接收 32 位操作数
- 不关心操作数的来源

#### 3. Decoder 输出与后续模块的连接映射

基于分析，创建连接映射表：

| 后续模块 | 需要的输入 | 来自 Decoder 的数据 | 数据准备逻辑 |
|---------|-----------|-------------------|------------|
| **ALU** | alu_in1 (32-bit) | - | 根据 `alu_in1_sel` 选择：ZERO 或 RS1 数据 |
| **ALU** | alu_in2 (32-bit) | `imm` (32-bit), `alu_in2_sel` | 根据 `alu_in2_sel` 选择：ZERO、RS2 数据、IMM_I 或 IMM_SHAMT5 |
| **ALU** | alu_op (4-bit) | `alu_op` | 直接连接 |
| **ALU** | cmp_op (3-bit) | `cmp_op` | 直接连接 |
| **Adder** | add_in1 (32-bit) | - | 根据 `add_in1_sel` 选择：ZERO、RS1 数据或 PC |
| **Adder** | add_in2 (32-bit) | `imm` (32-bit), `add_in2_sel` | 根据 `add_in2_sel` 选择：ZERO、IMM_I、IMM_S、IMM_B、IMM_J 或 UIMM |
| **Writeback** | wb_data (32-bit) | `imm` (32-bit), `wb_data_sel` | 根据 `wb_data_sel` 选择数据源，可能包含 IMM_LUI |

#### 4. 关键发现

**设计验证结论**：

1. **后续模块不直接接收 sel 信号**: ALU 和 Adder 模块只接收准备好的 32 位数据，不需要知道数据来源

2. **需要中间层（mux 逻辑）**: 在 decoder 和后续模块之间，需要有 mux 逻辑根据 sel 信号选择正确的数据：
   - 对于 ALU: 根据 `alu_in2_sel` 在 ZERO/RS2/imm 之间选择
   - 对于 Adder: 根据 `add_in2_sel` 在 ZERO/imm 之间选择（imm 已经是正确类型）
   - 对于 Writeback: 根据 `wb_data_sel` 在多个源之间选择

3. **imm 的角色**: decoder 输出的单一 `imm` 端口已经根据指令类型输出了正确预处理的立即数，中间层只需要根据 sel 信号决定是否使用它

4. **数据流设计**:
   ```
   Decoder → [imm + sel signals] → Mux Logic → [prepared 32-bit operands] → ALU/Adder
   ```

#### 5. 当前实现状态

从 `impl/gen_cpu/pipestage.py:91-111` 可见，Executor 模块的实现还是空的（line 109 注释说明需要实例化 ALU 和其他算术单元），这意味着：
- 中间的 mux 逻辑还未实现
- ALU/Adder 的实例化还未实现
- 这正是需要设计和实现的部分

---

## Step 4: 设计 sel 和 imm 的结合方式

**开始时间**: 2025-10-27
**完成时间**: 2025-10-27
**状态**: 完成

### 分析与设计

#### 1. 当前设计中的数据流

基于前面的分析，当前设计的数据流如下：

```
Instruction → InsDecoder (SV) → {
    imm: UInt(32)         // 已预处理的立即数
    alu_in1_sel: UInt(2)  // ALU 输入1选择器
    alu_in2_sel: UInt(2)  // ALU 输入2选择器
    add_in1_sel: UInt(2)  // Adder 输入1选择器
    add_in2_sel: UInt(3)  // Adder 输入2选择器
    wb_data_sel: UInt(3)  // Writeback 数据选择器
    ...其他控制信号...
} → 需要 Mux 逻辑 → ALU/Adder/Writeback
```

#### 2. 设计方案分析

**方案A: Decoder 输出所有类型的 imm**
- Decoder 输出多个 imm 端口：imm_i, imm_s, imm_b, imm_j, imm_u, imm_shamt
- 后续 mux 根据 sel 信号选择对应的 imm
- 优点：语义清晰，每种类型的 imm 都有明确的端口
- 缺点：增加接口复杂度，违反当前设计

**方案B: Decoder 输出单一 imm，后续模块直接使用**（当前设计）
- Decoder 根据指令类型输出对应的预处理 imm
- 后续 mux 只需要根据 sel 决定是否使用 imm
- 优点：接口简单，imm 已经是正确的值
- 缺点：需要确保 decoder 输出的 imm 与 sel 信号语义一致

#### 3. sel 和 imm 的结合方式设计

基于方案B（当前设计），sel 和 imm 的结合方式如下：

**a) ALU 输入准备逻辑**:
```python
# ALU Input 1 根据 alu_in1_sel 选择
alu_in1 = case alu_in1_sel:
    AluIn1Sel.ZERO => UInt(32)(0)
    AluIn1Sel.RS1  => rs1_data

# ALU Input 2 根据 alu_in2_sel 选择
alu_in2 = case alu_in2_sel:
    AluIn2Sel.ZERO        => UInt(32)(0)
    AluIn2Sel.RS2         => rs2_data
    AluIn2Sel.IMM_I       => decoder.imm  # decoder已输出正确的imm_i
    AluIn2Sel.IMM_SHAMT5  => decoder.imm  # decoder已输出正确的imm_shamt
```

**关键点**: 当 `alu_in2_sel` 为 `IMM_I` 或 `IMM_SHAMT5` 时，decoder 的 `imm` 输出已经是正确类型的立即数。因为：
- 对于 I 型算术指令（ADDI, ANDI 等）: decoder 输出 imm_i_internal
- 对于移位指令（SLLI, SRLI, SRAI）: decoder 根据 `alu_in2_sel` 输出 imm_shamt_internal

**b) Adder 输入准备逻辑**:
```python
# Adder Input 1 根据 add_in1_sel 选择
add_in1 = case add_in1_sel:
    AddIn1Sel.ZERO => UInt(32)(0)
    AddIn1Sel.RS1  => rs1_data
    AddIn1Sel.PC   => pc_value

# Adder Input 2 根据 add_in2_sel 选择
add_in2 = case add_in2_sel:
    AddIn2Sel.ZERO         => UInt(32)(0)
    AddIn2Sel.IMM_I        => decoder.imm  # imm_i
    AddIn2Sel.IMM_S        => decoder.imm  # imm_s
    AddIn2Sel.IMM_B_SHL1   => decoder.imm  # imm_b (已左移)
    AddIn2Sel.IMM_J_SHL1   => decoder.imm  # imm_j (已左移)
    AddIn2Sel.UIMM_SHL12   => decoder.imm  # imm_u (已左移12位)
```

**关键点**: 所有的 IMM_* 选项都直接使用 `decoder.imm`，因为 decoder 已经根据指令类型输出了正确预处理的立即数。

**c) Writeback 数据准备逻辑**:
```python
# Writeback 数据根据 wb_data_sel 选择
wb_data = case wb_data_sel:
    WbDataSel.NONE        => UInt(32)(0)
    WbDataSel.ALU         => alu_result
    WbDataSel.IMM_LUI     => decoder.imm  # imm_u (用于LUI)
    WbDataSel.ADDER       => adder_result
    WbDataSel.LOAD        => load_data
    WbDataSel.LOAD_ZEXT8  => load_data_zext8
    WbDataSel.PC_PLUS4    => pc_plus_4
```

#### 4. 设计的一致性验证

验证 decoder 输出的 imm 与 sel 信号的语义是否一致：

| 指令类型 | sel 信号可能的值 | decoder 输出的 imm | 是否一致 |
|---------|----------------|-------------------|---------|
| R 型 (ADD) | alu_in2_sel=RS2 | imm=0 | ✓ (不使用imm) |
| I 型算术 (ADDI) | alu_in2_sel=IMM_I | imm=imm_i | ✓ |
| I 型移位 (SLLI) | alu_in2_sel=IMM_SHAMT5 | imm=imm_shamt | ✓ |
| I 型加载 (LW) | add_in2_sel=IMM_I | imm=imm_i | ✓ |
| S 型 (SW) | add_in2_sel=IMM_S | imm=imm_s | ✓ |
| B 型 (BEQ) | add_in2_sel=IMM_B_SHL1 | imm=imm_b | ✓ |
| U 型 (LUI) | wb_data_sel=IMM_LUI | imm=imm_u | ✓ |
| U 型 (AUIPC) | add_in2_sel=UIMM_SHL12 | imm=imm_u | ✓ |
| J 型 (JAL) | add_in2_sel=IMM_J_SHL1 | imm=imm_j | ✓ |
| I 型 (JALR) | add_in2_sel=IMM_I | imm=imm_i | ✓ |

**验证结论**: ✅ 所有指令类型的 sel 信号与 decoder 输出的 imm 都是一致的。

#### 5. 设计方案总结

**最终设计方案**:
- 保持当前的单一 `imm` 输出设计
- Decoder 根据指令类型输出正确预处理的 imm
- 中间 Mux 逻辑只需要根据 sel 信号决定是否使用 `decoder.imm`
- 不需要区分 imm 的具体类型，因为 decoder 已经处理好了

**数据流示意**:
```
[InsDecoder SV]
  ├─ imm: 32-bit (已预处理)
  ├─ alu_in2_sel: 2-bit
  └─ add_in2_sel: 3-bit
       ↓
[Python Mux Logic]
  ├─ if alu_in2_sel in {IMM_I, IMM_SHAMT5}: use decoder.imm
  └─ if add_in2_sel in {IMM_I, IMM_S, IMM_B, IMM_J, UIMM}: use decoder.imm
       ↓
[ALU/Adder Modules]
  └─ 接收准备好的 32-bit 操作数
```

---

## Step 5: 检查接口设计的合理性

**开始时间**: 2025-10-27
**完成时间**: 2025-10-27
**状态**: 完成

### 用户反馈与问题识别

**用户反馈**: "我们的sv所对应的外部模块的端口是存在冗余的...我们明明已经通过预处理确保了imm已经能够兼容所有的情况，但是sel信号却还需要枚举所有的种类，这是不合理的。"

### 冗余分析

#### 1. AluIn2Sel 的冗余问题

**当前设计** (`decoder_defs.py:46-50`):
```python
class AluIn2Sel(IntEnum):
    ZERO = 0
    RS2 = 1
    IMM_I = 2
    IMM_SHAMT5 = 3
```

**问题分析**:
- `IMM_I` 和 `IMM_SHAMT5` 都是"使用立即数"的意思
- Decoder 已经根据指令类型输出了正确的 imm（imm_i 或 imm_shamt）
- 从 Python Mux 逻辑的角度看，这两个选项的操作是相同的：都是"使用 decoder.imm"
- **冗余**: 不需要区分是 IMM_I 还是 IMM_SHAMT5，只需要知道"是否使用 imm"

**优化方案**:
```python
class AluIn2Sel(IntEnum):
    ZERO = 0
    RS2 = 1
    IMM = 2  # 统一：使用立即数（decoder已预处理）
```

#### 2. AddIn2Sel 的冗余问题

**当前设计** (`decoder_defs.py:68-74`):
```python
class AddIn2Sel(IntEnum):
    ZERO = 0
    IMM_I = 1
    IMM_S = 2
    IMM_B_SHL1 = 3
    IMM_J_SHL1 = 4
    UIMM_SHL12 = 5
```

**问题分析**:
- 所有 `IMM_*` 选项的语义都是"使用立即数"
- Decoder 已经根据指令类型输出了正确预处理的 imm
- 从 Python Mux 逻辑的角度看，选项 1-5 的操作完全相同：都是"使用 decoder.imm"
- **严重冗余**: 不需要区分 IMM_I/IMM_S/IMM_B/IMM_J/UIMM，只需要知道"是否使用 imm"

**优化方案**:
```python
class AddIn2Sel(IntEnum):
    ZERO = 0
    IMM = 1  # 统一：使用立即数（decoder已预处理）
```

#### 3. WbDataSel 的分析

**当前设计** (`decoder_defs.py:90-97`):
```python
class WbDataSel(IntEnum):
    NONE = 0
    ALU = 1
    IMM_LUI = 2  # <-- 这里
    ADDER = 3
    LOAD = 4
    LOAD_ZEXT8 = 5
    PC_PLUS4 = 6
```

**问题分析**:
- `IMM_LUI` 表示"写回立即数（用于 LUI 指令）"
- 这里的命名虽然提到了 LUI，但实际上就是"写回 decoder.imm"
- **轻微冗余**: 名称具有误导性，应该简化

**优化方案**:
```python
class WbDataSel(IntEnum):
    NONE = 0
    ALU = 1
    IMM = 2  # 统一：写回立即数
    ADDER = 3
    LOAD = 4
    LOAD_ZEXT8 = 5
    PC_PLUS4 = 6
```

### 设计冗余的根本原因

**问题根源**: sel 信号的语义混淆

当前设计中，sel 信号编码了两层信息：
1. **数据来源类型**（寄存器/立即数/PC/ZERO）
2. **立即数的具体类型**（IMM_I/IMM_S/IMM_B等）

但是，**第二层信息是冗余的**，因为：
- Decoder (SV) 已经根据指令类型选择了正确的立即数类型
- Python Mux 逻辑不需要知道立即数的具体类型
- 后续模块（ALU/Adder）只接收 32 位值，不关心来源

### 优化后的设计

#### 简化的 Sel 枚举

```python
# 优化后的 AluIn2Sel
class AluIn2Sel(IntEnum):
    ZERO = 0
    RS2 = 1
    IMM = 2  # 使用立即数（已预处理）

# 优化后的 AddIn2Sel
class AddIn2Sel(IntEnum):
    ZERO = 0
    IMM = 1  # 使用立即数（已预处理）

# 优化后的 WbDataSel
class WbDataSel(IntEnum):
    NONE = 0
    ALU = 1
    IMM = 2  # 写回立即数
    ADDER = 3
    LOAD = 4
    LOAD_ZEXT8 = 5
    PC_PLUS4 = 6
```

#### 位宽优化

优化后的 sel 信号所需位宽：
- `alu_in2_sel`: 2 bits → **2 bits** (保持不变，3个选项)
- `add_in2_sel`: 3 bits → **1 bit** (只需要 ZERO/IMM，节省2位！)
- `wb_data_sel`: 3 bits → **3 bits** (保持不变，7个选项)

**总节省**: 2 bits per instruction

#### Mux 逻辑简化

```python
# 优化前：需要检查多个 IMM_* 值
alu_in2 = case alu_in2_sel:
    AluIn2Sel.ZERO => UInt(32)(0)
    AluIn2Sel.RS2 => rs2_data
    AluIn2Sel.IMM_I => decoder.imm       # 冗余
    AluIn2Sel.IMM_SHAMT5 => decoder.imm  # 冗余

# 优化后：统一处理
alu_in2 = case alu_in2_sel:
    AluIn2Sel.ZERO => UInt(32)(0)
    AluIn2Sel.RS2 => rs2_data
    AluIn2Sel.IMM => decoder.imm  # 简洁

# 优化前：add_in2_sel 需要处理5种 IMM 类型
add_in2 = case add_in2_sel:
    AddIn2Sel.ZERO => UInt(32)(0)
    AddIn2Sel.IMM_I => decoder.imm        # 冗余
    AddIn2Sel.IMM_S => decoder.imm        # 冗余
    AddIn2Sel.IMM_B_SHL1 => decoder.imm   # 冗余
    AddIn2Sel.IMM_J_SHL1 => decoder.imm   # 冗余
    AddIn2Sel.UIMM_SHL12 => decoder.imm   # 冗余

# 优化后：只需要1位选择
add_in2 = add_in2_sel.select(decoder.imm, UInt(32)(0))
# 或者：add_in2 = add_in2_sel ? decoder.imm : 0
```

### SV 文件需要的修改

对应的 `impl/external_src/ins_decoder.sv` 需要修改：

1. **修改 localparams** (line 67-90):
```systemverilog
// 修改前
localparam logic [1:0] ALU_IN2_IMM_I     = 2'd2;
localparam logic [1:0] ALU_IN2_IMM_SHAMT = 2'd3;

localparam logic [2:0] ADD_IN2_IMM_I     = 3'd1;
localparam logic [2:0] ADD_IN2_IMM_S     = 3'd2;
localparam logic [2:0] ADD_IN2_IMM_B     = 3'd3;
localparam logic [2:0] ADD_IN2_IMM_J     = 3'd4;
localparam logic [2:0] ADD_IN2_UIMM      = 3'd5;

// 修改后
localparam logic [1:0] ALU_IN2_IMM       = 2'd2;

localparam logic       ADD_IN2_IMM       = 1'b1;  // 1位即可
```

2. **修改端口定义** (line 14-20):
```systemverilog
// 修改前
output logic [2:0]  add_in2_sel,

// 修改后
output logic        add_in2_sel,  // 1位：0=ZERO, 1=IMM
```

3. **修改 case 语句中的赋值**: 所有原来赋值 IMM_I/IMM_S/IMM_B/IMM_J/UIMM 的地方统一改为 `ADD_IN2_IMM`

### 优化收益总结

| 优化项 | 当前设计 | 优化后 | 收益 |
|-------|---------|--------|------|
| AluIn2Sel 枚举 | 4个选项 | 3个选项 | 语义更清晰 |
| AddIn2Sel 枚举 | 6个选项 | 2个选项 | 大幅简化 |
| add_in2_sel 位宽 | 3 bits | 1 bit | 节省2位 |
| Mux 逻辑复杂度 | 多路判断 | 简单选择 | 代码更简洁 |
| 接口语义 | 混淆（类型+来源） | 清晰（仅来源） | 易于理解 |

### 设计原则确认

**核心原则**: **Sel 信号只应该编码"数据来源"，不应该编码"立即数类型"**

因为：
1. ✅ Decoder (SV) 已经根据指令类型处理了立即数类型
2. ✅ Mux 逻辑只需要知道"是否使用 imm"，不需要知道"imm 是什么类型"
3. ✅ 后续模块只接收值，不关心值的来源细节
4. ✅ 单一职责原则：Decoder 负责类型选择，Mux 负责数据路由

**ckpt-3 确认**: 用户确认修复方案正确，开始执行修复。

---

## Step 6: 实施修复

**开始时间**: 2025-10-27
**状态**: 进行中

### 修改计划

将按以下顺序修改文件：
1. `impl/gen_cpu/decoder_defs.py` - 枚举定义
2. `impl/gen_cpu/submodules.py` - InsDecoder 端口定义
3. `impl/external_src/ins_decoder.sv` - SV 实现

### 修改详情

#### 1. decoder_defs.py 修改 ✅

**修改内容**:
- `AluIn2Sel`: 从 4 个选项简化为 3 个 (ZERO, RS2, IMM)
- `AddIn2Sel`: 从 6 个选项简化为 2 个 (ZERO, IMM)
- `WbDataSel`: 重命名 IMM_LUI → IMM
- `DecoderOutputType.add_in2_sel`: 位宽从 UInt(3) 改为 Bits(1)

**文件位置**: `impl/gen_cpu/decoder_defs.py:46-50, 68-69, 88, 119`

#### 2. submodules.py 修改 ✅

**修改内容**:
- `InsDecoder.add_in2_sel`: 位宽从 `WireOut[UInt(3)]` 改为 `WireOut[Bits(1)]`
- 更新注释说明：0=ZERO, 1=IMM

**文件位置**: `impl/gen_cpu/submodules.py:53`

#### 3. ins_decoder.sv 修改 ✅

**修改内容**:

a) **端口定义** (line 20):
- `add_in2_sel`: 从 `logic [2:0]` 改为 `logic`

b) **Localparams** (line 67-85, 101):
- `ALU_IN2_IMM_I` 和 `ALU_IN2_IMM_SHAMT` → 统一为 `ALU_IN2_IMM`
- `ADD_IN2_IMM_I/S/B/J/UIMM` → 统一为 `ADD_IN2_IMM` (1 bit)
- `WB_IMM_LUI` → `WB_IMM`

c) **指令解码逻辑**:
- **I 型算术指令** (line 207-253): 使用 `use_shamt` 内部变量区分 imm_i 和 imm_shamt，统一使用 `ALU_IN2_IMM`
- **LUI** (line 261): `WB_IMM_LUI` → `WB_IMM`
- **AUIPC** (line 273): `ADD_IN2_UIMM` → `ADD_IN2_IMM`
- **LOAD** (line 296): `ADD_IN2_IMM_I` → `ADD_IN2_IMM`
- **STORE** (line 313): `ADD_IN2_IMM_S` → `ADD_IN2_IMM`
- **Branch** (line 344): `ADD_IN2_IMM_B` → `ADD_IN2_IMM`
- **JAL** (line 358): `ADD_IN2_IMM_J` → `ADD_IN2_IMM`
- **JALR** (line 374): `ADD_IN2_IMM_I` → `ADD_IN2_IMM`

**文件位置**: `impl/external_src/ins_decoder.sv`

### 修改验证

所有修改都遵循以下原则：
1. ✅ Sel 信号只编码"数据来源"，不编码"立即数类型"
2. ✅ Decoder 内部仍然根据指令类型选择正确的 imm
3. ✅ 接口简化，位宽优化（add_in2_sel: 3 bits → 1 bit）
4. ✅ 所有指令类型都已更新

**状态**: 完成

