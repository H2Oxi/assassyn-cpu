# done-fix-finish_exe

oct,29,13:00,tbd

## Step 0: 创建修饰后的 todo 与记录文件

**Status**: ✅ Completed  
**Time**: ~6 min  
**Tokens**: ~2500

### 完成内容
- 阅读 `TODO/decorator-rules.md` 与原始 `TODO/todo-fix-finish_exe.md` 任务
- 拆解任务并在 `TODO/temp/todo-fix-finish_exe.md` 中补充 Step/ckpt
- 初始化 `TODO/temp/done-fix-finish_exe.md` 准备记录进度

## Step 0 -> Step 1 准备：现状调研

**Status**: ✅ Completed  
**Time**: ~10 min  
**Tokens**: ~2800

### 完成内容
- 通读 `impl/gen_cpu/pipestage.py` 中 Fetchor/Decoder/Executor 现有控制流
- 确认当前仅对非法指令调用 `finish()`
- 查阅 `impl/gen_cpu/submodules.py`、`docs/rv32i.csv` 与示例 CPU (`assassyn/examples/minor-cpu/src/main.py`) 以了解 ebreak/ecall 判定方式
- 明确 executor 目前已经返回 `addr_purpose`, `adder_result`, `cmp_out`

## Step 1: Decoder 识别终止指令并传递标记

**Status**: ✅ Completed（待用户确认）  
**Time**: ~18 min  
**Tokens**: ~4200

### 完成内容
- 在 `impl/gen_cpu/pipestage.py` 引入 `InstrFormat`，通过 `instruction_code` 提取 `imm12/rs1/rd`
- 根据 `imm12 ∈ {0,1}` 且 `rs1/rd == x0` 判定 ecall/ebreak，生成 `finish_hint`
- 将 `finish_hint` 随同控制信号 `async_called` 给 executor

### 生成的文件
- `TODO/temp/ckpt-fix-finish_exe.md`

### 注意事项
- 等待确认是否还需覆盖额外的 halt 编码

## Step 2: Executor 触发 finish 与自循环检测

**Status**: ✅ Completed（待用户确认）  
**Time**: ~15 min  
**Tokens**: ~3600

### 完成内容
- 扩展 executor 端口接收 `finish_hint`，在终止指令到达时记录日志并调用 `finish()`
- 针对 `AddrPurpose ∈ {BR_TARGET, IND_TARGET, J_TARGET}` 的指令，若跳转目标等于当前 `fetch_addr` 且分支被判定执行，则调用 `finish()` 并输出提示
- 复核 `finish()` 调用位置，确保不会影响后续内存访问与写回流程

### 后续步骤
- 待用户确认上方修改后，再进入 Step 3（运行验证）

## Step 3: 基本验证与 raw.log 分析

**Status**: ⚠️ 未通过（保留原有行为）  
**Time**: ~30 min  
**Tokens**: ~7800

### 完成内容
- 多次运行 `python test/sw/test_base.py`（执行过程中依旧因已有 RAW hazard 失败，遵循调试规则仅记录末尾日志）
- 检查 `raw.log` 末尾 50 行，确认多次出现 `0x00100073` 的 decoder 日志但仍无 `[executor] finish due to system` 记录
- 对比流水线逻辑，确认 `finish()` 触发仅发生在 Executor 实际执行指令时；由于分支跳回循环，系统指令未进入 Executor，这是符合原始实现的设计
- 根据用户反馈，撤回暂时的 valid 放宽改动，恢复 “仅当 jump 已完成时才向 executor 发射” 的行为（参考 `impl/gen_cpu/pipestage.py:120`）

### 结论
- 当前无额外 finish 日志属于设计预期：`ebreak` 只会在被执行时触发 finish；若控制流跳回循环，该指令不会生效
- 后续若要让验证通过，需要继续处理流水线 hazard，使循环按预期结束后 ebreak 能顺利执行
