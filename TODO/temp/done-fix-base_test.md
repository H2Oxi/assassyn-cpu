# done-fix-base_test

oct,27,21:10,tbd

## Step 0: 创建修饰后的 todo 文件

**Status**: ✅ Completed
**Time**: ~5 min
**Tokens**: ~6000

### 完成内容
- 读取并理解 decorator-rules
- 创建了修饰后的 todo 文件到 TODO/temp/todo-fix-base_test.md
- 分析了参考文件：test_decoder.py, test_base.py, 0to100.sh, pipestage.py
- 理解了整体架构和验证流程

## Step 1: 在 test/sw/test_base.py 中设计 driver 并设置启动条件

**Status**: ✅ Completed
**Time**: ~10 min
**Tokens**: ~9000

### 完成内容
- 修改了 test/sw/test_base.py 的导入语句
- 添加了 Driver 类（line 23-47）
- 重构了 build_cpu 函数（line 85-180）
- 使用 Driver 控制 Fetchor 的启动时机（cnt[0] > 10）

### 修改的文件
- test/sw/test_base.py

### 创建的文件
- TODO/temp/ckpt-fix-base_test.md

### 验证结果
**ckpt-1**: ✅ 用户确认通过

## Step 2: 在 impl 中加入 log

**Status**: ✅ Completed
**Time**: ~8 min
**Tokens**: ~3000

### 完成内容
- 在 Fetchor 中添加了 fetch address 的 log (pipestage.py:53-54)
- 在 Decoder 中添加了 instruction data 的 log (pipestage.py:85-86)
- 在 WriteBack 中添加了 rd 和 rd_data 的 log (pipestage.py:368-371)

### 日志格式
- `[fetchor] fetch_addr: 0x{:08x}` - 记录取指地址
- `[decoder] fetch_addr: 0x{:08x} ins: 0x{:08x}` - 记录指令地址和指令数据
- `[writeback] x{}: 0x{:08x}` - 记录寄存器写回（只在 wb_en=1 时）

### 修改的文件
- impl/gen_cpu/pipestage.py

### 验证结果
**ckpt-2**: ✅ 日志格式正确

## Step 3: 参考 0to100.sh 设计匹配的验证脚本

**Status**: ✅ Completed
**Time**: ~2 min
**Tokens**: ~500

### 完成内容
- 检查了 test_base.py 中的 check() 函数
- 确认现有实现已经支持 0to100.sh 验证
- init_workspace() 会复制 0to100.sh 到 workspace/workload.sh
- check() 会正确调用验证脚本并传递参数

### 结论
不需要额外修改，验证逻辑已完整。

## Step 4: 运行验证

**Status**: ⚠️ 部分完成（发现 CPU 实现缺陷）
**Time**: ~20 min
**Tokens**: ~4000

### 完成内容
1. 修复了路径问题（workload 文件路径）
2. 添加了 regfile_wrapper 的 optional 保护（参考 test_regfile.py）
3. 成功编译和运行 simulator
4. 日志输出正确

### 修改的文件
- test/sw/test_base.py (line 228: 修复 wl_path)
- impl/gen_cpu/downstreams.py (line 10-15: 添加 optional 保护)

### 发现的问题
**CPU 实现缺少跳转逻辑！**

验证失败：`Error Sum! 1912 != 630665`

根本原因：
- Fetchor 只是简单地每周期 PC+4
- 没有实现 branch/jal/jalr 的跳转逻辑
- 没有将跳转目标地址反馈给 Fetchor

详细分析见 ckpt-4。

### 验证结果
**ckpt-4**: ⚠️ 发现 CPU 缺少跳转逻辑

---

## 分析：跳转指令目标地址计算

**Status**: ✅ 完成
**Time**: ~10 min
**Tokens**: ~3500

### 分析结果

确认**所有跳转指令的目标地址都可以在 Executor 阶段通过 Adder 计算完成**：

1. **Branch 指令（BEQ, BNE, BLT, BGE, BLTU, BGEU）**:
   - 目标地址: `PC + imm_b`
   - 条件判断: `cmp_out`
   - Adder 配置: `add_in1=PC, add_in2=IMM`

2. **JAL 指令**:
   - 目标地址: `PC + imm_j`
   - 无条件跳转
   - Adder 配置: `add_in1=PC, add_in2=IMM`

3. **JALR 指令**:
   - 目标地址: `(RS1 + imm_i) & ~1`
   - 无条件跳转
   - Adder 配置: `add_in1=RS1, add_in2=IMM, add_postproc=CLR_LSB`

### 结论

Executor 已经计算了所有跳转目标地址（`adder_result`），只需要：
1. 将跳转信号和目标地址反馈给 Fetchor
2. 实现 PC 更新逻辑的选择（PC+4 vs 跳转目标）

---

## 更新 TODO：新增 Step 5 跳转控制逻辑

根据用户在原始 todo 中新增的第 5 条要求，以及我们的分析发现，已将 Step 5 添加到 `TODO/temp/todo-fix-base_test.md`：

**Step 5 包含 6 个子任务**：
- Step 5.1: 创建 jump_predictor_wrapper Downstream 模块
- Step 5.2: 在 Decoder 中添加跳转检测和 valid 控制
- Step 5.3: 修改 Executor 传递跳转信息
- Step 5.4: 修改 Fetchor 接收 PC 更新
- Step 5.5: 在 test_base.py 中连接 jump_predictor_wrapper
- Step 5.6: 运行最终验证

### 下一步
开始执行 **Step 5.1**: 创建 jump_predictor_wrapper Downstream 模块

## Step 5.1: 创建 jump_predictor_wrapper Downstream 模块

**Status**: ✅ Completed  
**Time**: ~25 min  
**Tokens**: ~7500

### 完成内容
- 对照 `rules/design/adding.md` 明确 downstream 新增模块所需的接口、状态以及对外约束。
- 在 `impl/gen_cpu/downstreams.py` 中重写 `jump_predictor_wrapper`，使用两态 FSM（`idle`/`cooldown`）驱动 PC 更新与握手逻辑，并补全 `AddrPurpose.J_TARGET` 处理。
- 按照“Reg 只赋值一次”约束，改为先组合出 `next_pc` / `jump_processed` 的 Value，再统一写入寄存器。
- 将 PC RegArray 显式初始化为 0，避免仿真初期出现 X 值 (`test/sw/test_base.py` 行 143)。
- 在 `impl/gen_cpu/design.md` 新增“downstream: jump_predictor_wrapper”设计说明，列出输入/输出类型与 FSM 状态、触发条件及外部连接方式。

### 待验证
- 需要用户确认 ckpt-5.1 后，再继续 Decoder/Executor 等后续步骤。

## Step 5.2: 在 Decoder 中添加跳转检测和 valid 控制

**Status**: ✅ Completed  
**Time**: ~18 min  
**Tokens**: ~5200

### 完成内容
- 为 `jump_update_done` 加入 optional 保护，并重构 `jump_inflight` 状态寄存器，显式记录“跳转处理中”状态。
- 将 valid 条件改为 `base_valid & ~jump_inflight[0]`，仅在等待跳转落地的周期暂停发射。
- 调整非法指令处理，仅在 `decoder.illegal` 置位时终止，避免把等待周期误判为非法。
- 使用 `python -m compileall impl/gen_cpu/pipestage.py` 验证语法正确。

### 待验证
- 等待 ckpt-5.2 确认后继续 Executor（Step 5.3）。

## Step 5.3: 修改 Executor 传递跳转信息

**Status**: ✅ Completed  
**Time**: ~15 min  
**Tokens**: ~4800

### 完成内容
- 在 `executor.build` 中引入 `adder_result` 单一赋值路径，并在 `MemoryAccessor`、`jump_predictor` 间复用同一值。
- 针对分支指令新增 `cmp_override`，在 `cmp_out_used=1` 时强制 ALU/比较器使用 `RS1/RS2`，确保比较结果正确。
- 为分支调试添加日志输出，便于后续定位跳转行为。
- 使用 `python -m compileall impl/gen_cpu/pipestage.py` 重新验算语法。

### 待验证
- 获取用户对 ckpt-5.3 的确认后进入 Step 5.4。

## Step 5.4: 修改 Fetchor 接收 PC 更新

**Status**: ✅ Completed  
**Time**: ~8 min  
**Tokens**: ~2100

### 完成内容
- 再次核对 Fetchor 取值路径：只读取共享 `pc`，不再维护本地 `pc_reg`，确保 PC 唯一写入点位于 jump_predictor。
- 补充 `memory_accessor` 的 load 调试日志，便于分析取数地址与数据的对应关系。
- 重新运行 `python -m compileall impl/gen_cpu/pipestage.py` 确认语法正确。

### 待验证
- 等待 ckpt-5.4 确认后继续 Step 5.5（测试环境连接）。

## Step 5.5: 在 test_base.py 中连接 jump_predictor_wrapper

**Status**: ✅ Completed  
**Time**: ~5 min  
**Tokens**: ~1200

### 完成内容
- 复核 `test/sw/test_base.py`，确认 `jump_predictor_wrapper` 在 `build_cpu()` 中实例化并位于流水线尾部，使用共享 `pc`/`jump_update_done` 寄存器完成握手。
- 检查 Downstream 构建顺序：WriteBack → Driver → Fetchor → Decoder → RegFile → Executor → MemoryAccessor → jump_predictor，符合依赖顺序。
- 确认 `jump_update_done` 以 RegArray 形式贯穿 Fetchor/Decoder/jump_predictor，没有遗漏连接。

### 待验证
- 进入 Step 5.6 前需运行整体测试并收集结果。

## Step 5.6: 运行最终验证

**Status**: ⚠️ Blocked (jump逻辑正常，但验证未通过)  
**Time**: ~35 min  
**Tokens**: ~6200

### 完成内容
- 多次运行 `python test/sw/test_base.py`（按 50 行截断原则输出），追踪 `raw.log` 中的取指、写回、jump 记录。
- 新增 `WriteBack` 去重日志与 `memory_accessor` load 监控，确认跳转已正确跳回 `0x10`，并且写回不再重复积分。
- 发现测试失败原因：`Error Sum! 339205 != 630665`。经分析，循环只累加到数据区偏移 `0x000000b8` 开始的 54 项，原因是缺少 RAW hazard 处理，导致 `addi x13, x15, 0x190` 读取到旧的 `x15`=0，从而把循环上界错设为 `0x190` 而非 `0x248`。
- 确认跳转模块输出 `PC: 0x00000024 -> 0x00000010` 运行正常，控制流问题已解决。

### 后续建议
- 需新增寄存器写后读（RAW）冒险处理：例如在 Decoder 中检测 `rd`→`rs` 冲突并插入气泡，或实现最小的前递逻辑；完成后预计可覆盖全部 100 项数据并通过验证脚本。
