# ckpt-fix-base_test

## ckpt-1: Driver 实现

### 修改文件
- `test/sw/test_base.py`

### 修改内容

1. **导入更改**:
   - 从 `from impl.gen_cpu.main import top` 改为直接导入所有 pipeline stages
   - 添加了 `from assassyn.frontend import *`

2. **添加 Driver 类** (line 23-47):
   - 创建了一个 Module 来控制 CPU 启动时机
   - 使用计数器 cnt，当 cnt[0] > 10 时才调用 `fetchor.async_called()`
   - 这样可以给系统初始化时间

3. **重构 build_cpu 函数** (line 85-180):
   - 不再调用 `impl.gen_cpu.main.top()`
   - 直接在测试中实例化所有 pipeline stages
   - 按照正确的依赖顺序构建：WriteBack → Fetchor → Decoder → regfile → Executor → MemoryAccessor → Driver
   - 最后构建 Driver 来控制 Fetchor 的启动

### 设计说明

参考了 `test/sw/test_decoder.py` 中的 Driver 设计模式，但做了调整：
- test_decoder 中 Driver 直接驱动 SRAM 并调用 decoder
- test_base 中 Driver 只负责控制 fetchor 的启动时机
- CPU 的 Fetchor 本身已经有 PC 寄存器和 icache 访问逻辑

### 验证要点

1. Driver 的计数器是否正常工作
2. CPU 是否在 cnt > 10 时开始运行
3. Fetchor 是否能正常开始取指令

### 验证结果

✅ 用户确认通过，继续 Step 2

---

## ckpt-2: 日志功能实现

### 修改文件
- `impl/gen_cpu/pipestage.py`

### 修改内容

1. **Fetchor 日志** (line 53-54):
   ```python
   log('[fetchor] fetch_addr: 0x{:08x}', pc_reg[0])
   ```
   - 记录每次取指令的地址
   - 用于追踪 PC 的变化

2. **Decoder 日志** (line 85-86):
   ```python
   log('[decoder] fetch_addr: 0x{:08x} ins: 0x{:08x}', fetch_addr, instruction_code)
   ```
   - 记录取到的指令地址和指令内容
   - 可以验证指令是否正确读取

3. **WriteBack 日志** (line 368-371):
   ```python
   with Condition(wb_en == Bits(1)(1)):
       log('[writeback] x{}: 0x{:08x}', rd.bitcast(UInt(5)), rd_data)
   ```
   - 只在 writeback enable 时记录
   - 格式: `[writeback] x<寄存器编号>: 0x<数据>`
   - 匹配 0to100.sh 的 grep 模式: `writeback.*x14` 和 `writeback.*x10`

### 日志格式说明

所有日志都使用 `[module_name]` 前缀便于过滤：
- `[fetchor]` - Fetchor 阶段日志
- `[decoder]` - Decoder 阶段日志
- `[writeback]` - WriteBack 阶段日志（用于验证）

WriteBack 日志格式与 `0to100.sh` 验证脚本兼容：
- Line 9: `grep "writeback.*x14"` 会匹配 `[writeback] x14: 0x...`
- Line 10: `grep "writeback.*x10"` 会匹配 `[writeback] x10: 0x...`

### 验证结果

✅ 日志格式正确，与 0to100.sh 兼容

---

## ckpt-3: 验证脚本检查

**Status**: ✅ 完成
**发现**: test_base.py 中的验证逻辑已经完整，不需要额外修改

---

## ckpt-4: 运行验证 - 发现重大问题

**Status**: ⚠️ 测试失败

### 问题描述

运行测试时发现验证失败：
- Error: `Error Sum! 1912 != 630665`
- 原因：CPU 只执行了一次循环，没有正确跳转

### 根本原因分析

**CPU 实现缺少跳转逻辑！**

检查 `impl/gen_cpu/pipestage.py` 发现：

1. **Fetchor (line 36-37)**: PC 只是简单地每周期 +4
   ```python
   (pc_reg & self)[0] <= pc_reg[0] + UInt(32)(4)
   ```
   **没有任何跳转支持！**

2. **Executor**: 虽然计算了 `adder_result`（可用于跳转目标地址），但：
   - 没有判断是否需要跳转的逻辑
   - 没有将跳转目标地址反馈给 Fetchor

3. **缺失的功能**：
   - Branch 指令的条件判断和跳转
   - JAL/JALR 指令的无条件跳转
   - PC 更新逻辑（PC+4 vs 跳转目标）

### 修复需要

CPU 需要实现完整的控制流逻辑：
1. 在 Executor/MemoryAccessor 中判断是否需要跳转
2. 计算跳转目标地址
3. 将跳转信号和目标地址反馈给 Fetchor
4. Fetchor 根据跳转信号更新 PC

### 待确认

这是一个 CPU 实现的重大缺陷，需要用户确认：
1. 是否继续修复跳转逻辑？
2. 还是这是已知的未完成功能，需要在其他 todo 中处理？

---

## ckpt-5.1: jump_predictor_wrapper 模块创建完成

### 修改文件
- `impl/gen_cpu/downstreams.py`
- `test/sw/test_base.py`
- `impl/gen_cpu/design.md`

### 核心改动
1. 依据 `rules/design/adding.md` 明确 downstream 模块的输入、输出类型以及外部交互约束。
2. 在 `jump_predictor_wrapper` 中引入两态 FSM（`idle` / `cooldown`），分别负责触发跳转与等待流水线恢复，保证每个跳转只处理一次。
3. 覆盖 `AddrPurpose.BR_TARGET / IND_TARGET / J_TARGET`，根据 `cmp_out_used`、`cmp_out` 判定跳转是否成立，并在触发时记录日志。
4. 将 PC RegArray 初始化为 0，避免仿真初期出现 X 值；补充设计文档描述该模块的变量、状态与作用方式。

### 待用户确认
- 请确认新的 FSM 设计与设计文档描述是否满足规则要求，是否允许进入 Step 5.2（Decoder valid 控制）继续实现。

---

## ckpt-5.2: Decoder 跳转检测与 valid 控制

### 修改文件
- `impl/gen_cpu/pipestage.py`

### 核心改动
1. 引入 `jump_inflight` 寄存器跟踪“跳转处理中”状态，结合 `jump_update_done`（已 optional 保护）实现 valid 的暂停与恢复。
2. 将 valid 判定调整为 `base_valid & ~jump_inflight[0]`，确保跳转发射后只停顿一个周期。
3. 将非法指令处理逻辑限定在 `decoder.illegal` 触发时，避免把等待周期误判为非法并提前结束仿真。

### 待用户确认
- 请确认该控制策略符合预期，若 OK 我将继续 Step 5.3（Executor 传递跳转信息）。

---

## ckpt-5.3: Executor 跳转信息输出

### 修改文件
- `impl/gen_cpu/pipestage.py`

### 核心改动
1. 保持 `adder_result` 单一赋值路径，并在 MemoryAccessor / jump_predictor 间共享。
2. 当 `cmp_out_used=1` 时强制比较器使用 `RS1/RS2` 数据源，避免分支比较依赖 ALU 输入选择。
3. 为分支路径加入调试日志，帮助确认 `cmp_out`、`target` 与 `addr_purpose` 匹配。

### 待用户确认
- 若输出接口定义满足预期，我将继续 Step 5.4（Fetchor 接入新的 PC 流）。

---

## ckpt-5.4: Fetchor 接收 jump_predictor 的 PC

### 修改文件
- `impl/gen_cpu/pipestage.py`

### 核心改动
1. 再次确认 Fetchor 仅读取共享 `pc`，不再保留私有自增路径，保证 PC 唯一写入点为 jump_predictor。
2. 补充内存访问调试日志，协助定位跳转后的 load 地址与返回数据是否一致。

### 待用户确认
- 如以上行为与设计预期一致，我会继续 Step 5.5（测试脚本中完成模块连接）。

---

## ckpt-5.5: 测试脚本连接 jump_predictor

### 修改文件
- `test/sw/test_base.py`

### 核心改动
1. 在 `build_cpu()` 中确认 `jump_predictor_wrapper` 的实例化与构建顺序，保证依赖关系正确。
2. 共享 `pc` 与 `jump_update_done` RegArray，并确保 Fetchor/Decoder/jump_predictor 按需求使用。
3. 驱动顺序：WriteBack → Driver → Fetchor → Decoder → regfile_wrapper → Executor → MemoryAccessor → jump_predictor。

### 待用户确认
- 若连接方式无误，我将进行 Step 5.6（运行 `python test/sw/test_base.py` 并验证日志）。

---

## ckpt-5.6: 验证结果

### 运行情况
- 多次运行 `python test/sw/test_base.py`，按照“仅截取末尾 50 行”原则记录关键信息。
- 测试失败：`Error Sum! 339205 != 630665`，说明累加结果仍与参考值不符。

### 根因分析
- 分支与 PC 更新逻辑已正常：`jump_predictor` 日志显示 `PC: 0x00000024 -> 0x00000010`。
- RAW 数据冒险未处理：`addi x15, x15, 0xb8` 刚写回时，下一条 `addi x13, x15, 0x190` 读取到旧的 `x15`=0，使得 `x13` 只等于 `0x190`，循环范围变为 `[0xb8, 0x190)` 共 54 项，导致 sum=339205。

### 建议
- 需要在 Decoder/Executor 层实现最小的 RAW hazard 防护（插入气泡或前递），确保依赖的寄存器在下一条指令读取时已准备好。
